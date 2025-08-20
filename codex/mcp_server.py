"""
MCP (Model Context Protocol) server for Codex pattern queries.
Allows AI assistants to query patterns via standardized protocol.
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path
from typing import Any

import logfire
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Try to import dependencies, provide fallback if they're missing
try:
    from .ai_query import AIQueryInterface
    from .pattern_extractor import PatternExtractor
    from .unified_database import UnifiedDatabase

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)


# Set up comprehensive logging
def setup_logging():
    """Setup comprehensive logging for debugging."""
    log_dir = Path.home() / ".codex" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Setup file logging
    log_file = log_dir / "mcp_server.log"

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stderr)],
    )

    logger = logging.getLogger("codex-mcp-server")

    # Setup Logfire for comprehensive debugging
    logfire.configure(
        service_name="codex-mcp-server",
        send_to_logfire=False,  # Local logging only
    )
    logger.info("Logfire initialized for comprehensive debugging")

    return logger


logger = setup_logging()

# Create server instance
server = Server("codex-patterns")

# Global database interface
db_interface = None


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for pattern queries."""
    logger.info("🔧 MCP: Listing available tools")

    logfire.info(
        "handle_list_tools called",
        dependencies_available=DEPENDENCIES_AVAILABLE,
        import_error=IMPORT_ERROR if not DEPENDENCIES_AVAILABLE else None,
    )

    tools = [
        types.Tool(
            name="query_patterns",
            description="Search for coding patterns using natural language",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query for patterns (e.g., 'HTTP client', 'error handling')",
                    },
                    "limit": {"type": "number", "description": "Maximum patterns to return", "default": 5},
                    "priority": {
                        "type": "string",
                        "enum": ["MANDATORY", "CRITICAL", "HIGH", "MEDIUM", "LOW", "OPTIONAL"],
                        "description": "Filter by priority level",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_file_context",
            description="Get relevant patterns for a specific file being worked on",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file being worked on (e.g., 'src/api.py', 'tests/test_client.py')",
                    },
                    "max_patterns": {"type": "number", "description": "Maximum patterns to return", "default": 10},
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="explain_pattern",
            description="Get detailed explanation of a specific pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern_name": {
                        "type": "string",
                        "description": "Name of pattern to explain (e.g., 'use-httpx', 'ruff-TRY401')",
                    }
                },
                "required": ["pattern_name"],
            },
        ),
        types.Tool(
            name="validate_code",
            description="Check code snippet against patterns for violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code snippet to validate"},
                    "language": {"type": "string", "description": "Programming language", "default": "python"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="semantic_search",
            description="Search patterns based on coding intent or task",
            inputSchema={
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": "What you want to accomplish (e.g., 'make HTTP requests', 'handle errors', 'write tests')",
                    }
                },
                "required": ["intent"],
            },
        ),
        types.Tool(
            name="import_patterns",
            description="Import patterns from project-init.json files",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to project-init.json file to import"}
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="list_categories",
            description="List available pattern categories",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_stats",
            description="Get pattern database statistics and usage",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]

    logger.info(f"🔧 MCP: Returning {len(tools)} tools")
    logfire.info("tools_listed", tool_count=len(tools), tool_names=[tool.name for tool in tools])

    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls from AI assistants."""
    logger.info(f"🔧 MCP: Tool call received - {name}")

    logfire.info(
        "tool_call_received", tool_name=name, arguments=arguments, dependencies_available=DEPENDENCIES_AVAILABLE
    )

    if not DEPENDENCIES_AVAILABLE:
        error_msg = f"Dependencies not available: {IMPORT_ERROR}"
        logger.error(f"❌ MCP: {error_msg}")
        logfire.error("dependencies_missing", error=IMPORT_ERROR)
        return [types.TextContent(type="text", text=error_msg)]

    global db_interface

    try:
        if db_interface is None:
            logger.info("🔧 MCP: Initializing FTS database")
            db_interface = UnifiedDatabase()
            logfire.info("database_initialized", db_type="UnifiedDatabase")
    except Exception as e:
        error_msg = f"Failed to initialize database: {str(e)}"
        logger.error(f"❌ MCP: {error_msg}")
        logfire.error("database_init_failed", error=str(e), traceback=traceback.format_exc())
        return [types.TextContent(type="text", text=error_msg)]

    try:
        if name == "query_patterns":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            priority = arguments.get("priority")

            # Use FTS database for simple pattern search
            patterns = db_interface.query_patterns(query, limit=limit)

            if not patterns:
                return [types.TextContent(type="text", text=f"No patterns found for query: {query}")]

            # Filter by priority if specified
            if priority:
                patterns = [p for p in patterns if p.get("priority") == priority]

            # Format as markdown for AI consumption
            markdown = f"# Query: {query}\n\n"
            markdown += f"**Found {len(patterns)} patterns**\n\n"

            for pattern in patterns:
                name = pattern.get("name", "Unknown")
                priority_level = pattern.get("priority", "MEDIUM")
                description = pattern.get("description", "")
                detection = pattern.get("detection_pattern", "")
                fix_template = pattern.get("fix_template", "")
                rationale = pattern.get("rationale", "")

                markdown += f"## {name} [{priority_level}]\n"
                markdown += f"- **Description**: {description}\n"
                if rationale:
                    markdown += f"- **Why**: {rationale}\n"
                if detection:
                    markdown += f"- **Detect**: `{detection}`\n"
                if fix_template:
                    markdown += f"- **Fix**: {fix_template}\n"
                markdown += "\n"

            return [types.TextContent(type="text", text=markdown)]

        elif name == "get_file_context":
            file_path = arguments.get("file_path", "")
            max_patterns = arguments.get("max_patterns", 10)

            # Simple context based on file extension
            context = f"# File Context for: {file_path}\n\n"

            if file_path.endswith(".py"):
                patterns = db_interface.query_patterns("python", limit=max_patterns)
            elif file_path.endswith((".js", ".ts")):
                patterns = db_interface.query_patterns("javascript", limit=max_patterns)
            else:
                patterns = db_interface.list_all_patterns()[:max_patterns]

            if patterns:
                context += "**Relevant patterns for this file:**\n\n"
                for pattern in patterns:
                    name = pattern.get("name", "Unknown")
                    description = pattern.get("description", "")
                    context += f"- **{name}**: {description}\n"
            else:
                context += "No specific patterns found for this file type."

            return [types.TextContent(type="text", text=context)]

        elif name == "explain_pattern":
            pattern_name = arguments.get("pattern_name", "")

            # Search for the specific pattern
            patterns = db_interface.query_patterns(pattern_name, limit=1)

            if not patterns:
                return [types.TextContent(type="text", text=f"Pattern '{pattern_name}' not found in database.")]

            pattern = patterns[0]
            name = pattern.get("name", "Unknown")
            priority = pattern.get("priority", "MEDIUM")
            category = pattern.get("category", "general")
            description = pattern.get("description", "")
            rationale = pattern.get("rationale", "")
            detection = pattern.get("detection_pattern", "")
            fix_template = pattern.get("fix_template", "")
            good_example = pattern.get("example_good", "")
            bad_example = pattern.get("example_bad", "")

            markdown = f"# {name} [{priority}]\n\n"
            markdown += f"**Category**: {category}\n\n"
            markdown += f"**Description**: {description}\n\n"

            if rationale:
                markdown += f"**Rationale**: {rationale}\n\n"

            if detection:
                markdown += f"**Detection Pattern**: `{detection}`\n\n"

            if fix_template:
                markdown += f"**Fix Template**: `{fix_template}`\n\n"

            if good_example:
                markdown += f"**Good Example**:\n```\n{good_example}\n```\n\n"

            if bad_example:
                markdown += f"**Bad Example**:\n```\n{bad_example}\n```\n\n"

            return [types.TextContent(type="text", text=markdown)]

        elif name == "validate_code":
            code = arguments.get("code", "")
            language = arguments.get("language", "python")

            # Simple validation using pattern matching
            violations = []
            patterns = db_interface.query_patterns(language, limit=50)

            # Basic pattern matching against code
            for pattern in patterns:
                detection_rules = pattern.get("detection_rules", {})
                if isinstance(detection_rules, dict):
                    rules = detection_rules.get("rules", [])
                    for rule in rules:
                        if rule in code:
                            violations.append(
                                {
                                    "pattern": pattern.get("name", "Unknown"),
                                    "priority": pattern.get("priority", "MEDIUM"),
                                    "line": 1,  # Simple implementation
                                    "issue": f"Found pattern: {rule}",
                                    "fix": pattern.get("fix_template", "No fix available"),
                                }
                            )

            result = {
                "language": language,
                "score": 1.0 if not violations else 0.5,
                "is_compliant": len(violations) == 0,
                "violations": violations,
            }

            markdown = "# Code Validation Results\n\n"
            markdown += f"**Language**: {result['language']}\n"
            markdown += f"**Score**: {result['score']:.2f}\n"
            markdown += f"**Compliant**: {'✅ Yes' if result['is_compliant'] else '❌ No'}\n\n"

            if result["violations"]:
                markdown += f"## Found {len(result['violations'])} violation(s):\n\n"

                for i, violation in enumerate(result["violations"], 1):
                    markdown += f"### {i}. {violation['pattern']} [{violation['priority']}]\n"
                    markdown += f"- **Line {violation['line']}**: {violation['issue']}\n"
                    markdown += f"- **Fix**: {violation['fix']}\n\n"
            else:
                markdown += "✅ **No violations found!**\n"

            return [types.TextContent(type="text", text=markdown)]

        elif name == "semantic_search":
            intent = arguments.get("intent", "")

            # Simple semantic search using keyword matching
            patterns = db_interface.query_patterns(intent, limit=10)

            result = {
                "intent": intent,
                "query_used": intent,
                "summary": f"Found {len(patterns)} patterns related to '{intent}'",
                "patterns": [
                    {
                        "name": p.get("name", "Unknown"),
                        "priority": p.get("priority", "MEDIUM"),
                        "rule": p.get("description", ""),
                        "fix": p.get("fix_template", ""),
                        "why": p.get("rationale", ""),
                    }
                    for p in patterns
                ],
            }

            markdown = f"# Intent: {result['intent']}\n\n"
            markdown += f"**Query Used**: {result['query_used']}\n\n"
            markdown += f"**Summary**: {result['summary']}\n\n"

            for pattern in result["patterns"]:
                markdown += f"## {pattern['name']} [{pattern['priority']}]\n"
                markdown += f"- **Rule**: {pattern['rule']}\n"
                if pattern["fix"]:
                    markdown += f"- **Fix**: {pattern['fix']}\n"
                if pattern["why"]:
                    markdown += f"- **Why**: {pattern['why']}\n"
                markdown += "\n"

            return [types.TextContent(type="text", text=markdown)]

        elif name == "import_patterns":
            file_path = arguments.get("file_path", "")

            try:
                extractor = PatternExtractor()
                patterns = extractor.extract_from_project_init(file_path)

                db = UnifiedDatabase()
                imported_count = 0
                for pattern in patterns:
                    db.add_pattern(pattern)
                    imported_count += 1

                return [
                    types.TextContent(
                        type="text", text=f"✅ Successfully imported {imported_count} patterns from {file_path}"
                    )
                ]

            except Exception as e:
                return [types.TextContent(type="text", text=f"❌ Error importing patterns: {str(e)}")]

        elif name == "list_categories":
            db = UnifiedDatabase()

            # Get unique categories from database
            patterns = db.list_all_patterns()
            categories = list(set(p["category"] for p in patterns))
            categories.sort()

            markdown = "# Available Pattern Categories\n\n"
            for category in categories:
                count = sum(1 for p in patterns if p["category"] == category)
                markdown += f"- **{category}**: {count} patterns\n"

            return [types.TextContent(type="text", text=markdown)]

        elif name == "get_stats":
            # Get basic statistics from database
            patterns = db_interface.list_all_patterns()

            stats = {
                "total_patterns": len(patterns),
                "most_used": [],  # Not implemented yet
                "by_assistant": [],  # Not implemented yet
            }

            markdown = "# Pattern Database Statistics\n\n"
            markdown += f"**Total Patterns**: {stats['total_patterns']}\n\n"

            if stats["most_used"]:
                markdown += "## Most Used Patterns\n\n"
                for pattern in stats["most_used"][:5]:
                    markdown += f"- **{pattern['name']}** ({pattern['category']}) - {pattern['usage_count']} uses\n"
                markdown += "\n"

            if stats["by_assistant"]:
                markdown += "## Usage by AI Assistant\n\n"
                for assistant in stats["by_assistant"]:
                    markdown += f"- **{assistant['ai_assistant']}**: {assistant['count']} queries\n"

            return [types.TextContent(type="text", text=markdown)]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def main():
    """Run the MCP server."""
    logger.info("🚀 Starting Codex MCP Server")

    logfire.info(
        "mcp_server_starting",
        dependencies_available=DEPENDENCIES_AVAILABLE,
        server_name="codex-patterns",
        server_version="1.0.0",
    )

    if not DEPENDENCIES_AVAILABLE:
        error_msg = f"Dependencies not available: {IMPORT_ERROR}"
        logger.error(f"❌ {error_msg}")
        logger.error("Run: uv add pydantic sqlmodel rich typer")
        logfire.error("startup_failed_dependencies", error=IMPORT_ERROR)
        return

    try:
        # Setup database
        logger.info("🔧 Initializing database interface")
        global db_interface
        db_interface = UnifiedDatabase()
        logfire.info("database_setup_complete")

        # Run the server using stdio transport
        logger.info("🔧 Starting MCP stdio server")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logfire.info("stdio_server_started")

            logger.info("🔧 Running MCP server with capabilities")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="codex-patterns",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        error_msg = f"MCP Server failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logfire.error("mcp_server_failed", error=str(e), traceback=traceback.format_exc())
        raise


def run_mcp_server():
    """Entry point for running MCP server."""
    logger.info("Starting Codex MCP Server...")
    asyncio.run(main())


if __name__ == "__main__":
    run_mcp_server()

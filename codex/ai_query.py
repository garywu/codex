"""
AI-friendly query interface for pattern database.
"""

from pathlib import Path
from typing import Any

from .settings import settings
from .unified_database import UnifiedDatabase


class AIQueryInterface:
    """Interface for AI assistants to query patterns efficiently."""

    def __init__(self, db_path: Path | None = None):
        """Initialize with database path from settings."""
        if db_path is None:
            # Use path from settings - single source of truth!
            db_path = settings.database_path

        self.db = UnifiedDatabase(db_path)

    def query_patterns(self, query: str, limit: int = 5, format: str = "ai") -> dict[str, Any]:
        """
        Query patterns with natural language.

        Args:
            query: Natural language query
            limit: Maximum patterns to return
            format: "ai" for AI-friendly, "human" for human-readable

        Returns:
            Dictionary with patterns and metadata
        """
        results = self.db.query_patterns(query, limit)

        if format == "ai":
            return self._format_for_ai(results, query)
        else:
            return self._format_for_human(results, query)

    def get_context_for_file(self, file_path: str, max_patterns: int = 10) -> str:
        """
        Get relevant patterns for a specific file.
        Returns markdown formatted for AI consumption.
        """
        # Determine relevant categories based on file
        categories = self._get_categories_for_file(file_path)

        if not categories:
            return f"# No specific patterns for {file_path}\n"

        patterns = []
        for category in categories:
            patterns.extend(self.db.get_patterns_by_category(category))

        # Limit and sort by priority
        patterns = sorted(patterns, key=lambda p: self._priority_score(p["priority"]))
        patterns = patterns[:max_patterns]

        return self._format_file_context(file_path, patterns)

    def semantic_search(self, intent: str) -> dict[str, Any]:
        """
        Semantic search based on coding intent.

        Args:
            intent: What the developer wants to do

        Returns:
            Relevant patterns with summary
        """
        # Map intents to search queries
        query = self._intent_to_query(intent)
        patterns = self.db.query_patterns(query, limit=3)

        return {
            "intent": intent,
            "query_used": query,
            "patterns": [self._simplify_pattern(p) for p in patterns],
            "summary": self._generate_summary(patterns),
        }

    def explain_pattern(self, pattern_name: str) -> dict[str, Any] | None:
        """Get detailed explanation of a specific pattern."""
        pattern = self.db.get_pattern_by_name(pattern_name)

        if not pattern:
            return None

        return {
            "name": pattern["name"],
            "category": pattern["category"],
            "priority": pattern["priority"],
            "description": pattern["description"],
            "why": pattern["rationale"],
            "detect": pattern["detection_pattern"],
            "fix": pattern["fix_template"],
            "good_example": pattern["example_good"],
            "bad_example": pattern["example_bad"],
            "replaces": pattern["replaces"],
        }

    def validate_code_snippet(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Validate code snippet against patterns.

        Args:
            code: Code to validate
            language: Programming language

        Returns:
            Validation results with violations
        """
        violations = []

        # Simple pattern matching for common violations
        if "requests." in code:
            pattern = self.db.get_pattern_by_name("use-httpx")
            if pattern:
                violations.append(
                    {
                        "pattern": "use-httpx",
                        "line": self._find_line_number(code, "requests."),
                        "issue": "Use httpx instead of requests",
                        "fix": "Replace requests with httpx.AsyncClient()",
                        "priority": "HIGH",
                    }
                )

        if "pip install" in code:
            pattern = self.db.get_pattern_by_name("use-uv-not-pip")
            if pattern:
                violations.append(
                    {
                        "pattern": "use-uv-not-pip",
                        "line": self._find_line_number(code, "pip install"),
                        "issue": "Use uv instead of pip",
                        "fix": "uv add {package}",
                        "priority": "MANDATORY",
                    }
                )

        if "logging.exception(" in code and "{e}" in code:
            violations.append(
                {
                    "pattern": "ruff-TRY401",
                    "line": self._find_line_number(code, "logging.exception("),
                    "issue": "Redundant exception object in logging.exception call",
                    "fix": "Remove {e} from logging.exception() call",
                    "priority": "HIGH",
                }
            )

        return {
            "code": code,
            "language": language,
            "violations": violations,
            "is_compliant": len(violations) == 0,
            "score": max(0, 1.0 - (len(violations) * 0.2)),
        }

    def get_pattern_statistics(self) -> dict[str, Any]:
        """Get pattern usage statistics."""
        return self.db.get_usage_stats()

    def _format_for_ai(self, results: list[dict], query: str) -> dict[str, Any]:
        """Format results for AI consumption."""
        patterns = []
        for result in results:
            pattern = {
                "name": result["name"],
                "category": result["category"],
                "priority": result["priority"],
                "rule": result["description"],
                "why": result["rationale"],
                "detect": result["detection_pattern"],
                "fix": result["fix_template"],
                "match": result.get("match_context", ""),
            }

            # Only include examples if they're concise
            if result["example_good"] and len(result["example_good"]) < 200:
                pattern["good_example"] = result["example_good"]
            if result["example_bad"] and len(result["example_bad"]) < 200:
                pattern["bad_example"] = result["example_bad"]

            patterns.append(pattern)

        return {
            "query": query,
            "total_found": len(results),
            "patterns": patterns,
            "summary": self._generate_summary(results),
        }

    def _format_for_human(self, results: list[dict], query: str) -> dict[str, Any]:
        """Format results for human consumption."""
        return {"query": query, "total_found": len(results), "patterns": results}

    def _format_file_context(self, file_path: str, patterns: list[dict]) -> str:
        """Format patterns as markdown for file context."""
        output = f"# Patterns for {file_path}\n\n"

        current_priority = None
        for pattern in patterns:
            if pattern["priority"] != current_priority:
                current_priority = pattern["priority"]
                output += f"\n## {current_priority} Patterns\n\n"

            output += f"### {pattern['name']}\n"
            output += f"- **Rule**: {pattern['description']}\n"
            if pattern["rationale"]:
                output += f"- **Why**: {pattern['rationale']}\n"
            if pattern["detection_pattern"]:
                output += f"- **Detect**: `{pattern['detection_pattern']}`\n"
            if pattern["fix_template"]:
                output += f"- **Fix**: `{pattern['fix_template']}`\n"
            output += "\n"

        return output

    def _get_categories_for_file(self, file_path: str) -> list[str]:
        """Determine relevant pattern categories for a file."""
        categories = []
        file_lower = file_path.lower()

        # Always include core categories
        categories.extend(["package_management", "quality_tools"])

        if ".py" in file_path:
            categories.extend(["core_libraries", "ruff_errors", "exception_handling"])

        if "test" in file_lower:
            categories.extend(["testing", "dependency_injection"])

        if "api" in file_lower or "endpoint" in file_lower:
            categories.extend(["api_design", "core_libraries"])

        if "cli" in file_lower or "command" in file_lower:
            categories.extend(["cli_design"])

        if "database" in file_lower or "model" in file_lower:
            categories.extend(["database"])

        return categories

    def _intent_to_query(self, intent: str) -> str:
        """Convert intent to search query."""
        intent_lower = intent.lower()

        intent_mappings = {
            "http": "http client async httpx aiohttp",
            "request": "http client async httpx aiohttp",
            "error": "exception error logging try catch handling",
            "test": "test pytest coverage mock dependency injection",
            "dependency injection": "dependency injection DI testability constructor",
            "package": "uv pip poetry package install management",
            "lint": "ruff mypy lint format check quality",
            "async": "async await asyncio aiohttp httpx",
            "database": "sqlmodel sqlite database orm aiosqlite",
            "api": "fastapi api rest http endpoint pydantic",
            "security": "security vulnerability SQL injection eval pickle",
            "logging": "logging exception error handling",
        }

        for key, search_terms in intent_mappings.items():
            if key in intent_lower:
                return search_terms

        # Fallback to original intent
        return intent

    def _simplify_pattern(self, pattern: dict) -> dict[str, Any]:
        """Simplify pattern for AI consumption."""
        return {
            "name": pattern["name"],
            "priority": pattern["priority"],
            "rule": pattern["description"],
            "fix": pattern["fix_template"],
            "why": pattern["rationale"],
        }

    def _generate_summary(self, patterns: list[dict]) -> str:
        """Generate summary for AI consumption."""
        if not patterns:
            return "No patterns found for this query."

        mandatory = [p for p in patterns if p["priority"] in ["MANDATORY", "CRITICAL"]]
        if mandatory:
            return f"MUST use: {', '.join([p['name'] for p in mandatory])}"

        high_priority = [p for p in patterns if p["priority"] == "HIGH"]
        if high_priority:
            return f"Recommended: {', '.join([p['name'] for p in high_priority])}"

        return f"Consider: {', '.join([p['name'] for p in patterns[:2]])}"

    def _priority_score(self, priority: str) -> int:
        """Convert priority to numeric score for sorting."""
        scores = {"MANDATORY": 1, "CRITICAL": 2, "HIGH": 3, "MEDIUM": 4, "LOW": 5, "OPTIONAL": 6}
        return scores.get(priority, 7)

    def _find_line_number(self, code: str, search_text: str) -> int:
        """Find line number of text in code."""
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 1

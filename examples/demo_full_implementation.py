#!/usr/bin/env python3
"""
Full demonstration of the new Codex AI pattern query system.
This shows the complete implementation working end-to-end.
"""

import sqlite3
from pathlib import Path


# Copy of the core FTS implementation for demonstration
class FTSPattern:
    def __init__(self, name, category, priority, description, **kwargs):
        self.name = name
        self.category = category
        self.priority = priority
        self.description = description
        self.detection_pattern = kwargs.get("detection_pattern", "")
        self.fix_template = kwargs.get("fix_template", "")
        self.rationale = kwargs.get("rationale", "")
        self.example_good = kwargs.get("example_good", "")
        self.example_bad = kwargs.get("example_bad", "")
        self.replaces = kwargs.get("replaces", "")
        self.source_file = kwargs.get("source_file", "")
        self.full_context = kwargs.get("full_context", "")


class DemoFTSDatabase:
    def __init__(self, db_path="demo_patterns.db"):
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS patterns")
        cursor.execute("DROP TABLE IF EXISTS patterns_fts")

        cursor.execute("""
            CREATE TABLE patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                priority TEXT,
                description TEXT,
                detection_pattern TEXT,
                fix_template TEXT,
                rationale TEXT,
                example_good TEXT,
                example_bad TEXT,
                replaces TEXT,
                source_file TEXT,
                full_context TEXT
            )
        """)

        cursor.execute("""
            CREATE VIRTUAL TABLE patterns_fts USING fts5(
                name, category, description, rationale,
                detection_pattern, fix_template, example_good,
                example_bad, full_context,
                content=patterns, content_rowid=id
            )
        """)

        cursor.execute("""
            CREATE TRIGGER patterns_ai AFTER INSERT ON patterns BEGIN
                INSERT INTO patterns_fts(rowid, name, category, description, rationale,
                                        detection_pattern, fix_template, example_good,
                                        example_bad, full_context)
                VALUES (new.id, new.name, new.category, new.description, new.rationale,
                       new.detection_pattern, new.fix_template, new.example_good,
                       new.example_bad, new.full_context);
            END
        """)

        conn.commit()
        conn.close()

    def add_pattern(self, pattern):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO patterns (
                name, category, priority, description, detection_pattern,
                fix_template, rationale, example_good, example_bad,
                replaces, source_file, full_context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                pattern.name,
                pattern.category,
                pattern.priority,
                pattern.description,
                pattern.detection_pattern,
                pattern.fix_template,
                pattern.rationale,
                pattern.example_good,
                pattern.example_bad,
                pattern.replaces,
                pattern.source_file,
                pattern.full_context,
            ),
        )

        conn.commit()
        conn.close()

    def query_patterns(self, query, limit=5):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                p.name, p.category, p.priority, p.description,
                p.detection_pattern, p.fix_template, p.rationale,
                p.example_good, p.example_bad,
                snippet(patterns_fts, -1, '→', '←', '...', 20) as match_context,
                bm25(patterns_fts) as score
            FROM patterns p
            JOIN patterns_fts ON p.id = patterns_fts.rowid
            WHERE patterns_fts MATCH ?
            ORDER BY bm25(patterns_fts)
            LIMIT ?
        """,
            (query, limit),
        )

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results


class DemoPatternExtractor:
    def extract_sample_patterns(self):
        """Extract sample patterns similar to project-init.json."""
        return [
            FTSPattern(
                name="use-uv-not-pip",
                category="package_management",
                priority="MANDATORY",
                description="ALWAYS use UV for Python package management - NOT pip, poetry, or conda",
                detection_pattern="pip install|poetry add|conda install|pipenv install",
                fix_template="uv add {package}",
                rationale="UV is faster, more reliable, and handles dependency resolution better than pip/poetry",
                example_good="uv add httpx\nuv sync\nuv run pytest",
                example_bad="pip install httpx\npoetry add httpx\nconda install httpx",
                replaces="pip, poetry, pipenv, conda",
                source_file="project-init.json",
            ),
            FTSPattern(
                name="use-httpx",
                category="core_libraries",
                priority="HIGH",
                description="Use httpx instead of requests for async HTTP client",
                detection_pattern="import requests|requests.get|requests.post",
                fix_template="uv add httpx && replace with httpx.AsyncClient()",
                rationale="httpx provides async support, connection pooling, HTTP/2, and better performance",
                example_good="async with httpx.AsyncClient() as client:\n    response = await client.get(url)",
                example_bad="import requests\nresponse = requests.get(url)",
                replaces="requests",
                source_file="project-init.json",
            ),
            FTSPattern(
                name="ruff-TRY401",
                category="ruff_errors",
                priority="HIGH",
                description="Redundant exception object in logging.exception call",
                detection_pattern="logging.exception.*{.*}",
                fix_template="Remove exception variable from logging.exception() call",
                rationale="logging.exception() automatically includes exception details, so adding {e} is redundant",
                example_good='except Exception:\n    logging.exception("Operation failed")',
                example_bad='except Exception as e:\n    logging.exception(f"Operation failed: {e}")',
                replaces="",
                source_file="project-init.json",
            ),
            FTSPattern(
                name="dependency-injection-constructor",
                category="dependency_injection",
                priority="MANDATORY",
                description="Constructor injection for all services",
                detection_pattern="",
                fix_template="Pass dependencies via constructor parameters",
                rationale="Required for testability and clean architecture - allows easy mocking and testing",
                example_good="def __init__(self, database: Database, logger: Logger):\n    self.db = database\n    self.logger = logger",
                example_bad="def __init__(self):\n    self.db = Database()  # Hard dependency\n    self.logger = Logger()",
                replaces="",
                source_file="project-init-updated.json",
            ),
            FTSPattern(
                name="use-pydantic-basemodel",
                category="pydantic_usage",
                priority="HIGH",
                description="Use Pydantic BaseModel for API request/response models",
                detection_pattern="@dataclass|dataclasses.dataclass",
                fix_template="Replace dataclass with Pydantic BaseModel for API models",
                rationale="Better FastAPI integration, automatic validation, JSON serialization with model_dump()",
                example_good="class UserModel(BaseModel):\n    name: str\n    email: EmailStr",
                example_bad="@dataclass\nclass UserModel:\n    name: str\n    email: str",
                replaces="dataclass for API models",
                source_file="project-init.json",
            ),
            FTSPattern(
                name="exception-chaining",
                category="exception_handling",
                priority="HIGH",
                description="Chain exceptions to preserve original error context",
                detection_pattern="raise.*Exception.*(?!from)",
                fix_template="Add 'from e' to preserve exception chain",
                rationale="Preserves original exception context for debugging",
                example_good="except ValueError as e:\n    raise CustomError('Invalid input') from e",
                example_bad="except ValueError:\n    raise CustomError('Invalid input')",
                replaces="",
                source_file="project-init.json",
            ),
        ]


class DemoAIQueryInterface:
    def __init__(self, db):
        self.db = db

    def query_patterns(self, query, limit=5, format="ai"):
        results = self.db.query_patterns(query, limit)

        if format == "ai":
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

        return {"query": query, "patterns": results}

    def semantic_search(self, intent):
        query = self._intent_to_query(intent)
        patterns = self.db.query_patterns(query, limit=3)

        return {
            "intent": intent,
            "query_used": query,
            "patterns": [self._simplify_pattern(p) for p in patterns],
            "summary": self._generate_summary(patterns),
        }

    def get_context_for_file(self, file_path):
        categories = self._get_categories_for_file(file_path)

        # For demo, simulate getting patterns by category
        all_patterns = []
        for category in categories[:3]:  # Limit for demo
            results = self.db.query_patterns(category, limit=3)
            all_patterns.extend(results)

        # Format as markdown
        output = f"# Patterns for {file_path}\n\n"

        for pattern in all_patterns[:5]:  # Limit for demo
            output += f"## {pattern['name']} [{pattern['priority']}]\n"
            output += f"- **Rule**: {pattern['description']}\n"
            if pattern["rationale"]:
                output += f"- **Why**: {pattern['rationale']}\n"
            if pattern["fix_template"]:
                output += f"- **Fix**: {pattern['fix_template']}\n"
            output += "\n"

        return output

    def validate_code_snippet(self, code):
        violations = []

        if "requests." in code:
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
            violations.append(
                {
                    "pattern": "use-uv-not-pip",
                    "line": self._find_line_number(code, "pip install"),
                    "issue": "Use uv instead of pip",
                    "fix": "uv add {package}",
                    "priority": "MANDATORY",
                }
            )

        if "logging.exception(" in code and "{" in code:
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
            "violations": violations,
            "is_compliant": len(violations) == 0,
            "score": max(0, 1.0 - (len(violations) * 0.2)),
        }

    def _generate_summary(self, patterns):
        if not patterns:
            return "No patterns found for this query."

        mandatory = [p for p in patterns if p["priority"] in ["MANDATORY", "CRITICAL"]]
        if mandatory:
            return f"MUST use: {', '.join([p['name'] for p in mandatory])}"

        high_priority = [p for p in patterns if p["priority"] == "HIGH"]
        if high_priority:
            return f"Recommended: {', '.join([p['name'] for p in high_priority])}"

        return f"Consider: {', '.join([p['name'] for p in patterns[:2]])}"

    def _intent_to_query(self, intent):
        intent_lower = intent.lower()
        mappings = {
            "http": "http client async httpx",
            "request": "http client async httpx",
            "error": "exception error logging try catch handling",
            "test": "test pytest coverage mock dependency injection",
            "package": "uv pip poetry package install management",
            "dependency": "dependency injection DI testability constructor",
            "validation": "pydantic basemodel validation",
            "api": "pydantic basemodel api model",
        }

        for key, search_terms in mappings.items():
            if key in intent_lower:
                return search_terms

        return intent

    def _simplify_pattern(self, pattern):
        return {
            "name": pattern["name"],
            "priority": pattern["priority"],
            "rule": pattern["description"],
            "fix": pattern["fix_template"],
            "why": pattern["rationale"],
        }

    def _get_categories_for_file(self, file_path):
        categories = ["package_management", "core_libraries"]
        file_lower = file_path.lower()

        if "test" in file_lower:
            categories.extend(["dependency_injection", "testing"])
        if "api" in file_lower:
            categories.extend(["pydantic_usage", "api_design"])
        if ".py" in file_path:
            categories.extend(["ruff_errors", "exception_handling"])

        return categories

    def _find_line_number(self, code, search_text):
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 1


def demonstrate_complete_system():
    """Demonstrate the complete AI pattern query system."""
    print("🚀 CODEX AI PATTERN QUERY SYSTEM - COMPLETE DEMONSTRATION")
    print("=" * 80)

    # 1. Initialize system
    print("\n1. 📥 INITIALIZING SYSTEM")
    print("-" * 40)

    db = DemoFTSDatabase()
    extractor = DemoPatternExtractor()
    ai_query = DemoAIQueryInterface(db)

    # Import patterns
    patterns = extractor.extract_sample_patterns()
    for pattern in patterns:
        db.add_pattern(pattern)

    print(f"✅ Imported {len(patterns)} patterns into FTS database")
    print("✅ AI query interface ready")

    # 2. Demonstrate CLI-style queries
    print("\n2. 🔍 CLI QUERY COMMANDS")
    print("-" * 40)

    cli_queries = [
        ("HTTP client", "AI wants to make HTTP requests"),
        ("package management", "AI needs to install dependencies"),
        ("dependency injection", "AI implementing clean architecture"),
        ("logging exception", "AI got ruff error TRY401"),
    ]

    for query, description in cli_queries:
        print(f"\n📝 {description}")
        print(f"Command: codex query '{query}'")

        result = ai_query.query_patterns(query, limit=2, format="ai")
        print(f"Summary: {result['summary']}")

        for pattern in result["patterns"]:
            print(f"  • {pattern['name']} [{pattern['priority']}]: {pattern['rule']}")
            if pattern["fix"]:
                print(f"    Fix: {pattern['fix']}")

    # 3. Demonstrate context generation
    print("\n3. 📄 FILE CONTEXT GENERATION")
    print("-" * 40)

    test_files = ["src/api/endpoints.py", "tests/test_client.py", "src/services/database.py"]

    for file_path in test_files:
        print(f"\n📁 Context for: {file_path}")
        print(f"Command: codex context --file {file_path}")

        context = ai_query.get_context_for_file(file_path)
        lines = context.split("\n")
        print(f"Generated {len([l for l in lines if l.startswith('##')])} pattern sections")
        print("Preview:", lines[2][:60] + "..." if len(lines) > 2 else "")

    # 4. Demonstrate semantic search
    print("\n4. 🎯 SEMANTIC INTENT SEARCH")
    print("-" * 40)

    intents = [
        "I want to make HTTP requests to an API",
        "I need to handle errors properly",
        "I want to install a new package",
        "I need to make my code testable",
    ]

    for intent in intents:
        print(f"\n🤔 Intent: '{intent}'")
        print(f"Command: codex context --intent '{intent}'")

        result = ai_query.semantic_search(intent)
        print(f"Query used: '{result['query_used']}'")
        print(f"Summary: {result['summary']}")

    # 5. Demonstrate code validation
    print("\n5. ✅ CODE VALIDATION")
    print("-" * 40)

    test_codes = [
        {
            "description": "Bad HTTP client code",
            "code": """import requests
response = requests.get("https://api.example.com")
print(response.json())""",
        },
        {
            "description": "Bad package installation",
            "code": """# Install dependency
# pip install httpx
import httpx""",
        },
        {
            "description": "Bad exception logging",
            "code": """try:
    risky_operation()
except Exception as e:
    logging.exception(f"Error occurred: {e}")""",
        },
    ]

    for test in test_codes:
        print(f"\n🔍 Validating: {test['description']}")
        print("Command: codex validate --code '...'")

        result = ai_query.validate_code_snippet(test["code"])
        print(f"Score: {result['score']:.2f}")
        print(f"Compliant: {'✅' if result['is_compliant'] else '❌'}")

        for violation in result["violations"]:
            print(f"  • Line {violation['line']}: {violation['issue']} [{violation['priority']}]")
            print(f"    Fix: {violation['fix']}")

    # 6. Demonstrate MCP tool calls (simulated)
    print("\n6. 🤖 MCP SERVER TOOL CALLS (Simulated)")
    print("-" * 40)

    mcp_calls = [
        {
            "tool": "query_patterns",
            "args": {"query": "HTTP client", "limit": 2},
            "description": "AI assistant queries for HTTP patterns",
        },
        {
            "tool": "get_file_context",
            "args": {"file_path": "src/api.py"},
            "description": "AI gets context while editing file",
        },
        {
            "tool": "validate_code",
            "args": {"code": "import requests\nrequests.get(url)"},
            "description": "AI validates generated code",
        },
    ]

    for call in mcp_calls:
        print(f"\n🔧 {call['description']}")
        print(f"MCP Call: {call['tool']}({call['args']})")

        if call["tool"] == "query_patterns":
            result = ai_query.query_patterns(call["args"]["query"], call["args"]["limit"])
            print(f"Returned {len(result['patterns'])} patterns")
        elif call["tool"] == "get_file_context":
            context = ai_query.get_context_for_file(call["args"]["file_path"])
            print(f"Returned {len(context)} characters of context")
        elif call["tool"] == "validate_code":
            result = ai_query.validate_code_snippet(call["args"]["code"])
            print(f"Found {len(result['violations'])} violations")

    # 7. Show performance metrics
    print("\n7. 📊 PERFORMANCE METRICS")
    print("-" * 40)

    import os
    import time

    db_size = os.path.getsize("demo_patterns.db")
    print(f"Database size: {db_size:,} bytes ({db_size/1024:.1f} KB)")
    print(f"Patterns stored: {len(patterns)}")
    print(f"Bytes per pattern: {db_size/len(patterns):.0f}")

    # Test query performance
    test_queries = ["HTTP client", "dependency injection", "ruff errors"]

    print("\nQuery Performance:")
    for query in test_queries:
        start = time.time()
        results = db.query_patterns(query, limit=5)
        elapsed = (time.time() - start) * 1000
        print(f"  '{query}': {len(results)} results in {elapsed:.2f}ms")

    print("\n✅ DEMONSTRATION COMPLETE!")
    print("=" * 80)
    print("\nKey Benefits Demonstrated:")
    print("• 🔍 Natural language pattern queries (<1ms)")
    print("• 📄 File-specific context generation")
    print("• 🎯 Intent-based semantic search")
    print("• ✅ Real-time code validation")
    print("• 🤖 MCP server integration for AI assistants")
    print("• 📊 Efficient SQLite FTS storage")
    print("• 🚀 CLI and API interfaces")

    print(f"\nDatabase available at: {Path('demo_patterns.db').absolute()}")


if __name__ == "__main__":
    demonstrate_complete_system()

#!/usr/bin/env python3
"""
AI-Friendly Query Interface for Pattern Database
Shows how AI assistants can query patterns efficiently
"""

import sqlite3
from typing import Any


class PatternQueryInterface:
    def __init__(self, db_path: str = "patterns_fts.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

    def query_patterns(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Natural language query for patterns
        Returns simplified, AI-readable results
        """
        cursor = self.conn.cursor()

        # Clean query for FTS5
        fts_query = query.replace(".", " ")

        cursor.execute(
            """
            SELECT
                p.name,
                p.category,
                p.priority,
                p.description,
                p.detection_pattern,
                p.fix_template,
                p.rationale,
                p.example_good,
                p.example_bad,
                snippet(patterns_fts, 8, '→', '←', '...', 20) as match_context
            FROM patterns p
            JOIN patterns_fts ON p.id = patterns_fts.rowid
            WHERE patterns_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """,
            (fts_query, limit),
        )

        results = []
        for row in cursor.fetchall():
            pattern = {
                "name": row["name"],
                "category": row["category"],
                "priority": row["priority"],
                "rule": row["description"],
                "why": row["rationale"],
                "detect": row["detection_pattern"],
                "fix": row["fix_template"],
                "match": row["match_context"],
            }

            # Only include examples if they exist and are useful
            if row["example_good"] and len(row["example_good"]) < 200:
                pattern["good_example"] = row["example_good"]
            if row["example_bad"] and len(row["example_bad"]) < 200:
                pattern["bad_example"] = row["example_bad"]

            results.append(pattern)

        return results

    def get_context_for_file(self, file_path: str) -> str:
        """
        Get relevant patterns for a specific file type
        Returns markdown formatted for AI consumption
        """
        # Determine relevant categories based on file
        categories = []
        if ".py" in file_path:
            categories = ["package_management", "core_libraries", "quality_tools", "ruff_errors"]
        elif "test" in file_path.lower():
            categories.append("testing")
        elif "api" in file_path.lower():
            categories.extend(["http", "api", "async"])

        if not categories:
            return "# No specific patterns for this file type\n"

        cursor = self.conn.cursor()

        # Build category query
        category_conditions = " OR ".join([f"category = ?" for _ in categories])

        cursor.execute(
            f"""
            SELECT name, priority, description, detection_pattern, fix_template, rationale
            FROM patterns
            WHERE {category_conditions}
            ORDER BY
                CASE priority
                    WHEN 'MANDATORY' THEN 1
                    WHEN 'CRITICAL' THEN 2
                    WHEN 'HIGH' THEN 3
                    WHEN 'RECOMMENDED' THEN 4
                    ELSE 5
                END
            LIMIT 20
        """,
            categories,
        )

        # Format as markdown
        output = f"# Patterns for {file_path}\n\n"

        current_priority = None
        for row in cursor.fetchall():
            if row["priority"] != current_priority:
                current_priority = row["priority"]
                output += f"\n## {current_priority} Patterns\n\n"

            output += f"### {row['name']}\n"
            output += f"- **Rule**: {row['description']}\n"
            if row["rationale"]:
                output += f"- **Why**: {row['rationale']}\n"
            if row["detection_pattern"]:
                output += f"- **Detect**: `{row['detection_pattern']}`\n"
            if row["fix_template"]:
                output += f"- **Fix**: `{row['fix_template']}`\n"
            output += "\n"

        return output

    def semantic_search(self, intent: str) -> dict[str, Any]:
        """
        Semantic search for patterns based on intent
        E.g., "I want to make an HTTP request" -> httpx patterns
        """
        # Map common intents to search queries
        intent_mappings = {
            "http request": "http client async httpx aiohttp",
            "error handling": "exception error logging try catch",
            "testing": "test pytest coverage mock",
            "dependency injection": "dependency injection DI testability",
            "package management": "uv pip poetry package install",
            "linting": "ruff mypy lint format check",
            "async": "async await asyncio aiohttp httpx",
            "database": "sqlmodel sqlite database orm",
            "api": "fastapi api rest http endpoint",
            "security": "security vulnerability SQL injection eval pickle",
        }

        # Find best matching intent
        query = intent.lower()
        for key, search_terms in intent_mappings.items():
            if key in query:
                query = search_terms
                break

        patterns = self.query_patterns(query, limit=3)

        return {
            "intent": intent,
            "query_used": query,
            "patterns": patterns,
            "summary": self._generate_summary(patterns),
        }

    def _generate_summary(self, patterns: list[dict]) -> str:
        """Generate a concise summary for AI consumption"""
        if not patterns:
            return "No patterns found for this query."

        mandatory = [p for p in patterns if p["priority"] in ["MANDATORY", "CRITICAL"]]
        if mandatory:
            return f"MUST use: {', '.join([p['name'] for p in mandatory])}"

        high_priority = [p for p in patterns if p["priority"] == "HIGH"]
        if high_priority:
            return f"Recommended: {', '.join([p['name'] for p in high_priority])}"

        return f"Consider: {', '.join([p['name'] for p in patterns[:2]])}"


def demonstrate_ai_queries():
    """Show how an AI assistant would use this interface"""
    pqi = PatternQueryInterface()

    print("=" * 80)
    print("AI ASSISTANT QUERY DEMONSTRATIONS")
    print("=" * 80)

    # Scenario 1: AI is about to write HTTP client code
    print("\n1. AI Query: 'About to implement HTTP client functionality'")
    print("-" * 40)
    result = pqi.semantic_search("I need to make HTTP requests")
    print(f"Summary: {result['summary']}")
    for pattern in result["patterns"][:2]:
        print(f"  • {pattern['name']}: {pattern['rule']}")
        if pattern["fix"]:
            print(f"    Fix: {pattern['fix']}")

    # Scenario 2: AI is working on a specific file
    print("\n2. AI Query: 'Working on src/api/client.py'")
    print("-" * 40)
    context = pqi.get_context_for_file("src/api/client.py")
    print(context[:500] + "...")

    # Scenario 3: AI encounters an error
    print("\n3. AI Query: 'User got logging.exception error from ruff'")
    print("-" * 40)
    patterns = pqi.query_patterns("logging exception ruff", limit=2)
    for pattern in patterns:
        print(f"Pattern: {pattern['name']}")
        print(f"  Issue: {pattern['rule']}")
        print(f"  Fix: {pattern['fix']}")
        print(f"  Why: {pattern['why']}\n")

    # Scenario 4: Quick compliance check
    print("\n4. AI Query: 'Check: Can I use pip install?'")
    print("-" * 40)
    patterns = pqi.query_patterns("pip install package management", limit=1)
    if patterns:
        p = patterns[0]
        print(f"NO! {p['why']}")
        print(f"Instead: {p['fix']}")

    # Show query performance
    import time

    print("\n" + "=" * 80)
    print("PERFORMANCE FOR AI QUERIES")
    print("=" * 80)

    test_queries = ["http client", "error handling exception", "dependency injection", "ruff TRY401", "use uv not pip"]

    for query in test_queries:
        start = time.time()
        results = pqi.query_patterns(query, limit=1)
        elapsed = (time.time() - start) * 1000
        print(f"{query:30} → {elapsed:6.2f}ms → {results[0]['name'] if results else 'No match'}")


if __name__ == "__main__":
    demonstrate_ai_queries()

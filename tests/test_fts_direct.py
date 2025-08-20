#!/usr/bin/env python3
"""
Test FTS components directly without package dependencies.
"""

import sqlite3
from pathlib import Path


class SimpleFTSPattern:
    """Simple pattern for testing."""

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


def test_fts_database():
    """Test FTS database functionality directly."""
    print("🧪 Testing FTS Database Directly\n")

    # Create test database
    db_path = "test_direct.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create schema
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
            name,
            category,
            description,
            rationale,
            detection_pattern,
            fix_template,
            example_good,
            example_bad,
            full_context,
            content=patterns,
            content_rowid=id
        )
    """)

    # Create trigger
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

    # Insert test patterns
    test_patterns = [
        SimpleFTSPattern(
            name="use-httpx",
            category="core_libraries",
            priority="HIGH",
            description="Use httpx instead of requests for async HTTP",
            detection_pattern="import requests|requests.get",
            fix_template="uv add httpx && use httpx.AsyncClient()",
            rationale="httpx provides async support and better performance",
            example_good="async with httpx.AsyncClient() as client: await client.get(url)",
            example_bad="response = requests.get(url)",
        ),
        SimpleFTSPattern(
            name="use-uv-not-pip",
            category="package_management",
            priority="MANDATORY",
            description="Always use UV instead of pip for package management",
            detection_pattern="pip install|poetry add",
            fix_template="uv add {package}",
            rationale="UV is faster and more reliable than pip",
            example_good="uv add httpx",
            example_bad="pip install httpx",
        ),
        SimpleFTSPattern(
            name="ruff-TRY401",
            category="ruff_errors",
            priority="HIGH",
            description="Redundant exception object in logging.exception call",
            detection_pattern="logging.exception.*{e}",
            fix_template="Remove {e} from logging.exception() call",
            rationale="logging.exception() automatically includes exception details",
            example_good='logging.exception("Error occurred")',
            example_bad='logging.exception(f"Error: {e}")',
        ),
    ]

    for pattern in test_patterns:
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
    print(f"✅ Inserted {len(test_patterns)} test patterns")

    # Test FTS queries
    print("\n🔍 Testing FTS Queries:")

    test_queries = ["HTTP client", "package management", "logging exception", "async", "uv pip"]

    for query in test_queries:
        cursor.execute(
            """
            SELECT
                p.name,
                p.category,
                p.priority,
                p.description,
                snippet(patterns_fts, -1, '→', '←', '...', 20) as context
            FROM patterns p
            JOIN patterns_fts ON p.id = patterns_fts.rowid
            WHERE patterns_fts MATCH ?
            ORDER BY bm25(patterns_fts)
            LIMIT 3
        """,
            (query,),
        )

        results = cursor.fetchall()
        print(f"\n  Query: '{query}' → {len(results)} results")

        for row in results:
            print(f"    • {row['name']} [{row['priority']}]")
            print(f"      {row['description']}")
            print(f"      Match: {row['context']}")

    # Test AI-style queries
    print("\n🤖 Testing AI Query Interface:")

    def ai_query(query_text, limit=3):
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
                p.example_bad
            FROM patterns p
            JOIN patterns_fts ON p.id = patterns_fts.rowid
            WHERE patterns_fts MATCH ?
            ORDER BY bm25(patterns_fts)
            LIMIT ?
        """,
            (query_text, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "name": row["name"],
                    "category": row["category"],
                    "priority": row["priority"],
                    "rule": row["description"],
                    "detect": row["detection_pattern"],
                    "fix": row["fix_template"],
                    "why": row["rationale"],
                    "good_example": row["example_good"],
                    "bad_example": row["example_bad"],
                }
            )

        return results

    # Test queries an AI might ask
    ai_queries = ["I want to make HTTP requests", "How do I install packages?", "Got a logging error from ruff"]

    for query in ai_queries:
        # Map AI queries to search terms
        search_term = query.lower()
        if "http" in search_term:
            search_term = "HTTP client"
        elif "install" in search_term or "package" in search_term:
            search_term = "package management"
        elif "logging" in search_term or "error" in search_term:
            search_term = "logging exception"

        results = ai_query(search_term)
        print(f"\n  AI Query: '{query}'")
        print(f"    Search: '{search_term}'")

        if results:
            pattern = results[0]
            print(f"    → Use: {pattern['name']} [{pattern['priority']}]")
            print(f"    → Rule: {pattern['rule']}")
            if pattern["fix"]:
                print(f"    → Fix: {pattern['fix']}")
        else:
            print("    → No patterns found")

    conn.close()
    print("\n✅ FTS testing completed successfully!")
    print(f"Database created at: {Path(db_path).absolute()}")


if __name__ == "__main__":
    test_fts_database()

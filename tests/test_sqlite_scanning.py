#!/usr/bin/env python3
"""
Test script for SQLite-first scanning and AI querying system.

This demonstrates the new AI-optimized scanning and reporting workflow.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add codex to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from codex.ai_sqlite_query import NaturalLanguageQueryInterface
from codex.sqlite_scanner import SQLiteScanner


async def test_sqlite_scanning():
    """Test the SQLite scanning system."""

    print("🚀 Testing SQLite-First Scanning System")
    print("=" * 50)

    # Test database path
    test_db = Path("test_scan_results.db")
    if test_db.exists():
        test_db.unlink()

    # Create a test file with some code patterns
    test_file = Path("test_code_sample.py")
    test_file.write_text("""
import requests
import json

def fetch_data(url):
    print("Fetching data from", url)
    response = requests.get(url)
    return response.json()

class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, item):
        print("Processing:", item)
        self.data.append(item)
""")

    try:
        print("📊 Step 1: Scanning code with SQLite scanner...")

        # Initialize scanner
        scanner = SQLiteScanner(output_db=test_db, quiet=False, ai_context="Testing AI-first scanning workflow")

        # Scan the test file (parent directory)
        result_db = await scanner.scan_repository(Path.cwd())

        print(f"✅ Scan complete! Database created: {result_db}")
        print()

        print("🔍 Step 2: Testing natural language queries...")
        print()

        # Initialize query interface
        query_interface = NaturalLanguageQueryInterface(str(test_db))

        # Test various queries
        test_queries = [
            "Show me all violations",
            "What files have the most violations?",
            "Show me violations related to http",
            "Show me simple fixes",
            "Count violations",
            "Show me repository insights",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"Query {i}: {query}")
            print("-" * 40)

            try:
                result = query_interface.query(query)

                print(f"Summary: {result['summary']}")
                print(f"Results: {len(result['results'])} items found")

                if result.get("ai_insights"):
                    print(f"AI Insights: {result['ai_insights']}")

                if result.get("suggested_follow_ups"):
                    print(f"Suggested follow-ups: {result['suggested_follow_ups'][:2]}")

                print()

            except Exception as e:
                print(f"❌ Query failed: {e}")
                print()

        print("🎯 Step 3: Testing AI-optimized output...")
        print()

        # Test AI format output
        ai_result = query_interface.query("What should I fix first?")

        ai_output = {
            "query": ai_result["original_query"],
            "results": ai_result["results"][:5],
            "summary": ai_result["summary"],
            "ai_insights": ai_result.get("ai_insights", []),
            "suggested_follow_ups": ai_result.get("suggested_follow_ups", []),
        }

        print("AI-optimized JSON output:")
        print(json.dumps(ai_output, indent=2))

        scanner.close()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        if test_db.exists():
            test_db.unlink()

    print("\n✅ SQLite scanning test complete!")


async def demo_cli_commands():
    """Demonstrate the new CLI commands."""

    print("\n🎯 CLI Command Examples")
    print("=" * 30)

    print("# Scan repository to SQLite database:")
    print("codex scan-to-db src/ --output-db scan_results.db")
    print()

    print("# Query with natural language:")
    print('codex query-db scan_results.db "Show me all violations"')
    print('codex query-db scan_results.db "What files have the most violations?"')
    print('codex query-db scan_results.db "What should I fix first?"')
    print()

    print("# AI-optimized output:")
    print('codex query-db scan_results.db "Show me violations" --ai')
    print()

    print("# Show SQL query:")
    print('codex query-db scan_results.db "Count violations" --explain')
    print()

    print("# Get help with queries:")
    print("codex db-help")


if __name__ == "__main__":
    print("SQLite-First Scanning & AI Query System Test")
    print("This tests the new AI-optimized workflow for Codex")
    print()

    # Run the test
    asyncio.run(test_sqlite_scanning())

    # Show CLI examples
    asyncio.run(demo_cli_commands())

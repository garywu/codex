#!/usr/bin/env python3
"""
Demonstration of the AI-First Scanning & Reporting Workflow

This script shows the complete workflow from scanning to AI-assisted code improvement.
"""

import json
from pathlib import Path


def create_demo_repository():
    """Create a sample repository for demonstration."""

    demo_dir = Path("demo_repository")
    demo_dir.mkdir(exist_ok=True)

    # Create various Python files with different patterns

    # Client file with HTTP and logging issues
    (demo_dir / "client.py").write_text("""
import requests
import json

def fetch_user_data(user_id):
    print(f"Fetching data for user {user_id}")
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)
    data = response.json()  # No error handling
    return data

def process_users(user_ids):
    results = []
    for user_id in user_ids:
        print("Processing user:", user_id)
        try:
            data = fetch_user_data(user_id)
            results.append(data)
        except:
            pass  # Bare except clause
    return results
""")

    # Server file with validation and security issues
    (demo_dir / "server.py").write_text("""
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/users/<user_id>')
def get_user(user_id):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/update_user', methods=['POST'])
def update_user():
    data = request.json
    # No input validation
    user_id = data['id']
    name = data['name']
    email = data['email']

    print(f"Updating user {user_id}")  # Logging issue

    # More SQL injection
    query = f"UPDATE users SET name='{name}', email='{email}' WHERE id={user_id}"
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()

    return jsonify({"status": "updated"})
""")

    # Utils file with good and bad practices
    (demo_dir / "utils.py").write_text("""
import os
import hashlib
import logging

# Good: Proper logging setup
logger = logging.getLogger(__name__)

def hash_password(password):
    # Security issue: weak hashing
    return hashlib.md5(password.encode()).hexdigest()

def read_config_file(filename):
    # Path traversal vulnerability
    with open(filename, 'r') as f:
        return f.read()

def validate_email(email):
    # Weak validation
    return '@' in email and '.' in email

class DataProcessor:
    def __init__(self):
        self.data = []

    def add_item(self, item):
        print(f"Adding item: {item}")  # Should use logger
        self.data.append(item)

    def process_all(self):
        logger.info(f"Processing {len(self.data)} items")  # Good logging
        for item in self.data:
            self.process_item(item)

    def process_item(self, item):
        # Missing error handling
        result = item.upper()
        return result
""")

    # Create a requirements file
    (demo_dir / "requirements.txt").write_text("""
flask==2.0.1
requests==2.25.1
sqlite3  # This is built-in, shouldn't be in requirements
""")

    # Create a basic README
    (demo_dir / "README.md").write_text("""
# Demo Repository

This is a sample Python application for demonstrating Codex AI-first scanning.

## Features
- User data fetching
- Web API endpoints
- Data processing utilities

## Issues
This repository intentionally contains various code quality issues for demonstration:
- Security vulnerabilities
- Performance bottlenecks
- Poor error handling
- Inconsistent logging
- Outdated dependencies
""")

    print(f"✅ Created demo repository: {demo_dir}")
    return demo_dir


def show_cli_commands():
    """Show the CLI commands that would be used."""

    print("\n🎯 AI-First Workflow Commands")
    print("=" * 40)

    commands = [
        (
            "# Step 1: Scan repository to SQLite database",
            "codex scan-to-db demo_repository --output-db demo_scan.db --ai-context 'Security and performance audit'",
        ),
        ("# Step 2: Get overview of all issues", 'codex query-db demo_scan.db "Show me all violations"'),
        ("# Step 3: Identify worst files", 'codex query-db demo_scan.db "What files have the most violations?"'),
        ("# Step 4: Get prioritized fix list", 'codex query-db demo_scan.db "What should I fix first?"'),
        ("# Step 5: Find quick wins", 'codex query-db demo_scan.db "Show me simple fixes"'),
        ("# Step 6: Security focus", 'codex query-db demo_scan.db "Show me violations related to security"'),
        ("# Step 7: Get learning insights", 'codex query-db demo_scan.db "Help me learn from this codebase"'),
        ("# Step 8: AI-formatted output for Claude", 'codex query-db demo_scan.db "Show me repository insights" --ai'),
        ("# Step 9: Understand the analysis", 'codex query-db demo_scan.db "Count violations" --explain'),
        ("# Step 10: Get help with queries", "codex db-help"),
    ]

    for description, command in commands:
        print(f"\n{description}")
        print(f"$ {command}")


def simulate_ai_assistant_queries():
    """Simulate how Claude Code would use the SQLite interface."""

    print("\n🤖 AI Assistant Query Simulation")
    print("=" * 40)

    scenarios = [
        {
            "context": "User asks: 'What security issues should I fix first?'",
            "query": "Show me violations related to security",
            "ai_follow_up": "Based on the security violations found, I recommend prioritizing SQL injection fixes in server.py and updating the password hashing in utils.py to use bcrypt instead of MD5.",
        },
        {
            "context": "User asks: 'How can I improve the performance of this code?'",
            "query": "Show me violations related to performance",
            "ai_follow_up": "The main performance issue is using the synchronous requests library. I can help you migrate to httpx for better async support, which will significantly improve API response times.",
        },
        {
            "context": "User asks: 'What are some easy fixes I can make quickly?'",
            "query": "Show me simple fixes",
            "ai_follow_up": "Here are several quick wins: 1) Replace print statements with proper logging, 2) Add basic input validation, 3) Fix the requirements.txt file. These changes will improve code quality with minimal risk.",
        },
        {
            "context": "User asks: 'Give me an overview of the codebase quality'",
            "query": "Show me repository insights",
            "ai_follow_up": "This codebase shows good structure but has significant security and modernization opportunities. The Flask app follows good patterns but needs input validation. I recommend starting with security fixes, then modernizing the HTTP client.",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i} ---")
        print(f"Context: {scenario['context']}")
        print(f"Query: {scenario['query']}")
        print(f"AI Response: {scenario['ai_follow_up']}")


def show_benefits():
    """Show the benefits of the AI-first approach."""

    print("\n🚀 AI-First Approach Benefits")
    print("=" * 35)

    benefits = [
        (
            "🔍 Natural Language Queries",
            "Claude can ask questions in natural language and get structured, queryable results",
        ),
        (
            "🧠 Contextual Understanding",
            "AI gets rich context about violations, confidence scores, and business impact",
        ),
        ("⚡ Interactive Analysis", "Real-time querying allows for conversational code improvement workflows"),
        (
            "🎯 Prioritized Recommendations",
            "AI can intelligently prioritize fixes based on severity, confidence, and complexity",
        ),
        ("📊 Structured Insights", "SQLite format enables complex analysis and relationship discovery"),
        ("🔄 Iterative Improvement", "AI can track progress over time and suggest incremental improvements"),
        ("🤝 Collaborative Workflow", "Perfect for AI-assisted pair programming and code review sessions"),
        ("📈 Learning Enhancement", "AI can identify learning opportunities and explain why patterns matter"),
    ]

    for title, description in benefits:
        print(f"\n{title}")
        print(f"  {description}")


def show_json_output_example():
    """Show what AI-formatted output looks like."""

    print("\n📋 AI-Formatted Output Example")
    print("=" * 35)

    example_output = {
        "query": "What should I fix first?",
        "results": [
            {
                "pattern_name": "sql-injection-vulnerability",
                "file_path": "server.py",
                "line_number": 12,
                "severity": "CRITICAL",
                "confidence": 0.98,
                "fix_complexity": "medium",
                "ai_explanation": "Direct string formatting in SQL queries allows attackers to inject malicious SQL code",
                "business_impact": "Complete database compromise possible",
            },
            {
                "pattern_name": "weak-password-hashing",
                "file_path": "utils.py",
                "line_number": 8,
                "severity": "HIGH",
                "confidence": 0.95,
                "fix_complexity": "simple",
                "ai_explanation": "MD5 is cryptographically broken and unsuitable for password hashing",
                "business_impact": "User passwords easily crackable",
            },
        ],
        "summary": "Found 2 high-priority security violations requiring immediate attention",
        "ai_insights": [
            "Critical security vulnerabilities detected - address immediately",
            "Both issues are in core authentication/data access paths",
        ],
        "suggested_follow_ups": [
            "Show me all violations in server.py",
            "Show me simple security fixes",
            "Show me repository security summary",
        ],
    }

    print(json.dumps(example_output, indent=2))


def main():
    """Main demonstration function."""

    print("🚀 Codex AI-First Scanning & Reporting Workflow")
    print("=" * 55)
    print("This demonstrates how Codex transforms from static reporting")
    print("to interactive, AI-optimized code analysis.")
    print()

    # Create demo repository
    demo_dir = create_demo_repository()

    # Show the workflow
    show_cli_commands()

    # Simulate AI interactions
    simulate_ai_assistant_queries()

    # Show benefits
    show_benefits()

    # Show JSON output
    show_json_output_example()

    print(f"\n🎯 Next Steps")
    print("=" * 15)
    print("1. Try the commands above on the demo repository")
    print("2. Experiment with natural language queries")
    print("3. Use --ai flag for Claude Code integration")
    print("4. Integrate into your development workflow")

    print(f"\n📁 Demo files created in: {demo_dir}")
    print("💡 Run 'codex db-help' to see more query examples")

    # Cleanup option
    print(f"\n🧹 To clean up: rm -rf {demo_dir}")


if __name__ == "__main__":
    main()

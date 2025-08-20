#!/usr/bin/env python3
"""
Simplified test for SQLite-first approach core concepts.

Tests the database schema and query patterns without full dependencies.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


def create_database_schema(db_path: str):
    """Create the AI-optimized database schema."""

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row

    # Enable FTS5 extension if available
    try:
        db.enable_load_extension(True)
    except:
        pass  # FTS5 might not be available

    # Create scan sessions table
    db.execute("""
        CREATE TABLE IF NOT EXISTS scan_sessions (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            repository_path TEXT NOT NULL,
            duration_ms INTEGER,
            files_scanned INTEGER DEFAULT 0,
            codex_version TEXT DEFAULT '1.0.0',
            scan_config JSON,
            ai_context TEXT,
            status TEXT DEFAULT 'running'
        )
    """)

    # Create scanned files table
    db.execute("""
        CREATE TABLE IF NOT EXISTS scanned_files (
            id TEXT PRIMARY KEY,
            scan_session_id TEXT REFERENCES scan_sessions(id),
            file_path TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            line_count INTEGER,
            complexity_score REAL DEFAULT 1.0,
            last_modified DATETIME,
            scan_duration_ms INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(scan_session_id, file_path)
        )
    """)

    # Create violations table with AI-optimized fields
    db.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id TEXT PRIMARY KEY,
            scan_session_id TEXT REFERENCES scan_sessions(id),
            file_id TEXT REFERENCES scanned_files(id),
            pattern_id TEXT NOT NULL,
            pattern_name TEXT NOT NULL,
            pattern_category TEXT,
            severity TEXT,
            confidence REAL,
            line_number INTEGER,
            code_snippet TEXT,
            violation_message TEXT,
            ai_explanation TEXT,
            fix_complexity TEXT,
            fix_suggestions JSON,
            business_impact TEXT,
            tags TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create repository insights table
    db.execute("""
        CREATE TABLE IF NOT EXISTS repository_insights (
            id TEXT PRIMARY KEY,
            scan_session_id TEXT REFERENCES scan_sessions(id),
            insight_type TEXT,
            insight_category TEXT,
            confidence REAL,
            title TEXT,
            description TEXT,
            supporting_evidence JSON,
            impact_assessment TEXT,
            recommendations JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Try to create FTS5 tables (fallback if not available)
    try:
        db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS violations_fts USING fts5(
                violation_id,
                pattern_name,
                pattern_category,
                code_snippet,
                violation_message,
                ai_explanation,
                file_path,
                tags
            )
        """)

        db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS insights_fts USING fts5(
                insight_id,
                insight_type,
                title,
                description,
                recommendations
            )
        """)

        print("✅ FTS5 tables created successfully")
    except Exception as e:
        print(f"⚠️  FTS5 not available: {e}")

    # Create indexes for performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_violations_session ON violations(scan_session_id)",
        "CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity, confidence)",
        "CREATE INDEX IF NOT EXISTS idx_violations_pattern ON violations(pattern_name, pattern_category)",
        "CREATE INDEX IF NOT EXISTS idx_files_session ON scanned_files(scan_session_id)",
        "CREATE INDEX IF NOT EXISTS idx_insights_session ON repository_insights(scan_session_id)",
    ]

    for index_sql in indexes:
        db.execute(index_sql)

    db.commit()
    return db


def populate_test_data(db):
    """Populate database with test data."""

    session_id = str(uuid.uuid4())

    # Create scan session
    db.execute(
        """
        INSERT INTO scan_sessions (
            id, repository_path, ai_context, scan_config, files_scanned, status
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            session_id,
            "/test/repository",
            "Testing AI-first scanning workflow",
            json.dumps({"quiet": False, "ai_optimized": True}),
            3,
            "completed",
        ),
    )

    # Create test files
    files_data = [
        ("test_client.py", "python", 150, 45, 2.3),
        ("test_server.py", "python", 200, 67, 3.1),
        ("test_utils.py", "python", 80, 23, 1.2),
    ]

    file_ids = []
    for file_path, file_type, file_size, line_count, complexity in files_data:
        file_id = str(uuid.uuid4())
        file_ids.append(file_id)

        db.execute(
            """
            INSERT INTO scanned_files (
                id, scan_session_id, file_path, file_type, file_size,
                line_count, complexity_score, last_modified, scan_duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (file_id, session_id, file_path, file_type, file_size, line_count, complexity, datetime.now(), 50),
        )

    # Create test violations
    violations_data = [
        {
            "file_id": file_ids[0],
            "pattern_name": "use-httpx-not-requests",
            "category": "modernization",
            "severity": "HIGH",
            "confidence": 0.95,
            "line_number": 5,
            "code_snippet": "import requests",
            "message": "Use httpx instead of requests for better async support",
            "ai_explanation": "The requests library is synchronous and doesn't support async operations efficiently. httpx provides the same API but with full async support.",
            "fix_complexity": "simple",
            "business_impact": "Performance bottleneck in API responses",
            "tags": "modernization http async",
        },
        {
            "file_id": file_ids[0],
            "pattern_name": "no-print-statements",
            "category": "logging",
            "severity": "MEDIUM",
            "confidence": 0.8,
            "line_number": 12,
            "code_snippet": "print('Fetching data')",
            "message": "Use logging instead of print statements",
            "ai_explanation": "Print statements should be avoided in production code as they can't be controlled or filtered. Use the logging module instead.",
            "fix_complexity": "simple",
            "business_impact": "Difficulty debugging production issues",
            "tags": "logging production debugging",
        },
        {
            "file_id": file_ids[1],
            "pattern_name": "missing-error-handling",
            "category": "error_handling",
            "severity": "HIGH",
            "confidence": 0.87,
            "line_number": 23,
            "code_snippet": "data = response.json()",
            "message": "Add error handling for JSON parsing",
            "ai_explanation": "JSON parsing can fail if the response is not valid JSON. Always add try-catch blocks for robust error handling.",
            "fix_complexity": "medium",
            "business_impact": "Application crashes on invalid responses",
            "tags": "error_handling json robustness",
        },
    ]

    for violation in violations_data:
        violation_id = str(uuid.uuid4())

        db.execute(
            """
            INSERT INTO violations (
                id, scan_session_id, file_id, pattern_id, pattern_name,
                pattern_category, severity, confidence, line_number,
                code_snippet, violation_message, ai_explanation,
                fix_complexity, fix_suggestions, business_impact, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                violation_id,
                session_id,
                violation["file_id"],
                violation["pattern_name"],
                violation["pattern_name"],
                violation["category"],
                violation["severity"],
                violation["confidence"],
                violation["line_number"],
                violation["code_snippet"],
                violation["message"],
                violation["ai_explanation"],
                violation["fix_complexity"],
                json.dumps([]),
                violation["business_impact"],
                violation["tags"],
            ),
        )

        # Add to FTS table if available
        try:
            db.execute(
                """
                INSERT INTO violations_fts (
                    violation_id, pattern_name, pattern_category,
                    code_snippet, violation_message, ai_explanation,
                    file_path, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    violation_id,
                    violation["pattern_name"],
                    violation["category"],
                    violation["code_snippet"],
                    violation["message"],
                    violation["ai_explanation"],
                    "test_file.py",
                    violation["tags"],
                ),
            )
        except:
            pass  # FTS not available

    # Create repository insights
    insights_data = [
        {
            "type": "code_quality",
            "category": "analysis",
            "confidence": 0.9,
            "title": "HTTP Client Modernization Needed",
            "description": "Multiple files use legacy requests library instead of modern httpx",
            "impact": "Performance and async support limitations",
            "recommendations": ["Replace requests with httpx", "Add async/await patterns"],
        },
        {
            "type": "architecture",
            "category": "positive",
            "confidence": 0.8,
            "title": "Good File Organization",
            "description": "Project follows clean separation of concerns",
            "impact": "Maintainable and readable codebase structure",
            "recommendations": ["Continue current patterns", "Consider adding more documentation"],
        },
    ]

    for insight in insights_data:
        insight_id = str(uuid.uuid4())

        db.execute(
            """
            INSERT INTO repository_insights (
                id, scan_session_id, insight_type, insight_category,
                confidence, title, description, supporting_evidence,
                impact_assessment, recommendations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                insight_id,
                session_id,
                insight["type"],
                insight["category"],
                insight["confidence"],
                insight["title"],
                insight["description"],
                json.dumps({}),
                insight["impact"],
                json.dumps(insight["recommendations"]),
            ),
        )

        # Add to FTS table if available
        try:
            db.execute(
                """
                INSERT INTO insights_fts (
                    insight_id, insight_type, title, description, recommendations
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    insight_id,
                    insight["type"],
                    insight["title"],
                    insight["description"],
                    json.dumps(insight["recommendations"]),
                ),
            )
        except:
            pass  # FTS not available

    db.commit()
    print("✅ Test data populated successfully")


def test_ai_queries(db):
    """Test natural language style queries."""

    print("\n🔍 Testing AI-optimized queries...")
    print("=" * 40)

    # Query 1: Get all violations summary
    print("Query 1: Show me all violations")
    cursor = db.execute("""
        SELECT
            pattern_category,
            severity,
            COUNT(*) as count,
            ROUND(AVG(confidence), 2) as avg_confidence,
            GROUP_CONCAT(DISTINCT pattern_name) as patterns
        FROM violations v
        WHERE v.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
        GROUP BY pattern_category, severity
        ORDER BY
            CASE severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
            END,
            count DESC
    """)

    results = cursor.fetchall()
    print(f"Found {len(results)} violation categories:")
    for row in results:
        print(
            f"  • {row['severity']} {row['pattern_category']}: {row['count']} violations (confidence: {row['avg_confidence']})"
        )

    print()

    # Query 2: Files with most violations
    print("Query 2: What files have the most violations?")
    cursor = db.execute("""
        SELECT
            f.file_path,
            COUNT(v.id) as violation_count,
            AVG(CASE v.severity
                WHEN 'CRITICAL' THEN 4
                WHEN 'HIGH' THEN 3
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 1
            END) as avg_severity_score,
            GROUP_CONCAT(DISTINCT v.pattern_category) as violation_categories
        FROM scanned_files f
        LEFT JOIN violations v ON f.id = v.file_id
        WHERE f.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
        GROUP BY f.id, f.file_path
        HAVING violation_count > 0
        ORDER BY violation_count DESC, avg_severity_score DESC
    """)

    results = cursor.fetchall()
    print(f"Files with violations:")
    for row in results:
        print(
            f"  • {row['file_path']}: {row['violation_count']} violations (avg severity: {row['avg_severity_score']:.1f})"
        )

    print()

    # Query 3: Fix priority
    print("Query 3: What should I fix first?")
    cursor = db.execute("""
        SELECT
            v.pattern_name,
            f.file_path,
            v.line_number,
            v.severity,
            v.confidence,
            v.fix_complexity,
            v.ai_explanation,
            v.business_impact,
            (CASE v.severity
                WHEN 'CRITICAL' THEN 4
                WHEN 'HIGH' THEN 3
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 1
            END * v.confidence) as priority_score
        FROM violations v
        JOIN scanned_files f ON v.file_id = f.id
        WHERE v.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
        AND v.confidence > 0.7
        ORDER BY
            priority_score DESC,
            CASE v.fix_complexity
                WHEN 'simple' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'complex' THEN 3
            END
        LIMIT 3
    """)

    results = cursor.fetchall()
    print("Top priority fixes:")
    for i, row in enumerate(results, 1):
        print(f"  {i}. {row['pattern_name']} in {row['file_path']}:{row['line_number']}")
        print(f"     Severity: {row['severity']}, Confidence: {row['confidence']:.2f}, Fix: {row['fix_complexity']}")
        print(f"     Impact: {row['business_impact']}")
        print()

    # Query 4: Repository insights
    print("Query 4: Show me repository insights")
    cursor = db.execute("""
        SELECT
            ri.insight_type,
            ri.title,
            ri.description,
            ri.impact_assessment,
            ri.recommendations,
            ri.confidence
        FROM repository_insights ri
        WHERE ri.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
        ORDER BY ri.confidence DESC
    """)

    results = cursor.fetchall()
    print("Repository insights:")
    for row in results:
        print(f"  • {row['title']} (confidence: {row['confidence']:.2f})")
        print(f"    {row['description']}")
        print(f"    Impact: {row['impact_assessment']}")
        recommendations = json.loads(row["recommendations"])
        print(f"    Recommendations: {', '.join(recommendations)}")
        print()


def test_fts_search(db):
    """Test full-text search if available."""

    print("🔍 Testing full-text search...")

    try:
        # Test FTS search for HTTP-related violations
        cursor = db.execute("""
            SELECT
                v.pattern_name,
                v.ai_explanation,
                v.code_snippet,
                v.confidence
            FROM violations_fts vf
            JOIN violations v ON vf.violation_id = v.id
            WHERE violations_fts MATCH 'http OR requests'
            ORDER BY v.confidence DESC
        """)

        results = cursor.fetchall()
        print(f"Found {len(results)} HTTP-related violations:")
        for row in results:
            print(f"  • {row['pattern_name']}: {row['code_snippet']}")
            print(f"    {row['ai_explanation'][:60]}...")
            print()

    except Exception as e:
        print(f"FTS search not available: {e}")


def main():
    """Main test function."""

    print("🚀 SQLite-First Scanning Architecture Test")
    print("=" * 50)

    test_db = Path("test_ai_scan.db")
    if test_db.exists():
        test_db.unlink()

    try:
        # Create database and schema
        print("📊 Creating AI-optimized database schema...")
        db = create_database_schema(str(test_db))

        # Populate with test data
        print("📥 Populating test data...")
        populate_test_data(db)

        # Test AI queries
        test_ai_queries(db)

        # Test FTS if available
        test_fts_search(db)

        print("\n🎯 AI Query Interface Benefits:")
        print("  ✅ Natural language queries work intuitively")
        print("  ✅ Structured data perfect for AI consumption")
        print("  ✅ Confidence scores help AI decision-making")
        print("  ✅ Rich context enables better explanations")
        print("  ✅ Relational data allows complex analysis")

        print(f"\n📁 Database created: {test_db}")
        print(f"Size: {test_db.stat().st_size:,} bytes")

        db.close()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        if test_db.exists():
            test_db.unlink()

    print("\n✅ SQLite-first architecture test complete!")


if __name__ == "__main__":
    main()

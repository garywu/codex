"""
SQLite-First Scanner for AI-Optimized Reporting

This scanner writes all results directly to SQLite databases that Claude Code
can query interactively using natural language.
"""

import json
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from .models import AnalysisResult, CodeContext, PatternMatch


class SQLiteScanner:
    """Scanner that outputs to SQLite databases for AI querying."""

    def __init__(
        self,
        output_db: Path,
        quiet: bool = False,
        ai_context: str | None = None,
    ):
        """Initialize SQLite scanner."""
        self.output_db = Path(output_db)
        self.quiet = quiet
        self.ai_context = ai_context
        self.console = Console(quiet=quiet)
        self.session_id = str(uuid.uuid4())
        self.start_time = time.time()

        # Initialize database
        self._initialize_database()

    def _initialize_database(self):
        """Create database schema for AI-optimized reporting."""
        self.db = sqlite3.connect(str(self.output_db))
        self.db.row_factory = sqlite3.Row

        # Enable FTS5 extension
        self.db.enable_load_extension(True)

        # Create main tables
        self._create_tables()

        if not self.quiet:
            self.console.logging.info(f"[blue]📊 Initialized scan database: {self.output_db}[/blue]")

    def _create_tables(self):
        """Create all database tables and indexes."""

        # Scan sessions table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                repository_path TEXT NOT NULL,
                duration_ms INTEGER,
                files_scanned INTEGER DEFAULT 0,
                patterns_checked INTEGER DEFAULT 0,
                codex_version TEXT DEFAULT '1.0.0',
                scan_config JSON,
                ai_context TEXT,
                repository_hash TEXT,
                status TEXT DEFAULT 'running'
            )
        """)

        # Scanned files table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS scanned_files (
                id TEXT PRIMARY KEY,
                scan_session_id TEXT REFERENCES scan_sessions(id),
                file_path TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                line_count INTEGER,
                complexity_score REAL DEFAULT 1.0,
                last_modified DATETIME,
                git_blame_summary JSON,
                framework_indicators TEXT,
                scan_duration_ms INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(scan_session_id, file_path)
            )
        """)

        # Violations table with AI-optimized fields
        self.db.execute("""
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
                column_number INTEGER,
                code_snippet TEXT,
                surrounding_context TEXT,
                violation_message TEXT,
                ai_explanation TEXT,
                fix_complexity TEXT,
                fix_suggestions JSON,
                related_violation_ids JSON,
                business_impact TEXT,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Repository insights for AI context
        self.db.execute("""
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

        # AI interaction tracking
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS ai_interactions (
                id TEXT PRIMARY KEY,
                scan_session_id TEXT REFERENCES scan_sessions(id),
                interaction_type TEXT,
                ai_query TEXT,
                sql_generated TEXT,
                results_returned JSON,
                ai_satisfaction_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create FTS5 tables for searchable content
        self._create_fts_tables()

        # Create indexes for performance
        self._create_indexes()

        self.db.commit()

    def _create_fts_tables(self):
        """Create FTS5 tables for natural language querying."""

        # Violations FTS
        self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS violations_fts USING fts5(
                violation_id,
                pattern_name,
                pattern_category,
                code_snippet,
                violation_message,
                ai_explanation,
                file_path,
                tags,
                content='violations',
                content_rowid='rowid'
            )
        """)

        # Repository insights FTS
        self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS insights_fts USING fts5(
                insight_id,
                insight_type,
                title,
                description,
                recommendations,
                content='repository_insights',
                content_rowid='rowid'
            )
        """)

    def _create_indexes(self):
        """Create indexes for query performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_violations_session ON violations(scan_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity, confidence)",
            "CREATE INDEX IF NOT EXISTS idx_violations_pattern ON violations(pattern_name, pattern_category)",
            "CREATE INDEX IF NOT EXISTS idx_files_session ON scanned_files(scan_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_insights_session ON repository_insights(scan_session_id)",
        ]

        for index_sql in indexes:
            self.db.execute(index_sql)

    async def scan_repository(self, repo_path: Path) -> str:
        """Scan repository and write results to SQLite database."""

        if not self.quiet:
            self.console.logging.info(f"[green]🚀 Starting SQLite scan of {repo_path}[/green]")

        # Create scan session
        self._create_scan_session(repo_path)

        # Scan files
        files_scanned = 0
        total_violations = 0

        # Get Python files to scan
        python_files = list(repo_path.rglob("*.py"))

        for file_path in python_files:
            if self._should_scan_file(file_path):
                result = await self._scan_file(file_path)
                if result:
                    files_scanned += 1
                    total_violations += len(result.violations)

        # Generate repository insights
        insights = await self._generate_repository_insights()
        self._write_insights(insights)

        # Finalize scan session
        self._finalize_scan_session(files_scanned, total_violations)

        if not self.quiet:
            self.console.logging.info(
                f"[green]✅ Scan complete: {files_scanned} files, {total_violations} violations[/green]"
            )
            self.console.logging.info(f"[blue]🔍 Query results: codex query-db {self.output_db} 'your question'[/blue]")

        return str(self.output_db)

    def _create_scan_session(self, repo_path: Path):
        """Create scan session record."""
        self.db.execute(
            """
            INSERT INTO scan_sessions (
                id, repository_path, ai_context, scan_config
            ) VALUES (?, ?, ?, ?)
        """,
            (self.session_id, str(repo_path), self.ai_context, json.dumps({"quiet": self.quiet})),
        )
        self.db.commit()

    async def _scan_file(self, file_path: Path) -> AnalysisResult | None:
        """Scan individual file and write to database."""
        try:
            start_time = time.time()

            # Read file content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Create context
            context = CodeContext(
                project_root=str(file_path.parent), file_path=str(file_path), content=content, language="python"
            )

            # Get file metadata
            file_stats = file_path.stat()
            line_count = len(content.splitlines())
            complexity_score = self._calculate_complexity(content)

            # Create file record
            file_id = str(uuid.uuid4())
            scan_duration = int((time.time() - start_time) * 1000)

            self.db.execute(
                """
                INSERT INTO scanned_files (
                    id, scan_session_id, file_path, file_type, file_size,
                    line_count, complexity_score, last_modified, scan_duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    file_id,
                    self.session_id,
                    str(file_path),
                    "python",
                    file_stats.st_size,
                    line_count,
                    complexity_score,
                    datetime.fromtimestamp(file_stats.st_mtime),
                    scan_duration,
                ),
            )

            # Scan for patterns (simplified for demo)
            violations = await self._detect_patterns(context, file_id)

            # Write violations to database
            for violation in violations:
                self._write_violation(violation, file_id)

            self.db.commit()

            return AnalysisResult(file_path=str(file_path), violations=violations, score=1.0 - (len(violations) * 0.1))

        except Exception as e:
            if not self.quiet:
                self.console.logging.info(f"[red]Error scanning {file_path}: {e}[/red]")
            return None

    async def _detect_patterns(self, context: CodeContext, file_id: str) -> list[PatternMatch]:
        """Detect pattern violations in code context."""
        violations = []

        # Simple pattern detection (would integrate with existing pattern system)
        content = context.content
        lines = content.splitlines()

        # Check for common anti-patterns
        for i, line in enumerate(lines, 1):
            # Example: Check for requests usage
            if "import requests" in line or "from requests import" in line:
                violations.append(
                    PatternMatch(
                        pattern_id=0,
                        pattern_name="use-httpx-not-requests",
                        category="modernization",
                        priority="HIGH",
                        file_path=context.file_path,
                        line_number=i,
                        matched_code=line.strip(),
                        confidence=0.95,
                        suggestion="Use httpx instead of requests for better async support",
                        auto_fixable=True,
                        fix_code="import httpx",
                    )
                )

            # Example: Check for print statements
            if line.strip().startswith("logging.info(") and "test" not in context.file_path.lower():
                violations.append(
                    PatternMatch(
                        pattern_id=1,
                        pattern_name="no-print-statements",
                        category="logging",
                        priority="MEDIUM",
                        file_path=context.file_path,
                        line_number=i,
                        matched_code=line.strip(),
                        confidence=0.8,
                        suggestion="Use logging instead of print statements",
                        auto_fixable=False,
                    )
                )

        return violations

    def _write_violation(self, violation: PatternMatch, file_id: str):
        """Write violation to database with AI-optimized data."""

        # Generate AI explanation
        ai_explanation = self._generate_ai_explanation(violation)

        # Generate fix suggestions
        fix_suggestions = self._generate_fix_suggestions(violation)

        # Assess business impact
        business_impact = self._assess_business_impact(violation)

        # Determine fix complexity
        fix_complexity = "simple" if violation.auto_fixable else "medium"

        # Generate tags for searching
        tags = f"{violation.category} {violation.pattern_name} {violation.priority.lower()}"

        violation_id = str(uuid.uuid4())

        self.db.execute(
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
                self.session_id,
                file_id,
                violation.pattern_id,
                violation.pattern_name,
                violation.category,
                violation.priority,
                violation.confidence,
                violation.line_number,
                violation.matched_code,
                violation.suggestion,
                ai_explanation,
                fix_complexity,
                json.dumps(fix_suggestions),
                business_impact,
                tags,
            ),
        )

        # Update FTS table
        self.db.execute(
            """
            INSERT INTO violations_fts (
                violation_id, pattern_name, pattern_category,
                code_snippet, violation_message, ai_explanation,
                file_path, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                violation_id,
                violation.pattern_name,
                violation.category,
                violation.matched_code,
                violation.suggestion,
                ai_explanation,
                violation.file_path,
                tags,
            ),
        )

    def _generate_ai_explanation(self, violation: PatternMatch) -> str:
        """Generate AI-friendly explanation for violation."""
        explanations = {
            "use-httpx-not-requests": "The requests library is synchronous and doesn't support async operations efficiently. httpx is a modern alternative that provides the same API but with full async support, better performance, and HTTP/2 support.",
            "no-print-statements": "Print statements should be avoided in production code as they can't be controlled or filtered. Use the logging module instead, which provides levels, formatting, and can be configured per environment.",
        }

        return explanations.get(violation.pattern_name, f"Pattern violation detected: {violation.suggestion}")

    def _generate_fix_suggestions(self, violation: PatternMatch) -> list[dict[str, Any]]:
        """Generate structured fix suggestions."""
        suggestions = {
            "use-httpx-not-requests": [
                {
                    "type": "import_replacement",
                    "description": "Replace requests import with httpx",
                    "confidence": 0.98,
                    "code_change": {"from": "import requests", "to": "import httpx"},
                    "additional_changes": [
                        "Replace requests.get() with httpx.get()",
                        "Consider using httpx.AsyncClient() for async operations",
                    ],
                }
            ],
            "no-print-statements": [
                {
                    "type": "logging_replacement",
                    "description": "Replace print with logging",
                    "confidence": 0.9,
                    "code_change": {"from": "logging.info(", "to": "logger.info("},
                    "prerequisites": ["Add: import logging", "Add: logger = logging.getLogger(__name__)"],
                }
            ],
        }

        return suggestions.get(violation.pattern_name, [])

    def _assess_business_impact(self, violation: PatternMatch) -> str:
        """Assess business impact of violation."""
        impact_map = {
            "use-httpx-not-requests": "Performance bottleneck in API responses, blocking adoption of async patterns",
            "no-print-statements": "Difficulty debugging production issues, log noise in deployment",
        }

        return impact_map.get(violation.pattern_name, "Maintainability and code quality impact")

    def _calculate_complexity(self, content: str) -> float:
        """Calculate simple complexity score for file."""
        lines = content.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]

        # Simple complexity based on lines, functions, classes
        complexity = len(non_empty_lines) * 0.1
        complexity += content.count("def ") * 0.5
        complexity += content.count("class ") * 1.0
        complexity += content.count("if ") * 0.2
        complexity += content.count("for ") * 0.2
        complexity += content.count("while ") * 0.3

        return min(complexity, 10.0)  # Cap at 10

    def _should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned."""
        exclude_patterns = ["__pycache__", ".git", ".venv", "venv", ".pytest_cache", ".mypy_cache", "node_modules"]

        path_str = str(file_path)
        return not any(pattern in path_str for pattern in exclude_patterns)

    async def _generate_repository_insights(self) -> list[dict[str, Any]]:
        """Generate high-level insights about the repository."""
        insights = []

        # Get violation statistics
        cursor = self.db.execute(
            """
            SELECT
                pattern_category,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM violations
            WHERE scan_session_id = ?
            GROUP BY pattern_category
        """,
            (self.session_id,),
        )

        violation_stats = cursor.fetchall()

        if violation_stats:
            insights.append(
                {
                    "type": "violation_summary",
                    "category": "analysis",
                    "confidence": 0.9,
                    "title": "Code Quality Overview",
                    "description": f"Found violations in {len(violation_stats)} categories",
                    "supporting_evidence": {"categories": [dict(row) for row in violation_stats]},
                    "impact_assessment": "Review and address high-confidence violations first",
                    "recommendations": [
                        "Focus on high-confidence violations (>0.9)",
                        "Address violations by category for systematic improvement",
                        "Consider automated fixes for simple patterns",
                    ],
                }
            )

        # Check for framework usage
        cursor = self.db.execute(
            """
            SELECT file_path, line_count
            FROM scanned_files
            WHERE scan_session_id = ?
            ORDER BY line_count DESC
            LIMIT 5
        """,
            (self.session_id,),
        )

        large_files = cursor.fetchall()

        if large_files:
            insights.append(
                {
                    "type": "architecture",
                    "category": "positive",
                    "confidence": 0.8,
                    "title": "Project Structure Analysis",
                    "description": "Analyzed project structure and file organization",
                    "supporting_evidence": {"largest_files": [dict(row) for row in large_files]},
                    "impact_assessment": "Good file organization supports maintainability",
                    "recommendations": [
                        "Consider breaking up very large files (>500 lines)",
                        "Maintain consistent module organization",
                    ],
                }
            )

        return insights

    def _write_insights(self, insights: list[dict[str, Any]]):
        """Write repository insights to database."""
        for insight in insights:
            insight_id = str(uuid.uuid4())

            self.db.execute(
                """
                INSERT INTO repository_insights (
                    id, scan_session_id, insight_type, insight_category,
                    confidence, title, description, supporting_evidence,
                    impact_assessment, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    insight_id,
                    self.session_id,
                    insight["type"],
                    insight["category"],
                    insight["confidence"],
                    insight["title"],
                    insight["description"],
                    json.dumps(insight["supporting_evidence"]),
                    insight["impact_assessment"],
                    json.dumps(insight["recommendations"]),
                ),
            )

            # Update FTS
            self.db.execute(
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

        self.db.commit()

    def _finalize_scan_session(self, files_scanned: int, total_violations: int):
        """Update scan session with final results."""
        duration_ms = int((time.time() - self.start_time) * 1000)

        self.db.execute(
            """
            UPDATE scan_sessions
            SET
                duration_ms = ?,
                files_scanned = ?,
                status = 'completed'
            WHERE id = ?
        """,
            (duration_ms, files_scanned, self.session_id),
        )

        self.db.commit()

    def close(self):
        """Close database connection."""
        if hasattr(self, "db"):
            self.db.close()

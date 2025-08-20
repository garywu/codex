"""
Scan Manager - Orchestrates and manages all code quality scans.

Inspired by how tools like Ruff organize their rules:
- Each rule has a unique code (e.g., E501, F401)
- Rules are grouped into categories
- Rules can be enabled/disabled via configuration
- Results are aggregated and reported systematically
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from .scan_registry import ScanRegistry, ScanResult, ScanSeverity
from .tools import ToolRunner
from .unified_database import UnifiedDatabase


class ScanCode(str, Enum):
    """Unique codes for each scan type, inspired by Ruff's rule codes."""

    # Consistency Scans (C prefix)
    C001 = "hardcoded-paths"  # Hardcoded paths instead of settings
    C002 = "multiple-imports"  # Multiple conflicting imports
    C003 = "missing-settings"  # Missing settings usage
    C004 = "inconsistent-naming"  # Inconsistent naming conventions

    # Security Scans (S prefix)
    S001 = "hardcoded-secrets"  # Hardcoded secrets/passwords
    S002 = "unsafe-eval"  # Use of eval/exec
    S003 = "sql-injection"  # Potential SQL injection

    # Quality Scans (Q prefix)
    Q001 = "dead-code"  # Unreachable/dead code
    Q002 = "complex-function"  # Overly complex functions
    Q003 = "duplicate-code"  # Duplicate code blocks

    # External Tools (T prefix)
    T001 = "ruff"  # Ruff linter
    T002 = "ty"  # Astral's fast type checker (or mypy fallback)
    T003 = "typos"  # Spell checker

    # Pattern Scans (P prefix)
    P001 = "pattern-violations"  # Custom pattern violations
    P002 = "mandatory-patterns"  # Mandatory pattern compliance


@dataclass
class ScanConfiguration:
    """Configuration for scan execution."""

    # Which scans to run
    enabled_scans: set[str] = field(
        default_factory=lambda: {
            "C001",
            "C002",
            "C003",  # Consistency
            "S001",  # Security
            "T001",
            "T002",
            "T003",  # Tools
            "P001",
            "P002",  # Patterns
        }
    )

    # Scan parameters
    parallel: bool = True  # Run scans in parallel
    fail_fast: bool = False  # Stop on first failure
    fix: bool = False  # Apply automatic fixes

    # Output settings
    output_format: str = "human"  # human, json, junit, sarif
    verbose: bool = False  # Verbose output
    quiet: bool = False  # Suppress non-error output

    # Filtering
    include_paths: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(
        default_factory=lambda: [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
        ]
    )

    # Severity thresholds
    min_severity: ScanSeverity = ScanSeverity.LOW
    fail_on_severity: ScanSeverity = ScanSeverity.HIGH


@dataclass
class ScanSession:
    """Represents a complete scan session with all results."""

    session_id: str
    started_at: datetime
    completed_at: datetime | None
    configuration: ScanConfiguration
    results: dict[str, ScanResult]
    summary: dict[str, any]

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "configuration": {
                "enabled_scans": list(self.configuration.enabled_scans),
                "fix": self.configuration.fix,
                "output_format": self.configuration.output_format,
            },
            "results": {scan_id: result.get_summary() for scan_id, result in self.results.items()},
            "summary": self.summary,
        }


class ScanManager:
    """Manages scan execution, scheduling, and result storage."""

    def __init__(self):
        self.db = UnifiedDatabase()
        self.tool_runner = ToolRunner()
        self.scan_registry = ScanRegistry()
        self._init_scan_tables()

    def _init_scan_tables(self):
        """Initialize database tables for scan management."""
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_sessions (
                    session_id TEXT PRIMARY KEY,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    configuration JSON NOT NULL,
                    summary JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    result_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    scan_code TEXT NOT NULL,
                    scan_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    file_path TEXT,
                    line_number INTEGER,
                    message TEXT,
                    fix_available BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES scan_sessions(session_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scan_results_session
                ON scan_results(session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scan_results_severity
                ON scan_results(severity)
            """)

    async def run_scan_session(self, target_path: Path, configuration: ScanConfiguration | None = None) -> ScanSession:
        """Run a complete scan session with all configured scans."""

        if configuration is None:
            configuration = ScanConfiguration()

        session = ScanSession(
            session_id=str(uuid.uuid4()),
            started_at=datetime.utcnow(),
            completed_at=None,
            configuration=configuration,
            results={},
            summary={},
        )

        # Collect all scan tasks
        tasks = []
        scan_codes = []

        for scan_code in configuration.enabled_scans:
            if scan_code.startswith("C"):
                # Consistency scans
                scan = self.scan_registry.get_scan(ScanCode[scan_code].value)
                if scan:
                    tasks.append(scan.scan_directory(target_path))
                    scan_codes.append(scan_code)

            elif scan_code.startswith("T"):
                # Tool scans
                if scan_code == "T001":
                    tasks.append(self.tool_runner.run_ruff([target_path]))
                    scan_codes.append(scan_code)
                elif scan_code == "T002":
                    # Try ty first (Astral's fast type checker), fall back to mypy
                    tasks.append(self.tool_runner.run_ty_or_mypy([target_path]))
                    scan_codes.append(scan_code)
                elif scan_code == "T003":
                    tasks.append(self.tool_runner.run_typos([target_path]))
                    scan_codes.append(scan_code)

            elif scan_code.startswith("P"):
                # Pattern scans - use existing scanner
                from .scanner import Scanner

                scanner = Scanner(quiet=configuration.quiet, fix=configuration.fix)
                if scan_code == "P001":
                    tasks.append(scanner.scan_directory(target_path))
                    scan_codes.append(scan_code)

        # Run scans
        if configuration.parallel:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for task in tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    results.append(e)
                    if configuration.fail_fast:
                        break

        # Process results
        total_violations = 0
        failed_scans = 0

        for scan_code, result in zip(scan_codes, results):
            if isinstance(result, Exception):
                failed_scans += 1
                session.results[scan_code] = None
            else:
                session.results[scan_code] = result
                if hasattr(result, "violations"):
                    total_violations += len(result.violations)
                elif hasattr(result, "violations_count"):
                    total_violations += result.violations_count

        session.completed_at = datetime.utcnow()
        session.summary = {
            "total_scans": len(scan_codes),
            "failed_scans": failed_scans,
            "total_violations": total_violations,
            "duration_ms": int((session.completed_at - session.started_at).total_seconds() * 1000),
        }

        # Store session in database
        await self._store_session(session)

        return session

    async def _store_session(self, session: ScanSession):
        """Store scan session in database."""
        with self.db.get_connection() as conn:
            # Store session
            conn.execute(
                """
                INSERT INTO scan_sessions
                (session_id, started_at, completed_at, configuration, summary)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    session.session_id,
                    session.started_at,
                    session.completed_at,
                    json.dumps(
                        {
                            "enabled_scans": list(session.configuration.enabled_scans),
                            "fix": session.configuration.fix,
                        }
                    ),
                    json.dumps(session.summary),
                ),
            )

            # Store individual results
            for scan_code, result in session.results.items():
                if result and hasattr(result, "violations"):
                    for violation in result.violations:
                        conn.execute(
                            """
                            INSERT INTO scan_results
                            (result_id, session_id, scan_code, scan_name, severity,
                             file_path, line_number, message, fix_available)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                str(uuid.uuid4()),
                                session.session_id,
                                scan_code,
                                violation.pattern_name if hasattr(violation, "pattern_name") else scan_code,
                                violation.priority if hasattr(violation, "priority") else "MEDIUM",
                                violation.file_path if hasattr(violation, "file_path") else None,
                                violation.line_number if hasattr(violation, "line_number") else None,
                                violation.suggestion if hasattr(violation, "suggestion") else str(violation),
                                violation.auto_fixable if hasattr(violation, "auto_fixable") else False,
                            ),
                        )

    def get_session_history(self, limit: int = 10) -> list[dict]:
        """Get recent scan session history."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT session_id, started_at, completed_at, summary
                FROM scan_sessions
                ORDER BY started_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [
                {
                    "session_id": row[0],
                    "started_at": row[1],
                    "completed_at": row[2],
                    "summary": json.loads(row[3]) if row[3] else {},
                }
                for row in cursor.fetchall()
            ]

    def get_violation_trends(self, days: int = 30) -> dict[str, list]:
        """Get violation trends over time."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    DATE(s.started_at) as scan_date,
                    r.severity,
                    COUNT(*) as count
                FROM scan_results r
                JOIN scan_sessions s ON r.session_id = s.session_id
                WHERE s.started_at >= datetime('now', '-' || ? || ' days')
                GROUP BY scan_date, r.severity
                ORDER BY scan_date
            """,
                (days,),
            )

            trends = {}
            for row in cursor.fetchall():
                date, severity, count = row
                if severity not in trends:
                    trends[severity] = []
                trends[severity].append({"date": date, "count": count})

            return trends

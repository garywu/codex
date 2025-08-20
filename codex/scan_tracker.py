#!/usr/bin/env python3
"""
Scan Tracking System for Codex

Stores all scan results in a SQLite database (.codex/scans.db) for:
- Historical tracking
- Trend analysis
- Progress monitoring
- Violation history
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@dataclass
class ScanRecord:
    """Represents a single scan execution."""

    scan_id: str
    timestamp: str
    project_path: str
    total_files: int
    scanned_files: int
    total_violations: int
    violations_by_category: str  # JSON
    violations_by_module: str  # JSON
    violations_by_pattern: str  # JSON
    hotspot_files: str  # JSON
    scan_duration_ms: int
    git_commit: str | None = None
    git_branch: str | None = None
    codex_version: str | None = None

    @classmethod
    def generate_id(cls) -> str:
        """Generate unique scan ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]


@dataclass
class ViolationRecord:
    """Represents a single violation found in a scan."""

    scan_id: str
    file_path: str
    line_number: int
    pattern_name: str
    category: str
    message: str
    severity: str
    module: str
    folder: str
    fixed: bool = False
    fix_applied: str | None = None


class ScanTracker:
    """Manages scan result tracking in SQLite database."""

    def __init__(self, db_path: Path | None = None):
        self.console = Console()

        # Default to .codex/scans.db
        if db_path is None:
            codex_dir = Path.cwd() / ".codex"
            codex_dir.mkdir(exist_ok=True)
            db_path = codex_dir / "scans.db"

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()

        # Scans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                project_path TEXT NOT NULL,
                total_files INTEGER,
                scanned_files INTEGER,
                total_violations INTEGER,
                violations_by_category TEXT,  -- JSON
                violations_by_module TEXT,     -- JSON
                violations_by_pattern TEXT,    -- JSON
                hotspot_files TEXT,           -- JSON
                scan_duration_ms INTEGER,
                git_commit TEXT,
                git_branch TEXT,
                codex_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Violations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                pattern_name TEXT,
                category TEXT,
                message TEXT,
                severity TEXT,
                module TEXT,
                folder TEXT,
                fixed BOOLEAN DEFAULT 0,
                fix_applied TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_violations_scan_id
            ON violations(scan_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_violations_pattern
            ON violations(pattern_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_violations_category
            ON violations(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_violations_file
            ON violations(file_path)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_timestamp
            ON scans(timestamp)
        """)

        # Progress tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                violations_fixed INTEGER DEFAULT 0,
                violations_remaining INTEGER,
                fix_rate REAL,  -- Percentage
                notes TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
            )
        """)

        self.conn.commit()

    def record_scan(self, scan_result: dict) -> str:
        """Record a new scan in the database."""
        scan_id = ScanRecord.generate_id()
        timestamp = datetime.now().isoformat()

        # Get git info if available
        git_commit = self._get_git_commit()
        git_branch = self._get_git_branch()

        # Get codex version
        try:
            from codex import __version__

            codex_version = __version__
        except:
            codex_version = "unknown"

        # Create scan record
        scan_record = ScanRecord(
            scan_id=scan_id,
            timestamp=timestamp,
            project_path=str(Path.cwd()),
            total_files=scan_result.get("total_files", 0),
            scanned_files=scan_result.get("scanned_files", 0),
            total_violations=scan_result.get("total_violations", 0),
            violations_by_category=json.dumps(scan_result.get("by_category", {})),
            violations_by_module=json.dumps(scan_result.get("by_module", {})),
            violations_by_pattern=json.dumps(scan_result.get("by_pattern", {})),
            hotspot_files=json.dumps(scan_result.get("hotspots", [])),
            scan_duration_ms=scan_result.get("duration_ms", 0),
            git_commit=git_commit,
            git_branch=git_branch,
            codex_version=codex_version,
        )

        # Insert scan record
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO scans (
                scan_id, timestamp, project_path, total_files, scanned_files,
                total_violations, violations_by_category, violations_by_module,
                violations_by_pattern, hotspot_files, scan_duration_ms,
                git_commit, git_branch, codex_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                scan_record.scan_id,
                scan_record.timestamp,
                scan_record.project_path,
                scan_record.total_files,
                scan_record.scanned_files,
                scan_record.total_violations,
                scan_record.violations_by_category,
                scan_record.violations_by_module,
                scan_record.violations_by_pattern,
                scan_record.hotspot_files,
                scan_record.scan_duration_ms,
                scan_record.git_commit,
                scan_record.git_branch,
                scan_record.codex_version,
            ),
        )

        # Insert individual violations if provided
        if "violations" in scan_result:
            for violation in scan_result["violations"]:
                self.record_violation(scan_id, violation)

        self.conn.commit()
        return scan_id

    def record_violation(self, scan_id: str, violation: dict):
        """Record an individual violation."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO violations (
                scan_id, file_path, line_number, pattern_name, category,
                message, severity, module, folder, fixed, fix_applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                scan_id,
                violation.get("file_path"),
                violation.get("line_number"),
                violation.get("pattern_name"),
                violation.get("category"),
                violation.get("message"),
                violation.get("severity", "medium"),
                violation.get("module"),
                violation.get("folder"),
                violation.get("fixed", False),
                violation.get("fix_applied"),
            ),
        )
        self.conn.commit()

    def get_latest_scan(self) -> dict | None:
        """Get the most recent scan."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM scans
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_scan_history(self, limit: int = 10) -> list[dict]:
        """Get scan history."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM scans
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_violation_trends(self, pattern_name: str | None = None) -> list[dict]:
        """Get violation trends over time."""
        cursor = self.conn.cursor()

        if pattern_name:
            # Trend for specific pattern
            cursor.execute(
                """
                SELECT
                    s.timestamp,
                    s.scan_id,
                    COUNT(v.id) as count
                FROM scans s
                LEFT JOIN violations v ON s.scan_id = v.scan_id
                WHERE v.pattern_name = ?
                GROUP BY s.scan_id
                ORDER BY s.timestamp
            """,
                (pattern_name,),
            )
        else:
            # Overall trend
            cursor.execute("""
                SELECT
                    timestamp,
                    scan_id,
                    total_violations as count
                FROM scans
                ORDER BY timestamp
            """)

        return [dict(row) for row in cursor.fetchall()]

    def get_progress_report(self) -> dict:
        """Generate progress report comparing latest to previous scan."""
        history = self.get_scan_history(2)

        if len(history) < 2:
            return {"status": "insufficient_data"}

        latest = history[0]
        previous = history[1]

        # Calculate changes
        violations_change = latest["total_violations"] - previous["total_violations"]
        violations_pct_change = (
            (violations_change / previous["total_violations"] * 100) if previous["total_violations"] > 0 else 0
        )

        # Parse category changes
        latest_categories = json.loads(latest["violations_by_category"])
        prev_categories = json.loads(previous["violations_by_category"])

        category_changes = {}
        for cat in set(list(latest_categories.keys()) + list(prev_categories.keys())):
            latest_count = latest_categories.get(cat, 0)
            prev_count = prev_categories.get(cat, 0)
            category_changes[cat] = {
                "current": latest_count,
                "previous": prev_count,
                "change": latest_count - prev_count,
            }

        return {
            "status": "comparison_available",
            "latest_scan": latest["scan_id"],
            "previous_scan": previous["scan_id"],
            "total_violations": {
                "current": latest["total_violations"],
                "previous": previous["total_violations"],
                "change": violations_change,
                "change_pct": violations_pct_change,
            },
            "category_changes": category_changes,
            "time_between_scans": self._calculate_time_diff(previous["timestamp"], latest["timestamp"]),
        }

    def get_hotspot_evolution(self, limit: int = 5) -> dict:
        """Track how hotspot files evolve over time."""
        cursor = self.conn.cursor()

        # Get unique files with most violations across all scans
        cursor.execute(
            """
            SELECT
                file_path,
                COUNT(DISTINCT scan_id) as scan_appearances,
                SUM(CASE WHEN fixed = 0 THEN 1 ELSE 0 END) as unfixed_count,
                SUM(CASE WHEN fixed = 1 THEN 1 ELSE 0 END) as fixed_count
            FROM violations
            GROUP BY file_path
            ORDER BY unfixed_count DESC
            LIMIT ?
        """,
            (limit,),
        )

        hotspots = []
        for row in cursor.fetchall():
            hotspots.append(
                {
                    "file": row["file_path"],
                    "appearances": row["scan_appearances"],
                    "unfixed": row["unfixed_count"],
                    "fixed": row["fixed_count"],
                }
            )

        return {"hotspots": hotspots}

    def mark_violations_fixed(self, scan_id: str, file_path: str, pattern_names: list[str]):
        """Mark violations as fixed."""
        cursor = self.conn.cursor()
        for pattern in pattern_names:
            cursor.execute(
                """
                UPDATE violations
                SET fixed = 1, fix_applied = CURRENT_TIMESTAMP
                WHERE scan_id = ? AND file_path = ? AND pattern_name = ?
            """,
                (scan_id, file_path, pattern),
            )
        self.conn.commit()

    def print_summary(self):
        """Print database summary."""
        cursor = self.conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) as count FROM scans")
        scan_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM violations")
        violation_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM violations WHERE fixed = 1")
        fixed_count = cursor.fetchone()["count"]

        # Get latest scan
        latest = self.get_latest_scan()

        summary = Panel.fit(
            f"""[bold cyan]SCAN TRACKING DATABASE[/bold cyan]

📊 Database: [yellow]{self.db_path}[/yellow]
📈 Total Scans: [bold]{scan_count}[/bold]
🔍 Total Violations Tracked: [bold]{violation_count}[/bold]
✅ Violations Fixed: [bold green]{fixed_count}[/bold green]

Latest Scan:
  • ID: {latest['scan_id'] if latest else 'None'}
  • Time: {latest['timestamp'][:19] if latest else 'N/A'}
  • Violations: {latest['total_violations'] if latest else 0}
""",
            border_style="blue",
            box=box.DOUBLE,
        )
        self.console.print(summary)

    def print_history(self, limit: int = 10):
        """Print scan history table."""
        history = self.get_scan_history(limit)

        if not history:
            self.console.print("[yellow]No scan history found.[/yellow]")
            return

        table = Table(title=f"Scan History (Last {limit})", border_style="blue", box=box.ROUNDED)
        table.add_column("Scan ID", style="cyan")
        table.add_column("Timestamp", style="yellow")
        table.add_column("Files", justify="right")
        table.add_column("Violations", justify="right")
        table.add_column("Branch", style="green")
        table.add_column("Commit", style="dim")

        for scan in history:
            table.add_row(
                scan["scan_id"][:8],
                scan["timestamp"][:19],
                f"{scan['scanned_files']}/{scan['total_files']}",
                str(scan["total_violations"]),
                scan["git_branch"] or "N/A",
                scan["git_commit"][:8] if scan["git_commit"] else "N/A",
            )

        self.console.print(table)

    def print_progress(self):
        """Print progress report."""
        progress = self.get_progress_report()

        if progress["status"] == "insufficient_data":
            self.console.print("[yellow]Need at least 2 scans to show progress.[/yellow]")
            return

        # Overall progress
        total = progress["total_violations"]
        change_symbol = "📈" if total["change"] > 0 else "📉" if total["change"] < 0 else "➡️"
        change_color = "red" if total["change"] > 0 else "green" if total["change"] < 0 else "yellow"

        self.console.print(f"\n[bold]Progress Report[/bold]")
        self.console.print(
            f"{change_symbol} Total Violations: [bold]{total['current']}[/bold] "
            f"([{change_color}]{total['change']:+d}, {total['change_pct']:+.1f}%[/{change_color}])"
        )

        # Category breakdown
        self.console.print("\n[bold]By Category:[/bold]")
        for cat, data in progress["category_changes"].items():
            if data["change"] != 0:
                symbol = "↑" if data["change"] > 0 else "↓"
                color = "red" if data["change"] > 0 else "green"
                self.console.print(f"  • {cat}: {data['current']} ([{color}]{symbol} {abs(data['change'])}[/{color}])")

        self.console.print(f"\n[dim]Time between scans: {progress['time_between_scans']}[/dim]")

    def _get_git_commit(self) -> str | None:
        """Get current git commit hash."""
        try:
            import subprocess

            result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None

    def _get_git_branch(self) -> str | None:
        """Get current git branch."""
        try:
            import subprocess

            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None

    def _calculate_time_diff(self, start: str, end: str) -> str:
        """Calculate human-readable time difference."""
        from datetime import datetime

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        diff = end_dt - start_dt

        if diff.days > 0:
            return f"{diff.days} days"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours"
        else:
            return f"{diff.seconds // 60} minutes"

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """CLI for scan tracking."""
    import argparse

    parser = argparse.ArgumentParser(description="Codex Scan Tracking")
    parser.add_argument("command", choices=["summary", "history", "progress", "trends"], help="Command to run")
    parser.add_argument("--limit", type=int, default=10, help="Number of records to show")
    parser.add_argument("--pattern", type=str, help="Pattern name for trend analysis")

    args = parser.parse_args()

    tracker = ScanTracker()

    try:
        if args.command == "summary":
            tracker.print_summary()
        elif args.command == "history":
            tracker.print_history(args.limit)
        elif args.command == "progress":
            tracker.print_progress()
        elif args.command == "trends":
            trends = tracker.get_violation_trends(args.pattern)
            console = Console()
            console.print(trends)
    finally:
        tracker.close()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

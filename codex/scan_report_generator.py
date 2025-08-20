#!/usr/bin/env python3
"""
Automatic Report Generator for Scan Tracking Database

Generates comprehensive reports using SQL views, triggers, and aggregations.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table


class ScanReportGenerator:
    """Generates automatic reports from scan tracking database."""

    def __init__(self, db_path: Path | None = None):
        self.console = Console()

        if db_path is None:
            codex_dir = Path.cwd() / ".codex"
            db_path = codex_dir / "scans.db"

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row

        # Create views and triggers for automatic reporting
        self._setup_reporting_infrastructure()

    def _setup_reporting_infrastructure(self):
        """Create SQL views and triggers for automatic report generation."""
        cursor = self.conn.cursor()

        # View: Latest scan summary
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_latest_scan AS
            SELECT
                scan_id,
                timestamp,
                total_violations,
                scanned_files,
                git_branch,
                git_commit
            FROM scans
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        # View: Violation trends by category
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_category_trends AS
            SELECT
                s.timestamp,
                v.category,
                COUNT(*) as count
            FROM scans s
            JOIN violations v ON s.scan_id = v.scan_id
            GROUP BY s.scan_id, v.category
            ORDER BY s.timestamp DESC
        """)

        # View: Top violating files
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_hotspot_files AS
            SELECT
                file_path,
                COUNT(DISTINCT scan_id) as scan_count,
                COUNT(*) as total_violations,
                COUNT(DISTINCT pattern_name) as unique_patterns
            FROM violations
            GROUP BY file_path
            ORDER BY total_violations DESC
            LIMIT 10
        """)

        # View: Pattern frequency across all scans
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_pattern_frequency AS
            SELECT
                pattern_name,
                COUNT(*) as total_occurrences,
                COUNT(DISTINCT scan_id) as scan_appearances,
                COUNT(DISTINCT file_path) as affected_files
            FROM violations
            GROUP BY pattern_name
            ORDER BY total_occurrences DESC
        """)

        # View: Weekly summary
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_weekly_summary AS
            SELECT
                DATE(timestamp) as scan_date,
                COUNT(*) as scan_count,
                AVG(total_violations) as avg_violations,
                MIN(total_violations) as min_violations,
                MAX(total_violations) as max_violations
            FROM scans
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
        """)

        # View: Fix rate calculation
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_fix_rate AS
            SELECT
                COUNT(CASE WHEN fixed = 1 THEN 1 END) * 100.0 / COUNT(*) as fix_rate,
                COUNT(CASE WHEN fixed = 1 THEN 1 END) as fixed_count,
                COUNT(CASE WHEN fixed = 0 THEN 1 END) as unfixed_count,
                COUNT(*) as total_count
            FROM violations
        """)

        # View: Module health scores
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_module_health AS
            SELECT
                module,
                COUNT(DISTINCT file_path) as affected_files,
                COUNT(*) as total_violations,
                COUNT(DISTINCT pattern_name) as pattern_diversity,
                CASE
                    WHEN COUNT(*) = 0 THEN 100
                    WHEN COUNT(*) <= 10 THEN 90
                    WHEN COUNT(*) <= 25 THEN 75
                    WHEN COUNT(*) <= 50 THEN 50
                    WHEN COUNT(*) <= 100 THEN 25
                    ELSE 10
                END as health_score
            FROM violations
            WHERE scan_id = (SELECT scan_id FROM scans ORDER BY timestamp DESC LIMIT 1)
            GROUP BY module
        """)

        # Materialized view table for report summaries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_summaries (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_id TEXT,
                report_type TEXT,
                summary_json TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans(scan_id)
            )
        """)

        # Trigger: Auto-generate summary after each scan
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_generate_summary
            AFTER INSERT ON scans
            BEGIN
                INSERT INTO report_summaries (scan_id, report_type, summary_json)
                VALUES (
                    NEW.scan_id,
                    'auto_summary',
                    json_object(
                        'timestamp', NEW.timestamp,
                        'violations', NEW.total_violations,
                        'files', NEW.scanned_files,
                        'categories', NEW.violations_by_category
                    )
                );
            END
        """)

        self.conn.commit()

    def generate_executive_summary(self) -> str:
        """Generate executive summary using SQL aggregations."""
        cursor = self.conn.cursor()

        # Get latest scan info
        cursor.execute("SELECT * FROM v_latest_scan")
        latest = dict(cursor.fetchone()) if cursor.rowcount else {}

        # Get fix rate
        cursor.execute("SELECT * FROM v_fix_rate")
        fix_rate = dict(cursor.fetchone()) if cursor.rowcount else {}

        # Get trend (compare last 2 scans)
        cursor.execute("""
            SELECT
                s1.total_violations as current,
                s2.total_violations as previous,
                s1.total_violations - s2.total_violations as change
            FROM scans s1
            JOIN scans s2 ON s2.timestamp < s1.timestamp
            ORDER BY s1.timestamp DESC, s2.timestamp DESC
            LIMIT 1
        """)
        trend = dict(cursor.fetchone()) if cursor.rowcount else {}

        # Get top issues
        cursor.execute("""
            SELECT pattern_name, COUNT(*) as count
            FROM violations
            WHERE scan_id = (SELECT scan_id FROM v_latest_scan)
            GROUP BY pattern_name
            ORDER BY count DESC
            LIMIT 3
        """)
        top_issues = cursor.fetchall()

        # Build markdown report
        report = f"""# Executive Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Current Status
- **Latest Scan**: {latest.get('timestamp', 'N/A')}
- **Total Violations**: {latest.get('total_violations', 0)}
- **Files Scanned**: {latest.get('scanned_files', 0)}
- **Fix Rate**: {fix_rate.get('fix_rate', 0):.1f}% ({fix_rate.get('fixed_count', 0)} fixed / {fix_rate.get('total_count', 0)} total)

## Trend
- **Current**: {trend.get('current', 0)} violations
- **Previous**: {trend.get('previous', 0)} violations
- **Change**: {trend.get('change', 0):+d} ({('↑' if trend.get('change', 0) > 0 else '↓' if trend.get('change', 0) < 0 else '→')})

## Top Issues
"""
        for issue in top_issues:
            report += f"1. `{issue['pattern_name']}`: {issue['count']} occurrences\n"

        return report

    def generate_detailed_report(self) -> str:
        """Generate detailed report with all views."""
        cursor = self.conn.cursor()

        report = f"""# Detailed Scan Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Database: {self.db_path}

"""

        # Module Health
        report += "## Module Health Scores\n\n"
        report += "| Module | Files | Violations | Pattern Diversity | Health Score |\n"
        report += "|--------|-------|------------|-------------------|-------------|\n"

        cursor.execute("SELECT * FROM v_module_health ORDER BY health_score DESC")
        for row in cursor.fetchall():
            report += f"| {row['module']} | {row['affected_files']} | {row['total_violations']} | {row['pattern_diversity']} | {row['health_score']}/100 |\n"

        # Hotspot Files
        report += "\n## Hotspot Files\n\n"
        report += "| File | Total Violations | Scan Appearances | Unique Patterns |\n"
        report += "|------|-----------------|------------------|----------------|\n"

        cursor.execute("SELECT * FROM v_hotspot_files")
        for row in cursor.fetchall():
            report += (
                f"| {row['file_path']} | {row['total_violations']} | {row['scan_count']} | {row['unique_patterns']} |\n"
            )

        # Pattern Frequency
        report += "\n## Pattern Analysis\n\n"
        report += "| Pattern | Total | Scans | Files |\n"
        report += "|---------|-------|-------|-------|\n"

        cursor.execute("SELECT * FROM v_pattern_frequency LIMIT 10")
        for row in cursor.fetchall():
            report += f"| {row['pattern_name']} | {row['total_occurrences']} | {row['scan_appearances']} | {row['affected_files']} |\n"

        # Weekly Summary
        report += "\n## Weekly Activity\n\n"
        cursor.execute("SELECT * FROM v_weekly_summary")
        weekly = cursor.fetchall()
        if weekly:
            report += "| Date | Scans | Avg Violations | Min | Max |\n"
            report += "|------|-------|----------------|-----|-----|\n"
            for row in weekly:
                report += f"| {row['scan_date']} | {row['scan_count']} | {row['avg_violations']:.0f} | {row['min_violations']} | {row['max_violations']} |\n"

        return report

    def generate_sql_based_summary(self) -> dict:
        """Generate summary using pure SQL aggregation."""
        cursor = self.conn.cursor()

        # Single SQL query to get comprehensive summary
        cursor.execute("""
            WITH latest_scan AS (
                SELECT * FROM scans
                ORDER BY timestamp DESC
                LIMIT 1
            ),
            scan_comparison AS (
                SELECT
                    (SELECT total_violations FROM scans ORDER BY timestamp DESC LIMIT 1) as current,
                    (SELECT total_violations FROM scans ORDER BY timestamp DESC LIMIT 1 OFFSET 1) as previous
            ),
            category_summary AS (
                SELECT
                    category,
                    COUNT(*) as count
                FROM violations
                WHERE scan_id = (SELECT scan_id FROM latest_scan)
                GROUP BY category
            ),
            pattern_top5 AS (
                SELECT
                    pattern_name,
                    COUNT(*) as count
                FROM violations
                WHERE scan_id = (SELECT scan_id FROM latest_scan)
                GROUP BY pattern_name
                ORDER BY count DESC
                LIMIT 5
            )
            SELECT
                json_object(
                    'scan_id', (SELECT scan_id FROM latest_scan),
                    'timestamp', (SELECT timestamp FROM latest_scan),
                    'total_violations', (SELECT total_violations FROM latest_scan),
                    'scanned_files', (SELECT scanned_files FROM latest_scan),
                    'trend', json_object(
                        'current', (SELECT current FROM scan_comparison),
                        'previous', (SELECT previous FROM scan_comparison),
                        'change', (SELECT current - previous FROM scan_comparison)
                    ),
                    'categories', (
                        SELECT json_group_array(
                            json_object('name', category, 'count', count)
                        ) FROM category_summary
                    ),
                    'top_patterns', (
                        SELECT json_group_array(
                            json_object('name', pattern_name, 'count', count)
                        ) FROM pattern_top5
                    ),
                    'database_stats', json_object(
                        'total_scans', (SELECT COUNT(*) FROM scans),
                        'total_violations', (SELECT COUNT(*) FROM violations),
                        'unique_patterns', (SELECT COUNT(DISTINCT pattern_name) FROM violations),
                        'unique_files', (SELECT COUNT(DISTINCT file_path) FROM violations)
                    )
                ) as summary
        """)

        result = cursor.fetchone()
        if result and result["summary"]:
            import json

            return json.loads(result["summary"])
        return {}

    def print_automatic_report(self):
        """Print automatically generated report to console."""
        # Executive Summary
        self.console.print("[bold cyan]═══ AUTOMATIC SCAN REPORT ═══[/bold cyan]\n")

        # Get SQL-based summary
        summary = self.generate_sql_based_summary()

        if not summary:
            self.console.print("[yellow]No scan data available for report generation.[/yellow]")
            return

        # Status Panel
        from rich.panel import Panel

        status_text = f"""
📊 Scan ID: {summary.get('scan_id', 'N/A')}
📅 Timestamp: {summary.get('timestamp', 'N/A')[:19]}
📁 Files Scanned: {summary.get('scanned_files', 0)}
🔍 Total Violations: {summary.get('total_violations', 0)}
        """
        self.console.print(Panel(status_text.strip(), title="Current Status", border_style="blue"))

        # Trend
        if summary.get("trend"):
            trend = summary["trend"]
            change = trend.get("change", 0)
            symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            color = "red" if change > 0 else "green" if change < 0 else "yellow"
            self.console.print(f"\n{symbol} Trend: [{color}]{change:+d}[/{color}] violations vs previous scan\n")

        # Categories
        if summary.get("categories"):
            cat_table = Table(title="Violations by Category", box=box.ROUNDED)
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Count", justify="right")
            cat_table.add_column("Bar")

            max_count = max(c["count"] for c in summary["categories"])
            for cat in summary["categories"]:
                bar_length = int((cat["count"] / max_count) * 20) if max_count > 0 else 0
                bar = "█" * bar_length
                cat_table.add_row(cat["name"], str(cat["count"]), f"[blue]{bar}[/blue]")

            self.console.print(cat_table)

        # Top Patterns
        if summary.get("top_patterns"):
            self.console.print("\n[bold]Top 5 Patterns:[/bold]")
            for i, pattern in enumerate(summary["top_patterns"], 1):
                self.console.print(f"  {i}. [yellow]{pattern['name']}[/yellow]: {pattern['count']} occurrences")

        # Database Stats
        if summary.get("database_stats"):
            stats = summary["database_stats"]
            self.console.print(f"\n[dim]Database Statistics:[/dim]")
            self.console.print(f"[dim]  • Total Scans: {stats['total_scans']}[/dim]")
            self.console.print(f"[dim]  • Total Violations Tracked: {stats['total_violations']}[/dim]")
            self.console.print(f"[dim]  • Unique Patterns: {stats['unique_patterns']}[/dim]")
            self.console.print(f"[dim]  • Unique Files: {stats['unique_files']}[/dim]")

    def export_markdown_report(self, output_path: Path):
        """Export full report as markdown."""
        report = self.generate_executive_summary()
        report += "\n\n---\n\n"
        report += self.generate_detailed_report()

        output_path.write_text(report)
        self.console.print(f"[green]✅ Report exported to: {output_path}[/green]")

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Generate automatic report."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate automatic scan reports")
    parser.add_argument("--export", type=Path, help="Export report to markdown file")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")

    args = parser.parse_args()

    generator = ScanReportGenerator()

    try:
        if args.json:
            import json

            summary = generator.generate_sql_based_summary()
            print(json.dumps(summary, indent=2))
        elif args.export:
            generator.export_markdown_report(args.export)
        else:
            generator.print_automatic_report()
    finally:
        generator.close()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

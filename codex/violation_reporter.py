#!/usr/bin/env python3
"""
Violation Reporter for Codex Scanner

Provides clear, transparent reporting of violations with proper formatting
and complete context information.
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import logfire
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import PatternMatch


@dataclass
class ViolationReport:
    """Complete violation report with context and statistics."""

    scan_root: Path
    total_files_scanned: int
    total_violations: int
    violations_by_pattern: dict[str, int] = field(default_factory=dict)
    violations_by_file: dict[str, int] = field(default_factory=dict)
    violations_by_priority: dict[str, int] = field(default_factory=dict)
    scan_duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    all_violations: list[PatternMatch] = field(default_factory=list)


class ViolationReporter:
    """
    Transparent violation reporting with multiple output formats.

    Handles violation output with:
    - Clear file path display
    - Proper formatting without logger prefixes
    - Grouping and statistics
    - JSON export capability
    """

    def __init__(self, console: Console | None = None, quiet: bool = False):
        self.console = console or Console(file=sys.stderr)
        self.quiet = quiet
        self.violations: list[PatternMatch] = []
        self.files_scanned: int = 0

        # Initialize Logfire for local development (no authentication required)
        try:
            logfire.configure(
                service_name="codex-scanner",
                send_to_logfire=False,  # Don't send to cloud, just local logging
                console=False,  # Don't spam console with logfire logs
            )
        except Exception:
            # If Logfire fails to initialize, continue without it
            pass

    def report_violation(self, violation: PatternMatch) -> None:
        """Report a single violation with clear formatting."""
        self.violations.append(violation)

        # Log structured violation data to Logfire
        try:
            logfire.info(
                "Violation detected",
                file_path=violation.file_path,
                line_number=violation.line_number,
                pattern_name=violation.pattern_name,
                priority=violation.priority,
                matched_code=violation.matched_code,
                suggestion=violation.suggestion,
                confidence=violation.confidence,
            )
        except Exception:
            # Continue if logfire fails
            pass

        if not self.quiet:
            # Create a clean, formatted violation message
            file_path = violation.file_path
            line_num = violation.line_number or "?"
            pattern = violation.pattern_name
            suggestion = violation.suggestion or "No suggestion available"

            # Format: file:line: pattern - suggestion
            violation_text = f"{file_path}:{line_num}: {pattern} - {suggestion}"

            # Output to console without logging prefixes
            self.console.print(violation_text, style="red")

    def report_file_start(self, file_path: Path) -> None:
        """Report that scanning of a file has started."""
        self.files_scanned += 1

        # Log file scanning to Logfire for observability
        try:
            logfire.debug("File scan started", file_path=str(file_path))
        except Exception:
            pass

    def report_file_complete(self, file_path: Path, violation_count: int) -> None:
        """Report that scanning of a file is complete."""
        # Log completion with violation count to Logfire
        try:
            logfire.debug("File scan completed", file_path=str(file_path), violation_count=violation_count)
        except Exception:
            pass

        if not self.quiet and violation_count > 0:
            # Show summary for files with violations
            self.console.print(f"  → Found {violation_count} violations in {file_path}", style="yellow")

    def generate_report(self, scan_root: Path, scan_duration_ms: float = 0.0) -> ViolationReport:
        """Generate a complete violation report."""

        # Calculate statistics
        violations_by_pattern = {}
        violations_by_file = {}
        violations_by_priority = {}

        for violation in self.violations:
            # By pattern
            pattern = violation.pattern_name
            violations_by_pattern[pattern] = violations_by_pattern.get(pattern, 0) + 1

            # By file
            file_path = violation.file_path
            violations_by_file[file_path] = violations_by_file.get(file_path, 0) + 1

            # By priority
            priority = violation.priority
            violations_by_priority[priority] = violations_by_priority.get(priority, 0) + 1

        return ViolationReport(
            scan_root=scan_root,
            total_files_scanned=self.files_scanned,
            total_violations=len(self.violations),
            violations_by_pattern=violations_by_pattern,
            violations_by_file=violations_by_file,
            violations_by_priority=violations_by_priority,
            scan_duration_ms=scan_duration_ms,
            all_violations=self.violations.copy(),
        )

    def print_summary(self, report: ViolationReport) -> None:
        """Print a detailed summary of violations found."""

        if self.quiet:
            # Just print the count
            print(f"Found {report.total_violations} violations in {report.total_files_scanned} files")
            return

        # Main summary
        summary_table = Table(title="Scan Summary", border_style="cyan")
        summary_table.add_column("Metric", style="bold")
        summary_table.add_column("Value", justify="right")

        summary_table.add_row("Scan Root", str(report.scan_root))
        summary_table.add_row("Files Scanned", str(report.total_files_scanned))
        summary_table.add_row("Total Violations", f"[red]{report.total_violations}[/red]")
        summary_table.add_row("Scan Duration", f"{report.scan_duration_ms:.1f}ms")
        summary_table.add_row("Avg per File", f"{report.total_violations / max(report.total_files_scanned, 1):.1f}")

        self.console.print(summary_table)

        # Violations by priority
        if report.violations_by_priority:
            priority_table = Table(title="Violations by Priority", border_style="yellow")
            priority_table.add_column("Priority", style="bold")
            priority_table.add_column("Count", justify="right")
            priority_table.add_column("Percentage", justify="right")

            total = report.total_violations
            for priority in ["MANDATORY", "CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                count = report.violations_by_priority.get(priority, 0)
                if count > 0:
                    percentage = f"{count / total * 100:.1f}%"
                    color = (
                        "red" if priority in ["MANDATORY", "CRITICAL"] else "yellow" if priority == "HIGH" else "white"
                    )
                    priority_table.add_row(f"[{color}]{priority}[/{color}]", str(count), percentage)

            self.console.print(priority_table)

        # Top violations by pattern
        if report.violations_by_pattern:
            pattern_table = Table(title="Top Violations by Pattern", border_style="magenta")
            pattern_table.add_column("Pattern", style="bold")
            pattern_table.add_column("Count", justify="right")
            pattern_table.add_column("Percentage", justify="right")

            total = report.total_violations
            sorted_patterns = sorted(report.violations_by_pattern.items(), key=lambda x: x[1], reverse=True)

            for pattern, count in sorted_patterns[:10]:  # Top 10
                percentage = f"{count / total * 100:.1f}%"
                pattern_table.add_row(pattern, str(count), percentage)

            if len(sorted_patterns) > 10:
                remaining = sum(count for _, count in sorted_patterns[10:])
                pattern_table.add_row("... others", str(remaining), f"{remaining / total * 100:.1f}%")

            self.console.print(pattern_table)

        # Files with most violations
        if report.violations_by_file:
            file_table = Table(title="Files with Most Violations", border_style="blue")
            file_table.add_column("File", style="bold")
            file_table.add_column("Violations", justify="right")

            sorted_files = sorted(report.violations_by_file.items(), key=lambda x: x[1], reverse=True)

            for file_path, count in sorted_files[:10]:  # Top 10
                # Truncate long paths
                display_path = file_path
                if len(display_path) > 50:
                    display_path = "..." + display_path[-47:]
                file_table.add_row(display_path, str(count))

            self.console.print(file_table)

    def export_json(self, report: ViolationReport, output_path: Path) -> None:
        """Export violation report to JSON."""

        # Convert violations to dict format
        violations_data = []
        for violation in report.all_violations:
            violations_data.append(
                {
                    "file_path": violation.file_path,
                    "line_number": violation.line_number,
                    "pattern_id": violation.pattern_id,
                    "pattern_name": violation.pattern_name,
                    "priority": violation.priority,
                    "matched_code": violation.matched_code,
                    "suggestion": violation.suggestion,
                    "confidence": violation.confidence,
                }
            )

        report_data = {
            "scan_report": {
                "timestamp": report.timestamp,
                "scan_root": str(report.scan_root),
                "summary": {
                    "total_files_scanned": report.total_files_scanned,
                    "total_violations": report.total_violations,
                    "scan_duration_ms": report.scan_duration_ms,
                },
                "statistics": {
                    "violations_by_pattern": report.violations_by_pattern,
                    "violations_by_file": report.violations_by_file,
                    "violations_by_priority": report.violations_by_priority,
                },
                "violations": violations_data,
            }
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        self.console.print(f"[green]Violation report exported to: {output_path}[/green]")

    def print_violations_by_file(self, report: ViolationReport, max_files: int = 20) -> None:
        """Print violations grouped by file."""

        if self.quiet:
            return

        violations_by_file = {}
        for violation in report.all_violations:
            file_path = violation.file_path
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)

        # Sort files by violation count
        sorted_files = sorted(violations_by_file.items(), key=lambda x: len(x[1]), reverse=True)

        for i, (file_path, violations) in enumerate(sorted_files[:max_files]):
            panel_title = f"📄 {file_path} ({len(violations)} violations)"

            violation_lines = []
            for violation in violations[:10]:  # Show first 10 violations per file
                line_num = violation.line_number or "?"
                priority = violation.priority
                pattern = violation.pattern_name
                suggestion = violation.suggestion or "No suggestion"

                violation_lines.append(f"Line {line_num}: [{priority}] {pattern}")
                violation_lines.append(f"  → {suggestion}")

            if len(violations) > 10:
                violation_lines.append(f"  ... and {len(violations) - 10} more violations")

            content = "\n".join(violation_lines)
            self.console.print(Panel(content, title=panel_title, border_style="blue"))

        if len(sorted_files) > max_files:
            remaining = len(sorted_files) - max_files
            self.console.print(f"[dim]... and {remaining} more files with violations[/dim]")


if __name__ == "__main__":
    # Example usage
    from pathlib import Path

    reporter = ViolationReporter()

    # Create some example violations
    from .models import PatternMatch, PatternPriority

    violation1 = PatternMatch(
        pattern_id=1,
        pattern_name="no-cors-wildcard",
        priority=PatternPriority.CRITICAL,
        file_path="app.py",
        line_number=42,
        matched_code="origins = ['*']",
        suggestion="Replace with specific origins",
        confidence=0.9,
    )

    violation2 = PatternMatch(
        pattern_id=2,
        pattern_name="mock-code-naming",
        priority=PatternPriority.HIGH,
        file_path="test.py",
        line_number=15,
        matched_code="def fake_function():",
        suggestion="Use mock_ prefix",
        confidence=0.8,
    )

    # Report violations
    reporter.report_violation(violation1)
    reporter.report_violation(violation2)

    # Generate and print report
    report = reporter.generate_report(Path("."))
    reporter.print_summary(report)
    reporter.print_violations_by_file(report)

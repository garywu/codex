#!/usr/bin/env python3
"""
Scan Context - Complete Decision Tracking

Tracks every decision made during scanning with detailed reasoning,
providing complete transparency and auditability for scan operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import logfire


class DecisionType(str, Enum):
    """Types of decisions made during scanning."""

    FILE_INCLUDED = "file_included"
    FILE_EXCLUDED = "file_excluded"
    PATTERN_MATCHED = "pattern_matched"
    PATTERN_SKIPPED = "pattern_skipped"
    VIOLATION_DETECTED = "violation_detected"
    VIOLATION_FILTERED = "violation_filtered"
    FIX_APPLIED = "fix_applied"
    FIX_SKIPPED = "fix_skipped"
    SCAN_ERROR = "scan_error"


@dataclass
class Decision:
    """A single decision made during scanning."""

    timestamp: datetime
    decision_type: DecisionType
    context: str  # What was being processed
    reason: str  # Why the decision was made
    details: dict[str, Any] = field(default_factory=dict)
    file_path: str | None = None
    pattern_name: str | None = None
    confidence: float | None = None
    processing_time_ms: float | None = None


@dataclass
class ScanPhase:
    """A phase of the scanning process."""

    name: str
    start_time: datetime
    end_time: datetime | None = None
    decisions: list[Decision] = field(default_factory=list)
    subphases: list["ScanPhase"] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        """Calculate phase duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0


class ScanContext:
    """
    Complete scan context tracking all decisions and phases.

    This class provides full transparency by recording:
    - Every decision made during scanning
    - Why each decision was made
    - Performance metrics for each step
    - Complete audit trail of the scan process
    """

    def __init__(self, scan_root: Path, verbose: bool = False):
        self.scan_root = scan_root
        self.start_time = datetime.now()
        self.end_time: datetime | None = None
        self.verbose = verbose  # Verbose mode for detailed explanations

        # Decision tracking
        self.decisions: list[Decision] = []
        self.phases: list[ScanPhase] = []
        self.current_phase: ScanPhase | None = None

        # Performance tracking
        self.files_processed = 0
        self.patterns_checked = 0
        self.violations_found = 0
        self.errors_encountered = 0

        # Configuration tracking
        self.config_snapshot: dict[str, Any] = {}
        self.patterns_used: list[str] = []
        self.exclusions_applied: list[str] = []

        # Initialize Logfire for structured logging
        try:
            logfire.configure(service_name="codex-scan-context", send_to_logfire=False, console=False)
        except Exception:
            pass

    def start_phase(self, phase_name: str) -> ScanPhase:
        """Start a new scanning phase."""
        # End current phase if exists
        if self.current_phase and not self.current_phase.end_time:
            self.current_phase.end_time = datetime.now()

        # Start new phase
        phase = ScanPhase(name=phase_name, start_time=datetime.now())
        self.phases.append(phase)
        self.current_phase = phase

        # Log phase start
        try:
            logfire.info("Scan phase started", phase_name=phase_name, scan_root=str(self.scan_root))
        except Exception:
            pass

        return phase

    def end_phase(self, phase_name: str | None = None) -> None:
        """End the current or specified phase."""
        if self.current_phase:
            self.current_phase.end_time = datetime.now()

            # Log phase completion
            try:
                logfire.info(
                    "Scan phase completed",
                    phase_name=self.current_phase.name,
                    duration_ms=self.current_phase.duration_ms,
                    decisions_made=len(self.current_phase.decisions),
                )
            except Exception:
                pass

    def record_decision(
        self,
        decision_type: DecisionType,
        context: str,
        reason: str,
        file_path: Path | None = None,
        pattern_name: str | None = None,
        confidence: float | None = None,
        processing_time_ms: float | None = None,
        **details,
    ) -> Decision:
        """Record a decision made during scanning."""

        decision = Decision(
            timestamp=datetime.now(),
            decision_type=decision_type,
            context=context,
            reason=reason,
            file_path=str(file_path) if file_path else None,
            pattern_name=pattern_name,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            details=details,
        )

        # Add to global decisions
        self.decisions.append(decision)

        # Add to current phase
        if self.current_phase:
            self.current_phase.decisions.append(decision)

        # Update counters
        if decision_type == DecisionType.FILE_INCLUDED:
            self.files_processed += 1
        elif decision_type == DecisionType.PATTERN_MATCHED:
            self.patterns_checked += 1
        elif decision_type == DecisionType.VIOLATION_DETECTED:
            self.violations_found += 1
        elif decision_type == DecisionType.SCAN_ERROR:
            self.errors_encountered += 1

        # Log to Logfire
        try:
            logfire.debug(
                "Decision recorded",
                decision_type=decision_type.value,
                context=context,
                reason=reason,
                file_path=decision.file_path,
                pattern_name=pattern_name,
                confidence=confidence,
            )
        except Exception:
            pass

        # Verbose output for explain mode
        if self.verbose:
            import sys

            timestamp = decision.timestamp.strftime("%H:%M:%S.%f")[:-3]

            # Color-code by decision type
            if decision_type == DecisionType.FILE_INCLUDED:
                symbol = "✅"
                color = "\033[92m"  # Green
            elif decision_type == DecisionType.FILE_EXCLUDED:
                symbol = "❌"
                color = "\033[91m"  # Red
            elif decision_type == DecisionType.VIOLATION_DETECTED:
                symbol = "⚠️"
                color = "\033[93m"  # Yellow
            elif decision_type == DecisionType.PATTERN_MATCHED:
                symbol = "🔍"
                color = "\033[94m"  # Blue
            elif decision_type == DecisionType.SCAN_ERROR:
                symbol = "❗"
                color = "\033[91m"  # Red
            else:
                symbol = "•"
                color = "\033[0m"  # Default

            reset = "\033[0m"

            # Format the explanation
            explanation = f"{color}[{timestamp}] {symbol} {decision_type.value.upper()}{reset}\n"
            explanation += f"  Context: {context}\n"
            explanation += f"  Reason: {reason}\n"

            if decision.file_path:
                explanation += f"  File: {decision.file_path}\n"
            if pattern_name:
                explanation += f"  Pattern: {pattern_name}\n"
            if confidence is not None:
                explanation += f"  Confidence: {confidence:.1%}\n"
            if processing_time_ms is not None:
                explanation += f"  Time: {processing_time_ms:.2f}ms\n"
            if details:
                explanation += f"  Details: {details}\n"

            print(explanation, file=sys.stderr)

        return decision

    def record_file_included(
        self, file_path: Path, reason: str, file_size: int | None = None, language: str | None = None
    ) -> Decision:
        """Record that a file was included in scanning."""
        return self.record_decision(
            DecisionType.FILE_INCLUDED,
            f"Processing file: {file_path.name}",
            reason,
            file_path=file_path,
            file_size=file_size,
            language=language,
        )

    def record_file_excluded(self, file_path: Path, reason: str, matched_pattern: str | None = None) -> Decision:
        """Record that a file was excluded from scanning."""
        return self.record_decision(
            DecisionType.FILE_EXCLUDED,
            f"Excluding file: {file_path.name}",
            reason,
            file_path=file_path,
            matched_pattern=matched_pattern,
        )

    def record_pattern_check(
        self,
        pattern_name: str,
        file_path: Path,
        matched: bool,
        reason: str,
        processing_time_ms: float,
        confidence: float | None = None,
    ) -> Decision:
        """Record the result of checking a pattern against a file."""
        decision_type = DecisionType.PATTERN_MATCHED if matched else DecisionType.PATTERN_SKIPPED

        return self.record_decision(
            decision_type,
            f"Checking pattern '{pattern_name}' against {file_path.name}",
            reason,
            file_path=file_path,
            pattern_name=pattern_name,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
        )

    def record_violation(
        self,
        pattern_name: str,
        file_path: Path,
        line_number: int,
        matched_code: str,
        confidence: float,
        reason: str = "Pattern violation detected",
    ) -> Decision:
        """Record a violation detection."""
        return self.record_decision(
            DecisionType.VIOLATION_DETECTED,
            f"Violation in {file_path.name}:{line_number}",
            reason,
            file_path=file_path,
            pattern_name=pattern_name,
            confidence=confidence,
            line_number=line_number,
            matched_code=matched_code,
        )

    def record_error(
        self, context: str, error_message: str, file_path: Path | None = None, pattern_name: str | None = None
    ) -> Decision:
        """Record an error encountered during scanning."""
        return self.record_decision(
            DecisionType.SCAN_ERROR,
            context,
            f"Error: {error_message}",
            file_path=file_path,
            pattern_name=pattern_name,
            error_type=type(Exception).__name__,
            error_message=error_message,
        )

    def set_configuration(self, config: dict[str, Any]) -> None:
        """Record the configuration used for this scan."""
        self.config_snapshot = config.copy()

        # Extract key configuration elements
        if "patterns" in config:
            self.patterns_used = config["patterns"]
        if "exclude" in config:
            self.exclusions_applied = config["exclude"]

    def finalize_scan(self) -> None:
        """Finalize the scan context."""
        self.end_time = datetime.now()

        # End any open phase
        if self.current_phase and not self.current_phase.end_time:
            self.end_phase()

        # Log scan completion
        try:
            logfire.info(
                "Scan completed",
                scan_root=str(self.scan_root),
                duration_ms=self.total_duration_ms,
                files_processed=self.files_processed,
                violations_found=self.violations_found,
                errors_encountered=self.errors_encountered,
            )
        except Exception:
            pass

    @property
    def total_duration_ms(self) -> float:
        """Total scan duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return (datetime.now() - self.start_time).total_seconds() * 1000

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the scan context."""
        return {
            "scan_root": str(self.scan_root),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.total_duration_ms,
            "statistics": {
                "files_processed": self.files_processed,
                "patterns_checked": self.patterns_checked,
                "violations_found": self.violations_found,
                "errors_encountered": self.errors_encountered,
                "decisions_made": len(self.decisions),
            },
            "phases": [
                {"name": phase.name, "duration_ms": phase.duration_ms, "decisions_count": len(phase.decisions)}
                for phase in self.phases
            ],
            "configuration": self.config_snapshot,
        }

    def get_decisions_by_type(self, decision_type: DecisionType) -> list[Decision]:
        """Get all decisions of a specific type."""
        return [d for d in self.decisions if d.decision_type == decision_type]

    def get_decisions_by_file(self, file_path: Path) -> list[Decision]:
        """Get all decisions related to a specific file."""
        file_str = str(file_path)
        return [d for d in self.decisions if d.file_path == file_str]

    def get_decisions_by_pattern(self, pattern_name: str) -> list[Decision]:
        """Get all decisions related to a specific pattern."""
        return [d for d in self.decisions if d.pattern_name == pattern_name]

    def export_audit_trail(self, output_path: Path) -> None:
        """Export complete audit trail to JSON."""
        import json

        audit_data = {
            "scan_audit_trail": {
                "metadata": self.get_summary(),
                "phases": [
                    {
                        "name": phase.name,
                        "start_time": phase.start_time.isoformat(),
                        "end_time": phase.end_time.isoformat() if phase.end_time else None,
                        "duration_ms": phase.duration_ms,
                        "decisions": [
                            {
                                "timestamp": d.timestamp.isoformat(),
                                "type": d.decision_type.value,
                                "context": d.context,
                                "reason": d.reason,
                                "file_path": d.file_path,
                                "pattern_name": d.pattern_name,
                                "confidence": d.confidence,
                                "processing_time_ms": d.processing_time_ms,
                                "details": d.details,
                            }
                            for d in phase.decisions
                        ],
                    }
                    for phase in self.phases
                ],
                "all_decisions": [
                    {
                        "timestamp": d.timestamp.isoformat(),
                        "type": d.decision_type.value,
                        "context": d.context,
                        "reason": d.reason,
                        "file_path": d.file_path,
                        "pattern_name": d.pattern_name,
                        "confidence": d.confidence,
                        "processing_time_ms": d.processing_time_ms,
                        "details": d.details,
                    }
                    for d in self.decisions
                ],
            }
        }

        with open(output_path, "w") as f:
            json.dump(audit_data, f, indent=2)

    def print_decision_summary(self, console=None) -> None:
        """Print a summary of decisions made."""
        if console is None:
            from rich.console import Console

            console = Console()

        from rich.panel import Panel
        from rich.table import Table

        # Decision type summary
        decision_counts = {}
        for decision_type in DecisionType:
            count = len(self.get_decisions_by_type(decision_type))
            if count > 0:
                decision_counts[decision_type.value] = count

        # Create summary table
        table = Table(title="Scan Decision Summary", border_style="cyan")
        table.add_column("Decision Type", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Description", style="dim")

        descriptions = {
            "file_included": "Files processed for scanning",
            "file_excluded": "Files excluded from scanning",
            "pattern_matched": "Patterns that found violations",
            "pattern_skipped": "Patterns that found no violations",
            "violation_detected": "Code violations identified",
            "violation_filtered": "Violations filtered out",
            "fix_applied": "Automatic fixes applied",
            "fix_skipped": "Fixes that were skipped",
            "scan_error": "Errors encountered during scan",
        }

        for decision_type, count in decision_counts.items():
            description = descriptions.get(decision_type, "")
            table.add_row(decision_type.replace("_", " ").title(), str(count), description)

        console.print(table)

        # Performance summary
        perf_panel = Panel(
            f"[bold]Performance Summary[/bold]\n\n"
            f"Total Duration: {self.total_duration_ms:.1f}ms\n"
            f"Files/Second: {self.files_processed / (self.total_duration_ms / 1000):.1f}\n"
            f"Patterns/Second: {self.patterns_checked / (self.total_duration_ms / 1000):.1f}\n"
            f"Avg per File: {self.total_duration_ms / max(self.files_processed, 1):.1f}ms",
            border_style="green",
        )
        console.print(perf_panel)


if __name__ == "__main__":
    # Example usage

    # Create scan context
    context = ScanContext(Path("."))

    # Start phases and record decisions
    context.start_phase("File Discovery")
    context.record_file_included(Path("test.py"), "Python file matching scan pattern", file_size=1024)
    context.record_file_excluded(Path("build/test.py"), "In build directory", matched_pattern="build")
    context.end_phase()

    context.start_phase("Pattern Checking")
    context.record_pattern_check("no-cors-wildcard", Path("test.py"), True, "Found CORS wildcard", 5.2, 0.9)
    context.record_violation("no-cors-wildcard", Path("test.py"), 42, "origins = ['*']", 0.9)
    context.end_phase()

    # Finalize and show summary
    context.finalize_scan()
    context.print_decision_summary()

    # Export audit trail
    context.export_audit_trail(Path("scan_audit.json"))
    print(f"\nAudit trail exported to scan_audit.json")

#!/usr/bin/env python3
"""
Fix Orchestrator

Coordinates all fixing systems and provides a unified, safe interface
for applying fixes with comprehensive monitoring and rollback capabilities.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .fix_audit_trail import FixAuditTrail, FixDecision
from .fix_context_analyzer import FixConflictDetector, FixContextAnalyzer
from .fix_validation_rules import FixSafetyAnalyzer
from .safe_fixer import SafeFixer


class FixMode(str, Enum):
    """Fixing modes with different safety levels."""

    SIMULATE = "simulate"  # Dry run, no changes
    CONSERVATIVE = "conservative"  # Only very safe fixes
    STANDARD = "standard"  # Normal safety checks
    AGGRESSIVE = "aggressive"  # More permissive (still safe)
    INTERACTIVE = "interactive"  # Ask for each fix


@dataclass
class FixCheckpoint:
    """Checkpoint for incremental fixing."""

    checkpoint_id: str
    timestamp: datetime
    files_processed: set[str]
    fixes_applied: list[str]
    can_resume: bool
    state_data: dict[str, Any]


@dataclass
class FixSimulationResult:
    """Result of simulating a fix."""

    would_succeed: bool
    estimated_changes: int
    affected_files: list[str]
    potential_issues: list[str]
    risk_assessment: str
    confidence_score: float


@dataclass
class FixImpactAnalysis:
    """Analysis of fix impact on codebase."""

    total_lines_affected: int
    functions_modified: list[str]
    classes_modified: list[str]
    imports_changed: list[str]
    test_coverage_impact: float | None
    performance_impact: str | None
    breaking_change_risk: str  # low, medium, high
    dependencies_affected: list[str]


class FixOrchestrator:
    """
    Master orchestrator for all fixing operations.

    Coordinates:
    - Safety validation
    - Context analysis
    - Conflict resolution
    - Audit trail
    - Progress monitoring
    - Checkpointing
    - Rollback
    """

    def __init__(
        self, mode: FixMode = FixMode.STANDARD, console: Console | None = None, enable_monitoring: bool = True
    ):
        self.mode = mode
        self.console = console or Console()
        self.enable_monitoring = enable_monitoring

        # Initialize all subsystems
        self.safe_fixer = SafeFixer(console=self.console)
        self.context_analyzer = FixContextAnalyzer()
        self.conflict_detector = FixConflictDetector()
        self.safety_analyzer = FixSafetyAnalyzer()
        self.audit_trail = FixAuditTrail()

        # State tracking
        self.current_checkpoint: FixCheckpoint | None = None
        self.fix_queue: list[dict[str, Any]] = []
        self.completed_fixes: list[str] = []
        self.failed_fixes: list[dict[str, Any]] = []
        self.skipped_fixes: list[dict[str, Any]] = []

        # Monitoring
        self.start_time: float | None = None
        self.metrics: dict[str, Any] = {}

    async def orchestrate_fixes(
        self, violations: list[dict[str, Any]], checkpoint_file: Path | None = None
    ) -> dict[str, Any]:
        """
        Orchestrate the entire fixing process.

        Args:
            violations: List of violations to fix
            checkpoint_file: Optional checkpoint file for resume capability

        Returns:
            Summary of all fixes applied
        """
        self.start_time = time.time()

        # Load checkpoint if resuming
        if checkpoint_file and checkpoint_file.exists():
            self._load_checkpoint(checkpoint_file)

        # Phase 1: Analysis and Planning
        self.console.print(Panel.fit("[bold cyan]Phase 1: Analysis and Planning[/bold cyan]", border_style="cyan"))

        analysis_results = await self._analyze_all_violations(violations)

        # Phase 2: Conflict Resolution
        self.console.print(Panel.fit("[bold yellow]Phase 2: Conflict Resolution[/bold yellow]", border_style="yellow"))

        resolved_fixes = self._resolve_conflicts(analysis_results)

        # Phase 3: Safety Validation
        self.console.print(Panel.fit("[bold magenta]Phase 3: Safety Validation[/bold magenta]", border_style="magenta"))

        safe_fixes = self._validate_safety(resolved_fixes)

        # Phase 4: Simulation (if enabled)
        if self.mode == FixMode.SIMULATE:
            self.console.print(Panel.fit("[bold blue]Phase 4: Simulation[/bold blue]", border_style="blue"))
            return await self._simulate_fixes(safe_fixes)

        # Phase 5: Execution
        self.console.print(Panel.fit("[bold green]Phase 5: Execution[/bold green]", border_style="green"))

        if self.enable_monitoring:
            return await self._execute_with_monitoring(safe_fixes, checkpoint_file)
        else:
            return await self._execute_fixes(safe_fixes)

    async def _analyze_all_violations(self, violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Analyze context for all violations."""
        analyzed = []

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=self.console
        ) as progress:
            task = progress.add_task("Analyzing violations...", total=len(violations))

            for violation in violations:
                file_path = Path(violation["file_path"])
                line_number = violation.get("line_number", 0)

                # Get context
                context = self.context_analyzer.analyze_violation_context(file_path, line_number)

                # Get safety assessment
                is_safe, safety_reason = self.safety_analyzer.is_fix_safe(
                    violation["pattern_name"], str(file_path), violation.get("matched_code", "")
                )

                # Get risk level
                risk_level = self.safety_analyzer.estimate_risk_level(violation["pattern_name"], str(file_path))

                analyzed.append(
                    {
                        **violation,
                        "context": context,
                        "is_safe": is_safe,
                        "safety_reason": safety_reason,
                        "risk_level": risk_level,
                    }
                )

                progress.update(task, advance=1)

        return analyzed

    def _resolve_conflicts(self, fixes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Resolve conflicts between fixes."""
        conflicts = self.conflict_detector.detect_conflicts(fixes)

        if conflicts:
            self.console.print(f"[yellow]Found {len(conflicts)} conflicts[/yellow]")

            # Show conflicts table
            table = Table(title="Fix Conflicts", border_style="yellow")
            table.add_column("Fix 1")
            table.add_column("Fix 2")
            table.add_column("Reason")

            for i, j, reason in conflicts[:5]:  # Show first 5
                table.add_row(
                    f"{fixes[i]['pattern_name']} @ L{fixes[i].get('line_number', '?')}",
                    f"{fixes[j]['pattern_name']} @ L{fixes[j].get('line_number', '?')}",
                    reason,
                )

            self.console.print(table)

            # Resolve conflicts
            resolved = self.conflict_detector.resolve_conflicts(fixes, conflicts)
            self.console.print(f"[green]Resolved to {len(resolved)} non-conflicting fixes[/green]")
            return resolved

        return fixes

    def _validate_safety(self, fixes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate safety based on mode."""
        safe_fixes = []

        for fix in fixes:
            # Check mode-specific safety
            if self.mode == FixMode.CONSERVATIVE:
                # Only very safe fixes
                if fix["risk_level"] == "low" and fix["is_safe"]:
                    safe_fixes.append(fix)
                else:
                    self.skipped_fixes.append({**fix, "skip_reason": "Not safe enough for conservative mode"})

            elif self.mode == FixMode.STANDARD:
                # Standard safety
                if fix["risk_level"] in ["low", "medium"] and fix["is_safe"]:
                    safe_fixes.append(fix)
                else:
                    self.skipped_fixes.append({**fix, "skip_reason": fix["safety_reason"]})

            elif self.mode == FixMode.AGGRESSIVE:
                # More permissive but still check critical
                if fix["risk_level"] != "critical":
                    safe_fixes.append(fix)
                else:
                    self.skipped_fixes.append({**fix, "skip_reason": "Critical risk even in aggressive mode"})

            else:  # INTERACTIVE or SIMULATE
                safe_fixes.append(fix)

        self.console.print(f"[green]✓ {len(safe_fixes)} fixes passed safety validation[/green]")
        if self.skipped_fixes:
            self.console.print(f"[yellow]⚠ {len(self.skipped_fixes)} fixes skipped for safety[/yellow]")

        return safe_fixes

    async def _simulate_fixes(self, fixes: list[dict[str, Any]]) -> dict[str, Any]:
        """Simulate fixes without applying them."""
        simulation_results = []

        self.console.print("[cyan]Running simulation...[/cyan]")

        for fix in fixes:
            result = await self._simulate_single_fix(fix)
            simulation_results.append({"fix": fix, "simulation": result})

        # Generate simulation report
        report = self._generate_simulation_report(simulation_results)

        # Show simulation summary
        self._show_simulation_summary(simulation_results)

        return report

    async def _simulate_single_fix(self, fix: dict[str, Any]) -> FixSimulationResult:
        """Simulate a single fix."""
        file_path = Path(fix["file_path"])

        # Basic simulation
        would_succeed = fix["is_safe"] and file_path.exists()

        # Estimate changes
        estimated_changes = 1  # Line being fixed
        if fix["pattern_name"] in ["import-order", "unused-imports"]:
            estimated_changes = 5  # Multiple import lines

        # Assess risk
        potential_issues = []
        if fix["context"].in_conditional:
            potential_issues.append("Fix is within conditional block")
        if fix["context"].surrounding_try_except:
            potential_issues.append("Fix is within try/except block")
        if fix["context"].is_async:
            potential_issues.append("Fix is in async context")

        # Calculate confidence
        confidence = 1.0
        confidence -= len(potential_issues) * 0.1
        confidence -= 0.2 if fix["risk_level"] == "high" else 0
        confidence -= 0.1 if fix["risk_level"] == "medium" else 0

        return FixSimulationResult(
            would_succeed=would_succeed,
            estimated_changes=estimated_changes,
            affected_files=[str(file_path)],
            potential_issues=potential_issues,
            risk_assessment=fix["risk_level"],
            confidence_score=max(0, confidence),
        )

    async def _execute_with_monitoring(
        self, fixes: list[dict[str, Any]], checkpoint_file: Path | None = None
    ) -> dict[str, Any]:
        """Execute fixes with real-time monitoring."""
        total_fixes = len(fixes)

        # Create monitoring display
        with Live(console=self.console, refresh_per_second=2) as live:
            # Initialize progress
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            )

            main_task = progress.add_task("Applying fixes...", total=total_fixes)

            # Create monitoring table
            monitor_table = Table(title="Fix Monitoring", border_style="green")
            monitor_table.add_column("Metric", style="cyan")
            monitor_table.add_column("Value", style="yellow")

            for i, fix in enumerate(fixes):
                # Update display
                monitor_table = self._update_monitor_table(i, total_fixes)
                live.update(Panel(progress, title="Progress"))

                # Apply fix
                success = await self._apply_single_fix(fix)

                if success:
                    self.completed_fixes.append(fix["pattern_name"])
                else:
                    self.failed_fixes.append(fix)

                # Update progress
                progress.update(main_task, advance=1)

                # Save checkpoint periodically
                if checkpoint_file and i % 10 == 0:
                    self._save_checkpoint(checkpoint_file, i, fixes)

        return self._generate_final_report()

    async def _execute_fixes(self, fixes: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute fixes without monitoring."""
        for fix in fixes:
            await self._apply_single_fix(fix)

        return self._generate_final_report()

    async def _apply_single_fix(self, fix: dict[str, Any]) -> bool:
        """Apply a single fix with full safety."""
        file_path = Path(fix["file_path"])
        pattern_name = fix["pattern_name"]
        line_number = fix.get("line_number", 0)

        # Record in audit trail
        audit_id = self.audit_trail.record_fix_attempt(
            file_path=file_path,
            pattern_name=pattern_name,
            line_number=line_number,
            violation_text=fix.get("matched_code", ""),
            fix_strategy=fix.get("fix_strategy", "automatic"),
            context_data={"risk_level": fix["risk_level"]},
        )

        # Interactive mode - ask user
        if self.mode == FixMode.INTERACTIVE:
            if not self._ask_user_confirmation(fix):
                self.audit_trail.record_decision(audit_id, FixDecision.USER_REJECTED, "User rejected fix")
                return False

        # Apply fix using safe fixer
        start_time = time.time()

        # Create fix function based on pattern
        fix_function = self._create_fix_function(pattern_name)
        if not fix_function:
            self.audit_trail.record_decision(audit_id, FixDecision.SYSTEM_REJECTED, "No fix function available")
            return False

        success, attempt = self.safe_fixer.apply_fix_safely(
            file_path=file_path, fix_function=fix_function, pattern_name=pattern_name, line_number=line_number
        )

        execution_time = (time.time() - start_time) * 1000

        # Update audit trail
        if success and attempt and attempt.validation:
            self.audit_trail.update_validation_results(
                audit_id,
                syntax_valid=attempt.validation.syntax_valid,
                imports_valid=attempt.validation.imports_valid,
                tests_passed=attempt.validation.test_status == "PASSED" if attempt.validation.test_status else None,
            )

            if attempt.applied:
                self.audit_trail.record_application(
                    audit_id,
                    file_hash_after=attempt.validation.modified_hash,
                    execution_time_ms=execution_time,
                    lines_changed=1,  # Calculate from diff
                )

        return success

    def _create_fix_function(self, pattern_name: str) -> callable | None:
        """Create appropriate fix function for pattern."""
        # Import fix functions
        from .batch_fixer import BatchFixer

        fixer = BatchFixer()

        # Map patterns to fix functions
        fix_map = {
            "mock-code-naming": lambda content: fixer._fix_mock_naming_batch(content)[0],
            "use-uv-package-manager": lambda content: fixer._fix_uv_package_manager_batch(content)[0],
            "no-print-production": lambda content: fixer._fix_print_statements_batch(content)[0],
            "standard-import-order": lambda content: fixer._fix_import_order_batch(content)[0],
        }

        return fix_map.get(pattern_name)

    def _ask_user_confirmation(self, fix: dict[str, Any]) -> bool:
        """Ask user to confirm a fix."""
        from rich.prompt import Confirm

        self.console.print(f"\n[yellow]Fix proposal:[/yellow]")
        self.console.print(f"  Pattern: {fix['pattern_name']}")
        self.console.print(f"  File: {fix['file_path']}:{fix.get('line_number', '?')}")
        self.console.print(f"  Risk: {fix['risk_level']}")

        return Confirm.ask("Apply this fix?", default=True)

    def _update_monitor_table(self, current: int, total: int) -> Table:
        """Update monitoring table."""
        table = Table(title="Fix Monitoring", border_style="green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        elapsed = time.time() - self.start_time if self.start_time else 0
        rate = current / elapsed if elapsed > 0 else 0

        table.add_row("Fixes Applied", str(len(self.completed_fixes)))
        table.add_row("Fixes Failed", str(len(self.failed_fixes)))
        table.add_row("Fixes Skipped", str(len(self.skipped_fixes)))
        table.add_row("Progress", f"{current}/{total}")
        table.add_row("Elapsed Time", f"{elapsed:.1f}s")
        table.add_row("Fix Rate", f"{rate:.1f}/s")
        table.add_row("Est. Remaining", f"{(total - current) / rate:.1f}s" if rate > 0 else "N/A")

        return table

    def _save_checkpoint(self, checkpoint_file: Path, current_index: int, all_fixes: list[dict[str, Any]]) -> None:
        """Save checkpoint for resume capability."""
        checkpoint = FixCheckpoint(
            checkpoint_id=f"ckpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            files_processed=set(self.completed_fixes),
            fixes_applied=self.completed_fixes,
            can_resume=True,
            state_data={
                "current_index": current_index,
                "remaining_fixes": len(all_fixes) - current_index,
                "failed_fixes": self.failed_fixes,
                "skipped_fixes": self.skipped_fixes,
            },
        )

        with open(checkpoint_file, "w") as f:
            json.dump(
                {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "timestamp": checkpoint.timestamp.isoformat(),
                    "files_processed": list(checkpoint.files_processed),
                    "fixes_applied": checkpoint.fixes_applied,
                    "can_resume": checkpoint.can_resume,
                    "state_data": checkpoint.state_data,
                },
                f,
                indent=2,
            )

    def _load_checkpoint(self, checkpoint_file: Path) -> None:
        """Load checkpoint for resuming."""
        with open(checkpoint_file) as f:
            data = json.load(f)

        self.current_checkpoint = FixCheckpoint(
            checkpoint_id=data["checkpoint_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            files_processed=set(data["files_processed"]),
            fixes_applied=data["fixes_applied"],
            can_resume=data["can_resume"],
            state_data=data["state_data"],
        )

        self.completed_fixes = data["fixes_applied"]
        self.failed_fixes = data["state_data"].get("failed_fixes", [])
        self.skipped_fixes = data["state_data"].get("skipped_fixes", [])

        self.console.print(f"[green]Resumed from checkpoint {data['checkpoint_id']}[/green]")
        self.console.print(f"  Already completed: {len(self.completed_fixes)} fixes")

    def _show_simulation_summary(self, results: list[dict[str, Any]]) -> None:
        """Show simulation summary."""
        successful = sum(1 for r in results if r["simulation"].would_succeed)
        total_changes = sum(r["simulation"].estimated_changes for r in results)
        avg_confidence = sum(r["simulation"].confidence_score for r in results) / len(results) if results else 0

        summary = Panel(
            f"""[bold]Simulation Results[/bold]

Would succeed: {successful}/{len(results)}
Estimated changes: {total_changes} lines
Average confidence: {avg_confidence:.1%}
High risk fixes: {sum(1 for r in results if r['simulation'].risk_assessment == 'high')}

[yellow]This is a simulation - no files were modified[/yellow]""",
            border_style="blue",
        )

        self.console.print(summary)

    def _generate_simulation_report(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate detailed simulation report."""
        return {
            "mode": "simulation",
            "timestamp": datetime.now().isoformat(),
            "total_fixes_simulated": len(results),
            "would_succeed": sum(1 for r in results if r["simulation"].would_succeed),
            "estimated_total_changes": sum(r["simulation"].estimated_changes for r in results),
            "average_confidence": sum(r["simulation"].confidence_score for r in results) / len(results)
            if results
            else 0,
            "risk_breakdown": {
                "low": sum(1 for r in results if r["simulation"].risk_assessment == "low"),
                "medium": sum(1 for r in results if r["simulation"].risk_assessment == "medium"),
                "high": sum(1 for r in results if r["simulation"].risk_assessment == "high"),
                "critical": sum(1 for r in results if r["simulation"].risk_assessment == "critical"),
            },
            "potential_issues": [issue for r in results for issue in r["simulation"].potential_issues],
            "detailed_results": results,
        }

    def _generate_final_report(self) -> dict[str, Any]:
        """Generate final execution report."""
        elapsed = time.time() - self.start_time if self.start_time else 0

        return {
            "mode": self.mode.value,
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": elapsed,
            "fixes_applied": len(self.completed_fixes),
            "fixes_failed": len(self.failed_fixes),
            "fixes_skipped": len(self.skipped_fixes),
            "success_rate": len(self.completed_fixes) / (len(self.completed_fixes) + len(self.failed_fixes)) * 100
            if self.completed_fixes or self.failed_fixes
            else 0,
            "completed_patterns": self.completed_fixes,
            "failed_fixes": self.failed_fixes,
            "skipped_fixes": self.skipped_fixes,
            "session_id": self.audit_trail.current_session_id,
            "checkpoint": self.current_checkpoint.checkpoint_id if self.current_checkpoint else None,
        }

    async def analyze_fix_impact(self, fixes: list[dict[str, Any]]) -> FixImpactAnalysis:
        """Analyze the impact of applying fixes."""
        total_lines = 0
        functions_modified = set()
        classes_modified = set()
        imports_changed = set()
        dependencies = set()

        for fix in fixes:
            context = fix.get("context")
            if context:
                if context.function_name:
                    functions_modified.add(context.function_name)
                if context.class_name:
                    classes_modified.add(context.class_name)

                # Check if import-related
                if fix["pattern_name"] in ["import-order", "unused-imports"]:
                    imports_changed.update(context.imports)

                dependencies.update(context.dependencies)

            # Estimate lines affected
            if fix["pattern_name"] in ["import-order"]:
                total_lines += 10  # Import section
            else:
                total_lines += 1  # Single line fix

        # Assess breaking change risk
        breaking_risk = "low"
        if classes_modified or functions_modified:
            breaking_risk = "medium"
        if imports_changed:
            breaking_risk = "high" if len(imports_changed) > 5 else "medium"

        return FixImpactAnalysis(
            total_lines_affected=total_lines,
            functions_modified=list(functions_modified),
            classes_modified=list(classes_modified),
            imports_changed=list(imports_changed),
            test_coverage_impact=None,  # Would need coverage data
            performance_impact=None,  # Would need profiling
            breaking_change_risk=breaking_risk,
            dependencies_affected=list(dependencies),
        )


if __name__ == "__main__":
    import asyncio

    # Example usage
    orchestrator = FixOrchestrator(mode=FixMode.SIMULATE)

    # Example violations
    violations = [
        {
            "file_path": "test.py",
            "line_number": 10,
            "pattern_name": "mock-code-naming",
            "matched_code": "def fake_function():",
            "fix_strategy": "automatic",
        },
        {
            "file_path": "test.py",
            "line_number": 20,
            "pattern_name": "use-uv-package-manager",
            "matched_code": "pip install requests",
            "fix_strategy": "automatic",
        },
    ]

    # Run orchestration
    result = asyncio.run(orchestrator.orchestrate_fixes(violations))

    print(json.dumps(result, indent=2))

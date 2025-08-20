"""
CLI interface for Codex - A pattern-based code scanner.

Default command is 'scan' for pre-commit hook integration.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

# Configure Rich Console for proper stdout/stderr separation
_console = Console(stderr=True)  # Status messages go to stderr
_data_console = Console(stderr=False)  # Data output goes to stdout


# Fix for console.logging.info pattern that's used throughout the code
class ConsoleLogger:
    """Wrapper to provide logging-like interface for Rich Console."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def info(self, message: str) -> None:
        self.console.print(message)

    def error(self, message: str) -> None:
        self.console.print(f"[red]{message}[/red]")

    def warning(self, message: str) -> None:
        self.console.print(f"[yellow]{message}[/yellow]")


# Add logging interface with type ignore for dynamic attribute
_console.logging = ConsoleLogger(_console)  # type: ignore[attr-defined]
_data_console.logging = ConsoleLogger(_data_console)  # type: ignore[attr-defined]

# Use the consoles with the understanding they have logging
console = _console  # type: ignore[assignment]
data_console = _data_console  # type: ignore[assignment]

from rich.table import Table

# Check UV environment before running
if not os.environ.get("UV_PROJECT_ENVIRONMENT"):
    from .uv_check import ensure_uv_environment

    ensure_uv_environment()

from .config import load_config

# Database import removed - using unified_database only

# Optional import for Farm client
try:
    from .client import CodexClient
except ImportError:
    CodexClient = None
import logging

from . import pattern_cli
from .ai_query import AIQueryInterface
from .ai_sqlite_query import NaturalLanguageQueryInterface
from .gitignore_handler import GitIgnoreHandler
from .models import PatternCategory
from .pattern_extractor import PatternExtractor
from .pattern_importer import PatternImporter
from .portable_tools import PortableToolManager, RepositoryInitializer
from .project_config import ProjectConfigManager
from .scan_discovery import ScanDiscovery
from .scanner import Scanner
from .settings import settings
from .sqlite_scanner import SQLiteScanner
from .unified_database import UnifiedDatabase

app = typer.Typer(
    name="codex",
    help="Pattern-based code scanner and quality checker",
    rich_markup_mode="rich",
    invoke_without_command=True,
)
# console already configured above with stderr=True

# Add pattern management subcommand
app.add_typer(pattern_cli.app, name="pattern", help="Pattern management commands")

# Add config management subcommand
from . import config_cli

app.add_typer(config_cli.app, name="config", help="Configuration discovery and management")


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version")] = False,
) -> None:
    """
    Codex - Pattern-based code scanner.

    Default action is to scan current directory for pattern violations.
    """
    if version:
        from . import __version__

        console.logging.info(f"codex {__version__}")
        raise typer.Exit(0)

    # If no command specified, run scan
    if ctx.invoked_subcommand is None:
        scan()


@app.command(name="scan", help="Scan files for pattern violations (default)")
def scan(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files or directories to scan")] = None,
    fix: Annotated[bool, typer.Option("--fix", "-f", help="Apply automatic fixes")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Minimal output")] = False,
    diff: Annotated[bool, typer.Option("--diff", help="Show diff of proposed fixes")] = False,
    exclude: Annotated[str | None, typer.Option("--exclude", help="Glob pattern to exclude")] = None,
    no_tools: Annotated[bool, typer.Option("--no-tools", help="Skip external tools (ruff, mypy, typos)")] = False,
    best_practices: Annotated[
        bool,
        typer.Option(
            "--best-practices", "-bp", help="Include negative space analysis for evidence-based best practices"
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output results in JSON format")] = False,
    export_json: Annotated[
        Path | None, typer.Option("--export-json", help="Export detailed results to JSON file")
    ] = None,
    export_audit: Annotated[
        Path | None, typer.Option("--export-audit", help="Export complete audit trail to JSON file")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be scanned without actually scanning")
    ] = False,
    list_files: Annotated[bool, typer.Option("--list-files", help="List all files that would be scanned")] = False,
    explain: Annotated[bool, typer.Option("--explain", help="Verbose mode explaining every decision")] = False,
    fail_on_violations: Annotated[
        bool, typer.Option("--fail-on-violations", help="Exit with code 1 if violations found (for CI/CD)")
    ] = False,
    recommendations: Annotated[
        bool, typer.Option("--recommendations", help="Include technology and architecture recommendations")
    ] = False,
) -> None:
    """Scan files for pattern violations."""

    # Default to current directory if no paths specified
    if not paths:
        paths = [Path.cwd()]

    # Load configuration with auto-init
    from .config import auto_init_project, should_auto_init

    if should_auto_init():
        auto_init_project(Path(".codex/config.toml"))
        if not quiet:
            console.print("[dim]Initialized .codex/config.toml for this project[/dim]")

    config_data, config_path = load_config()

    # Override tools setting if no_tools flag is set
    if no_tools:
        config_data["run_tools"] = False

    async def _scan() -> int:
        """
        Enhanced scan function with negative space analysis integration.

        Uses the new Scanner class with comprehensive pattern detection
        and optional evidence-based best practices analysis.
        """

        # Handle dry-run and list-files modes
        if dry_run or list_files:
            discovery = ScanDiscovery()
            for path in paths:
                if path.is_dir():
                    discovery_result = discovery.discover_files(path)

                    if dry_run:
                        print(f"\n🔍 Dry-run Discovery for {path}:", file=sys.stderr)
                        discovery.print_discovery_summary(discovery_result)
                        print(f"\nWould scan {len(discovery_result.files_to_scan)} files", file=sys.stderr)
                        if len(discovery_result.excluded_files) > 0:
                            print(f"Would exclude {len(discovery_result.excluded_files)} files", file=sys.stderr)

                    if list_files:
                        print(f"\n📄 Files that would be scanned in {path}:", file=sys.stderr)
                        for file_path in sorted(discovery_result.files_to_scan):
                            print(f"  {file_path}")

                        if len(discovery_result.files_to_scan) == 0:
                            print("  (no files match scan criteria)", file=sys.stderr)
                elif path.is_file():
                    if list_files:
                        print(f"  {path}")

            # Exit early for dry-run/list-files
            return 0

        # Show pre-scan discovery summary if not quiet
        if not quiet or explain:
            discovery = ScanDiscovery()

            # Perform discovery for the first directory path
            for path in paths:
                if path.is_dir():
                    discovery_result = discovery.discover_files(path)
                    print(f"\n📋 Pre-scan Discovery for {path}:", file=sys.stderr)
                    discovery.print_discovery_summary(discovery_result)

                    if explain:
                        # Show detailed exclusion reasons
                        print("\n🔍 Detailed Exclusion Explanations:", file=sys.stderr)
                        exclusion_counts = {}
                        for decision in discovery_result.excluded_files[:20]:  # Show first 20
                            reason_key = (
                                f"{decision.reason} ({decision.matched_pattern})"
                                if decision.matched_pattern
                                else decision.reason
                            )
                            if reason_key not in exclusion_counts:
                                exclusion_counts[reason_key] = []
                            exclusion_counts[reason_key].append(decision.file_path)

                        for reason, files in exclusion_counts.items():
                            print(f"\n  Reason: {reason}", file=sys.stderr)
                            for f in files[:5]:  # Show first 5 files per reason
                                print(f"    - {f}", file=sys.stderr)
                            if len(files) > 5:
                                print(f"    ... and {len(files) - 5} more", file=sys.stderr)

                    break  # Only show for first directory to avoid clutter

        # Initialize enhanced scanner with negative space capability
        scanner = Scanner(
            config=config_data,
            quiet=quiet and not explain,  # Never quiet in explain mode
            fix=fix,
            show_diff=diff,
            exclude_pattern=exclude,
            enable_negative_space=best_practices,
            verbose=explain,  # Enable verbose mode when explain is true
        )

        total_violations = 0

        # Process each path
        for path in paths:
            if path.is_file():
                # Scan single file
                result = await scanner.scan_file(path)
                if result.violations:
                    total_violations += len(result.violations)
                    # Violations are already reported by the scanner during scan
                    # No need to report them again here

            elif path.is_dir():
                # Scan directory
                results = await scanner.scan_directory(path)
                for result in results:
                    if result.violations:
                        total_violations += len(result.violations)
                        # Violations are already reported by the scanner during scan
                        # No need to report them again here

                # Run negative space analysis if requested
                if best_practices:
                    try:
                        negative_space_results = await scanner.analyze_project_negative_space(path)

                        if not quiet and "error" not in negative_space_results:
                            logging.info("🌟 Best Practices Analysis Complete!")
                            logging.info(
                                f"Excellence Level: {negative_space_results.get('excellence_level', 'Unknown')}"
                            )
                            logging.info(
                                f"Organization Score: {negative_space_results.get('organization_score', 0):.1%}"
                            )

                    except Exception as e:
                        if not quiet:
                            logging.warning(f"Negative space analysis failed: {e}")
            else:
                if not quiet:
                    logging.warning(f"{path} not found")

        # Finalize scanner and show context summary
        scanner.finalize_scan()

        # Handle JSON output and exports
        scan_context = scanner.get_scan_context()
        violation_reporter = scanner.violation_reporter

        if json_output or export_json or export_audit:
            # Generate violation report
            scan_root = paths[0] if paths else Path.cwd()
            report = violation_reporter.generate_report(
                scan_root, scan_context.total_duration_ms if scan_context else 0.0
            )

            if json_output:
                # Output JSON to stdout for machine processing
                json_data = {
                    "scan_summary": {
                        "total_violations": total_violations,
                        "files_scanned": violation_reporter.files_scanned,
                        "exit_code": 1 if (total_violations > 0 and fail_on_violations) else 0,
                        "scan_duration_ms": scan_context.total_duration_ms if scan_context else 0.0,
                    },
                    "violations": [
                        {
                            "file_path": v.file_path,
                            "line_number": v.line_number,
                            "pattern_name": v.pattern_name,
                            "priority": v.priority,
                            "matched_code": v.matched_code,
                            "suggestion": v.suggestion,
                            "confidence": v.confidence,
                        }
                        for v in report.all_violations
                    ],
                }
                print(json.dumps(json_data, indent=2))
                return 1 if (total_violations > 0 and fail_on_violations) else 0

            if export_json:
                # Export detailed report to JSON file
                violation_reporter.export_json(report, export_json)

            if export_audit and scan_context:
                # Export audit trail to JSON file
                scan_context.export_audit_trail(export_audit)

        # Technology recommendations if requested
        if recommendations and not quiet:
            from .recommendation_engine import ProjectArchitectureAnalyzer

            analyzer = ProjectArchitectureAnalyzer(quiet=quiet)
            tech_recommendations = analyzer.analyze_project(Path.cwd())
            analyzer.print_recommendations(tech_recommendations)

        # Show final summary using console output (no logging prefixes)
        if total_violations > 0:
            if not quiet:
                # Clean summary to stdout (not stderr)
                console.print(f"Found {total_violations} violation(s)")

                # Show scan context summary if available
                if scan_context:
                    scan_context.print_decision_summary()
            # New exit code logic: only fail if explicitly requested
            return 1 if fail_on_violations else 0
        else:
            if not quiet:
                message = "✓ No violations found"
                if best_practices:
                    message += " (includes best practices analysis)"
                if recommendations:
                    message += " (with technology recommendations)"
                console.print(message)

                # Show scan context summary if available
                if scan_context:
                    scan_context.print_decision_summary()
            return 0

    exit_code = asyncio.run(_scan())
    raise typer.Exit(exit_code)


@app.command(name="precommit", help="Pre-commit hook mode - blocks commits on violations")
def precommit(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files to check")] = None,
    recommendations: Annotated[
        bool, typer.Option("--recommendations", help="Include technology recommendations")
    ] = False,
) -> None:
    """Pre-commit hook mode that fails on violations to block commits."""

    # Force fail-on-violations for pre-commit hooks
    import sys
    from pathlib import Path

    if not paths:
        paths = [Path.cwd()]

    # Call scan with pre-commit settings
    sys.argv = ["codex", "scan", "--fail-on-violations", "--quiet"]
    if recommendations:
        sys.argv.append("--recommendations")
    for path in paths:
        sys.argv.append(str(path))

    # Re-invoke scan with pre-commit settings
    from .config import auto_init_project, should_auto_init

    if should_auto_init():
        auto_init_project(Path(".codex/config.toml"))

    config_data, config_path = load_config()

    async def _precommit_scan() -> int:
        from .scanner import Scanner

        scanner = Scanner(quiet=True)

        total_violations = 0
        for path in paths:
            if path.is_file():
                result = await scanner.scan_file(path)
                total_violations += len(result.violations) if result.violations else 0
            elif path.is_dir():
                results = await scanner.scan_directory(path)
                for result in results:
                    total_violations += len(result.violations) if result.violations else 0

        return 1 if total_violations > 0 else 0

    exit_code = asyncio.run(_precommit_scan())
    raise typer.Exit(exit_code)


@app.command(name="ci", help="CI/CD mode - structured output for automation")
def ci(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files or directories to check")] = None,
    format_output: Annotated[str, typer.Option("--format", help="Output format: json, text")] = "text",
    recommendations: Annotated[
        bool, typer.Option("--recommendations", help="Include technology recommendations")
    ] = False,
    no_fail: Annotated[bool, typer.Option("--no-fail", help="Don't exit with error code on violations")] = False,
) -> None:
    """CI/CD mode with structured output for automation."""

    # Default to current directory if no paths specified
    if not paths:
        paths = [Path.cwd()]

    # Auto-init if needed
    from .config import auto_init_project, should_auto_init

    if should_auto_init():
        auto_init_project(Path(".codex/config.toml"))

    config_data, config_path = load_config()

    async def _check_scan() -> int:
        from .scanner import Scanner

        scanner = Scanner(quiet=True)
        all_violations = []

        for path in paths:
            if path.is_file():
                result = await scanner.scan_file(path)
                if result.violations:
                    all_violations.extend(result.violations)
            elif path.is_dir():
                results = await scanner.scan_directory(path)
                for result in results:
                    if result.violations:
                        all_violations.extend(result.violations)

        # Technology recommendations if requested
        if recommendations:
            from .recommendation_engine import ProjectArchitectureAnalyzer

            analyzer = ProjectArchitectureAnalyzer(quiet=True)
            tech_recommendations = analyzer.analyze_project(Path.cwd())
        else:
            tech_recommendations = []

        # Output results
        if format_output == "json":
            import json

            result = {
                "violations": len(all_violations),
                "files_scanned": len([p for p in paths if p.is_file()]),
                "recommendations": [
                    {
                        "technology": rec.technology,
                        "priority": rec.priority,
                        "reason": rec.reason,
                        "effort": rec.implementation_effort,
                    }
                    for rec in tech_recommendations
                ],
                "exit_code": 1 if (len(all_violations) > 0 and not no_fail) else 0,
            }
            print(json.dumps(result, indent=2))
        else:
            # Text output
            if all_violations:
                console.print(f"Found {len(all_violations)} violations")
            else:
                console.print("✓ No violations found")

            if tech_recommendations:
                console.print(f"Found {len(tech_recommendations)} technology recommendations")

        return 1 if (len(all_violations) > 0 and not no_fail) else 0

    exit_code = asyncio.run(_check_scan())
    raise typer.Exit(exit_code)


@app.command(name="fix", help="Interactive fixing of code violations with Claude assistance")
def fix_interactive(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files or directories to fix")] = None,
    pattern: Annotated[str | None, typer.Option("--pattern", "-p", help="Fix only specific pattern")] = None,
    auto: Annotated[bool, typer.Option("--auto", "-a", help="Auto-approve all safe fixes")] = False,
    rollback: Annotated[bool, typer.Option("--rollback", "-r", help="Rollback previous fix session")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet mode - minimal output")] = False,
) -> None:
    """
    Interactive fixing of code violations with Claude assistance.

    This command provides intelligent fixing capabilities:
    - Automatic fixes for simple patterns (mock naming, package manager)
    - Guided fixes with user input (logging, error handling)
    - Intelligent fixes using Claude's analysis (security, validation)
    - Manual guidance for complex patterns (test coverage)

    Examples:
        # Fix all violations interactively
        codex fix .

        # Fix only CORS wildcard violations
        codex fix . --pattern no-cors-wildcard

        # Auto-approve safe fixes
        codex fix . --auto

        # Rollback previous changes
        codex fix --rollback
    """
    from .interactive_fixer import InteractiveFixer

    async def _fix():
        fixer = InteractiveFixer(quiet=quiet, auto_approve=auto)

        if rollback:
            return await fixer.rollback_changes()

        # Use current directory if no paths specified
        target_paths = paths or [Path(".")]

        for path in target_paths:
            if not path.exists():
                console.print(f"[red]Error: Path does not exist: {path}[/red]")
                return 1

            exit_code = await fixer.run_interactive_fix(path, pattern)
            if exit_code != 0:
                return exit_code

        return 0

    exit_code = asyncio.run(_fix())
    raise typer.Exit(exit_code)


@app.command(name="fix-safe", help="Ultra-safe fixing with comprehensive validation and monitoring")
def fix_safe(
    paths: Annotated[list[Path] | None, typer.Argument(help="Files or directories to fix")] = None,
    mode: Annotated[
        str, typer.Option("--mode", "-m", help="Fix mode: simulate, conservative, standard, aggressive, interactive")
    ] = "standard",
    checkpoint: Annotated[
        Path | None, typer.Option("--checkpoint", "-c", help="Checkpoint file for resume capability")
    ] = None,
    impact: Annotated[bool, typer.Option("--impact", "-i", help="Show impact analysis before fixing")] = False,
    audit_report: Annotated[Path | None, typer.Option("--audit-report", help="Export audit report to file")] = None,
) -> None:
    """
    Ultra-safe fixing with comprehensive validation and monitoring.

    This command uses the full orchestrator with:
    - Multi-phase validation
    - Context analysis
    - Conflict resolution
    - Real-time monitoring
    - Checkpoint/resume capability
    - Full audit trail

    Modes:
    - simulate: Dry run, show what would be fixed
    - conservative: Only very safe fixes
    - standard: Normal safety checks (default)
    - aggressive: More permissive (still safe)
    - interactive: Ask for each fix

    Examples:
        # Simulate fixes to see what would happen
        codex fix-safe . --mode simulate

        # Conservative fixing with checkpoint
        codex fix-safe . --mode conservative --checkpoint fixes.ckpt

        # Show impact analysis first
        codex fix-safe . --impact

        # Export audit report
        codex fix-safe . --audit-report audit.json
    """
    from .fix_orchestrator import FixMode, FixOrchestrator
    from .scanner import Scanner

    async def _fix_safe():
        # Map mode string to enum
        mode_map = {
            "simulate": FixMode.SIMULATE,
            "conservative": FixMode.CONSERVATIVE,
            "standard": FixMode.STANDARD,
            "aggressive": FixMode.AGGRESSIVE,
            "interactive": FixMode.INTERACTIVE,
        }

        fix_mode = mode_map.get(mode.lower(), FixMode.STANDARD)

        # Initialize orchestrator
        orchestrator = FixOrchestrator(mode=fix_mode, console=console)

        # Use current directory if no paths specified
        target_paths = paths or [Path(".")]

        # Scan for violations
        scanner = Scanner(quiet=False)
        all_violations = []

        console.print("[cyan]Scanning for violations...[/cyan]")
        for path in target_paths:
            if not path.exists():
                console.print(f"[red]Error: Path does not exist: {path}[/red]")
                return 1

            if path.is_file():
                result = await scanner.scan_file(path)
                violations = [
                    {
                        "file_path": result.file_path,
                        "line_number": v.line_number,
                        "pattern_name": v.pattern_name,
                        "matched_code": v.matched_code,
                        "fix_strategy": "automatic" if v.auto_fixable else "manual",
                    }
                    for v in result.violations
                ]
                all_violations.extend(violations)
            else:
                results = await scanner.scan_directory(path)
                for result in results:
                    violations = [
                        {
                            "file_path": result.file_path,
                            "line_number": v.line_number,
                            "pattern_name": v.pattern_name,
                            "matched_code": v.matched_code,
                            "fix_strategy": "automatic" if v.auto_fixable else "manual",
                        }
                        for v in result.violations
                    ]
                    all_violations.extend(violations)

        if not all_violations:
            console.print("[green]No violations found![/green]")
            return 0

        console.print(f"[yellow]Found {len(all_violations)} violations[/yellow]")

        # Show impact analysis if requested
        if impact:
            console.print("\n[cyan]Analyzing fix impact...[/cyan]")
            impact_analysis = await orchestrator.analyze_fix_impact(all_violations)

            from rich.table import Table

            impact_table = Table(title="Fix Impact Analysis", border_style="cyan")
            impact_table.add_column("Metric", style="yellow")
            impact_table.add_column("Value")

            impact_table.add_row("Total lines affected", str(impact_analysis.total_lines_affected))
            impact_table.add_row("Functions modified", str(len(impact_analysis.functions_modified)))
            impact_table.add_row("Classes modified", str(len(impact_analysis.classes_modified)))
            impact_table.add_row("Imports changed", str(len(impact_analysis.imports_changed)))
            impact_table.add_row("Breaking change risk", impact_analysis.breaking_change_risk)
            impact_table.add_row("Dependencies affected", str(len(impact_analysis.dependencies_affected)))

            console.print(impact_table)

            if fix_mode != FixMode.SIMULATE:
                from rich.prompt import Confirm

                if not Confirm.ask("Proceed with fixes?", default=True):
                    return 0

        # Run orchestrated fixes
        result = await orchestrator.orchestrate_fixes(all_violations, checkpoint)

        # Show summary
        from rich.panel import Panel

        summary = Panel(
            f"""[bold]Fix Summary[/bold]

Mode: {fix_mode.value}
Fixes applied: {result.get("fixes_applied", 0)}
Fixes failed: {result.get("fixes_failed", 0)}
Fixes skipped: {result.get("fixes_skipped", 0)}
Success rate: {result.get("success_rate", 0):.1f}%
Execution time: {result.get("execution_time_seconds", 0):.1f}s

Session ID: {result.get("session_id", "N/A")}""",
            border_style="green" if result.get("fixes_failed", 0) == 0 else "yellow",
        )
        console.print(summary)

        # Export audit report if requested
        if audit_report:
            orchestrator.audit_trail.export_audit_report(audit_report)
            console.print(f"[green]Audit report exported to {audit_report}[/green]")

        # Learn from history
        learnings = orchestrator.audit_trail.learn_from_history()
        if learnings.get("recommendations"):
            console.print("\n[yellow]Recommendations based on history:[/yellow]")
            for rec in learnings["recommendations"]:
                console.print(f"  • {rec}")

        return 0 if result.get("fixes_failed", 0) == 0 else 1

    exit_code = asyncio.run(_fix_safe())
    raise typer.Exit(exit_code)


@app.command(name="init", help="Initialize Codex database and configuration")
def init(
    import_from: Annotated[Path | None, typer.Option("--import", help="Import patterns from file")] = None,
    farm_url: Annotated[str | None, typer.Option("--farm-url", help="Farm SDK URL")] = "http://localhost:8001",  # noqa: ARG001
) -> None:
    """Initialize Codex with pattern database."""

    async def _init() -> None:
        # Initialize unified database
        db = UnifiedDatabase()
        # Database is initialized automatically in __init__

        # Import default patterns if specified
        if import_from and import_from.exists():
            importer = PatternImporter(db)
            with open(import_from) as f:
                data = json.load(f)
            patterns = await importer.import_from_project_init(data)
            console.logging.info(f"[green]Imported {len(patterns)} patterns[/green]")

        # Create default config file
        config_path = Path(".codex.toml")
        if not config_path.exists():
            config_content = """# Codex configuration
[codex]
# Patterns to check
patterns = ["all"]

# Exclude patterns
exclude = ["*.pyc", "__pycache__", ".git", ".venv", "venv"]

# Auto-fix violations
auto_fix = false

# Farm SDK URL (optional)
farm_url = "http://localhost:8001"

# Pattern priorities to enforce
enforce = ["mandatory", "critical", "high"]
"""
            config_path.write_text(config_content)
            console.logging.info("[green]Created .codex.toml configuration[/green]")

        await db.close()

    asyncio.run(_init())
    console.logging.info("[green]✓ Codex initialized[/green]")


@app.command(name="check", help="Check specific patterns", hidden=True)
def check(
    pattern: Annotated[str, typer.Argument(help="Pattern name to check")],
    paths: Annotated[list[Path] | None, typer.Argument(help="Files to check")] = None,
) -> None:
    """Check for specific pattern violations."""

    if not paths:
        paths = [Path.cwd()]

    async def _check() -> int:
        scanner = Scanner()
        violations = await scanner.check_pattern(pattern, paths)

        if violations:
            console.logging.info(f"[red]Found {len(violations)} violations of '{pattern}'[/red]")
            for v in violations:
                console.logging.info(f"  {v.file_path}:{v.line_number} - {v.suggestion}")
            return 1
        else:
            console.logging.info(f"[green]✓ No violations of '{pattern}' found[/green]")
            return 0

    exit_code = asyncio.run(_check())
    raise typer.Exit(exit_code)


@app.command(name="patterns", help="Manage patterns", hidden=True)
def patterns(
    list_all: Annotated[bool, typer.Option("--list", "-l", help="List all patterns")] = False,
    category: Annotated[PatternCategory | None, typer.Option("--category", "-c")] = None,
    add: Annotated[Path | None, typer.Option("--add", "-a", help="Add patterns from file")] = None,
) -> None:
    """Manage pattern database."""

    async def _patterns() -> None:
        from .database import Database

        db = Database()

        if add and add.exists():
            importer = PatternImporter(db)
            with open(add) as f:
                data = json.load(f)
            patterns = await importer.import_from_project_init(data)
            console.logging.info(f"[green]Added {len(patterns)} patterns[/green]")

        elif list_all or category:
            if category:
                patterns = await db.get_patterns_by_category(category)
            else:
                patterns = await db.get_all_patterns()

            for p in patterns:
                priority_color = {
                    "MANDATORY": "red",
                    "CRITICAL": "yellow",
                    "HIGH": "cyan",
                    "MEDIUM": "blue",
                    "LOW": "green",
                    "OPTIONAL": "white",
                }.get(p.priority, "white")

                console.logging.info(
                    f"[{priority_color}]{p.priority:10}[/{priority_color}] "
                    f"[magenta]{p.name:30}[/magenta] {p.description[:50]}"
                )

        await db.close()

    asyncio.run(_patterns())


@app.command(name="train", help="Train Farm agents", hidden=True)
def train(
    name: Annotated[str, typer.Argument(help="Agent name")],
    category: Annotated[PatternCategory, typer.Argument(help="Pattern category")],
    farm_url: Annotated[str | None, typer.Option("--farm-url", help="Farm SDK URL")] = "http://localhost:8001",
) -> None:
    """Train a Farm agent for pattern detection."""

    if CodexClient is None:
        console.logging.info("[red]Farm SDK not available. Install with: uv pip install farm-sdk[/red]")
        raise typer.Exit(1)

    async def _train() -> None:
        client = CodexClient(farm_url=farm_url)
        agent_name = await client.train_pattern_agent(name, category)
        console.logging.info(f"[green]✓ Trained agent: {agent_name}[/green]")
        await client.close()

    asyncio.run(_train())


@app.command(name="query", help="Query patterns with natural language")
def query(
    query_text: Annotated[str, typer.Argument(help="Natural language query")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Maximum patterns to return")] = 5,
    ai_format: Annotated[bool, typer.Option("--ai", help="Format output for AI consumption")] = False,
    priority: Annotated[str | None, typer.Option("--priority", "-p", help="Filter by priority")] = None,  # noqa: ARG001
) -> None:
    """Query patterns using natural language search."""

    ai_query = AIQueryInterface()

    if ai_format:
        result = ai_query.query_patterns(query_text, limit, format="ai")

        console.logging.info(f"# Query: {query_text}\n")
        console.logging.info(f"**Found {result['total_found']} patterns**\n")
        console.logging.info(f"**Summary**: {result['summary']}\n")

        for pattern in result["patterns"]:
            console.logging.info(f"## {pattern['name']} [{pattern['priority']}]")
            console.logging.info(f"- **Rule**: {pattern['rule']}")
            if pattern["why"]:
                console.logging.info(f"- **Why**: {pattern['why']}")
            if pattern["detect"]:
                console.logging.info(f"- **Detect**: `{pattern['detect']}`")
            if pattern["fix"]:
                console.logging.info(f"- **Fix**: `{pattern['fix']}`")
            console.logging.info()
    else:
        result = ai_query.query_patterns(query_text, limit, format="human")

        console.logging.info(f"[bold]🔍 Found {result['total_found']} patterns for '{query_text}':[/bold]\n")

        for i, pattern in enumerate(result["patterns"], 1):
            priority_color = {
                "MANDATORY": "red",
                "CRITICAL": "yellow",
                "HIGH": "cyan",
                "MEDIUM": "blue",
                "LOW": "green",
                "OPTIONAL": "white",
            }.get(pattern["priority"], "white")

            console.logging.info(
                f"[bold]{i}. [{priority_color}]{pattern['priority']}[/{priority_color}] {pattern['name']}[/bold]"
            )
            console.logging.info(f"   {pattern['description']}")
            if pattern["rationale"]:
                console.logging.info(f"   [dim]Why: {pattern['rationale'][:100]}...[/dim]")
            console.logging.info()


@app.command(name="context", help="Get patterns relevant to specific context")
def context(
    file_path: Annotated[str | None, typer.Option("--file", "-f", help="File path for context")] = None,
    intent: Annotated[str | None, typer.Option("--intent", "-i", help="Coding intent")] = None,
    category: Annotated[str | None, typer.Option("--category", "-c", help="Pattern category")] = None,
    ai_format: Annotated[bool, typer.Option("--ai", help="Format output for AI consumption")] = False,
    max_patterns: Annotated[int, typer.Option("--limit", "-l", help="Maximum patterns to return")] = 10,
) -> None:
    """Get contextual patterns for files, intents, or categories."""

    ai_query = AIQueryInterface()

    if file_path:
        context_output = ai_query.get_context_for_file(file_path, max_patterns)
        if ai_format:
            console.logging.info(context_output)
        else:
            console.logging.info(f"[bold]📄 Patterns for {file_path}:[/bold]\n")
            console.logging.info(context_output)

    elif intent:
        result = ai_query.semantic_search(intent)
        if ai_format:
            console.logging.info(f"# Intent: {result['intent']}\n")
            console.logging.info(f"**Query**: {result['query_used']}\n")
            console.logging.info(f"**Summary**: {result['summary']}\n")

            for pattern in result["patterns"]:
                console.logging.info(f"## {pattern['name']} [{pattern['priority']}]")
                console.logging.info(f"- **Rule**: {pattern['rule']}")
                if pattern["fix"]:
                    console.logging.info(f"- **Fix**: {pattern['fix']}")
                console.logging.info()
        else:
            console.logging.info(f"[bold]🎯 Patterns for intent '{intent}':[/bold]\n")
            console.logging.info(f"Summary: {result['summary']}\n")

            for pattern in result["patterns"]:
                console.logging.info(f"• [bold]{pattern['name']}[/bold] [{pattern['priority']}]")
                console.logging.info(f"  {pattern['rule']}")
                console.logging.info()

    elif category:
        db = UnifiedDatabase()
        # Get patterns by category - need to filter from all patterns
        all_patterns = db.get_all_patterns()
        patterns = [p for p in all_patterns if p.category.value == category]

        console.logging.info(f"[bold]📂 Patterns in category '{category}':[/bold]\n")

        for pattern in patterns:
            priority_color = {
                "MANDATORY": "red",
                "CRITICAL": "yellow",
                "HIGH": "cyan",
                "MEDIUM": "blue",
                "LOW": "green",
                "OPTIONAL": "white",
            }.get(pattern["priority"], "white")

            console.logging.info(
                f"[{priority_color}]{pattern['priority']:10}[/{priority_color}] [bold]{pattern['name']}[/bold]"
            )
            console.logging.info(f"  {pattern['description']}")
            console.logging.info()

    else:
        console.logging.info("[red]Error: Specify --file, --intent, or --category[/red]")
        raise typer.Exit(1)


@app.command(name="explain", help="Explain a specific pattern in detail")
def explain(
    pattern_name: Annotated[str, typer.Argument(help="Pattern name to explain")],
    ai_format: Annotated[bool, typer.Option("--ai", help="Format output for AI consumption")] = False,
) -> None:
    """Get detailed explanation of a specific pattern."""

    ai_query = AIQueryInterface()
    pattern = ai_query.explain_pattern(pattern_name)

    if not pattern:
        console.logging.info(f"[red]Pattern '{pattern_name}' not found[/red]")
        raise typer.Exit(1)

    if ai_format:
        console.logging.info(f"# {pattern['name']} [{pattern['priority']}]\n")
        console.logging.info(f"**Category**: {pattern['category']}\n")
        console.logging.info(f"**Description**: {pattern['description']}\n")
        if pattern["why"]:
            console.logging.info(f"**Rationale**: {pattern['why']}\n")
        if pattern["detect"]:
            console.logging.info(f"**Detection**: `{pattern['detect']}`\n")
        if pattern["fix"]:
            console.logging.info(f"**Fix**: `{pattern['fix']}`\n")
        if pattern["good_example"]:
            console.logging.info(f"**Good Example**:\n```\n{pattern['good_example']}\n```\n")
        if pattern["bad_example"]:
            console.logging.info(f"**Bad Example**:\n```\n{pattern['bad_example']}\n```\n")
    else:
        console.logging.info(f"[bold]🔍 Pattern: {pattern['name']}[/bold]\n")
        console.logging.info(f"[bold]Category:[/bold] {pattern['category']}")
        console.logging.info(f"[bold]Priority:[/bold] {pattern['priority']}")
        console.logging.info(f"[bold]Description:[/bold] {pattern['description']}\n")

        if pattern["why"]:
            console.logging.info(f"[bold]Why:[/bold] {pattern['why']}\n")

        if pattern["detect"]:
            console.logging.info(f"[bold]Detection Pattern:[/bold] {pattern['detect']}\n")

        if pattern["fix"]:
            console.logging.info(f"[bold]Fix Template:[/bold] {pattern['fix']}\n")

        if pattern["good_example"]:
            console.logging.info(f"[bold]Good Example:[/bold]\n{pattern['good_example']}\n")

        if pattern["bad_example"]:
            console.logging.info(f"[bold]Bad Example:[/bold]\n{pattern['bad_example']}\n")


@app.command(name="validate", help="Validate code snippet against patterns")
def validate(
    code_file: Annotated[Path | None, typer.Argument(help="File to validate")] = None,
    code_text: Annotated[str | None, typer.Option("--code", "-c", help="Code snippet to validate")] = None,
    language: Annotated[str, typer.Option("--language", "-l", help="Programming language")] = "python",
) -> None:
    """Validate code against patterns."""

    if not code_file and not code_text:
        console.logging.info("[red]Error: Specify either a file or --code option[/red]")
        raise typer.Exit(1)

    if code_file:
        if not code_file.exists():
            console.logging.info(f"[red]File not found: {code_file}[/red]")
            raise typer.Exit(1)
        code_text = code_file.read_text()

    ai_query = AIQueryInterface()
    result = ai_query.validate_code_snippet(code_text, language)

    console.logging.info("[bold]🔍 Code Validation Results[/bold]\n")
    console.logging.info(f"[bold]Language:[/bold] {result['language']}")
    console.logging.info(f"[bold]Score:[/bold] {result['score']:.2f}")
    console.logging.info(f"[bold]Compliant:[/bold] {'✅ Yes' if result['is_compliant'] else '❌ No'}\n")

    if result["violations"]:
        console.logging.info(f"[bold red]Found {len(result['violations'])} violation(s):[/bold red]\n")

        for i, violation in enumerate(result["violations"], 1):
            priority_color = {
                "MANDATORY": "red",
                "CRITICAL": "yellow",
                "HIGH": "cyan",
                "MEDIUM": "blue",
                "LOW": "green",
            }.get(violation["priority"], "white")

            console.logging.info(
                f"[bold]{i}. [{priority_color}]{violation['priority']}[/{priority_color}] {violation['pattern']}[/bold]"
            )
            console.logging.info(f"   [bold]Line {violation['line']}:[/bold] {violation['issue']}")
            console.logging.info(f"   [bold]Fix:[/bold] {violation['fix']}")
            console.logging.info()
    else:
        console.logging.info("[green]✅ No violations found![/green]")


@app.command(name="import-patterns", help="Import patterns from project-init files")
def import_patterns(
    file_path: Annotated[Path, typer.Argument(help="Path to project-init.json file")],
    db_path: Annotated[str | None, typer.Option("--db", help="Database path")] = None,
) -> None:
    """Import patterns from project-init.json files."""

    if not file_path.exists():
        console.logging.info(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    console.logging.info(f"[bold]📥 Importing patterns from {file_path}...[/bold]")

    extractor = PatternExtractor()
    patterns = extractor.extract_from_project_init(str(file_path))

    db = UnifiedDatabase(db_path) if db_path else UnifiedDatabase()

    imported_count = 0
    for pattern in patterns:
        db.add_pattern(pattern)
        imported_count += 1

    console.logging.info(f"[green]✅ Imported {imported_count} patterns successfully![/green]")


@app.command(name="stats", help="Show pattern usage statistics")
def stats() -> None:
    """Show pattern database statistics."""

    ai_query = AIQueryInterface()
    stats = ai_query.get_pattern_statistics()

    console.logging.info("[bold]📊 Pattern Database Statistics[/bold]\n")
    console.logging.info(f"[bold]Total Patterns:[/bold] {stats['total_patterns']}")

    if stats["most_used"]:
        console.logging.info("\n[bold]Most Used Patterns:[/bold]")
        for pattern in stats["most_used"][:5]:
            console.logging.info(f"  • {pattern['name']} ({pattern['category']}) - {pattern['usage_count']} uses")

    if stats["by_assistant"]:
        console.logging.info("\n[bold]Usage by AI Assistant:[/bold]")
        for assistant in stats["by_assistant"]:
            console.logging.info(f"  • {assistant['ai_assistant']}: {assistant['count']} queries")


@app.command(name="export", help="Export patterns to various formats")
def export(
    format: Annotated[str, typer.Option("--format", "-f", help="Export format (markdown, json)")] = "markdown",
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Export patterns to different formats."""

    db = UnifiedDatabase()

    try:
        exported_data = db.export_patterns(format)

        if output:
            output.write_text(exported_data)
            console.logging.info(f"[green]✅ Exported patterns to {output}[/green]")
        else:
            console.logging.info(exported_data)

    except ValueError as e:
        console.logging.info(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command(name="serve", help="Start MCP server for AI assistants")
def serve(
    mcp: Annotated[bool, typer.Option("--mcp", help="Run as MCP server")] = False,
    stdio: Annotated[bool, typer.Option("--stdio", help="Use stdio transport")] = True,
) -> None:
    """Start MCP server for AI assistant integration."""

    if mcp or stdio:
        console.logging.info("[bold]🚀 Starting Codex MCP Server...[/bold]")
        console.logging.info("[dim]Use Ctrl+C to stop[/dim]\n")

        try:
            from .mcp_server import run_mcp_server

            run_mcp_server()
        except KeyboardInterrupt:
            console.logging.info("\n[yellow]Server stopped by user[/yellow]")
        except ImportError:
            console.logging.info("[red]Error: MCP dependencies not installed[/red]")
            console.logging.info("Install with: uv add mcp")
            raise typer.Exit(1) from None
        except Exception as e:
            console.logging.info(f"[red]Server error: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.logging.info("[red]Error: Specify --mcp or --stdio[/red]")
        raise typer.Exit(1)


@app.command(name="install-startup", help="Install Codex MCP server to start automatically")
def install_startup(
    system: Annotated[bool, typer.Option("--system", help="Install as system service (requires sudo)")] = False,
    user: Annotated[bool, typer.Option("--user", help="Install as user service")] = True,
) -> None:
    """Install Codex MCP server to start automatically at boot."""

    import platform
    import shutil
    from pathlib import Path

    # Determine paths
    codex_root = Path(__file__).parent.parent.absolute()

    if platform.system() == "Darwin":
        # macOS - use launchd
        plist_source = codex_root / "config" / "com.codex.mcp-server.plist"

        if system:
            plist_dest = Path("/Library/LaunchDaemons/com.codex.mcp-server.plist")
            console.logging.info("[yellow]Installing as system daemon (requires sudo)...[/yellow]")
        else:
            plist_dest = Path.home() / "Library" / "LaunchAgents" / "com.codex.mcp-server.plist"
            console.logging.info("[blue]Installing as user agent...[/blue]")

        try:
            # Ensure destination directory exists
            plist_dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy plist file
            shutil.copy2(plist_source, plist_dest)

            # Load the service
            import subprocess

            if system:
                result = subprocess.run(["sudo", "launchctl", "load", str(plist_dest)], capture_output=True, text=True)
            else:
                result = subprocess.run(["launchctl", "load", str(plist_dest)], capture_output=True, text=True)

            if result.returncode == 0:
                console.logging.info("[green]✅ Installed Codex MCP server startup service[/green]")
                console.logging.info(f"[dim]Config: {plist_dest}[/dim]")
                console.logging.info(f"[dim]Logs: {codex_root}/logs/[/dim]")

                # Start the service immediately
                service_name = "com.codex.mcp-server"
                if system:
                    subprocess.run(["sudo", "launchctl", "start", service_name])
                else:
                    subprocess.run(["launchctl", "start", service_name])

                console.logging.info("[green]✅ Service started[/green]")
            else:
                console.logging.info(f"[red]❌ Failed to load service: {result.stderr}[/red]")
                raise typer.Exit(1) from None

        except Exception as e:
            console.logging.info(f"[red]❌ Installation failed: {e}[/red]")
            raise typer.Exit(1)

    elif platform.system() == "Linux":
        # Linux - use systemd
        service_source = codex_root / "config" / "codex-mcp.service"

        if system:
            service_dest = Path("/etc/systemd/system/codex-mcp.service")
            console.logging.info("[yellow]Installing as system service (requires sudo)...[/yellow]")
        else:
            service_dest = Path.home() / ".config" / "systemd" / "user" / "codex-mcp.service"
            console.logging.info("[blue]Installing as user service...[/blue]")

        try:
            # Ensure destination directory exists
            service_dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy service file
            shutil.copy2(service_source, service_dest)

            # Reload systemd and enable service
            import subprocess

            if system:
                subprocess.run(["sudo", "systemctl", "daemon-reload"])
                subprocess.run(["sudo", "systemctl", "enable", "codex-mcp.service"])
                subprocess.run(["sudo", "systemctl", "start", "codex-mcp.service"])
            else:
                subprocess.run(["systemctl", "--user", "daemon-reload"])
                subprocess.run(["systemctl", "--user", "enable", "codex-mcp.service"])
                subprocess.run(["systemctl", "--user", "start", "codex-mcp.service"])

            console.logging.info("[green]✅ Installed Codex MCP server startup service[/green]")
            console.logging.info(f"[dim]Config: {service_dest}[/dim]")

        except Exception as e:
            console.logging.info(f"[red]❌ Installation failed: {e}[/red]")
            raise typer.Exit(1)

    else:
        console.logging.info(f"[red]❌ Unsupported platform: {platform.system()}[/red]")
        console.logging.info("Supported platforms: macOS (Darwin), Linux")
        raise typer.Exit(1)


@app.command(name="uninstall-startup", help="Remove Codex MCP server from startup")
def uninstall_startup(
    system: Annotated[bool, typer.Option("--system", help="Remove system service (requires sudo)")] = False,
) -> None:
    """Remove Codex MCP server from automatic startup."""

    import platform
    import subprocess
    from pathlib import Path

    if platform.system() == "Darwin":
        # macOS - remove launchd service
        if system:
            plist_path = Path("/Library/LaunchDaemons/com.codex.mcp-server.plist")
        else:
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.codex.mcp-server.plist"

        try:
            service_name = "com.codex.mcp-server"

            # Stop the service
            if system:
                subprocess.run(["sudo", "launchctl", "stop", service_name])
                subprocess.run(["sudo", "launchctl", "unload", str(plist_path)])
            else:
                subprocess.run(["launchctl", "stop", service_name])
                subprocess.run(["launchctl", "unload", str(plist_path)])

            # Remove plist file
            if plist_path.exists():
                plist_path.unlink()

            console.logging.info("[green]✅ Removed Codex MCP server from startup[/green]")

        except Exception as e:
            console.logging.info(f"[red]❌ Removal failed: {e}[/red]")
            raise typer.Exit(1)

    elif platform.system() == "Linux":
        # Linux - remove systemd service
        if system:
            service_path = Path("/etc/systemd/system/codex-mcp.service")
        else:
            service_path = Path.home() / ".config" / "systemd" / "user" / "codex-mcp.service"

        try:
            # Stop and disable service
            if system:
                subprocess.run(["sudo", "systemctl", "stop", "codex-mcp.service"])
                subprocess.run(["sudo", "systemctl", "disable", "codex-mcp.service"])
            else:
                subprocess.run(["systemctl", "--user", "stop", "codex-mcp.service"])
                subprocess.run(["systemctl", "--user", "disable", "codex-mcp.service"])

            # Remove service file
            if service_path.exists():
                service_path.unlink()

            # Reload systemd
            if system:
                subprocess.run(["sudo", "systemctl", "daemon-reload"])
            else:
                subprocess.run(["systemctl", "--user", "daemon-reload"])

            console.logging.info("[green]✅ Removed Codex MCP server from startup[/green]")

        except Exception as e:
            console.logging.info(f"[red]❌ Removal failed: {e}[/red]")
            raise typer.Exit(1)


@app.command(name="startup-status", help="Check startup service status")
def startup_status() -> None:
    """Check the status of Codex MCP server startup service."""

    import os
    import platform
    import subprocess
    from pathlib import Path

    if platform.system() == "Darwin":
        # macOS - check launchd service
        console.logging.info("[bold]🔍 Checking macOS launchd service status...[/bold]\n")

        # Check system daemon
        system_plist = Path("/Library/LaunchDaemons/com.codex.mcp-server.plist")
        if system_plist.exists():
            console.logging.info("[bold]System Daemon:[/bold] ✅ Installed")
            try:
                result = subprocess.run(
                    ["sudo", "launchctl", "print", "system/com.codex.mcp-server"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    console.logging.info("Status: 🟢 Running")
                else:
                    console.logging.info("Status: 🔴 Not running")
            except Exception:
                console.logging.info("Status: ❓ Unknown")
        else:
            console.logging.info("[bold]System Daemon:[/bold] ❌ Not installed")

        # Check user agent
        user_plist = Path.home() / "Library" / "LaunchAgents" / "com.codex.mcp-server.plist"
        if user_plist.exists():
            console.logging.info("[bold]User Agent:[/bold] ✅ Installed")
            try:
                result = subprocess.run(
                    ["launchctl", "print", f"gui/{os.getuid()}/com.codex.mcp-server"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    console.logging.info("Status: 🟢 Running")
                else:
                    console.logging.info("Status: 🔴 Not running")
            except Exception:
                console.logging.info("Status: ❓ Unknown")
        else:
            console.logging.info("[bold]User Agent:[/bold] ❌ Not installed")

    elif platform.system() == "Linux":
        # Linux - check systemd service
        console.logging.info("[bold]🔍 Checking Linux systemd service status...[/bold]\n")

        # Check system service
        system_service = Path("/etc/systemd/system/codex-mcp.service")
        if system_service.exists():
            console.logging.info("[bold]System Service:[/bold] ✅ Installed")
            try:
                result = subprocess.run(["systemctl", "is-active", "codex-mcp.service"], capture_output=True, text=True)
                status = result.stdout.strip()
                if status == "active":
                    console.logging.info("Status: 🟢 Running")
                else:
                    console.logging.info(f"Status: 🔴 {status}")
            except Exception:
                console.logging.info("Status: ❓ Unknown")
        else:
            console.logging.info("[bold]System Service:[/bold] ❌ Not installed")

        # Check user service
        user_service = Path.home() / ".config" / "systemd" / "user" / "codex-mcp.service"
        if user_service.exists():
            console.logging.info("[bold]User Service:[/bold] ✅ Installed")
            try:
                result = subprocess.run(
                    ["systemctl", "--user", "is-active", "codex-mcp.service"], capture_output=True, text=True
                )
                status = result.stdout.strip()
                if status == "active":
                    console.logging.info("Status: 🟢 Running")
                else:
                    console.logging.info(f"Status: 🔴 {status}")
            except Exception:
                console.logging.info("Status: ❓ Unknown")
        else:
            console.logging.info("[bold]User Service:[/bold] ❌ Not installed")

    else:
        console.logging.info(f"[red]❌ Unsupported platform: {platform.system()}[/red]")

    # Check if logs exist
    codex_root = Path(__file__).parent.parent.absolute()
    log_dir = codex_root / "logs"

    console.logging.info(f"\n[bold]📁 Log Directory:[/bold] {log_dir}")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            console.logging.info(f"Log files: {len(log_files)} files")
            for log_file in sorted(log_files):
                size = log_file.stat().st_size
                console.logging.info(f"  • {log_file.name} ({size:,} bytes)")
        else:
            console.logging.info("No log files found")
    else:
        console.logging.info("Log directory does not exist")


@app.command(name="portable", help="Run portable code quality tools (batteries included)")
def portable(
    target_dir: Annotated[Path | None, typer.Argument(help="Target directory to scan")] = None,
    fix: Annotated[bool, typer.Option("--fix", "-f", help="Apply automatic fixes")] = False,
    install_missing: Annotated[
        bool, typer.Option("--install", "-i", help="Install missing tools automatically")
    ] = True,
    no_config: Annotated[bool, typer.Option("--no-config", help="Don't generate default configs")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Minimal output")] = False,
) -> None:
    """
    Run portable code quality tools on any repository.

    This command brings "batteries included" approach - it will:
    - Detect available tools (ruff, mypy, typos)
    - Install missing tools if requested
    - Generate working configurations
    - Run comprehensive quality checks
    - Apply fixes if requested

    Works on any repository, even without existing tool setup.
    """

    if target_dir is None:
        target_dir = Path.cwd()

    if not target_dir.exists():
        console.logging.info(f"[red]Directory not found: {target_dir}[/red]")
        raise typer.Exit(1)

    async def _portable_scan() -> int:
        manager = PortableToolManager(
            target_dir=target_dir,
            quiet=quiet,
            fix=fix,
            install_missing=install_missing,
            generate_configs=not no_config,
        )

        results = await manager.run_portable_scan()
        manager.print_results(results)

        # Determine exit code
        total_violations = sum(r.violations for r in results.values())
        return 1 if total_violations > 0 else 0

    exit_code = asyncio.run(_portable_scan())
    raise typer.Exit(exit_code)


@app.command(name="init-repo", help="Initialize any repository with Codex patterns and tools")
def init_repo(
    repo_path: Annotated[Path | None, typer.Argument(help="Repository path to initialize")] = None,
    patterns: Annotated[list[Path] | None, typer.Option("--patterns", "-p", help="Pattern files to import")] = None,
    precommit: Annotated[bool, typer.Option("--precommit/--no-precommit", help="Set up pre-commit hooks")] = True,
    tools: Annotated[bool, typer.Option("--tools/--no-tools", help="Set up quality tools")] = True,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Minimal output")] = False,
) -> None:
    """
    Initialize any repository with Codex patterns and quality tools.

    This makes any repository "Codex-ready" by:
    - Setting up portable tool configurations
    - Creating .codex.toml configuration
    - Setting up pre-commit hooks
    - Importing organizational patterns

    Perfect for bringing code quality standards to existing projects.
    """

    if repo_path is None:
        repo_path = Path.cwd()

    if not repo_path.exists():
        console.logging.info(f"[red]Directory not found: {repo_path}[/red]")
        raise typer.Exit(1)

    async def _init_repo() -> int:
        initializer = RepositoryInitializer(quiet=quiet)

        success = await initializer.init_repository(
            repo_path=repo_path,
            pattern_sources=patterns,
            setup_precommit=precommit,
            setup_tools=tools,
        )

        return 0 if success else 1

    exit_code = asyncio.run(_init_repo())
    raise typer.Exit(exit_code)


@app.command(name="tools", help="Manage portable code quality tools")
def tools_command(
    check: Annotated[bool, typer.Option("--check", "-c", help="Check tool availability")] = False,
    install: Annotated[str | None, typer.Option("--install", "-i", help="Install specific tool")] = None,
    config: Annotated[str | None, typer.Option("--config", help="Generate config for tool")] = None,
    target_dir: Annotated[Path | None, typer.Option("--dir", "-d", help="Target directory")] = None,
) -> None:
    """
    Manage portable code quality tools.

    Check what tools are available, install missing ones, or generate configurations.
    """

    if target_dir is None:
        target_dir = Path.cwd()

    async def _tools() -> None:
        manager = PortableToolManager(target_dir, quiet=False)

        if check:
            console.logging.info("[bold]🔍 Checking tool availability...[/bold]\n")
            tools = await manager.analyze_repository()

            for tool_name, tool_info in tools.items():
                status_icon = {
                    "available": "✅",
                    "missing": "❌",
                    "installed_by_codex": "🔧",
                }[tool_info.availability.value]

                console.logging.info(f"{status_icon} [bold]{tool_name}[/bold]: {tool_info.availability.value}")
                if tool_info.version:
                    console.logging.info(f"   Version: {tool_info.version}")
                if tool_info.install_command:
                    console.logging.info(f"   Install: {tool_info.install_command}")
                console.logging.info()

        elif install:
            console.logging.info(f"[bold]📦 Installing {install}...[/bold]")
            success = await manager._install_tool(install)
            if success:
                console.logging.info(f"[green]✅ {install} installed successfully[/green]")
            else:
                console.logging.info(f"[red]❌ Failed to install {install}[/red]")

        elif config:
            console.logging.info(f"[bold]📝 Generating {config} configuration...[/bold]")
            success = await manager._ensure_config(config)
            if success:
                console.logging.info(f"[green]✅ {config} config created[/green]")
            else:
                console.logging.info(f"[yellow]⚠️  {config} config already exists or failed[/yellow]")

        else:
            console.logging.info("[yellow]Use --check, --install <tool>, or --config <tool>[/yellow]")
            console.logging.info("\nAvailable tools: ruff, black, mypy, ty, typos, uv")

    asyncio.run(_tools())


@app.command(name="any-repo", help="Apply Codex to any repository (one-shot)")
def any_repo(
    repo_path: Annotated[Path, typer.Argument(help="Path to any repository")],
    fix: Annotated[bool, typer.Option("--fix", "-f", help="Apply automatic fixes")] = False,
    init: Annotated[bool, typer.Option("--init", help="Initialize repository first")] = False,
    patterns: Annotated[Path | None, typer.Option("--patterns", "-p", help="Pattern file to use")] = None,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Minimal output")] = False,
) -> None:
    """
    Apply Codex quality standards to any repository in one command.

    This is the ultimate "batteries included" command that can take any
    repository and apply code quality patterns and tools, regardless of
    what's currently set up.

    Perfect for:
    - Auditing unknown codebases
    - Applying company standards to legacy projects
    - One-off quality checks on external repositories
    """

    if not repo_path.exists():
        console.logging.info(f"[red]Repository not found: {repo_path}[/red]")
        raise typer.Exit(1)

    if not repo_path.is_dir():
        console.logging.info(f"[red]Path is not a directory: {repo_path}[/red]")
        raise typer.Exit(1)

    async def _any_repo() -> int:
        total_violations = 0

        # Step 1: Initialize if requested
        if init:
            if not quiet:
                console.logging.info(f"[blue]🚀 Initializing {repo_path}...[/blue]")

            initializer = RepositoryInitializer(quiet=quiet)
            pattern_sources = [patterns] if patterns else None

            await initializer.init_repository(
                repo_path=repo_path,
                pattern_sources=pattern_sources,
                setup_precommit=False,  # Don't modify external repos
                setup_tools=True,
            )

        # Step 2: Import patterns if provided
        if patterns and patterns.exists():
            if not quiet:
                console.logging.info(f"[blue]📥 Importing patterns from {patterns}...[/blue]")

            extractor = PatternExtractor()
            pattern_list = extractor.extract_from_project_init(str(patterns))

            db = UnifiedDatabase()
            for pattern in pattern_list:
                db.add_pattern(pattern)

            if not quiet:
                console.logging.info(f"[green]✅ Imported {len(pattern_list)} patterns[/green]")

        # Step 3: Run portable tools
        if not quiet:
            console.logging.info(f"[blue]🔍 Running portable quality scan on {repo_path}...[/blue]")

        manager = PortableToolManager(
            target_dir=repo_path,
            quiet=quiet,
            fix=fix,
            install_missing=False,  # Don't auto-install for external repos
            generate_configs=True,
        )

        results = await manager.run_portable_scan()
        manager.print_results(results)

        # Count violations from tools
        total_violations += sum(r.violations for r in results.values())

        # Step 4: Run Codex pattern scan if we have patterns
        if patterns:
            if not quiet:
                console.logging.info("\n[blue]🎯 Running pattern analysis...[/blue]")

            scanner = Scanner(quiet=quiet, fix=fix)
            scan_results = await scanner.scan_directory(repo_path)

            pattern_violations = sum(len(r.violations) for r in scan_results)
            total_violations += pattern_violations

            if not quiet:
                if pattern_violations > 0:
                    console.logging.info(f"[yellow]⚠️  Found {pattern_violations} pattern violation(s)[/yellow]")
                else:
                    console.logging.info("[green]✅ No pattern violations found[/green]")

        # Summary
        if not quiet:
            console.logging.info(f"\n[bold]📊 Summary for {repo_path.name}:[/bold]")
            console.logging.info(f"Total violations: {total_violations}")
            if total_violations == 0:
                console.logging.info("[green]🎉 Repository meets quality standards![/green]")
            else:
                console.logging.info("[yellow]⚠️  Quality improvements needed[/yellow]")

        return 1 if total_violations > 0 else 0

    exit_code = asyncio.run(_any_repo())
    raise typer.Exit(exit_code)


@app.command(name="scan-to-db", help="Scan repository and output to SQLite database for AI querying")
def scan_to_database(
    paths: Annotated[list[Path] | None, typer.Argument(help="Paths to scan")] = None,
    output_db: Annotated[Path, typer.Option("--output-db", "-o", help="Output database path")] = Path(
        "scan_results.db"
    ),
    ai_context: Annotated[str | None, typer.Option("--ai-context", help="AI context for scan")] = None,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Minimal output")] = False,
) -> None:
    """
    Scan files and output results to SQLite database for AI querying.

    Creates a queryable SQLite database instead of static reports,
    optimized for Claude Code interaction and natural language queries.
    """

    if not paths:
        paths = [Path.cwd()]

    async def _scan_to_db() -> int:
        scanner = SQLiteScanner(output_db=output_db, quiet=quiet, ai_context=ai_context)

        try:
            for path in paths:
                if path.is_dir():
                    await scanner.scan_repository(path)
                elif path.is_file():
                    # For individual files, scan the parent directory but focus on the file
                    await scanner.scan_repository(path.parent)
                else:
                    if not quiet:
                        console.logging.info(f"[yellow]Warning: {path} not found[/yellow]")

            if not quiet:
                console.logging.info(f"[blue]🔍 Query results: codex query-db {output_db} 'your question'[/blue]")

            return 0

        except Exception as e:
            if not quiet:
                console.logging.info(f"[red]Scan failed: {e}[/red]")
            return 1

        finally:
            scanner.close()

    exit_code = asyncio.run(_scan_to_db())
    raise typer.Exit(exit_code)


@app.command(name="query-db", help="Query scan results database with natural language")
def query_database(
    db_path: Annotated[Path, typer.Argument(help="Path to scan results database")],
    query: Annotated[str, typer.Argument(help="Natural language query")],
    ai_format: Annotated[bool, typer.Option("--ai", help="AI-optimized output")] = False,
    explain: Annotated[bool, typer.Option("--explain", help="Show SQL and explanation")] = False,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Limit results")] = 20,
) -> None:
    """
    Query scan results database with natural language.

    Examples:
      codex query-db scan.db "Show me all violations"
      codex query-db scan.db "What files have the most violations?"
      codex query-db scan.db "Show me violations related to http"
      codex query-db scan.db "What should I fix first?"
    """

    if not db_path.exists():
        console.logging.info(f"[red]Database not found: {db_path}[/red]")
        raise typer.Exit(1)

    try:
        query_interface = NaturalLanguageQueryInterface(str(db_path), quiet=False)
        result = query_interface.query(query)

        if explain:
            console.logging.info(f"[bold]Generated SQL:[/bold]\n{result.get('sql_executed', 'N/A')}\n")

        if ai_format:
            # Output optimized for Claude Code consumption
            output = {
                "query": result["original_query"],
                "results": result["results"][:limit],
                "summary": result["summary"],
                "result_type": result.get("result_type", "unknown"),
                "result_count": result.get("result_count", 0),
                "ai_insights": result.get("ai_insights", []),
                "suggested_follow_ups": result.get("suggested_follow_ups", []),
            }
            logging.info(json.dumps(output, indent=2))
        else:
            # Human-readable output
            console.logging.info(f"[bold green]Results for:[/bold green] {query}\n")
            console.logging.info(f"[dim]{result['summary']}[/dim]\n")

            results = result["results"][:limit]
            for i, row in enumerate(results, 1):
                if isinstance(row, dict):
                    console.logging.info(f"[bold]{i}.[/bold] {dict(row)}")
                else:
                    console.logging.info(f"[bold]{i}.[/bold] {row}")

            if len(result["results"]) > limit:
                console.logging.info(f"\n[dim]... and {len(result['results']) - limit} more results[/dim]")

            # Show AI insights if available
            if result.get("ai_insights"):
                console.logging.info("\n[bold blue]💡 AI Insights:[/bold blue]")
                for insight in result["ai_insights"]:
                    console.logging.info(f"  • {insight}")

            # Show suggested follow-ups
            if result.get("suggested_follow_ups"):
                console.logging.info("\n[bold blue]🔍 Suggested follow-up queries:[/bold blue]")
                for suggestion in result["suggested_follow_ups"][:3]:
                    console.logging.info(f"  • {suggestion}")

    except Exception as e:
        console.logging.info(f"[red]Query failed: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="db-help", help="Show example queries for database interaction")
def database_help() -> None:
    """
    Show example natural language queries for database interaction.

    Helps users understand what kinds of questions they can ask the scan database.
    """

    console.logging.info("[bold]🔍 Natural Language Database Queries[/bold]\n")

    examples = [
        ("Show me all violations", "Get overview of all violations by category and severity"),
        ("What files have the most violations?", "Find files that need the most attention"),
        ("Show me violations related to http", "Find HTTP-related code issues"),
        ("What should I fix first?", "Get prioritized list of violations to address"),
        ("Show me simple fixes", "Find easy wins that can be fixed quickly"),
        ("Show me repository insights", "Get high-level analysis and recommendations"),
        ("Count violations", "Get violation statistics by severity"),
        ("Show me critical violations", "Find the most serious issues"),
        ("Show me violations in client.py", "Analyze specific file"),
        ("Help me learn from this codebase", "Find learning opportunities and best practices"),
    ]

    for i, (query, description) in enumerate(examples, 1):
        console.logging.info(f'[bold]{i:2}.[/bold] [cyan]codex query-db scan.db "{query}"[/cyan]')
        console.logging.info(f"     [dim]{description}[/dim]\n")

    console.logging.info("[bold blue]💡 Tips:[/bold blue]")
    console.logging.info("  • Use natural language - the system understands intent")
    console.logging.info("  • Be specific about files, patterns, or categories")
    console.logging.info("  • Ask for priorities, summaries, or learning opportunities")
    console.logging.info("  • Use --ai flag for structured output suitable for AI assistants")
    console.logging.info("  • Use --explain to see the generated SQL query")


@app.command(name="config", help="Manage project-specific configuration")
def config_cmd(
    action: Annotated[str, typer.Argument(help="Action: init, show, set, get, clean")],
    key: Annotated[str | None, typer.Argument(help="Configuration key for get/set")] = None,
    value: Annotated[str | None, typer.Option("--value", "-v", help="Value to set")] = None,
    template: Annotated[str, typer.Option("--template", "-t", help="Template for init")] = "python",
    project_root: Annotated[Path | None, typer.Option("--project", "-p", help="Project root directory")] = None,
) -> None:
    """Manage project-specific Codex configuration."""

    config_manager = ProjectConfigManager(project_root)

    if action == "init":
        # Initialize project configuration
        config = config_manager.init_project(template)
        console.logging.info(f"[green]✅ Initialized Codex configuration for {config.project_name}[/green]")
        console.logging.info(f"Config file: {config_manager.config_file}")
        console.logging.info(f"Template: {template}")

    elif action == "show":
        # Show current configuration
        summary = config_manager.get_project_summary()

        table = Table(title="Project Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        for key, value in summary.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            table.add_row(key, str(value))

        console.logging.info(table)

    elif action == "set":
        # Set configuration value
        if not key or value is None:
            console.logging.info("[red]❌ Both key and value required for set action[/red]")
            raise typer.Exit(1)

        try:
            config_manager.update_setting(key, value)
            console.logging.info(f"[green]✅ Set {key} = {value}[/green]")
        except ValueError as e:
            console.logging.info(f"[red]❌ {e}[/red]")
            raise typer.Exit(1)

    elif action == "get":
        # Get configuration value
        if not key:
            console.logging.info("[red]❌ Key required for get action[/red]")
            raise typer.Exit(1)

        config = config_manager.load_config()
        if hasattr(config, key):
            value = getattr(config, key)
            console.logging.info(f"{key}: {value}")
        else:
            console.logging.info(f"[red]❌ Unknown configuration key: {key}[/red]")
            raise typer.Exit(1)

    elif action == "clean":
        # Clean cache files
        config_manager.clean_cache()
        console.logging.info("[green]✅ Cleaned cache files[/green]")

    else:
        console.logging.info(f"[red]❌ Unknown action: {action}[/red]")
        console.logging.info("Available actions: init, show, set, get, clean")
        raise typer.Exit(1)


@app.command(name="check-gitignore", help="Validate .gitignore file and exclusion patterns")
def check_gitignore(
    project_root: Annotated[Path | None, typer.Option("--project", "-p", help="Project root directory")] = None,
) -> None:
    """Validate .gitignore file and show exclusion patterns."""

    root = Path(project_root or Path.cwd()).resolve()
    gitignore_handler = GitIgnoreHandler(root)

    console.logging.info(f"[blue]📁 Project: {root}[/blue]\n")

    # Show patterns summary
    summary = gitignore_handler.get_patterns_summary()
    console.logging.info(f"[cyan]Loaded {summary['total_patterns']} exclusion patterns[/cyan]")
    console.logging.info(f"GitIgnore file exists: {'✅' if summary['gitignore_exists'] else '❌'}\n")

    # Validate .gitignore
    suggestions = gitignore_handler.validate_gitignore()

    if suggestions:
        console.logging.info("[yellow]📋 GitIgnore Suggestions:[/yellow]")
        for suggestion in suggestions:
            console.logging.info(f"  • {suggestion}")
        console.logging.info()
    else:
        console.logging.info("[green]✅ GitIgnore file looks good![/green]\n")

    # Show sample patterns
    if summary["sample_patterns"]:
        console.logging.info("[cyan]📜 Sample Exclusion Patterns:[/cyan]")
        for pattern in summary["sample_patterns"]:
            console.logging.info(f"  • {pattern}")

    # Test with some common files
    test_files = [
        "src/main.py",
        "__pycache__/module.pyc",
        ".venv/lib/python3.11/site-packages/",
        "node_modules/package/index.js",
        ".git/config",
        "build/dist/app.js",
    ]

    console.logging.info("\n[cyan]🧪 Test File Exclusions:[/cyan]")
    for test_file in test_files:
        test_path = root / test_file
        excluded = gitignore_handler.should_exclude(test_path)
        status = "❌ Excluded" if excluded else "✅ Included"
        console.logging.info(f"  {status}: {test_file}")


@app.command(name="mcp-server", help="Start MCP server for Claude Code integration")
def mcp_server() -> None:
    """Start Codex MCP server for Claude Code integration."""
    try:
        import asyncio

        from .mcp_server import main

        # Don't print to stdout - it interferes with MCP stdio communication
        # Only log to stderr or files

        asyncio.run(main())

    except ImportError:
        console.logging.info("[red]❌ MCP library not available. Install with:[/red]")
        console.logging.info("  uv pip install mcp")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.logging.info("\n[yellow]📴 MCP Server stopped[/yellow]")


@app.command(name="install-mcp", help="Install Codex MCP server for Claude Code")
def install_mcp(
    user_scope: Annotated[
        bool, typer.Option("--user/--project", help="Install for current user vs project only")
    ] = True,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing configuration")] = False,
):
    """Install Codex MCP server configuration for Claude Code."""
    import shutil

    # Get the codex executable path
    codex_path = shutil.which("codex")
    if not codex_path:
        console.logging.info("[red]❌ Codex not found in PATH. Install globally first:[/red]")
        console.logging.info("  uv tool install --editable .")
        raise typer.Exit(1)

    if user_scope:
        # User-level installation using proper Claude CLI command
        import subprocess

        console.logging.info("[bold blue]🔧 Installing Codex MCP Server (User Level)[/bold blue]\n")

        # Check if already installed
        if not force:
            try:
                result = subprocess.run(["claude", "mcp", "get", "codex"], capture_output=True, text=True)
                if result.returncode == 0 and "codex:" in result.stdout:
                    console.logging.info("[yellow]⚠️  Codex MCP server already configured[/yellow]")
                    console.logging.info("[dim]Use --force to overwrite[/dim]")
                    console.logging.info("\n[blue]Current configuration:[/blue]")
                    console.logging.info(result.stdout)
                    return
            except FileNotFoundError:
                console.logging.info("[red]❌ Claude CLI not found. Please install Claude Code first.[/red]")
                raise typer.Exit(1)

        # Remove existing if force is specified
        if force:
            try:
                subprocess.run(["claude", "mcp", "remove", "codex", "-s", "user"], capture_output=True, text=True)
            except Exception:
                pass  # Ignore if doesn't exist

        # Add the MCP server using Claude CLI
        try:
            result = subprocess.run(
                ["claude", "mcp", "add", "--scope", "user", "codex", codex_path, "mcp-server"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                console.logging.info("[green]✅ Codex MCP server installed successfully![/green]")
                console.logging.info(f"[blue]Command:[/blue] {codex_path} mcp-server")
                console.logging.info("[blue]Scope:[/blue] User (available in all projects)")

                # Show the configuration
                config_result = subprocess.run(["claude", "mcp", "get", "codex"], capture_output=True, text=True)
                if config_result.returncode == 0:
                    console.logging.info("\n[blue]Configuration:[/blue]")
                    console.logging.info(config_result.stdout)

                console.logging.info("\n[bold]🎯 Available Tools:[/bold]")
                console.logging.info("   • [cyan]query_patterns[/cyan] - Search for coding patterns")
                console.logging.info("   • [cyan]get_file_context[/cyan] - Get patterns for current file")
                console.logging.info("   • [cyan]validate_code[/cyan] - Check code against patterns")
                console.logging.info("   • [cyan]semantic_search[/cyan] - Find patterns by intent")
                console.logging.info("   • [cyan]explain_pattern[/cyan] - Get detailed pattern explanations")

                console.logging.info("\n[bold]✅ Server Installed![/bold]")
                console.logging.info("The Codex MCP server is now available in all Claude Code sessions.")
                console.logging.info("Start a new Claude Code session to use the Codex tools!")

            else:
                console.logging.info("[red]❌ Failed to install MCP server:[/red]")
                console.logging.info(result.stderr)
                raise typer.Exit(1)

        except FileNotFoundError:
            console.logging.info("[red]❌ Claude CLI not found. Please install Claude Code first.[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.logging.info(f"[red]❌ Installation failed: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Project-level installation - create .mcp.json file
        import json
        from pathlib import Path

        project_root = Path.cwd()
        mcp_file = project_root / ".mcp.json"

        console.logging.info("[bold blue]🔧 Installing Codex MCP Server (Project Level)[/bold blue]")
        console.logging.info(f"[blue]Project:[/blue] {project_root}")

        # Check if file already exists
        if mcp_file.exists() and not force:
            try:
                with open(mcp_file) as f:
                    existing_config = json.load(f)

                if "codex" in existing_config.get("mcpServers", {}):
                    console.logging.info("[yellow]⚠️  Codex MCP server already configured in .mcp.json[/yellow]")
                    console.logging.info("[dim]Use --force to overwrite[/dim]")
                    return
            except (json.JSONDecodeError, OSError):
                # File exists but is invalid, we'll overwrite
                pass

        # MCP configuration for project
        mcp_config = {"mcpServers": {"codex": {"command": codex_path, "args": ["mcp-server"], "env": {}}}}

        # If file exists, merge with existing config
        if mcp_file.exists():
            try:
                with open(mcp_file) as f:
                    existing_config = json.load(f)

                # Merge configurations
                if "mcpServers" not in existing_config:
                    existing_config["mcpServers"] = {}

                existing_config["mcpServers"]["codex"] = mcp_config["mcpServers"]["codex"]
                mcp_config = existing_config

            except (json.JSONDecodeError, OSError):
                # Use new config if existing is invalid
                pass

        # Write configuration
        try:
            with open(mcp_file, "w") as f:
                json.dump(mcp_config, f, indent=2)

            console.logging.info("[green]✅ Codex MCP server installed successfully![/green]")
            console.logging.info(f"[blue]Config file:[/blue] {mcp_file}")
            console.logging.info(f"[blue]Command:[/blue] {codex_path} mcp-server")
            console.logging.info("\n[dim]Note: .mcp.json should be committed to version control[/dim]")

        except OSError as e:
            console.logging.info(f"[red]❌ Failed to write config file: {e}[/red]")
            raise typer.Exit(1)


@app.command(name="uninstall-mcp", help="Remove Codex MCP server from Claude Code")
def uninstall_mcp(
    user_scope: Annotated[bool, typer.Option("--user", help="Remove from current user only")] = True,
):
    """Remove Codex MCP server configuration from Claude Code."""
    import json
    from pathlib import Path

    # Determine config directory
    if user_scope:
        config_dir = Path.home() / ".config" / "claude-code"
    else:
        config_dir = Path("/etc/claude-code")

    config_file = config_dir / "mcp_servers.json"

    if not config_file.exists():
        console.logging.info("[yellow]⚠️  No MCP configuration found[/yellow]")
        return

    try:
        with open(config_file) as f:
            config = json.load(f)

        if "mcpServers" in config and "codex" in config["mcpServers"]:
            del config["mcpServers"]["codex"]

            # Write back the configuration
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            console.logging.info("[green]✅ Codex MCP server removed successfully![/green]")
            console.logging.info("[dim]Restart Claude Code to apply changes[/dim]")
        else:
            console.logging.info("[yellow]⚠️  Codex MCP server not found in configuration[/yellow]")

    except (json.JSONDecodeError, OSError) as e:
        console.logging.info(f"[red]❌ Failed to update config file: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="mcp-status", help="Check Codex MCP server configuration status")
def mcp_status():
    """Check the status of Codex MCP server configuration."""
    import json
    import shutil
    from pathlib import Path

    console.logging.info("[bold]🔍 Codex MCP Server Status[/bold]\n")

    # Check if codex is installed
    codex_path = shutil.which("codex")
    if codex_path:
        console.logging.info(f"[green]✅ Codex executable:[/green] {codex_path}")
    else:
        console.logging.info("[red]❌ Codex not found in PATH[/red]")
        console.logging.info("[dim]Run: uv tool install --editable .[/dim]")
        return

    # Test MCP server functionality
    console.logging.info("\n[dim]Testing MCP server...[/dim]")
    try:
        import subprocess

        result = subprocess.run([codex_path, "mcp-server", "--help"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.logging.info("[green]✅ MCP server responds correctly[/green]")
        else:
            console.logging.info("[red]❌ MCP server test failed[/red]")
            return
    except Exception as e:
        console.logging.info(f"[red]❌ MCP server test error: {e}[/red]")
        return

    # Check for project-level MCP configuration
    project_mcp = Path.cwd() / ".mcp.json"
    if project_mcp.exists():
        try:
            with open(project_mcp) as f:
                config = json.load(f)

            if "mcpServers" in config and "codex" in config["mcpServers"]:
                console.logging.info(f"[green]✅ Project MCP config:[/green] {project_mcp}")
                codex_config = config["mcpServers"]["codex"]
                console.logging.info(f"[blue]Command:[/blue] {codex_config.get('command', 'N/A')}")
                console.logging.info(f"[blue]Args:[/blue] {' '.join(codex_config.get('args', []))}")
        except (json.JSONDecodeError, OSError) as e:
            console.logging.info(f"[yellow]⚠️  Invalid project MCP config:[/yellow] {project_mcp}")

    # Installation instructions
    console.logging.info("\n[bold]📋 Installation Instructions:[/bold]")
    console.logging.info("\n[bold]For User-Level Installation (Recommended):[/bold]")
    console.logging.info("1. Run: [cyan]codex install-mcp[/cyan]")
    console.logging.info("2. Copy the /mcp command shown")
    console.logging.info("3. Paste it in Claude Code")
    console.logging.info("4. Restart Claude Code")

    console.logging.info("\n[bold]For Project-Level Installation:[/bold]")
    console.logging.info("1. Run: [cyan]codex install-mcp --project[/cyan]")
    console.logging.info("2. Commit .mcp.json to version control")
    console.logging.info("3. Restart Claude Code")

    console.logging.info("\n[bold]📍 MCP Command for Claude Code:[/bold]")
    console.logging.info(f"   [cyan]/mcp install codex {codex_path} mcp-server[/cyan]")


@app.command(name="learn", help="Teach Codex new patterns from AI assistant experience")
def learn_pattern(
    name: Annotated[str, typer.Argument(help="Pattern name (e.g., 'prefer-pathlib-over-os-path')")],
    rule: Annotated[
        str, typer.Argument(help="Rule description (e.g., 'Use pathlib instead of os.path for file operations')")
    ],
    category: Annotated[str, typer.Option("--category", "-c", help="Pattern category")] = "best_practices",
    priority: Annotated[str, typer.Option("--priority", "-p", help="Priority level")] = "MEDIUM",
    detect: Annotated[str | None, typer.Option("--detect", "-d", help="Detection pattern/regex")] = None,
    fix: Annotated[str | None, typer.Option("--fix", "-f", help="Fix template or suggestion")] = None,
    why: Annotated[str | None, typer.Option("--why", "-w", help="Rationale for this pattern")] = None,
    good_example: Annotated[str | None, typer.Option("--good", help="Good code example")] = None,
    bad_example: Annotated[str | None, typer.Option("--bad", help="Bad code example")] = None,
    language: Annotated[str, typer.Option("--language", "-l", help="Programming language")] = "python",
    source: Annotated[
        str, typer.Option("--source", help="Source of pattern (e.g., 'claude-3.5-sonnet')")
    ] = "ai-assistant",
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Interactive pattern creation")] = False,
    anti_pattern: Annotated[str | None, typer.Option("--anti-pattern", help="Related anti-pattern name")] = None,
):
    """Learn new patterns from AI assistant experience and code reviews."""

    if interactive:
        _interactive_pattern_creation()
        return

    # Validate required fields
    if not detect and not why:
        console.logging.info("[red]Either --detect or --why must be provided[/red]")
        raise typer.Exit(1)

    # Create pattern dictionary
    pattern = {
        "name": name,
        "description": rule,
        "category": category,
        "priority": priority.upper(),
        "detection_pattern": detect,
        "fix_template": fix,
        "rationale": why or f"Best practice pattern learned from {source}",
        "example_good": good_example,
        "example_bad": bad_example,
        "source_file": f"ai-learned/{source}",
        "full_context": f"Pattern learned from AI assistant experience. Language: {language}",
    }

    try:
        # Add to FTS database using SQLite directly for now
        import sqlite3

        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO patterns (name, description, category, priority, detection_pattern, fix_template, rationale, example_good, example_bad, source_file, full_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                pattern["name"],
                pattern["description"],
                pattern["category"],
                pattern["priority"],
                pattern.get("detection_pattern"),
                pattern.get("fix_template"),
                pattern["rationale"],
                pattern.get("example_good"),
                pattern.get("example_bad"),
                pattern["source_file"],
                pattern["full_context"],
            ),
        )

        conn.commit()
        conn.close()

        console.logging.info(f"[green]✓ Learned new pattern: {name}[/green]")
        console.logging.info(f"[blue]Category:[/blue] {category}")
        console.logging.info(f"[blue]Priority:[/blue] {priority}")
        console.logging.info(f"[blue]Rule:[/blue] {rule}")

        if detect:
            console.logging.info(f"[blue]Detection:[/blue] {detect}")
        if fix:
            console.logging.info(f"[blue]Fix:[/blue] {fix}")
        if why:
            console.logging.info(f"[blue]Why:[/blue] {why}")

    except Exception as e:
        console.logging.info(f"[red]Failed to learn pattern: {e}[/red]")
        raise typer.Exit(1)


def _interactive_pattern_creation():
    """Interactive pattern creation wizard."""
    console.logging.info("\n[bold blue]🤖 Interactive Pattern Learning Wizard[/bold blue]")
    console.logging.info("Help Codex learn from your coding experience!\n")

    # Collect pattern info interactively
    name = typer.prompt("Pattern name (kebab-case)")
    rule = typer.prompt("Rule description")

    console.logging.info("\nCategories: security, performance, readability, testing, error_handling, best_practices")
    category = typer.prompt("Category", default="best_practices")

    console.logging.info("\nPriorities: MANDATORY, CRITICAL, HIGH, MEDIUM, LOW, OPTIONAL")
    priority = typer.prompt("Priority", default="MEDIUM")

    detect = typer.prompt("Detection pattern (regex/string to find violations)", default="")
    fix = typer.prompt("Fix suggestion or template", default="")
    why = typer.prompt("Why is this important?")

    # Optional examples
    if typer.confirm("Add code examples?"):
        good_example = typer.prompt("Good example code", default="")
        bad_example = typer.prompt("Bad example code", default="")
    else:
        good_example = bad_example = ""

    language = typer.prompt("Programming language", default="python")
    source = typer.prompt("Your identifier (for tracking)", default="ai-assistant")

    # Create and save pattern
    pattern = {
        "name": name,
        "description": rule,
        "category": category,
        "priority": priority.upper(),
        "detection_pattern": detect or None,
        "fix_template": fix or None,
        "rationale": why,
        "example_good": good_example or None,
        "example_bad": bad_example or None,
        "source_file": f"ai-learned/{source}",
        "full_context": f"Interactively learned pattern. Language: {language}",
    }

    # Preview and confirm
    console.logging.info("\n[bold]Pattern Preview:[/bold]")
    table = Table()
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    for key, value in pattern.items():
        if value:
            table.add_row(key.replace("_", " ").title(), str(value))

    console.logging.info(table)

    if typer.confirm("\nSave this pattern?"):
        try:
            import sqlite3

            conn = sqlite3.connect(settings.database_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO patterns (name, description, category, priority, detection_pattern, fix_template, rationale, example_good, example_bad, source_file, full_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern["name"],
                    pattern["description"],
                    pattern["category"],
                    pattern["priority"],
                    pattern.get("detection_pattern"),
                    pattern.get("fix_template"),
                    pattern["rationale"],
                    pattern.get("example_good"),
                    pattern.get("example_bad"),
                    pattern["source_file"],
                    pattern["full_context"],
                ),
            )

            conn.commit()
            conn.close()
            console.logging.info(f"[green]✓ Successfully learned pattern: {name}[/green]")
        except Exception as e:
            console.logging.info(f"[red]Failed to save pattern: {e}[/red]")
    else:
        console.logging.info("[yellow]Pattern discarded[/yellow]")


@app.command(name="feedback", help="Provide feedback on pattern effectiveness")
def pattern_feedback(
    pattern_name: Annotated[str, typer.Argument(help="Name of pattern to give feedback on")],
    rating: Annotated[int | None, typer.Option("--rating", "-r", help="Effectiveness rating (1-5)")] = None,
    comment: Annotated[str | None, typer.Option("--comment", "-c", help="Feedback comment")] = None,
    helped: Annotated[bool, typer.Option("--helped/--not-helpful", help="Did this pattern help?")] = True,
    context: Annotated[str | None, typer.Option("--context", help="Context where pattern was used")] = None,
    assistant: Annotated[str, typer.Option("--assistant", help="AI assistant identifier")] = "ai-assistant",
):
    """Provide feedback on how effective patterns are in practice."""

    try:
        import sqlite3

        conn = sqlite3.connect(settings.database_path)
        cursor = conn.cursor()

        # Find the pattern
        cursor.execute("SELECT * FROM patterns WHERE name LIKE ?", (f"%{pattern_name}%",))
        pattern_row = cursor.fetchone()

        if not pattern_row:
            console.logging.info(f"[red]Pattern '{pattern_name}' not found[/red]")
            raise typer.Exit(1)

        # If interactive rating needed
        if rating is None:
            console.logging.info(f"\n[bold]Providing feedback for pattern: {pattern_row[1]}[/bold]")  # name is column 1
            console.logging.info(f"[blue]Rule:[/blue] {pattern_row[4] or 'N/A'}")  # description is column 4
            rating = typer.prompt("Rate effectiveness (1-5)", type=int)

        if comment is None:
            comment = typer.prompt("Optional comment", default="")

        # Store feedback in pattern_usage table
        cursor.execute(
            """
            INSERT INTO pattern_usage (pattern_id, success, ai_assistant, project_path)
            VALUES (?, ?, ?, ?)
        """,
            (pattern_row[0], helped, assistant, context or f"feedback-{rating}/5"),
        )

        conn.commit()
        conn.close()

        console.logging.info(f"[green]✓ Feedback recorded for pattern: {pattern_name}[/green]")
        console.logging.info(f"[blue]Rating:[/blue] {rating}/5")
        if comment:
            console.logging.info(f"[blue]Comment:[/blue] {comment}")

    except Exception as e:
        console.logging.info(f"[red]Failed to record feedback: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="scan-history", help="View scan history and trends")
def scan_history(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Number of scans to show")] = 10,
    show_progress: Annotated[bool, typer.Option("--progress", "-p", help="Show progress report")] = False,
    show_trends: Annotated[bool, typer.Option("--trends", "-t", help="Show violation trends")] = False,
    pattern: Annotated[str | None, typer.Option("--pattern", help="Pattern name for trend analysis")] = None,
):
    """View scan history, progress, and trends from the tracking database."""
    from codex.scan_tracker import ScanTracker

    tracker = ScanTracker()

    try:
        if show_progress:
            tracker.print_progress()
        elif show_trends:
            trends = tracker.get_violation_trends(pattern)
            if trends:
                console.print("\n[bold]Violation Trends[/bold]")
                for entry in trends:
                    console.print(f"  {entry['timestamp'][:10]}: {entry['count']} violations")
            else:
                console.print("[yellow]No trend data available.[/yellow]")
        else:
            tracker.print_summary()
            console.print()
            tracker.print_history(limit)
    finally:
        tracker.close()

    raise typer.Exit(0)


@app.command(name="scan-report", help="Generate automatic scan report from database")
def scan_report(
    export: Annotated[Path | None, typer.Option("--export", "-e", help="Export report to markdown file")] = None,
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output JSON summary")] = False,
    detailed: Annotated[bool, typer.Option("--detailed", "-d", help="Include detailed analysis")] = False,
):
    """Generate comprehensive automatic report from scan tracking database."""
    from codex.scan_report_generator import ScanReportGenerator

    generator = ScanReportGenerator()

    try:
        if json_output:
            import json

            summary = generator.generate_sql_based_summary()
            console.print(json.dumps(summary, indent=2))
        elif export:
            generator.export_markdown_report(export)
        elif detailed:
            report = generator.generate_detailed_report()
            from rich.markdown import Markdown

            console.print(Markdown(report))
        else:
            generator.print_automatic_report()
    finally:
        generator.close()

    raise typer.Exit(0)


@app.command(name="scan-progress", help="Show progress between scans")
def scan_progress():
    """Show detailed progress report comparing recent scans."""
    from codex.scan_tracker import ScanTracker

    tracker = ScanTracker()

    try:
        tracker.print_progress()

        # Also show hotspot evolution
        console.print("\n[bold]Hotspot Evolution:[/bold]")
        hotspots = tracker.get_hotspot_evolution()
        for hotspot in hotspots["hotspots"]:
            console.print(f"  • {hotspot['file']}: {hotspot['unfixed']} unfixed ({hotspot['fixed']} fixed)")
    finally:
        tracker.close()

    raise typer.Exit(0)


@app.command(name="analyze-violations", help="Comprehensive violation analysis by location and category")
def analyze_violations(
    input_file: Annotated[Path | None, typer.Option("--input", "-i", help="Path to scan output file")] = None,
    export_json: Annotated[Path | None, typer.Option("--export", "-e", help="Export analysis to JSON")] = None,
    show_location: Annotated[bool, typer.Option("--location/--no-location", help="Show location analysis")] = True,
    show_category: Annotated[bool, typer.Option("--category/--no-category", help="Show category analysis")] = True,
    show_cross: Annotated[bool, typer.Option("--cross/--no-cross", help="Show cross-dimensional analysis")] = True,
):
    """
    Analyze violations comprehensively by:
    - Location (module, folder, file)
    - Category (error types)
    - Cross-dimensional patterns
    """
    import subprocess

    from codex.violation_analysis import ViolationAnalyzer

    analyzer = ViolationAnalyzer()

    # Get scan output
    if input_file and input_file.exists():
        console.print(f"[bold]Reading violations from {input_file}...[/bold]")
        scan_output = input_file.read_text()
    else:
        console.print("[bold]Running Codex scan to collect violations...[/bold]")
        try:
            result = subprocess.run(["uv", "run", "codex", "scan"], capture_output=True, text=True, cwd=Path.cwd())
            scan_output = result.stdout + result.stderr
        except Exception as e:
            console.print(f"[red]Error running scan: {e}[/red]")
            raise typer.Exit(1)

    # Parse violations
    violations = analyzer.parse_scan_output(scan_output)

    if not violations:
        console.print("[yellow]No violations found or unable to parse scan output.[/yellow]")
        raise typer.Exit(0)

    # Analyze
    report = analyzer.analyze(violations)

    # Store in scan tracking database
    from codex.scan_tracker import ScanTracker

    tracker = ScanTracker()

    # Prepare scan result for tracking
    scan_result = {
        "total_files": report.total_files,
        "scanned_files": report.total_files,
        "total_violations": report.total_violations,
        "by_category": {cat: len(viols) for cat, viols in report.by_category.items()},
        "by_module": {mod: len(viols) for mod, viols in report.by_module.items()},
        "by_pattern": report.patterns_frequency,
        "hotspots": report.hotspots,
        "violations": [
            {
                "file_path": v.file_path,
                "line_number": v.line_number,
                "pattern_name": v.pattern_name,
                "category": v.category,
                "message": v.message,
                "severity": v.severity,
                "module": v.module,
                "folder": v.folder,
            }
            for v in violations
        ],
    }

    scan_id = tracker.record_scan(scan_result)
    tracker.close()

    # Print reports based on options
    analyzer.print_summary()

    if show_location:
        analyzer.print_location_analysis()

    if show_category:
        analyzer.print_category_analysis()

    if show_cross:
        analyzer.print_cross_analysis()

    console.print(f"\n[green]✅ Scan recorded:[/green] {scan_id}")
    console.print("[dim]Database: .codex/scans.db[/dim]")

    # Export if requested
    if export_json:
        analyzer.export_json(export_json)

    raise typer.Exit(0)


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()

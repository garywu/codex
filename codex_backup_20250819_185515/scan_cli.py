"""
Scan CLI - Command-line interface for scan management.

Inspired by Astral's tool design (Ruff, uv):
- Clear, predictable command structure
- Fast execution
- Helpful error messages
- Machine-readable output formats
"""

import asyncio
import json
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .scan_manager import ScanCode, ScanConfiguration, ScanManager
from .scan_registry import ScanCategory, ScanSeverity
import logging

app = typer.Typer(help="Codex scan management commands")
console = Console(stderr=True)


class OutputFormat(str, Enum):
    """Output formats for scan results."""
    HUMAN = "human"
    JSON = "json"
    GITHUB = "github"     # GitHub Actions format
    GITLAB = "gitlab"     # GitLab CI format
    JUNIT = "junit"       # JUnit XML format
    SARIF = "sarif"       # Static Analysis Results Interchange Format


@app.command()
def run(
    path: Path = typer.Argument(Path.cwd(), help="Path to scan"),
    select: list[str] | None = typer.Option(None, "--select", "-s", help="Select specific scan codes (e.g., C001,T001)"),
    ignore: list[str] | None = typer.Option(None, "--ignore", "-i", help="Ignore specific scan codes"),
    category: ScanCategory | None = typer.Option(None, "--category", "-c", help="Run all scans in category"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Apply automatic fixes where possible"),
    format: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format", help="Output format"),
    parallel: bool = typer.Option(True, "--parallel/--serial", help="Run scans in parallel"),
    fail_on: ScanSeverity | None = typer.Option(ScanSeverity.HIGH, "--fail-on", help="Exit with error on this severity"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run scans on the specified path.
    
    Examples:
        # Run all default scans
        codex scan run
        
        # Run only consistency scans
        codex scan run --category consistency
        
        # Run specific scans
        codex scan run --select C001,C002
        
        # Fix issues automatically
        codex scan run --fix
        
        # Output as JSON for CI/CD
        codex scan run --format json
    """
    
    # Build configuration
    config = ScanConfiguration(
        parallel=parallel,
        fix=fix,
        output_format=format.value,
        quiet=quiet,
        verbose=verbose,
    )
    
    # Handle scan selection
    if select:
        # Parse comma-separated codes
        selected_codes = set()
        for code_str in select:
            for code in code_str.split(','):
                selected_codes.add(code.strip().upper())
        config.enabled_scans = selected_codes
    elif category:
        # Select all scans in category
        config.enabled_scans = _get_scans_by_category(category)
    
    # Handle ignores
    if ignore:
        ignored_codes = set()
        for code_str in ignore:
            for code in code_str.split(','):
                ignored_codes.add(code.strip().upper())
        config.enabled_scans -= ignored_codes
    
    # Run scans
    manager = ScanManager()
    
    async def _run():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Running scans...", total=None)
            session = await manager.run_scan_session(path, config)
            progress.update(task, completed=True)
        return session
    
    session = asyncio.run(_run())
    
    # Output results
    _output_results(session, format, quiet, verbose)
    
    # Determine exit code
    exit_code = 0
    if fail_on and session.summary.get("total_violations", 0) > 0:
        # Check if any violations meet the severity threshold
        for result in session.results.values():
            if result and hasattr(result, 'violations'):
                for violation in result.violations:
                    if hasattr(violation, 'priority'):
                        violation_severity = ScanSeverity[violation.priority]
                        if _severity_gte(violation_severity, fail_on):
                            exit_code = 1
                            break
            if exit_code == 1:
                break
    
    raise typer.Exit(exit_code)


@app.command()
def list(
    category: ScanCategory | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    enabled_only: bool = typer.Option(False, "--enabled", help="Show only enabled scans"),
    format: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format", help="Output format"),
):
    """List all available scans.
    
    Examples:
        # List all scans
        codex scan list
        
        # List only consistency scans
        codex scan list --category consistency
        
        # List as JSON
        codex scan list --format json
    """
    from .scan_registry import ScanRegistry
    
    scans = ScanRegistry.list_scans(category)
    if enabled_only:
        scans = [s for s in scans if s.enabled]
    
    if format == OutputFormat.JSON:
        data = [
            {
                "id": scan.id,
                "name": scan.name,
                "description": scan.description,
                "category": scan.category.value,
                "severity": scan.severity.value,
                "enabled": scan.enabled,
                "tags": scan.tags,
            }
            for scan in scans
        ]
        logging.info(json.dumps(data, indent=2))
    else:
        table = Table(title="Available Scans")
        table.add_column("Code", style="cyan")
        table.add_column("ID", style="blue")
        table.add_column("Name", style="green")
        table.add_column("Category")
        table.add_column("Severity")
        table.add_column("Enabled")
        
        # Map scan IDs to codes
        scan_code_map = {code.value: code.name for code in ScanCode}
        
        for scan in scans:
            code = scan_code_map.get(scan.id, "???")
            table.add_row(
                code,
                scan.id,
                scan.name,
                scan.category.value,
                scan.severity.value,
                "✓" if scan.enabled else "✗"
            )
        
        console.logging.info(table)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of sessions to show"),
    format: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format", help="Output format"),
):
    """Show scan history.
    
    Examples:
        # Show last 10 scan sessions
        codex scan history
        
        # Show last 50 sessions
        codex scan history --limit 50
    """
    manager = ScanManager()
    sessions = manager.get_session_history(limit)
    
    if format == OutputFormat.JSON:
        logging.info(json.dumps(sessions, indent=2, default=str))
    else:
        table = Table(title=f"Last {limit} Scan Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Started", style="blue")
        table.add_column("Duration")
        table.add_column("Scans")
        table.add_column("Violations", style="red")
        
        for session in sessions:
            summary = session.get("summary", {})
            started = session.get("started_at", "")
            completed = session.get("completed_at", "")
            
            # Calculate duration
            duration = "N/A"
            if summary.get("duration_ms"):
                duration_ms = summary["duration_ms"]
                if duration_ms < 1000:
                    duration = f"{duration_ms}ms"
                else:
                    duration = f"{duration_ms/1000:.1f}s"
            
            table.add_row(
                session.get("session_id", "")[:8],
                started.split("T")[0] if started else "",
                duration,
                str(summary.get("total_scans", 0)),
                str(summary.get("total_violations", 0)),
            )
        
        console.logging.info(table)


@app.command()
def trends(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    format: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format", help="Output format"),
):
    """Show violation trends over time.
    
    Examples:
        # Show trends for last 30 days
        codex scan trends
        
        # Show trends for last week
        codex scan trends --days 7
    """
    manager = ScanManager()
    trends = manager.get_violation_trends(days)
    
    if format == OutputFormat.JSON:
        logging.info(json.dumps(trends, indent=2))
    else:
        console.logging.info(f"\n[bold]Violation Trends (Last {days} Days)[/bold]\n")
        
        for severity, data in trends.items():
            console.logging.info(f"[yellow]{severity}[/yellow]:")
            for point in data:
                date = point["date"]
                count = point["count"]
                bar = "█" * min(count, 50)
                console.logging.info(f"  {date}: {bar} ({count})")
            console.logging.info()


@app.command()
def explain(
    code: str = typer.Argument(..., help="Scan code to explain (e.g., C001)"),
):
    """Explain what a scan code means.
    
    Examples:
        # Explain hardcoded paths scan
        codex scan explain C001
        
        # Explain ruff scan
        codex scan explain T001
        
        # Explain type checker scan
        codex scan explain T002
    """
    try:
        scan_code = ScanCode[code.upper()]
        from .scan_registry import ScanRegistry
        
        definition = ScanRegistry.get_definition(scan_code.value)
        if definition:
            console.logging.info(f"\n[bold cyan]{code.upper()}[/bold cyan]: {definition.name}\n")
            console.logging.info(f"[yellow]Category:[/yellow] {definition.category.value}")
            console.logging.info(f"[yellow]Severity:[/yellow] {definition.severity.value}")
            console.logging.info(f"[yellow]Description:[/yellow] {definition.description}")
            
            if definition.tags:
                console.logging.info(f"[yellow]Tags:[/yellow] {', '.join(definition.tags)}")
            
            console.logging.info(f"\n[yellow]Status:[/yellow] {'Enabled' if definition.enabled else 'Disabled'}")
            
            # Show examples if available
            if code.upper() == "C001":
                console.logging.info("\n[yellow]Examples of violations:[/yellow]")
                console.logging.info("  • Path(__file__).parent / 'data'")
                console.logging.info("  • db_path = settings.database_path")
                console.logging.info("  • config_dir = settings.config_dir")
                console.logging.info("\n[green]Fix:[/green] Use settings module instead")
                console.logging.info("  • from .settings import settings")
                console.logging.info("  • settings.database_path")
                console.logging.info("  • settings.config_dir")
        else:
            console.logging.info(f"[red]Unknown scan code: {code}[/red]")
    except KeyError:
        console.logging.info(f"[red]Invalid scan code: {code}[/red]")
        console.logging.info("\nUse 'codex scan list' to see all available codes")


def _get_scans_by_category(category: ScanCategory) -> set:
    """Get all scan codes for a category."""
    codes = set()
    
    if category == ScanCategory.CONSISTENCY:
        codes.update(["C001", "C002", "C003"])
    elif category == ScanCategory.SECURITY:
        codes.update(["S001", "S002", "S003"])
    elif category == ScanCategory.QUALITY:
        codes.update(["Q001", "Q002", "Q003"])
    
    # Always include tools
    codes.update(["T001", "T002", "T003"])
    
    return codes


def _severity_gte(sev1: ScanSeverity, sev2: ScanSeverity) -> bool:
    """Check if severity1 >= severity2."""
    severity_order = {
        ScanSeverity.INFO: 0,
        ScanSeverity.LOW: 1,
        ScanSeverity.MEDIUM: 2,
        ScanSeverity.HIGH: 3,
        ScanSeverity.CRITICAL: 4,
    }
    return severity_order[sev1] >= severity_order[sev2]


def _output_results(session, format: OutputFormat, quiet: bool, verbose: bool):
    """Output scan results in the specified format."""
    
    if format == OutputFormat.JSON:
        logging.info(json.dumps(session.to_dict(), indent=2, default=str))
    
    elif format == OutputFormat.GITHUB:
        # GitHub Actions format
        for scan_code, result in session.results.items():
            if result and hasattr(result, 'violations'):
                for violation in result.violations:
                    file_path = getattr(violation, 'file_path', '')
                    line = getattr(violation, 'line_number', 0)
                    message = getattr(violation, 'suggestion', str(violation))
                    logging.info(f"::error file={file_path},line={line}::{scan_code}: {message}")
    
    else:  # HUMAN format
        if not quiet:
            console.logging.info(f"\n[bold]Scan Results[/bold]")
            console.logging.info(f"Session: {session.session_id[:8]}")
            console.logging.info(f"Duration: {session.summary.get('duration_ms', 0)}ms")
            console.logging.info()
            
            # Summary table
            table = Table(title="Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Scans", str(session.summary.get("total_scans", 0)))
            table.add_row("Failed Scans", str(session.summary.get("failed_scans", 0)))
            table.add_row("Total Violations", str(session.summary.get("total_violations", 0)))
            
            console.logging.info(table)
            
            # Detailed violations if verbose
            if verbose and session.summary.get("total_violations", 0) > 0:
                console.logging.info("\n[bold]Violations:[/bold]")
                
                for scan_code, result in session.results.items():
                    if result and hasattr(result, 'violations') and result.violations:
                        console.logging.info(f"\n[yellow]{scan_code}:[/yellow]")
                        for violation in result.violations[:10]:  # Limit output
                            file_path = getattr(violation, 'file_path', 'unknown')
                            line = getattr(violation, 'line_number', 0)
                            message = getattr(violation, 'suggestion', str(violation))
                            console.logging.info(f"  {file_path}:{line} - {message}")


if __name__ == "__main__":
    app()
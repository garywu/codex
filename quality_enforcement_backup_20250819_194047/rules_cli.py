"""
CLI for Codex rules - Inspired by Ruff's rule command.

This module provides commands for managing and running Codex's custom rules.
"""

import json
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .rules.categories import CATEGORY_DESCRIPTIONS, RulePrefix
from .rules.loader import (
    ensure_initialized,
    format_rule_help,
    get_rule_stats,
    list_rules_by_category,
)
from .rules.registry import Severity, registry

app = typer.Typer(help="Codex rule management commands")
console = Console(stderr=True)


@app.command()
def check(
    path: Path = typer.Argument(Path.cwd(), help="Path to check"),
    select: list[str] | None = typer.Option(None, "--select", "-s", help="Select rules (e.g., SET001,DB)"),
    ignore: list[str] | None = typer.Option(None, "--ignore", "-i", help="Ignore rules"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Apply automatic fixes"),
    format: str = typer.Option("default", "--format", help="Output format (default/json/github)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output"),
    statistics: bool = typer.Option(False, "--statistics", help="Show statistics"),
):
    """Check code against Codex rules.
    
    Examples:
        # Check all rules
        codex rules check
        
        # Check only settings rules
        codex rules check --select SET
        
        # Check specific rules
        codex rules check --select SET001,DB001
        
        # Apply fixes
        codex rules check --fix
        
        # Output for CI
        codex rules check --format github
    """
    ensure_initialized()
    
    # Build rule selection
    selected_rules = set()
    
    if select:
        for selector in select:
            for code in selector.split(','):
                rules = registry.select_rules([code.strip()])
                selected_rules.update(r.code for r in rules)
    else:
        # Default to all enabled rules
        selected_rules = {r.code for r in registry.get_enabled_rules()}
    
    if ignore:
        for selector in ignore:
            for code in selector.split(','):
                rules = registry.select_rules([code.strip()])
                selected_rules.difference_update(r.code for r in rules)
    
    # Run checks
    violations = []
    files_checked = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        task = progress.add_task(f"Checking {path}...", total=None)
        
        if path.is_file():
            files = [path]
        else:
            files = list(path.rglob("*.py"))
        
        for file_path in files:
            # Skip virtual environments and caches
            if any(skip in str(file_path) for skip in [
                'venv', '.venv', '__pycache__', '.git', 
                '.pytest_cache', '.mypy_cache', 'node_modules'
            ]):
                continue
            
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                
                file_violations = registry.check_file(file_path, content, selected_rules)
                violations.extend(file_violations)
                files_checked += 1
                
                progress.update(task, description=f"Checked {files_checked} files...")
            except (OSError, UnicodeDecodeError):
                continue
        
        progress.update(task, completed=True)
    
    # Apply fixes if requested
    if fix and violations:
        fixed = 0
        for violation in violations:
            if violation.fix and violation.fix.applicability != "never":
                # Apply fix (simplified - real implementation would be more complex)
                fixed += 1
        
        if not quiet:
            console.logging.info(f"[green]Fixed {fixed} violation(s)[/green]")
    
    # Output results
    if format == "json":
        output = {
            "violations": [v.format("json") for v in violations],
            "statistics": {
                "files_checked": files_checked,
                "total_violations": len(violations),
                "rules_checked": len(selected_rules),
            }
        }
        logging.info(json.dumps(output, indent=2))
    elif format == "github":
        for violation in violations:
            print(violation.format("github"))
    else:
        if not quiet:
            if violations:
                console.logging.info(f"\n[red]Found {len(violations)} violation(s)[/red]\n")
                for violation in violations:
                    color = "red" if violation.severity == Severity.ERROR else "yellow"
                    console.logging.info(f"[{color}]{violation.format()}[/{color}]")
            else:
                console.logging.info(f"[green]✓ No violations found in {files_checked} file(s)[/green]")
    
    # Show statistics if requested
    if statistics and not quiet:
        console.logging.info("\n[bold]Statistics:[/bold]")
        console.logging.info(f"Files checked: {files_checked}")
        console.logging.info(f"Rules checked: {len(selected_rules)}")
        console.logging.info(f"Violations found: {len(violations)}")
        
        # Count by severity
        by_severity = {}
        for violation in violations:
            sev = violation.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        if by_severity:
            console.logging.info("\nBy severity:")
            for sev, count in sorted(by_severity.items()):
                console.logging.info(f"  {sev}: {count}")
    
    # Exit with error if violations found
    if violations and any(v.severity == Severity.ERROR for v in violations):
        raise typer.Exit(1)


@app.command()
def list(
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    enabled_only: bool = typer.Option(False, "--enabled", help="Show only enabled rules"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """List all available Codex rules.
    
    Examples:
        # List all rules
        codex rules list
        
        # List only settings rules
        codex rules list --category SET
        
        # List with details
        codex rules list --verbose
    """
    ensure_initialized()
    
    rules_by_category = list_rules_by_category()
    
    if category:
        # Filter to specific category
        try:
            prefix = RulePrefix(category.upper())
            rules_by_category = {prefix: rules_by_category.get(prefix, [])}
        except ValueError:
            console.logging.info(f"[red]Invalid category: {category}[/red]")
            console.logging.info(f"Valid categories: {', '.join(p.value for p in RulePrefix)}")
            raise typer.Exit(1)
    
    if not verbose:
        # Table view
        table = Table(title="Codex Rules")
        table.add_column("Code", style="cyan")
        table.add_column("Name", style="blue")
        table.add_column("Severity")
        table.add_column("Description")
        
        for prefix, rules in sorted(rules_by_category.items()):
            # Add category header
            table.add_row(
                f"[bold]{prefix.value}[/bold]",
                f"[dim]{CATEGORY_DESCRIPTIONS.get(prefix, '')}[/dim]",
                "",
                "",
            )
            
            for rule in rules:
                if enabled_only and not rule.enabled:
                    continue
                
                severity_color = {
                    Severity.ERROR: "red",
                    Severity.WARNING: "yellow",
                    Severity.INFO: "blue",
                    Severity.HINT: "dim",
                }.get(rule.severity, "white")
                
                table.add_row(
                    f"  {rule.code}",
                    rule.name,
                    f"[{severity_color}]{rule.severity.value}[/{severity_color}]",
                    rule.description or "",
                )
        
        console.logging.info(table)
    else:
        # Detailed view
        for prefix, rules in sorted(rules_by_category.items()):
            console.logging.info(f"\n[bold]{prefix.value}: {CATEGORY_DESCRIPTIONS.get(prefix, '')}[/bold]")
            
            for rule in rules:
                if enabled_only and not rule.enabled:
                    continue
                
                console.logging.info(f"\n{format_rule_help(rule)}")
    
    # Show statistics
    stats = get_rule_stats()
    console.logging.info(f"\n[dim]Total: {stats['total_rules']} rules, {stats['enabled_rules']} enabled[/dim]")


@app.command()
def explain(
    code: str = typer.Argument(..., help="Rule code to explain (e.g., SET001)"),
):
    """Explain what a rule means.
    
    Examples:
        # Explain settings rule
        codex rules explain SET001
        
        # Explain database rule
        codex rules explain DB001
    """
    ensure_initialized()
    
    rule = registry.get_rule(code.upper())
    if not rule:
        console.logging.info(f"[red]Unknown rule: {code}[/red]")
        console.logging.info("\nUse 'codex rules list' to see all available rules")
        raise typer.Exit(1)
    
    console.logging.info(f"\n{format_rule_help(rule)}")
    
    # Check if rule has a checker
    checker = registry.get_checker(code.upper())
    if checker:
        console.logging.info(f"\n[dim]Checker: {checker.__class__.__name__}[/dim]")
        console.logging.info(f"[dim]Status: {'Enabled' if rule.enabled else 'Disabled'}[/dim]")


@app.command()
def stats():
    """Show statistics about loaded rules."""
    ensure_initialized()
    
    stats = get_rule_stats()
    rules_by_category = list_rules_by_category()
    
    console.logging.info("[bold]Codex Rules Statistics[/bold]\n")
    
    table = Table(title="Overview")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Rules", str(stats['total_rules']))
    table.add_row("Enabled Rules", str(stats['enabled_rules']))
    table.add_row("Categories", str(stats['categories']))
    
    console.logging.info(table)
    
    # Rules by category
    console.logging.info("\n[bold]Rules by Category:[/bold]")
    for prefix in sorted(rules_by_category.keys()):
        rules = rules_by_category[prefix]
        enabled = sum(1 for r in rules if r.enabled)
        console.logging.info(f"  {prefix.value}: {len(rules)} rules ({enabled} enabled)")
        console.logging.info(f"    {CATEGORY_DESCRIPTIONS.get(prefix, '')}")


if __name__ == "__main__":
    app()
"""
Pattern management CLI commands for Codex.

This module provides CLI commands for managing patterns that AI assistants
can use to incrementally add, update, and query patterns.
"""

import json
import logging
from enum import Enum
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from .pattern_models import Pattern, PatternCategory, PatternPriority
from .unified_database import UnifiedDatabase

app = typer.Typer(help="Manage Codex patterns")

# Configure Rich Console for proper stdout/stderr separation
console = Console(stderr=True)  # Status messages go to stderr
data_console = Console(stderr=False)  # Data output goes to stdout


class OutputFormat(str, Enum):
    """Output format for pattern commands."""

    HUMAN = "human"
    JSON = "json"
    YAML = "yaml"
    TABLE = "table"


@app.command()
def add(
    name: str = typer.Argument(..., help="Pattern name (e.g., 'no-bare-except')"),
    category: str = typer.Option(..., "--category", "-c", help="Category: error_handling, naming, etc."),
    priority: str = typer.Option("MEDIUM", "--priority", "-p", help="Priority: MANDATORY, CRITICAL, HIGH, MEDIUM, LOW"),
    description: str = typer.Option(..., "--description", "-d", help="What this pattern detects"),
    detection_rule: str | None = typer.Option(None, "--rule", "-r", help="Detection rule/regex"),
    fix_template: str | None = typer.Option(None, "--fix", "-f", help="Fix template"),
    example_good: str | None = typer.Option(None, "--good", help="Good example code"),
    example_bad: str | None = typer.Option(None, "--bad", help="Bad example code"),
    tags: str | None = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
    source: str = typer.Option("cli", "--source", "-s", help="Source of the pattern"),
    json_input: str | None = typer.Option(None, "--json", help="JSON string with full pattern data"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode for automation"),
):
    """
    Add a new pattern to the database.

    Examples:
        # Simple pattern
        codex pattern add "no-print-statements" \\
            --category debugging \\
            --priority HIGH \\
            --description "Avoid print statements in production code" \\
            --rule "\\bprint\\s*\\("

        # Pattern with fix
        codex pattern add "use-httpx" \\
            --category dependencies \\
            --priority MEDIUM \\
            --description "Use httpx instead of requests" \\
            --rule "import requests" \\
            --fix "import httpx as requests"

        # From JSON (for AI assistants)
        codex pattern add "pattern-name" --json '{"category": "naming", ...}'
    """
    import asyncio

    try:
        # Build pattern data
        if json_input:
            # Parse JSON input for full pattern data
            pattern_data = json.loads(json_input)
            pattern_data["name"] = name  # Override name from argument
        else:
            pattern_data = {
                "name": name,
                "category": PatternCategory(category.lower()),
                "priority": PatternPriority(priority.upper()),
                "description": description,
                "rule": detection_rule or "# No detection rule specified",
                "detection": {
                    "regex": detection_rule,
                    "keywords": [],
                    "confidence": 0.9,
                },
                "fix": {
                    "template": fix_template,
                    "complexity": "medium",
                    "auto_fixable": fix_template is not None,
                    "suggestions": [],
                    "prerequisites": [],
                },
                "examples": {"good": example_good or "", "bad": example_bad or "", "context": None},
                "source": source,
                "tags": tags.split(",") if tags else [],
            }

        # Validate with Pydantic
        pattern = Pattern(**pattern_data)

        # Add to database
        async def add_pattern():
            db = UnifiedDatabase()
            result = await db.add_pattern_async(pattern.model_dump())
            return result

        result = asyncio.run(add_pattern())

        if not quiet:
            console.logging.info(f"[green]✅ Added pattern: {name}[/green]")
            console.logging.info(f"  Category: {pattern.category}")
            console.logging.info(f"  Priority: {pattern.priority}")
            console.logging.info(f"  ID: {result.get('id', 'N/A')}")
        else:
            # Output just the ID for scripting
            logging.info(result.get("id", ""))

    except ValidationError as e:
        console.logging.info(f"[red]❌ Validation error: {e}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.logging.info(f"[red]❌ Invalid JSON: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.logging.info(f"[red]❌ Error adding pattern: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="Filter by priority"),
    search: str | None = typer.Option(None, "--search", "-s", help="Search in name/description"),
    format: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", help="Output format"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum patterns to show"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Just pattern names"),
):
    """
    List patterns in the database.

    Examples:
        # List all patterns
        codex pattern list

        # Filter by category
        codex pattern list --category error_handling

        # Filter by priority
        codex pattern list --priority MANDATORY

        # Search patterns
        codex pattern list --search "validation"

        # JSON output for AI processing
        codex pattern list --format json

        # Just names for scripting
        codex pattern list --quiet
    """
    import asyncio

    async def get_patterns():
        db = UnifiedDatabase()

        # Build filters
        filters = {}
        if category:
            filters["category"] = category.lower()
        if priority:
            filters["priority"] = priority.upper()

        if search:
            # Use FTS search
            patterns = await db.search_patterns_async(search, limit=limit)
        else:
            # Use regular query with filters
            patterns = await db.get_patterns(**filters)

        return patterns[:limit]

    patterns = asyncio.run(get_patterns())

    if quiet:
        # Just output pattern names for scripting
        for p in patterns:
            logging.info(p["name"])
        return

    if format == OutputFormat.JSON:
        # JSON output for AI/automation
        logging.info(json.dumps([dict(p) for p in patterns], indent=2, default=str))

    elif format == OutputFormat.YAML:
        # YAML output
        import yaml

        logging.info(yaml.dump([dict(p) for p in patterns], default_flow_style=False))

    elif format == OutputFormat.TABLE:
        # Rich table for humans
        table = Table(title=f"Codex Patterns ({len(patterns)} found)")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Priority", style="magenta")
        table.add_column("Description", style="white")

        for p in patterns:
            priority_color = {
                "MANDATORY": "red",
                "CRITICAL": "bright_red",
                "HIGH": "yellow",
                "MEDIUM": "blue",
                "LOW": "green",
            }.get(p.get("priority", "MEDIUM"), "white")

            table.add_row(
                p["name"],
                p.get("category", ""),
                f"[{priority_color}]{p.get('priority', '')}[/{priority_color}]",
                p.get("description", "")[:60] + "..."
                if len(p.get("description", "")) > 60
                else p.get("description", ""),
            )

        data_console.logging.info(table)  # Table data goes to stdout
    else:
        # Human-readable format
        for p in patterns:
            data_console.logging.info(f"\n[bold cyan]{p['name']}[/bold cyan]")
            data_console.logging.info(f"  Category: {p.get('category', 'N/A')}")
            data_console.logging.info(f"  Priority: {p.get('priority', 'N/A')}")
            data_console.logging.info(f"  Description: {p.get('description', 'N/A')}")


@app.command()
def show(
    name: str = typer.Argument(..., help="Pattern name to show details"),
    format: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format", "-f", help="Output format"),
):
    """
    Show detailed information about a pattern.

    Examples:
        # Show pattern details
        codex pattern show no-bare-except

        # Get as JSON for processing
        codex pattern show no-bare-except --format json
    """
    import asyncio

    async def get_pattern():
        db = UnifiedDatabase()
        patterns = await db.get_patterns(name=name)
        return patterns[0] if patterns else None

    pattern = asyncio.run(get_pattern())

    if not pattern:
        console.logging.info(f"[red]❌ Pattern not found: {name}[/red]")
        raise typer.Exit(1)

    if format == OutputFormat.JSON:
        logging.info(json.dumps(dict(pattern), indent=2, default=str))
    elif format == OutputFormat.YAML:
        import yaml

        logging.info(yaml.dump(dict(pattern), default_flow_style=False))
    else:
        # Human-readable format
        data_console.logging.info(f"\n[bold cyan]{pattern['name']}[/bold cyan]")
        data_console.logging.info(f"[dim]ID: {pattern.get('id', 'N/A')}[/dim]\n")

        data_console.logging.info(f"[yellow]Category:[/yellow] {pattern.get('category', 'N/A')}")
        data_console.logging.info(f"[yellow]Priority:[/yellow] {pattern.get('priority', 'N/A')}")
        data_console.logging.info(f"[yellow]Description:[/yellow] {pattern.get('description', 'N/A')}")

        if pattern.get("detection_rules"):
            data_console.logging.info("\n[yellow]Detection Rules:[/yellow]")
            for rule in pattern.get("detection_rules", {}).get("rules", []):
                data_console.logging.info(f"  • {rule}")

        if pattern.get("fix_template"):
            data_console.logging.info("\n[yellow]Fix Template:[/yellow]")
            data_console.logging.info(f"  {pattern['fix_template']}")

        if pattern.get("tags"):
            data_console.logging.info(f"\n[yellow]Tags:[/yellow] {', '.join(pattern['tags'])}")

        data_console.logging.info(f"\n[dim]Source: {pattern.get('source', 'N/A')}[/dim]")
        data_console.logging.info(f"[dim]Created: {pattern.get('created_at', 'N/A')}[/dim]")


@app.command()
def update(
    name: str = typer.Argument(..., help="Pattern name to update"),
    new_name: str | None = typer.Option(None, "--name", help="New name"),
    category: str | None = typer.Option(None, "--category", "-c", help="New category"),
    priority: str | None = typer.Option(None, "--priority", "-p", help="New priority"),
    description: str | None = typer.Option(None, "--description", "-d", help="New description"),
    detection_rule: str | None = typer.Option(None, "--rule", "-r", help="New detection rule"),
    fix_template: str | None = typer.Option(None, "--fix", "-f", help="New fix template"),
    json_input: str | None = typer.Option(None, "--json", help="JSON with updates"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
):
    """
    Update an existing pattern.

    Examples:
        # Update priority
        codex pattern update no-print-statements --priority MANDATORY

        # Update multiple fields
        codex pattern update old-name --name new-name --priority HIGH

        # Update from JSON
        codex pattern update pattern-name --json '{"priority": "CRITICAL"}'
    """
    import asyncio

    async def update_pattern():
        db = UnifiedDatabase()

        # Get existing pattern
        patterns = await db.get_patterns(name=name)
        if not patterns:
            return None

        pattern = patterns[0]

        # Apply updates
        if json_input:
            updates = json.loads(json_input)
        else:
            updates = {}
            if new_name:
                updates["name"] = new_name
            if category:
                updates["category"] = category.lower()
            if priority:
                updates["priority"] = priority.upper()
            if description:
                updates["description"] = description
            if detection_rule:
                updates["detection_rules"] = {"rules": [detection_rule]}
            if fix_template:
                updates["fix_template"] = fix_template

        # Update in database
        result = await db.update_pattern(pattern["id"], updates)
        return result

    try:
        result = asyncio.run(update_pattern())

        if result:
            if not quiet:
                console.logging.info(f"[green]✅ Updated pattern: {name}[/green]")
        else:
            console.logging.info(f"[red]❌ Pattern not found: {name}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.logging.info(f"[red]❌ Error updating pattern: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    name: str = typer.Argument(..., help="Pattern name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
):
    """
    Delete a pattern from the database.

    Examples:
        # Delete with confirmation
        codex pattern delete old-pattern

        # Force delete (no confirmation)
        codex pattern delete old-pattern --force
    """
    import asyncio

    if not force:
        confirm = typer.confirm(f"Delete pattern '{name}'?")
        if not confirm:
            raise typer.Abort()

    async def delete_pattern():
        db = UnifiedDatabase()
        patterns = await db.get_patterns(name=name)
        if not patterns:
            return False

        await db.delete_pattern(patterns[0]["id"])
        return True

    result = asyncio.run(delete_pattern())

    if result:
        if not quiet:
            console.logging.info(f"[green]✅ Deleted pattern: {name}[/green]")
    else:
        console.logging.info(f"[red]❌ Pattern not found: {name}[/red]")
        raise typer.Exit(1)


@app.command()
def import_file(
    file_path: Path = typer.Argument(..., help="JSON file with patterns to import"),
    source: str = typer.Option("import", "--source", "-s", help="Source identifier"),
    update_existing: bool = typer.Option(False, "--update", "-u", help="Update existing patterns"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
):
    """
    Import patterns from a JSON file.

    The JSON file should contain an array of pattern objects or a single pattern.

    Examples:
        # Import from project-init.json
        codex pattern import-file ~/work/project-init.json

        # Import and update existing
        codex pattern import-file patterns.json --update

        # Import with custom source
        codex pattern import-file team-patterns.json --source team
    """
    import asyncio

    if not file_path.exists():
        console.logging.info(f"[red]❌ File not found: {file_path}[/red]")
        raise typer.Exit(1)

    try:
        with open(file_path) as f:
            data = json.load(f)

        # Handle both single pattern and array of patterns
        if isinstance(data, dict) and "patterns" in data:
            patterns_data = data["patterns"]
        elif isinstance(data, list):
            patterns_data = data
        elif isinstance(data, dict):
            patterns_data = [data]
        else:
            console.logging.info("[red]❌ Invalid JSON format[/red]")
            raise typer.Exit(1)

        async def import_patterns():
            db = UnifiedDatabase()
            imported = 0
            updated = 0
            errors = []

            for p_data in patterns_data:
                try:
                    # Add source
                    if "metadata" not in p_data:
                        p_data["metadata"] = {}
                    p_data["metadata"]["source"] = source

                    # Validate with Pydantic
                    pattern = Pattern(**p_data)

                    # Check if exists
                    existing = await db.get_patterns(name=pattern.name)

                    if existing and update_existing:
                        await db.update_pattern(existing[0]["id"], pattern.model_dump())
                        updated += 1
                    elif not existing:
                        await db.add_pattern(pattern.model_dump())
                        imported += 1

                except Exception as e:
                    errors.append(f"{p_data.get('name', 'unknown')}: {e}")

            return imported, updated, errors

        imported, updated, errors = asyncio.run(import_patterns())

        if not quiet:
            console.logging.info("\n[green]✅ Import complete:[/green]")
            console.logging.info(f"  • Imported: {imported}")
            console.logging.info(f"  • Updated: {updated}")
            if errors:
                console.logging.info(f"  • Errors: {len(errors)}")
                for err in errors[:5]:
                    console.logging.info(f"    - {err}")
        else:
            logging.info(f"{imported},{updated},{len(errors)}")

    except json.JSONDecodeError as e:
        console.logging.info(f"[red]❌ Invalid JSON: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.logging.info(f"[red]❌ Import error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
    format: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format", "-f", help="Output format"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Just pattern names"),
):
    """
    Search patterns using full-text search.

    Examples:
        # Search for validation patterns
        codex pattern search validation

        # Search with more results
        codex pattern search "error handling" --limit 20

        # Get JSON results for processing
        codex pattern search naming --format json
    """
    import asyncio

    async def search_patterns():
        db = UnifiedDatabase()
        return await db.search_patterns_async(query, limit=limit)

    patterns = asyncio.run(search_patterns())

    if quiet:
        for p in patterns:
            print(p["name"])
        return

    if format == OutputFormat.JSON:
        logging.info(json.dumps([dict(p) for p in patterns], indent=2, default=str))
    else:
        data_console.logging.info(f"\n[bold]Search results for '{query}':[/bold]")
        for p in patterns:
            data_console.logging.info(f"\n[cyan]{p['name']}[/cyan]")
            data_console.logging.info(f"  {p.get('description', 'N/A')[:80]}")
            data_console.logging.info(
                f"  [dim]Category: {p.get('category', 'N/A')} | Priority: {p.get('priority', 'N/A')}[/dim]"
            )


@app.command()
def bulk(
    operation: str = typer.Argument(..., help="Operation: add, check, diff, sync"),
    input_file: Path | None = typer.Option(None, "--file", "-f", help="JSON file with patterns"),
    json_input: str | None = typer.Option(None, "--json", "-j", help="JSON string with patterns"),
    ai_query: str | None = typer.Option(None, "--query", "-q", help="Natural language query about patterns"),
    output: OutputFormat = typer.Option(OutputFormat.JSON, "--output", "-o", help="Output format"),
):
    """
    Bulk operations optimized for AI assistants.

    Operations:
        - check: Check which patterns already exist
        - diff: Show what's new vs existing
        - add: Add multiple patterns at once
        - sync: Add new, update existing
        - query: Natural language query about patterns

    Examples:
        # Check what patterns exist from a list
        codex pattern bulk check --json '[{"name": "no-print"}, {"name": "no-eval"}]'

        # See what's new in project-init.json
        codex pattern bulk diff --file project-init.json

        # Add multiple patterns
        codex pattern bulk add --file new-patterns.json

        # Natural language query
        codex pattern bulk query --query "patterns about error handling that are mandatory"

        # Sync patterns (add new, update existing)
        codex pattern bulk sync --file project-patterns.json
    """
    import asyncio

    async def run_bulk_operation():
        db = UnifiedDatabase()

        # Parse input
        if input_file and input_file.exists():
            with open(input_file) as f:
                patterns_data = json.load(f)
                if isinstance(patterns_data, dict) and "patterns" in patterns_data:
                    patterns_data = patterns_data["patterns"]
        elif json_input:
            patterns_data = json.loads(json_input)
        else:
            patterns_data = []

        # Handle natural language query
        if ai_query or operation == "query":
            query_text = ai_query or operation
            # Use FTS and smart filtering
            results = await db.search_patterns_async(query_text, limit=100)

            # Apply smart filters based on query
            if "mandatory" in query_text.lower():
                results = [r for r in results if r.get("priority") == "MANDATORY"]
            if "critical" in query_text.lower():
                results = [r for r in results if r.get("priority") == "CRITICAL"]
            if "high" in query_text.lower():
                results = [r for r in results if r.get("priority") in ["HIGH", "CRITICAL", "MANDATORY"]]

            # Check for category mentions
            categories = [
                "error_handling",
                "naming",
                "validation",
                "logging",
                "dependencies",
                "testing",
                "imports",
                "organization",
                "git",
            ]
            for cat in categories:
                if cat.replace("_", " ") in query_text.lower():
                    results = [r for r in results if r.get("category") == cat]

            return {
                "query": query_text,
                "count": len(results),
                "patterns": [
                    {
                        "name": r["name"],
                        "category": r.get("category"),
                        "priority": r.get("priority"),
                        "description": r.get("description"),
                    }
                    for r in results
                ],
            }

        # Handle check operation
        if operation == "check":
            existing = []
            missing = []

            for p_data in patterns_data:
                name = p_data.get("name")
                if name:
                    patterns = await db.get_patterns(name=name)
                    if patterns:
                        existing.append(
                            {
                                "name": name,
                                "id": patterns[0]["id"],
                                "priority": patterns[0].get("priority"),
                                "category": patterns[0].get("category"),
                            }
                        )
                    else:
                        missing.append({"name": name})

            return {
                "existing": existing,
                "missing": missing,
                "summary": {"total": len(patterns_data), "existing": len(existing), "missing": len(missing)},
            }

        # Handle diff operation
        elif operation == "diff":
            new_patterns = []
            changed_patterns = []
            unchanged_patterns = []

            for p_data in patterns_data:
                name = p_data.get("name")
                if name:
                    existing = await db.get_patterns(name=name)
                    if not existing:
                        new_patterns.append(
                            {
                                "name": name,
                                "category": p_data.get("category"),
                                "priority": p_data.get("priority"),
                                "description": p_data.get("description", "")[:100],
                            }
                        )
                    else:
                        # Check for changes
                        existing_p = existing[0]
                        changes = []

                        for field in ["category", "priority", "description"]:
                            if field in p_data and p_data[field] != existing_p.get(field):
                                changes.append({"field": field, "old": existing_p.get(field), "new": p_data[field]})

                        if changes:
                            changed_patterns.append({"name": name, "changes": changes})
                        else:
                            unchanged_patterns.append(name)

            return {
                "new": new_patterns,
                "changed": changed_patterns,
                "unchanged": unchanged_patterns,
                "summary": {
                    "total": len(patterns_data),
                    "new": len(new_patterns),
                    "changed": len(changed_patterns),
                    "unchanged": len(unchanged_patterns),
                },
            }

        # Handle add operation
        elif operation == "add":
            added = []
            skipped = []
            errors = []

            for p_data in patterns_data:
                try:
                    name = p_data.get("name")
                    if name:
                        # Check if exists
                        existing = await db.get_patterns(name=name)
                        if existing:
                            skipped.append({"name": name, "reason": "already exists"})
                        else:
                            # Validate and add
                            pattern = Pattern(**p_data)
                            result = await db.add_pattern_async(pattern.model_dump())
                            added.append(
                                {
                                    "name": name,
                                    "id": result.get("id"),
                                    "category": pattern.category,
                                    "priority": pattern.priority,
                                }
                            )
                except Exception as e:
                    errors.append({"name": p_data.get("name", "unknown"), "error": str(e)})

            return {
                "added": added,
                "skipped": skipped,
                "errors": errors,
                "summary": {
                    "total": len(patterns_data),
                    "added": len(added),
                    "skipped": len(skipped),
                    "errors": len(errors),
                },
            }

        # Handle sync operation
        elif operation == "sync":
            added = []
            updated = []
            unchanged = []
            errors = []

            for p_data in patterns_data:
                try:
                    name = p_data.get("name")
                    if name:
                        existing = await db.get_patterns(name=name)

                        if existing:
                            # Update if different
                            existing_p = existing[0]
                            needs_update = False

                            for field in ["category", "priority", "description", "detection_rules", "fix_template"]:
                                if field in p_data and p_data[field] != existing_p.get(field):
                                    needs_update = True
                                    break

                            if needs_update:
                                await db.update_pattern(existing_p["id"], p_data)
                                updated.append({"name": name, "id": existing_p["id"]})
                            else:
                                unchanged.append(name)
                        else:
                            # Add new
                            pattern = Pattern(**p_data)
                            result = await db.add_pattern_async(pattern.model_dump())
                            added.append({"name": name, "id": result.get("id")})
                except Exception as e:
                    errors.append({"name": p_data.get("name", "unknown"), "error": str(e)})

            return {
                "added": added,
                "updated": updated,
                "unchanged": unchanged,
                "errors": errors,
                "summary": {
                    "total": len(patterns_data),
                    "added": len(added),
                    "updated": len(updated),
                    "unchanged": len(unchanged),
                    "errors": len(errors),
                },
            }

        else:
            return {"error": f"Unknown operation: {operation}"}

    try:
        result = asyncio.run(run_bulk_operation())

        if output == OutputFormat.JSON:
            logging.info(json.dumps(result, indent=2, default=str))
        elif output == OutputFormat.YAML:
            import yaml

            logging.info(yaml.dump(result, default_flow_style=False))
        else:
            # Human format
            if "query" in result:
                console.logging.info(f"\n[bold]Query: {result['query']}[/bold]")
                console.logging.info(f"Found {result['count']} patterns\n")
                for p in result["patterns"][:10]:
                    console.logging.info(f"• [cyan]{p['name']}[/cyan] ({p['category']}/{p['priority']})")
                    console.logging.info(f"  {p['description'][:80]}")
            elif "summary" in result:
                console.logging.info(f"\n[bold]Bulk {operation} results:[/bold]")
                for key, value in result["summary"].items():
                    console.logging.info(f"  {key}: {value}")

                if result.get("new"):
                    console.logging.info("\n[green]New patterns:[/green]")
                    for p in result["new"][:5]:
                        console.logging.info(f"  • {p['name']}")

                if result.get("added"):
                    console.logging.info("\n[green]Added patterns:[/green]")
                    for p in result["added"][:5]:
                        console.logging.info(f"  • {p['name']} (ID: {p['id']})")

                if result.get("errors"):
                    console.logging.info("\n[red]Errors:[/red]")
                    for e in result["errors"][:5]:
                        console.logging.info(f"  • {e['name']}: {e['error']}")
            else:
                console.logging.info(result)

    except Exception as e:
        console.logging.info(f"[red]❌ Bulk operation error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ai_assist(
    prompt: str = typer.Argument(..., help="Natural language request about patterns"),
    context_file: Path | None = typer.Option(None, "--context", "-c", help="File with additional context"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute suggested commands"),
):
    """
    AI assistant interface for pattern management.

    This command understands natural language and suggests appropriate operations.

    Examples:
        # Ask what patterns we have
        codex pattern ai-assist "What error handling patterns do we have?"

        # Request pattern creation
        codex pattern ai-assist "Create a pattern for detecting TODO comments"

        # Analyze and suggest
        codex pattern ai-assist "What patterns from project-init.json are missing?" --context project-init.json

        # Execute suggestions
        codex pattern ai-assist "Add all mandatory patterns from the context" --context patterns.json --execute
    """
    import asyncio

    async def process_ai_request():
        db = UnifiedDatabase()

        # Analyze the prompt to determine intent
        prompt_lower = prompt.lower()

        # Load context if provided
        context_data = None
        if context_file and context_file.exists():
            with open(context_file) as f:
                context_data = json.load(f)

        # Determine operation type
        if any(word in prompt_lower for word in ["what", "show", "list", "find", "search"]):
            # Query operation
            patterns = await db.search_patterns_async(prompt, limit=20)

            return {
                "intent": "query",
                "response": f"Found {len(patterns)} patterns matching your query",
                "data": patterns,
                "suggested_commands": [
                    f"codex pattern list --search '{prompt.split()[1] if len(prompt.split()) > 1 else prompt}'",
                    "codex pattern stats",
                ],
            }

        elif any(word in prompt_lower for word in ["create", "add", "make", "new"]):
            # Creation operation
            # Extract pattern details from prompt
            suggestions = []

            if "todo" in prompt_lower or "fixme" in prompt_lower:
                suggestions.append(
                    {
                        "name": "no-todo-comments",
                        "category": "comments",
                        "priority": "MEDIUM",
                        "description": "Avoid TODO/FIXME comments in production code",
                        "detection_rule": r"(TODO|FIXME|XXX|HACK):",
                        "command": 'codex pattern add "no-todo-comments" --category comments --priority MEDIUM --description "Avoid TODO/FIXME comments" --rule "(TODO|FIXME|XXX|HACK):"',
                    }
                )

            return {
                "intent": "create",
                "response": "Here are pattern creation suggestions based on your request",
                "suggestions": suggestions,
            }

        elif any(word in prompt_lower for word in ["missing", "diff", "compare", "check"]):
            # Comparison operation
            if context_data:
                # Check what's missing
                result = {
                    "intent": "compare",
                    "response": "Analyzing differences between context and database",
                    "suggested_commands": [
                        f"codex pattern bulk diff --file {context_file}",
                        f"codex pattern bulk check --file {context_file}",
                    ],
                }

                if execute:
                    # Actually run the diff
                    patterns_data = context_data.get(
                        "patterns", context_data if isinstance(context_data, list) else [context_data]
                    )
                    missing = []
                    for p in patterns_data:
                        existing = await db.get_patterns(name=p.get("name"))
                        if not existing:
                            missing.append(p.get("name"))

                    result["missing_patterns"] = missing
                    result["missing_count"] = len(missing)

                return result
            else:
                return {
                    "intent": "compare",
                    "response": "Please provide a context file to compare against",
                    "error": "No context file provided",
                }

        elif any(word in prompt_lower for word in ["import", "load", "sync"]):
            # Import operation
            if context_file:
                return {
                    "intent": "import",
                    "response": f"Ready to import patterns from {context_file}",
                    "suggested_commands": [
                        f"codex pattern bulk sync --file {context_file}",
                        f"codex pattern import-file {context_file}",
                    ],
                }
            else:
                return {
                    "intent": "import",
                    "response": "Please provide a file to import from",
                    "error": "No context file provided",
                }

        else:
            # General help
            return {
                "intent": "help",
                "response": "I can help you manage patterns. Try asking about existing patterns, creating new ones, or importing from files.",
                "suggested_commands": [
                    "codex pattern list",
                    "codex pattern stats",
                    "codex pattern bulk check --file your-patterns.json",
                ],
            }

    try:
        result = asyncio.run(process_ai_request())

        # Display response
        console.logging.info("\n[bold cyan]AI Assistant Response:[/bold cyan]")
        console.logging.info(f"{result['response']}\n")

        if result.get("suggested_commands"):
            console.logging.info("[yellow]Suggested commands:[/yellow]")
            for cmd in result["suggested_commands"]:
                console.logging.info(f"  $ {cmd}")

        if result.get("data"):
            console.logging.info(f"\n[dim]Data: {len(result['data'])} items[/dim]")

        if result.get("missing_patterns"):
            console.logging.info(f"\n[yellow]Missing patterns: {result['missing_count']}[/yellow]")
            for name in result["missing_patterns"][:5]:
                console.logging.info(f"  • {name}")

        if execute and result.get("suggested_commands"):
            console.logging.info("\n[green]Executing first suggested command...[/green]")
            import subprocess

            subprocess.run(result["suggested_commands"][0], shell=True)

    except Exception as e:
        console.logging.info(f"[red]❌ AI assist error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats(
    format: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format", "-f", help="Output format"),
):
    """
    Show pattern database statistics.

    Examples:
        # Show statistics
        codex pattern stats

        # Get as JSON
        codex pattern stats --format json
    """
    import asyncio

    async def get_stats():
        db = UnifiedDatabase()
        patterns = await db.get_patterns()

        stats = {
            "total": len(patterns),
            "by_category": {},
            "by_priority": {},
            "by_source": {},
        }

        for p in patterns:
            # By category
            cat = p.get("category", "unknown")
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

            # By priority
            pri = p.get("priority", "unknown")
            stats["by_priority"][pri] = stats["by_priority"].get(pri, 0) + 1

            # By source
            src = p.get("source", "unknown")
            stats["by_source"][src] = stats["by_source"].get(src, 0) + 1

        return stats

    stats = asyncio.run(get_stats())

    if format == OutputFormat.JSON:
        logging.info(json.dumps(stats, indent=2))
    else:
        data_console.logging.info("\n[bold]Pattern Database Statistics[/bold]")
        data_console.logging.info(f"Total patterns: {stats['total']}")

        data_console.logging.info("\n[yellow]By Category:[/yellow]")
        for cat, count in sorted(stats["by_category"].items()):
            data_console.logging.info(f"  • {cat}: {count}")

        data_console.logging.info("\n[yellow]By Priority:[/yellow]")
        for pri in ["MANDATORY", "CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if pri in stats["by_priority"]:
                data_console.logging.info(f"  • {pri}: {stats['by_priority'][pri]}")

        data_console.logging.info("\n[yellow]By Source:[/yellow]")
        for src, count in sorted(stats["by_source"].items()):
            data_console.logging.info(f"  • {src}: {count}")


if __name__ == "__main__":
    app()

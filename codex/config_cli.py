#!/usr/bin/env python3
"""
Configuration discovery and management CLI for Codex.

Makes settings discoverable and easy to understand.
"""

import os
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.tree import Tree

from .config import get_default_config, load_config

app = typer.Typer(help="Configuration management commands")
console = Console()


@app.command()
def show(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all settings including defaults"),
):
    """Show current configuration and where each setting comes from."""

    # Load configurations from all sources
    default_config = get_default_config()
    loaded_config = load_config()

    # Determine source of each setting
    config_with_sources = _analyze_config_sources(default_config, loaded_config)

    if json_output:
        console.print_json(data=config_with_sources)
        return

    # Create a nice table
    table = Table(title="Current Configuration", border_style="blue")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_column("Source", style="yellow")

    for setting, info in config_with_sources.items():
        # Skip defaults unless verbose
        if not verbose and info["source"] == "defaults":
            continue

        value_str = _format_value(info["value"])
        table.add_row(setting, value_str, info["source"])

    console.print(table)

    # Show summary
    if not verbose:
        console.print(
            f"\n[dim]Showing {len([s for s, i in config_with_sources.items() if i['source'] != 'defaults'])} customized settings. Use --verbose to see all.[/dim]"
        )


@app.command()
def sources():
    """Show where configuration is loaded from."""

    sources_info = []

    # Check each potential source
    sources_info.append(("Default settings (built-in)", True, "always"))

    # User config
    user_config = Path.home() / ".config" / "codex" / "settings.toml"
    sources_info.append((f"User config ({user_config})", user_config.exists(), str(user_config)))

    # Project configs
    codex_toml = Path(".codex.toml")
    sources_info.append((f"Project config (.codex.toml)", codex_toml.exists(), str(codex_toml)))

    pyproject = Path("pyproject.toml")
    has_codex_section = False
    if pyproject.exists():
        import tomllib

        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
            has_codex_section = "tool" in data and "codex" in data["tool"]
    sources_info.append((f"Project config (pyproject.toml [tool.codex])", has_codex_section, str(pyproject)))

    # Environment variables
    env_vars = [k for k in os.environ if k.startswith("CODEX_")]
    sources_info.append((f"Environment variables", len(env_vars) > 0, ", ".join(env_vars) if env_vars else "none"))

    # Create tree view
    tree = Tree("📁 Configuration Sources (in order of precedence)")

    for i, (name, exists, details) in enumerate(sources_info, 1):
        symbol = "✅" if exists else "❌"
        if exists:
            tree.add(f"{i}. {symbol} {name}")
        else:
            tree.add(f"{i}. {symbol} {name} [dim](not found)[/dim]")

    console.print(tree)

    # Show active env vars if any
    if env_vars:
        console.print("\n[yellow]Active environment variables:[/yellow]")
        for var in env_vars:
            console.print(f"  • {var} = {os.environ[var]}")


@app.command()
def init():
    """Interactive configuration wizard."""

    console.print(Panel.fit("🧙 [bold cyan]Codex Configuration Wizard[/bold cyan]", border_style="cyan"))

    # Choose where to save
    console.print("\n[bold]Where should we save the configuration?[/bold]")
    choices = [
        ".codex.toml (project-specific)",
        "pyproject.toml (in [tool.codex] section)",
        "~/.config/codex/settings.toml (user-global)",
    ]

    for i, choice in enumerate(choices, 1):
        console.print(f"  {i}. {choice}")

    choice = Prompt.ask("Choice", choices=["1", "2", "3"], default="1")

    # Build configuration
    config = {}

    # Exclusions
    console.print("\n[bold]What should be excluded from scanning?[/bold]")

    exclude_options = [
        ("Python artifacts (*.pyc, __pycache__)", ["*.pyc", "__pycache__", "*.pyo"]),
        ("Virtual environments (.venv, venv)", [".venv", "venv", "env"]),
        ("Version control (.git)", [".git", ".svn", ".hg"]),
        ("Build artifacts (build/, dist/)", ["build/", "dist/", "*.egg-info"]),
        ("Backup directories (*_backup_*/)", ["*_backup_*/", "*.backup"]),
        ("Documentation (docs/, *.md)", ["docs/", "*.md", "README.*"]),
        ("Tests (tests/)", ["tests/"]),
        ("Cache directories", [".pytest_cache", ".mypy_cache", ".ruff_cache"]),
    ]

    exclude_patterns = []
    for name, patterns in exclude_options:
        if Confirm.ask(f"  Exclude {name}?", default=True if "Backup" not in name else True):
            exclude_patterns.extend(patterns)

    config["exclude"] = exclude_patterns

    # Tools
    if Confirm.ask("\n[bold]Enable external tools?[/bold]", default=True):
        config["run_tools"] = True
        config["tools"] = {
            "ruff": Confirm.ask("  • Run ruff (fast linter)?", default=True),
            "mypy": Confirm.ask("  • Run mypy (type checker)?", default=True),
            "typos": Confirm.ask("  • Run typos (spell checker)?", default=False),
        }
    else:
        config["run_tools"] = False

    # gitignore
    config["use_gitignore"] = Confirm.ask("\n[bold]Use .gitignore patterns?[/bold]", default=True)

    # Save configuration
    if choice == "1":
        _save_codex_toml(config)
    elif choice == "2":
        _save_pyproject_toml(config)
    else:
        _save_user_config(config)

    console.print("\n[green]✅ Configuration saved![/green]")
    console.print("Run [cyan]'codex config validate'[/cyan] to test your configuration")


@app.command()
def validate():
    """Validate current configuration."""

    console.print("[bold]Validating configuration...[/bold]\n")

    issues = []
    warnings = []

    # Load config
    try:
        config = load_config()
        console.print("✅ Configuration file is valid")
    except Exception as e:
        console.print(f"❌ Failed to load configuration: {e}")
        return

    # Check exclude patterns
    exclude_patterns = config.get("exclude", [])
    if exclude_patterns:
        console.print(f"✅ Found {len(exclude_patterns)} exclude patterns")

        # Analyze impact of exclude patterns
        for pattern in exclude_patterns:
            if "*_backup*" in pattern:
                # Check for backup directories
                backup_dirs = list(Path.cwd().glob(pattern))
                if backup_dirs:
                    file_count = sum(len(list(d.rglob("*"))) for d in backup_dirs if d.is_dir())
                    warnings.append(
                        f"Pattern '{pattern}' will exclude {len(backup_dirs)} directories ({file_count} files)"
                    )

    # Check tools availability
    if config.get("run_tools", True):
        tools = config.get("tools", {"ruff": True, "mypy": True, "typos": True})
        available_tools = []
        missing_tools = []

        for tool, enabled in tools.items():
            if enabled:
                # Check if tool is available
                import shutil

                if shutil.which(tool):
                    available_tools.append(tool)
                else:
                    missing_tools.append(tool)

        if available_tools:
            console.print(f"✅ External tools available: {', '.join(available_tools)}")
        if missing_tools:
            console.print(f"⚠️  Missing tools: {', '.join(missing_tools)}")
            warnings.append(f"Install missing tools with: uv pip install {' '.join(missing_tools)}")

    # Check for conflicts
    console.print("✅ No conflicting settings detected")

    # Show warnings
    if warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  ⚠️  {warning}")

    # Summary
    if not issues:
        console.print("\n[green]✅ Configuration is valid and ready to use![/green]")
    else:
        console.print("\n[red]❌ Configuration has issues that need fixing[/red]")


@app.command(name="list")
def list_settings():
    """List all available settings with descriptions."""

    settings_info = [
        ("exclude", "Patterns to exclude from scanning", "list[str]"),
        ("use_gitignore", "Also exclude .gitignore patterns", "bool"),
        ("use_codexignore", "Use .codexignore file if present", "bool"),
        ("max_file_size", "Skip files larger than this", "size"),
        ("run_tools", "Run external tools (ruff, mypy, typos)", "bool"),
        ("tools", "Which external tools to run", "dict"),
        ("pattern_priorities", "Pattern priorities to enforce", "list[str]"),
        ("pattern_exclusions", "Exclude patterns from specific paths", "dict"),
        ("auto_fix", "Automatically apply fixes", "bool"),
        ("output_format", "Output format (human|json|markdown)", "enum"),
        ("quiet", "Minimal output mode", "bool"),
        ("show_diff", "Show diffs for proposed fixes", "bool"),
    ]

    table = Table(title="Available Settings", border_style="cyan")
    table.add_column("Setting", style="bold cyan")
    table.add_column("Description", style="white")
    table.add_column("Type", style="yellow")

    for name, desc, type_str in settings_info:
        table.add_row(name, desc, type_str)

    console.print(table)
    console.print("\n[dim]Use 'codex config show' to see current values[/dim]")


@app.command()
def add_exclude(pattern: str):
    """Add an exclusion pattern to configuration."""

    # Load current config
    config = load_config()
    exclude = config.get("exclude", [])

    if pattern in exclude:
        console.print(f"[yellow]Pattern '{pattern}' already in exclusions[/yellow]")
        return

    # Add pattern
    exclude.append(pattern)
    config["exclude"] = exclude

    # Save back
    config_file = Path(".codex.toml")
    if config_file.exists():
        _save_codex_toml(config)
        console.print(f"[green]✅ Added '{pattern}' to exclusions in .codex.toml[/green]")
    else:
        # Create new config file
        _save_codex_toml(config)
        console.print(f"[green]✅ Created .codex.toml and added '{pattern}' to exclusions[/green]")

    # Show impact
    import glob

    matches = glob.glob(pattern, recursive=True)
    if matches:
        console.print(f"[dim]This will exclude {len(matches)} files/directories[/dim]")


def _analyze_config_sources(default_config: dict, loaded_config: dict) -> dict[str, dict[str, Any]]:
    """Analyze where each config value comes from."""

    result = {}

    # Check all keys from both configs
    all_keys = set(default_config.keys()) | set(loaded_config.keys())

    for key in all_keys:
        default_value = default_config.get(key)
        loaded_value = loaded_config.get(key)

        # Determine source
        if loaded_value != default_value:
            # Check if from env var
            env_var = f"CODEX_{key.upper()}"
            if env_var in os.environ:
                source = f"env:{env_var}"
            elif Path(".codex.toml").exists():
                source = ".codex.toml"
            elif Path("pyproject.toml").exists():
                source = "pyproject.toml"
            else:
                source = "unknown"
        else:
            source = "defaults"

        result[key] = {
            "value": loaded_value if loaded_value is not None else default_value,
            "source": source,
        }

    return result


def _format_value(value: Any) -> str:
    """Format a config value for display."""

    if isinstance(value, list):
        if len(value) <= 3:
            return str(value)
        else:
            return f"[{', '.join(map(str, value[:2]))}, ... +{len(value)-2} more]"
    elif isinstance(value, dict):
        return f"<dict with {len(value)} keys>"
    elif isinstance(value, bool):
        return "✓" if value else "✗"
    else:
        return str(value)


def _save_codex_toml(config: dict[str, Any]):
    """Save configuration to .codex.toml."""

    import toml

    # Add helpful comments
    config_with_comments = f"""# Codex Configuration File
# Generated by: codex config init
# Documentation: https://github.com/yourusername/codex

[codex]
"""

    # Convert config to TOML
    toml_str = toml.dumps({"codex": config})

    # Write file
    with open(".codex.toml", "w") as f:
        f.write(config_with_comments)
        f.write(toml_str[8:])  # Skip [codex] header since we added it

    console.print("[green]Created .codex.toml[/green]")


def _save_pyproject_toml(config: dict[str, Any]):
    """Save configuration to pyproject.toml."""

    import toml

    pyproject = Path("pyproject.toml")

    if pyproject.exists():
        # Load existing
        with open(pyproject) as f:
            data = toml.load(f)
    else:
        data = {}

    # Add codex config
    if "tool" not in data:
        data["tool"] = {}
    data["tool"]["codex"] = config

    # Write back
    with open(pyproject, "w") as f:
        toml.dump(data, f)

    console.print(f"[green]Updated {pyproject}[/green]")


def _save_user_config(config: dict[str, Any]):
    """Save configuration to user config directory."""

    import toml

    config_dir = Path.home() / ".config" / "codex"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "settings.toml"

    with open(config_file, "w") as f:
        toml.dump(config, f)

    console.print(f"[green]Created {config_file}[/green]")


if __name__ == "__main__":
    app()

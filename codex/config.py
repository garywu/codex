"""
Configuration management for Codex.

Loads settings from .codex.toml files.
"""

import tomllib
from pathlib import Path
from typing import Any


def load_config() -> tuple[dict[str, Any], Path]:
    """
    Load configuration from project-based files.

    Search order:
    1. .codex/config.toml (project-specific) - PRIMARY
    2. ~/.config/codex/config.toml (user-global)
    3. pyproject.toml [tool.codex] section (legacy)
    4. Default configuration + auto-init if needed
    """
    config = get_default_config()

    # Try project-specific .codex/config.toml (PRIMARY)
    project_config = Path(".codex/config.toml")
    if project_config.exists():
        config.update(load_toml_config(project_config))
        return config, project_config

    # Try user-global config
    user_config = Path.home() / ".config" / "codex" / "config.toml"
    if user_config.exists():
        config.update(load_toml_config(user_config))
        # Still return project path for potential auto-init
        return config, project_config

    # Try legacy pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
            if "tool" in data and "codex" in data["tool"]:
                config.update(data["tool"]["codex"])
                return config, project_config

    # No config found - return defaults with project path for auto-init
    return config, project_config


def load_toml_config(path: Path) -> dict[str, Any]:
    """Load configuration from TOML file."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    # Support both root-level and [codex] section
    if "codex" in data:
        result: dict[str, Any] = data["codex"]
        return result
    return data


def get_default_config() -> dict[str, Any]:
    """Get default configuration."""
    return {
        "patterns": ["all"],
        "exclude": [
            "*.pyc",
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            "populate_*pattern*.py",
            "*_rules.py",
            "validate_violations.py",
            "populate_ensemble*.py",
        ],
        "auto_fix": False,
        "enforce": ["mandatory", "critical", "high"],
        "farm_url": "http://localhost:8001",
        "quiet": False,
        "show_diff": False,
        "run_tools": True,
        "tools": {
            "ruff": True,
            "mypy": True,
            "typos": True,
        },
    }


def auto_init_project(project_config_path: Path) -> bool:
    """
    Auto-initialize project with .codex/config.toml.

    Returns True if initialization was performed.
    """
    if project_config_path.exists():
        return False

    # Create .codex directory
    codex_dir = project_config_path.parent
    codex_dir.mkdir(exist_ok=True)

    # Create default config
    default_config = get_default_config()

    # Write config file (need to install tomli-w if not available)
    try:
        import tomli_w

        with open(project_config_path, "wb") as f:
            tomli_w.dump({"codex": default_config}, f)
    except ImportError:
        # Fallback to manual TOML writing
        with open(project_config_path, "w") as f:
            f.write("[codex]\n")
            f.write('patterns = ["all"]\n')
            f.write("exclude = [\n")
            for pattern in default_config["exclude"]:
                f.write(f'  "{pattern}",\n')
            f.write("]\n")
            f.write("auto_fix = false\n")
            f.write('enforce = ["mandatory", "critical", "high"]\n')
            f.write('farm_url = "http://localhost:8001"\n')
            f.write("quiet = false\n")
            f.write("show_diff = false\n")
            f.write("run_tools = true\n")
            f.write("\n[codex.tools]\n")
            f.write("ruff = true\n")
            f.write("mypy = true\n")
            f.write("typos = true\n")

    # Create cache directory
    cache_dir = codex_dir / "cache"
    cache_dir.mkdir(exist_ok=True)

    return True


def should_auto_init() -> bool:
    """Check if project should be auto-initialized."""
    project_config = Path(".codex/config.toml")
    return not project_config.exists()

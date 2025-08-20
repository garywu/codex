"""
Configuration management for Codex.

Loads settings from .codex.toml files.
"""

import tomllib
from pathlib import Path
from typing import Any


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load configuration from file.

    Search order:
    1. Specified config_path
    2. .codex.toml in current directory
    3. pyproject.toml [tool.codex] section
    4. Default configuration
    """
    config = get_default_config()

    # Try specified path
    if config_path and config_path.exists():
        config.update(load_toml_config(config_path))
        return config

    # Try .codex.toml in current directory
    local_config = Path(".codex.toml")
    if local_config.exists():
        config.update(load_toml_config(local_config))
        return config

    # Try pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
            if "tool" in data and "codex" in data["tool"]:
                config.update(data["tool"]["codex"])

    return config


def load_toml_config(path: Path) -> dict[str, Any]:
    """Load configuration from TOML file."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    # Support both root-level and [codex] section
    if "codex" in data:
        return data["codex"]
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

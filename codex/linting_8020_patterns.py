"""
80/20 Linting Configuration Patterns.

This module provides intelligent linting configurations based on the 80/20 principle:
- Focus on the 20% of issues that matter (real bugs)
- Ignore the 80% that are style preferences

Based on analysis of successful projects like Django, FastAPI, and Pandas.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class LintingStrategy:
    """Represents an 80/20 linting strategy."""

    name: str
    description: str
    config: dict[str, Any]
    rationale: str


# Ruff 80/20 Configuration
RUFF_8020_CONFIG = {
    "line-length": 120,
    "target-version": "py311",
    "lint": {
        # Focus on real issues (20% that matter)
        "select": [
            "E",  # pycodestyle errors (syntax)
            "F",  # Pyflakes (undefined names, unused imports)
            "I",  # isort (import sorting)
            "UP",  # pyupgrade (Python version-specific)
            "B",  # flake8-bugbear (likely bugs)
            "C4",  # flake8-comprehensions (performance)
            "RUF",  # Ruff-specific rules
        ],
        # Extended for gradual adoption
        "extend-select": [
            "SIM",  # simplify (but configured intelligently)
            "ARG",  # unused arguments
            "TRY",  # exception handling
        ],
        # Ignore noise (80% that doesn't matter)
        "ignore": [
            # Legitimate patterns
            "E501",  # Line length (formatter handles)
            "PLC0415",  # Late imports (needed for circular deps)
            "B008",  # Function calls in defaults
            "ARG002",  # Unused args (callbacks/interfaces)
            # Style preferences
            "SIM102",  # Collapsible if
            "SIM105",  # contextlib.suppress
            "SIM108",  # Ternary operator
            # Complexity (refactor gradually)
            "PLR0912",  # Too many branches
            "PLR0913",  # Too many arguments
            "PLR0915",  # Too many statements
            "PLR0911",  # Too many returns
            # Design choices
            "LOG015",  # Root logger (OK in CLIs)
            "TRY003",  # Long exceptions
            "TRY300",  # Consider else
            # False positives
            "PLR2004",  # Magic values
            "PERF401",  # Manual list comp
            "RUF012",  # Mutable class attrs
        ],
        # Smart auto-fixing
        "fixable": [
            "F401",  # Remove unused imports
            "I",  # Sort imports
            "UP",  # Upgrade syntax
            "F541",  # f-string placeholders
            "B007",  # Unused loop vars
            "RUF100",  # Remove unused noqa
        ],
        # Context-aware per-file ignores
        "per-file-ignores": {
            # CLI/UI code - complex but not critical
            "**/cli.py": ["E402", "PLC0415", "PLR"],
            "**/cli_*.py": ["PLR"],
            # Tests - different patterns
            "tests/**/*.py": ["ARG", "PLR2004", "S101", "F841"],
            "test_*.py": ["ARG", "S101"],
            # Experimental/scripts - minimal rules
            "experiments/**/*.py": ["ALL"],
            "scripts/**/*.py": ["ALL"],
            # Special files
            "**/__init__.py": ["E402", "F401", "F403"],
            "**/migrations/*.py": ["E501"],
        },
    },
}


# MyPy 80/20 Configuration
MYPY_8020_CONFIG = {
    "python_version": "3.11",
    # Global: Start permissive
    "ignore_missing_imports": True,
    "allow_untyped_defs": True,
    "allow_untyped_calls": True,
    "warn_return_any": False,
    "warn_unused_ignores": False,
    "check_untyped_defs": False,
    "no_implicit_optional": True,
    "show_error_codes": True,
    # Overrides for different module types
    "overrides": [
        {
            # Critical paths - strict typing
            "module": [
                "*.models",
                "*.model",
                "*.database",
                "*.db",
                "*.config",
                "*.core",
                "*.api.schemas",
            ],
            "disallow_untyped_defs": True,
            "check_untyped_defs": True,
            "warn_return_any": True,
        },
        {
            # UI/CLI code - ignore most errors
            "module": [
                "*.cli",
                "*.ui",
                "*.views",
                "*.commands",
                "*.tools",
                "*.utils",
            ],
            "ignore_errors": True,
        },
        {
            # Tests - no type checking
            "module": "tests.*",
            "ignore_errors": True,
        },
        {
            # Third-party integrations
            "module": [
                "*.migrations.*",
                "*.vendor.*",
                "*.contrib.*",
            ],
            "ignore_errors": True,
        },
    ],
}


# Pre-commit 80/20 Configuration
PRECOMMIT_8020_CONFIG = {
    "repos": [
        {
            "repo": "https://github.com/astral-sh/ruff-pre-commit",
            "rev": "v0.8.0",
            "hooks": [
                {
                    "id": "ruff",
                    "args": ["--fix"],
                },
                {
                    "id": "ruff-format",
                },
            ],
        },
        {
            "repo": "https://github.com/pre-commit/mirrors-mypy",
            "rev": "v1.13.0",
            "hooks": [
                {
                    "id": "mypy",
                    "additional_dependencies": ["pydantic", "sqlmodel", "typer"],
                    "args": ["--config-file", "pyproject.toml"],
                },
            ],
        },
        {
            # Basic quality checks everyone should have
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v4.5.0",
            "hooks": [
                {"id": "trailing-whitespace"},
                {"id": "end-of-file-fixer"},
                {"id": "check-yaml"},
                {"id": "check-json"},
                {"id": "check-toml"},
                {"id": "check-merge-conflict"},
            ],
        },
    ],
}


# Linting strategies for different project types
LINTING_STRATEGIES = {
    "web-api": LintingStrategy(
        name="Web API Project",
        description="FastAPI/Django style - strict on API contracts, loose on internals",
        config={
            "ruff": {
                **RUFF_8020_CONFIG,
                "lint": {
                    **RUFF_8020_CONFIG["lint"],
                    "extend-select": ["S"],  # Add security checks
                },
            },
            "mypy": {
                **MYPY_8020_CONFIG,
                "overrides": [
                    *MYPY_8020_CONFIG["overrides"],
                    {
                        "module": "*.api.*",
                        "disallow_untyped_defs": True,  # Strict API typing
                    },
                ],
            },
        },
        rationale="APIs need type safety at boundaries but flexibility internally",
    ),
    "cli-tool": LintingStrategy(
        name="CLI Tool",
        description="Click/Typer style - focus on errors, ignore complexity",
        config={
            "ruff": {
                **RUFF_8020_CONFIG,
                "lint": {
                    **RUFF_8020_CONFIG["lint"],
                    "ignore": [
                        *RUFF_8020_CONFIG["lint"]["ignore"],
                        "PLR",  # Ignore all complexity metrics
                    ],
                },
            },
            "mypy": MYPY_8020_CONFIG,
        },
        rationale="CLIs have complex control flow but need error checking",
    ),
    "data-science": LintingStrategy(
        name="Data Science Project",
        description="Pandas/NumPy style - performance focus, loose typing",
        config={
            "ruff": {
                **RUFF_8020_CONFIG,
                "lint": {
                    **RUFF_8020_CONFIG["lint"],
                    "select": [
                        *RUFF_8020_CONFIG["lint"]["select"],
                        "NPY",  # NumPy-specific
                        "PD",  # Pandas-specific
                        "PERF",  # Performance focus
                    ],
                },
            },
            "mypy": {
                **MYPY_8020_CONFIG,
                "allow_untyped_defs": True,  # Very permissive
                "ignore_errors": True,  # Focus on notebooks/experiments
            },
        },
        rationale="Data science code is exploratory, focus on performance",
    ),
    "library": LintingStrategy(
        name="Python Library",
        description="Strict everywhere - users depend on correctness",
        config={
            "ruff": {
                **RUFF_8020_CONFIG,
                "lint": {
                    **RUFF_8020_CONFIG["lint"],
                    "select": ["ALL"],  # Everything
                    "ignore": [
                        "D",  # Docstrings (separate tool)
                        "ANN",  # Type annotations (MyPy handles)
                        "COM",  # Commas (formatter handles)
                    ],
                },
            },
            "mypy": {
                **MYPY_8020_CONFIG,
                "strict": True,  # Full strict mode
                "disallow_untyped_defs": True,
            },
        },
        rationale="Libraries need maximum correctness for users",
    ),
}


def get_project_type_from_files(project_path: Path) -> str:
    """Detect project type from files present."""

    # Check for various indicators
    has_fastapi = (
        (project_path / "main.py").exists() and "fastapi" in (project_path / "requirements.txt").read_text().lower()
        if (project_path / "requirements.txt").exists()
        else False
    )
    has_django = (project_path / "manage.py").exists()
    has_click = (
        "click" in (project_path / "setup.py").read_text().lower() if (project_path / "setup.py").exists() else False
    )
    has_notebooks = any(project_path.glob("*.ipynb"))
    has_setup_py = (project_path / "setup.py").exists()

    if has_fastapi or has_django:
        return "web-api"
    elif has_click or (project_path / "cli.py").exists():
        return "cli-tool"
    elif has_notebooks or any(project_path.glob("**/data")):
        return "data-science"
    elif has_setup_py:
        return "library"
    else:
        return "cli-tool"  # Default


def generate_pyproject_config(strategy: str = "cli-tool") -> str:
    """Generate pyproject.toml configuration for 80/20 linting."""
    import toml

    selected_strategy = LINTING_STRATEGIES.get(strategy, LINTING_STRATEGIES["cli-tool"])

    config = {
        "tool": {
            "ruff": selected_strategy.config["ruff"],
            "mypy": selected_strategy.config["mypy"],
        }
    }

    return toml.dumps(config)


def generate_precommit_config() -> str:
    """Generate .pre-commit-config.yaml for 80/20 linting."""
    import yaml

    return yaml.dump(PRECOMMIT_8020_CONFIG, default_flow_style=False)


# Pattern definitions for Codex scanner
LINTING_8020_PATTERNS = [
    {
        "name": "ruff-config-8020",
        "description": "Use 80/20 Ruff configuration",
        "pattern": "Missing intelligent Ruff configuration",
        "recommendation": "Apply 80/20 Ruff config focusing on real bugs not style",
        "category": "linting",
        "severity": "medium",
        "rationale": "Focus linting on the 20% that matters (bugs) not the 80% noise (style)",
    },
    {
        "name": "mypy-config-8020",
        "description": "Use 80/20 MyPy configuration",
        "pattern": "Missing intelligent MyPy configuration",
        "recommendation": "Type check critical paths strictly, UI/glue code loosely",
        "category": "type-checking",
        "severity": "medium",
        "rationale": "Type safety where it matters (data models) not everywhere (UI code)",
    },
    {
        "name": "precommit-config-8020",
        "description": "Use balanced pre-commit hooks",
        "pattern": "Overly strict or missing pre-commit hooks",
        "recommendation": "Use pre-commit for real issues not style nitpicks",
        "category": "ci-cd",
        "severity": "low",
        "rationale": "Pre-commit should catch bugs not enforce personal preferences",
    },
]

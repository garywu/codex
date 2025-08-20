"""
Project-specific configuration for Codex.

Each project can have its own .codex directory with:
- config.toml: Project-specific settings
- cache/: Local cache for patterns and scan results
- logs/: Project-specific logs
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import toml

from .settings import settings


@dataclass
class ProjectConfig:
    """Project-specific configuration."""

    # Project identification
    project_root: Path
    project_name: str

    # Scanning configuration
    scan_patterns: list[str] = field(default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts"])
    exclude_patterns: list[str] = field(default_factory=list)
    max_file_size: int = 10 * 1024 * 1024  # 10MB default

    # Pattern configuration
    enabled_categories: list[str] = field(default_factory=lambda: ["all"])
    min_priority: str = "MEDIUM"
    custom_patterns: list[dict[str, Any]] = field(default_factory=list)

    # Cache configuration
    cache_enabled: bool = True
    cache_ttl_hours: int = 24

    # Output configuration
    output_format: str = "human"  # human, json, markdown
    quiet_mode: bool = False

    # Integration configuration
    pre_commit_enabled: bool = True
    ci_mode: bool = False

    # Advanced configuration
    parallel_scanning: bool = True
    max_workers: int | None = None

    def __post_init__(self):
        """Post-initialization setup."""
        self.project_root = Path(self.project_root).resolve()
        if not self.project_name:
            self.project_name = self.project_root.name


class ProjectConfigManager:
    """Manage project-specific configuration."""

    CONFIG_DIR_NAME = ".codex"
    CONFIG_FILE_NAME = "config.toml"

    def __init__(self, project_root: Path | None = None):
        """Initialize with project root."""
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.config_dir = self.project_root / self.CONFIG_DIR_NAME
        self.config_file = self.config_dir / self.CONFIG_FILE_NAME
        self._config: ProjectConfig | None = None

    def ensure_config_dir(self):
        """Ensure .codex directory exists with proper structure."""
        # Create main config directory
        self.config_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.config_dir / "cache").mkdir(exist_ok=True)
        (self.config_dir / "logs").mkdir(exist_ok=True)
        (self.config_dir / "temp").mkdir(exist_ok=True)

        # Create .gitignore for .codex directory
        gitignore_file = self.config_dir / ".gitignore"
        if not gitignore_file.exists():
            gitignore_content = """# Codex cache and temporary files
cache/
logs/
temp/
*.tmp
*.log

# Keep the config file
!config.toml
!README.md
"""
            gitignore_file.write_text(gitignore_content)

        # Create README for documentation
        readme_file = self.config_dir / "README.md"
        if not readme_file.exists():
            readme_content = f"""# Codex Configuration for {self.project_root.name}

This directory contains project-specific Codex configuration and cache files.

## Files:
- `config.toml`: Project-specific Codex settings
- `cache/`: Cached pattern data and scan results
- `logs/`: Codex execution logs for this project
- `temp/`: Temporary files

## Configuration:
Edit `config.toml` to customize Codex behavior for this project.

Run `codex config --help` for configuration options.
"""
            readme_file.write_text(readme_content)

    def load_config(self) -> ProjectConfig:
        """Load project configuration."""
        if self._config is not None:
            return self._config

        # Default configuration
        config_data = {
            "project_root": self.project_root,
            "project_name": self.project_root.name,
        }

        # Load from file if exists
        if self.config_file.exists():
            try:
                file_config = toml.load(self.config_file)
                config_data.update(file_config)
            except (toml.TomlDecodeError, OSError) as e:
                logging.info(f"Warning: Could not load {self.config_file}: {e}")

        # Create ProjectConfig instance
        self._config = ProjectConfig(**config_data)
        return self._config

    def save_config(self, config: ProjectConfig | None = None):
        """Save project configuration."""
        if config is None:
            config = self._config

        if config is None:
            raise ValueError("No configuration to save")

        self.ensure_config_dir()

        # Convert to dictionary for TOML serialization
        config_dict = {
            "project_name": config.project_name,
            "scan_patterns": config.scan_patterns,
            "exclude_patterns": config.exclude_patterns,
            "max_file_size": config.max_file_size,
            "enabled_categories": config.enabled_categories,
            "min_priority": config.min_priority,
            "custom_patterns": config.custom_patterns,
            "cache_enabled": config.cache_enabled,
            "cache_ttl_hours": config.cache_ttl_hours,
            "output_format": config.output_format,
            "quiet_mode": config.quiet_mode,
            "pre_commit_enabled": config.pre_commit_enabled,
            "ci_mode": config.ci_mode,
            "parallel_scanning": config.parallel_scanning,
            "max_workers": config.max_workers,
        }

        try:
            with open(self.config_file, "w") as f:
                toml.dump(config_dict, f)
        except OSError as e:
            raise RuntimeError(f"Could not save configuration: {e}")

    def init_project(self, template: str = "python") -> ProjectConfig:
        """Initialize project with template configuration."""
        self.ensure_config_dir()

        # Template configurations
        templates = {
            "python": {
                "scan_patterns": ["**/*.py"],
                "exclude_patterns": [
                    "__pycache__",
                    "*.pyc",
                    ".venv",
                    "venv",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".coverage",
                ],
                "enabled_categories": ["naming", "error_handling", "security", "testing"],
                "min_priority": "HIGH",
            },
            "javascript": {
                "scan_patterns": ["**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx"],
                "exclude_patterns": ["node_modules", "dist", "build", "*.min.js", ".next", ".nuxt", "coverage"],
                "enabled_categories": ["naming", "security", "testing"],
                "min_priority": "HIGH",
            },
            "fullstack": {
                "scan_patterns": [
                    "**/*.py",
                    "**/*.js",
                    "**/*.ts",
                    "**/*.jsx",
                    "**/*.tsx",
                    "**/*.html",
                    "**/*.css",
                    "**/*.scss",
                    "**/*.yaml",
                    "**/*.yml",
                ],
                "exclude_patterns": [
                    "__pycache__",
                    "*.pyc",
                    ".venv",
                    "venv",
                    "node_modules",
                    "dist",
                    "build",
                    "*.min.js",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".coverage",
                ],
                "enabled_categories": ["all"],
                "min_priority": "MEDIUM",
            },
        }

        template_config = templates.get(template, templates["python"])

        config = ProjectConfig(project_root=self.project_root, project_name=self.project_root.name, **template_config)

        self.save_config(config)
        self._config = config

        return config

    def get_cache_file(self, name: str) -> Path:
        """Get path to a cache file."""
        cache_dir = self.config_dir / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / name

    def get_log_file(self, name: str) -> Path:
        """Get path to a log file."""
        logs_dir = self.config_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir / name

    def get_temp_file(self, name: str) -> Path:
        """Get path to a temporary file."""
        temp_dir = self.config_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir / name

    def clean_cache(self, older_than_hours: int | None = None):
        """Clean cache files."""
        if older_than_hours is None:
            config = self.load_config()
            older_than_hours = config.cache_ttl_hours

        cache_dir = self.config_dir / "cache"
        if not cache_dir.exists():
            return

        import time

        cutoff_time = time.time() - (older_than_hours * 3600)

        for cache_file in cache_dir.iterdir():
            if cache_file.is_file():
                try:
                    if cache_file.stat().st_mtime < cutoff_time:
                        cache_file.unlink()
                except OSError:
                    pass  # Ignore files we can't delete

    def get_project_summary(self) -> dict[str, Any]:
        """Get summary of project configuration."""
        config = self.load_config()

        return {
            "project_name": config.project_name,
            "project_root": str(config.project_root),
            "config_dir": str(self.config_dir),
            "config_exists": self.config_file.exists(),
            "cache_enabled": config.cache_enabled,
            "enabled_categories": config.enabled_categories,
            "min_priority": config.min_priority,
            "scan_patterns": config.scan_patterns,
            "exclude_patterns": config.exclude_patterns,
        }

    def update_setting(self, key: str, value: Any):
        """Update a single configuration setting."""
        config = self.load_config()

        if hasattr(config, key):
            setattr(config, key, value)
            self.save_config(config)
        else:
            raise ValueError(f"Unknown configuration key: {key}")

    def merge_with_global_settings(self) -> dict[str, Any]:
        """Merge project config with global settings."""
        config = self.load_config()

        # Start with global settings
        merged = {
            "database_path": settings.database_path,
            "config_dir": settings.config_dir,
            "data_dir": settings.data_dir,
            "cache_dir": settings.cache_dir,
            "enable_fts": settings.enable_fts,
            "run_external_tools": settings.run_external_tools,
            "ai_confidence_threshold": settings.ai_confidence_threshold,
        }

        # Override with project-specific settings
        merged.update(
            {
                "project_root": config.project_root,
                "project_name": config.project_name,
                "scan_patterns": config.scan_patterns,
                "exclude_patterns": config.exclude_patterns,
                "enabled_categories": config.enabled_categories,
                "min_priority": config.min_priority,
                "cache_enabled": config.cache_enabled,
                "output_format": config.output_format,
                "quiet_mode": config.quiet_mode,
                "parallel_scanning": config.parallel_scanning,
                "max_workers": config.max_workers,
            }
        )

        return merged

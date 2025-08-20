"""
Pydantic Settings for Codex - Single source of truth for configuration.
"""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_xdg_path(xdg_var: str, default_suffix: str) -> Path:
    """Get XDG directory path with fallback."""
    if xdg_path := os.environ.get(xdg_var):
        return Path(xdg_path) / "codex"
    return Path.home() / default_suffix / "codex"


class CodexSettings(BaseSettings):
    """Central configuration for Codex using Pydantic settings with XDG conventions."""
    
    model_config = SettingsConfigDict(
        env_prefix="CODEX_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # XDG Base Directory paths
    config_dir: Path = Field(
        default_factory=lambda: get_xdg_path("XDG_CONFIG_HOME", ".config"),
        description="Configuration directory (XDG_CONFIG_HOME/codex)"
    )
    
    data_dir: Path = Field(
        default_factory=lambda: get_xdg_path("XDG_DATA_HOME", ".local/share"),
        description="Data directory (XDG_DATA_HOME/codex)"
    )
    
    cache_dir: Path = Field(
        default_factory=lambda: get_xdg_path("XDG_CACHE_HOME", ".cache"),
        description="Cache directory (XDG_CACHE_HOME/codex)"
    )
    
    state_dir: Path = Field(
        default_factory=lambda: get_xdg_path("XDG_STATE_HOME", ".local/state"),
        description="State directory (XDG_STATE_HOME/codex)"
    )
    
    # Database settings - SINGLE SQLite database in XDG_DATA_HOME
    database_path: Path = Field(
        default_factory=lambda: get_xdg_path("XDG_DATA_HOME", ".local/share") / "codex.db",
        description="Path to the single SQLite database"
    )
    
    # Enable FTS5 for full-text search
    enable_fts: bool = Field(
        default=True,
        description="Enable SQLite FTS5 for AI queries"
    )
    
    # Scanning settings
    scan_exclude_patterns: list[str] = Field(
        default=[
            "__pycache__", ".git", ".venv", "venv", 
            ".pytest_cache", ".mypy_cache", "node_modules",
            "*.pyc", "*.pyo", "*.bak", "*~"
        ],
        description="Patterns to exclude from scanning"
    )
    
    # Tool settings
    run_external_tools: bool = Field(
        default=True,
        description="Run external tools (ruff, mypy, typos)"
    )
    
    tools_timeout: int = Field(
        default=120,
        description="Timeout for external tools in seconds"
    )
    
    # AI settings
    ai_context_enabled: bool = Field(
        default=True,
        description="Enable AI context generation"
    )
    
    ai_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for AI suggestions"
    )
    
    # Pattern settings
    pattern_priorities: list[str] = Field(
        default=["MANDATORY", "CRITICAL", "HIGH"],
        description="Pattern priorities to enforce"
    )
    
    auto_fix: bool = Field(
        default=False,
        description="Automatically apply fixes"
    )
    
    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    quiet_mode: bool = Field(
        default=False,
        description="Minimal output mode"
    )
    
    # Farm SDK settings (optional)
    farm_url: str | None = Field(
        default=None,
        description="Farm SDK URL for AI agents"
    )
    
    farm_enabled: bool = Field(
        default=False,
        description="Enable Farm SDK integration"
    )
    
    # Repository settings
    repository_path: Path = Field(
        default=Path.cwd(),
        description="Current repository path"
    )
    
    # Output settings
    output_format: str = Field(
        default="human",
        pattern="^(human|json|ai|markdown)$",
        description="Output format for results"
    )
    
    # Cache settings
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching for performance"
    )
    
    cache_ttl: int = Field(
        default=900,  # 15 minutes
        description="Cache TTL in seconds"
    )
    
    def ensure_directories(self) -> None:
        """Ensure all XDG directories exist."""
        for dir_path in [self.config_dir, self.data_dir, self.cache_dir, self.state_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        # Also ensure database directory
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_config_file(self, filename: str) -> Path:
        """Get path to a config file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        return self.config_dir / filename
    
    def get_cache_file(self, filename: str) -> Path:
        """Get path to a cache file."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / filename
    
    def get_data_file(self, filename: str) -> Path:
        """Get path to a data file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / filename
    
    def get_state_file(self, filename: str) -> Path:
        """Get path to a state file."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir / filename
    
    def get_database_url(self) -> str:
        """Get SQLite database URL."""
        self.ensure_directories()
        return f"sqlite:///{self.database_path}"
    
    def get_async_database_url(self) -> str:
        """Get async SQLite database URL."""
        self.ensure_directories()
        return f"sqlite+aiosqlite:///{self.database_path}"


# Global settings instance
settings = CodexSettings()
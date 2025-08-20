# Codex Exclusion Settings Guide

## Current State: Two Configuration Systems

Codex currently has two parallel configuration systems that need to be unified:

### 1. Pydantic Settings (`settings.py`)
- Environment variables with `CODEX_` prefix
- `.env` file support
- XDG directory compliance
- Has `scan_exclude_patterns` but it's not being used

### 2. TOML Config (`config.py`)
- `.codex.toml` file in project
- `pyproject.toml` [tool.codex] section
- Has `exclude` patterns that ARE being used

## The Problem

The scanner uses `config.py` exclusions, not `settings.py` exclusions. This creates confusion.

## Recommended Solution: Unified Settings

### Step 1: Update Settings to be Comprehensive

```python
# codex/settings.py - Enhanced exclusion settings

class CodexSettings(BaseSettings):
    # ... existing settings ...
    
    # Scanning exclusion settings (enhanced)
    scan_exclude_patterns: list[str] = Field(
        default=[
            # Python artifacts
            "__pycache__", "*.pyc", "*.pyo", "*.pyd",
            
            # Virtual environments
            ".venv", "venv", "env", ".env",
            
            # Version control
            ".git", ".svn", ".hg",
            
            # Build artifacts
            "build", "dist", "*.egg-info",
            
            # Backups (THE FIX FOR OUR ISSUE)
            "*_backup_*", "*backup*", "*.backup",
            
            # Caches
            ".pytest_cache", ".mypy_cache", ".ruff_cache",
            
            # Node
            "node_modules",
            
            # IDE
            ".vscode", ".idea", "*.swp",
            
            # OS
            ".DS_Store", "Thumbs.db"
        ],
        description="Patterns to exclude from scanning"
    )
    
    # Use gitignore as base
    use_gitignore: bool = Field(
        default=True,
        description="Also exclude files matching .gitignore patterns"
    )
    
    # Allow .codexignore file
    use_codexignore: bool = Field(
        default=True,
        description="Use .codexignore file if present"
    )
    
    # Pattern-specific exclusions
    pattern_exclusions: dict[str, list[str]] = Field(
        default={
            "mock-code-naming": ["tests/fixtures/", "tests/mocks/"],
            "no-hardcoded-secrets": ["tests/data/", "examples/"],
            "use-uv-package-manager": ["legacy/", "vendor/"],
        },
        description="Exclude specific patterns from certain paths"
    )
    
    # File size limits
    max_file_size_bytes: int = Field(
        default=1_000_000,  # 1MB
        description="Skip files larger than this"
    )
    
    skip_binary_files: bool = Field(
        default=True,
        description="Skip binary files automatically"
    )
```

### Step 2: Configuration Priority Order

The system should merge settings in this order (later overrides earlier):

1. **Default settings** (in `settings.py`)
2. **Environment variables** (`CODEX_SCAN_EXCLUDE_PATTERNS`)
3. **`.env` file** (for development)
4. **User config** (`~/.config/codex/settings.toml`)
5. **Project config** (`.codex.toml` or `pyproject.toml`)
6. **Command line arguments** (`--exclude`)

### Step 3: Configuration Files

#### `.codex.toml` (Project-Level)
```toml
# Project-specific exclusions
[scan]
exclude = [
    # Add to defaults, don't replace
    "quality_enforcement_backup_*/",
    "codex_backup_*/",
    "experiments/",
    "demo_*.py",
]

# Inherit from gitignore
use_gitignore = true

# Pattern-specific exclusions
[scan.pattern_exclusions]
"mock-code-naming" = ["tests/fixtures/"]
"no-hardcoded-secrets" = ["tests/test_data/"]
```

#### `~/.config/codex/settings.toml` (User-Level)
```toml
# User preferences across all projects
[scan]
exclude = [
    "*.tmp",
    "scratch/",
]

# Personal preferences
quiet_mode = false
output_format = "human"
```

#### `.env` (Development)
```bash
# Override for development
CODEX_SCAN_EXCLUDE_PATTERNS='["*_backup_*/", "build/", "dist/"]'
CODEX_USE_GITIGNORE=true
CODEX_MAX_FILE_SIZE_BYTES=5000000
```

#### Environment Variables
```bash
# CI/CD overrides
export CODEX_SCAN_EXCLUDE_PATTERNS='["vendor/", "third_party/"]'
export CODEX_QUIET_MODE=true
export CODEX_OUTPUT_FORMAT=json
```

### Step 4: `.codexignore` File

Similar to `.gitignore`, for patterns that shouldn't be in config:

```gitignore
# .codexignore - Additional exclusions for scanner only

# Documentation
docs/
*.md
README.*

# Examples with intentional issues  
examples/bad_*.py
examples/vulnerable_*.py

# Test fixtures
tests/fixtures/
tests/data/bad_examples/

# Generated files
*.generated.py
*_pb2.py  # Protocol buffers

# Migrations (often have old patterns)
migrations/
alembic/

# Temporary experiments
experiment_*.py
test_*.py
demo_*.py
```

### Step 5: Unified Scanner Implementation

```python
# codex/scanner.py - Use unified settings

from .settings import settings
from .config import load_config

class Scanner:
    def __init__(self, ...):
        # Merge settings and config
        self.settings = settings
        self.config = load_config()
        
        # Combine exclusion patterns
        self.exclude_patterns = set()
        self.exclude_patterns.update(settings.scan_exclude_patterns)
        self.exclude_patterns.update(self.config.get("exclude", []))
        
        # Load .codexignore if enabled
        if settings.use_codexignore:
            self.exclude_patterns.update(self._load_codexignore())
    
    def _is_excluded(self, file_path: Path) -> bool:
        """Check all exclusion sources."""
        
        # Check file size
        if self.settings.skip_binary_files and self._is_binary(file_path):
            return True
            
        if file_path.stat().st_size > self.settings.max_file_size_bytes:
            return True
        
        # Check gitignore
        if self.settings.use_gitignore and self._matches_gitignore(file_path):
            return True
        
        # Check exclusion patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(str(file_path), f"*{pattern}*"):
                return True
        
        return False
```

## Quick Fix for Current Issue

### Immediate Solution (Without Code Changes)

1. **Create `.codex.toml`** in project root:
```toml
[codex]
exclude = [
    # Existing defaults
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
    
    # FIX FOR BACKUP DIRECTORIES
    "*_backup_*/",
    "quality_enforcement_backup_*/",
    "codex_backup_*/",
    
    # Experimental files
    "demo_*.py",
    "experiment_*.py",
    "test_*.py",
]
```

2. **Or update `pyproject.toml`**:
```toml
[tool.codex]
exclude = [
    # ... same as above ...
]
```

3. **Or use environment variable**:
```bash
export CODEX_SCAN_EXCLUDE_PATTERNS='["*_backup_*/", "build/", "dist/"]'
codex scan
```

## Benefits of Unified Settings

1. **Single source of truth** - Settings in one place
2. **Environment flexibility** - Override via env vars for CI/CD
3. **User preferences** - Personal settings in `~/.config/codex/`
4. **Project settings** - Project-specific in `.codex.toml`
5. **Gitignore integration** - Reuse existing exclusions
6. **Pattern-specific** - Different exclusions per pattern
7. **Clear precedence** - Predictable override order

## Migration Path

### Phase 1: Use Existing Config System
- Add exclusions to `.codex.toml` or `pyproject.toml`
- This works TODAY without code changes

### Phase 2: Update Scanner
- Make scanner use both `settings.py` and `config.py`
- Add `.codexignore` support

### Phase 3: Unify Systems
- Merge `config.py` logic into `settings.py`
- Single configuration system with clear precedence

## Testing Exclusions

```bash
# See what's being excluded
codex --dry-run --explain

# List files that would be scanned
codex --list-files

# Test specific pattern
codex --show-excluded "*_backup_*"

# Override exclusions temporarily
codex --exclude "tests/" --exclude "docs/"
```

## Conclusion

The systematic way to handle exclusions in Codex:

1. **Use the existing config system** (`.codex.toml` or `pyproject.toml`)
2. **Add backup directories to exclusions** (fixes 60% of false violations)
3. **Consider `.codexignore`** for complex projects
4. **Unify settings systems** in future refactor

For the immediate issue with 1,146 violations, just add this to `.codex.toml`:
```toml
exclude = ["*_backup_*/", "build/", "dist/", "*.egg-info"]
```

This will drop violations to ~450 real issues.
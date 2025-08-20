# Systematic File Exclusion Strategy for Codex Scanner

## Overview

Codex needs a multi-layered exclusion system because `.gitignore` alone isn't sufficient. Git and code scanning have different needs:
- **Git**: Excludes files from version control
- **Scanner**: Excludes files from quality checking

## The Three-Layer Exclusion System

### 1. `.gitignore` (Version Control)
**Purpose**: Files that shouldn't be in the repository
```gitignore
# Virtual environments
.venv/
venv/
env/

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.egg-info/
build/
dist/

# IDE
.vscode/
.idea/
*.swp

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
```

### 2. `.codexignore` (Scanner-Specific)
**Purpose**: Additional files to exclude from scanning that ARE in version control
```gitignore
# Documentation that doesn't need scanning
docs/
*.md
README.rst
CHANGELOG

# Example/demo files that intentionally have issues
examples/
demo_*.py
bad_*.py

# Generated files that are committed
*.generated.py
*_pb2.py  # Protocol buffers

# Vendor/third-party code
vendor/
third_party/

# Test fixtures with intentional violations
tests/fixtures/
tests/data/bad_examples/

# Migration scripts (often have old patterns)
migrations/
alembic/

# Backup directories (shouldn't be in git but sometimes are)
*_backup_*/
*.backup/
backup/

# Experimental code
experiments/
scratch/
playground/
```

### 3. Configuration File (`.codex.toml` or `pyproject.toml`)
**Purpose**: Project-wide settings and overrides

#### Option A: `.codex.toml` (Dedicated Config)
```toml
[scan]
# Inherit from .gitignore
use_gitignore = true

# Additional patterns to exclude
exclude = [
    "*_backup_*/",
    "build/",
    "experiments/",
    "demo_*.py",
]

# Override gitignore for specific patterns
include_despite_gitignore = [
    "dist/*.whl",  # Want to scan built wheels
]

# File size limits
max_file_size = "1MB"
skip_binary = true

[patterns]
# Disable specific patterns for certain paths
disable = [
    { pattern = "use-uv-package-manager", paths = ["legacy/", "vendor/"] },
    { pattern = "mock-code-naming", paths = ["tests/fixtures/"] },
]
```

#### Option B: `pyproject.toml` (Integrated Config)
```toml
[tool.codex]
use_gitignore = true
use_codexignore = true  # Look for .codexignore file

exclude = [
    "*_backup_*/",
    "build/",
    "experiments/",
]

# Pattern-specific exclusions
[[tool.codex.pattern_exclude]]
pattern = "use-uv-package-manager"
paths = ["legacy/", "vendor/"]

[[tool.codex.pattern_exclude]]
pattern = "no-hardcoded-secrets"
paths = ["tests/fixtures/", "examples/"]
```

## Implementation Strategy

### 1. File Discovery Order
```python
def should_scan_file(file_path: Path) -> bool:
    """
    Systematic exclusion check order:
    1. Binary file check
    2. File size check
    3. .gitignore patterns (if use_gitignore=true)
    4. .codexignore patterns
    5. Config exclude patterns
    6. Override includes
    """

    # 1. Skip binary files
    if is_binary(file_path):
        return False

    # 2. Skip large files
    if file_path.stat().st_size > max_file_size:
        return False

    # 3. Check .gitignore
    if use_gitignore and matches_gitignore(file_path):
        if not in_override_includes(file_path):
            return False

    # 4. Check .codexignore
    if matches_codexignore(file_path):
        return False

    # 5. Check config excludes
    if matches_config_excludes(file_path):
        return False

    return True
```

### 2. Pattern-Specific Exclusions
```python
def should_check_pattern(pattern_name: str, file_path: Path) -> bool:
    """
    Some patterns shouldn't apply to certain files/directories
    """
    pattern_excludes = config.get_pattern_excludes(pattern_name)

    for exclude_path in pattern_excludes:
        if file_path.match(exclude_path):
            return False

    return True
```

## Best Practices

### 1. **Use `.gitignore` as the Base**
- Most files excluded from git shouldn't be scanned
- Set `use_gitignore = true` by default

### 2. **Add `.codexignore` for Scanner-Specific Exclusions**
- Documentation files
- Example code with intentional issues
- Test fixtures
- Generated code

### 3. **Use Config for Dynamic Exclusions**
- Temporary exclusions during refactoring
- Pattern-specific exclusions
- Project-specific rules

### 4. **Be Explicit About Overrides**
- If you need to scan something in `.gitignore`, explicitly include it
- Document why certain files are excluded

## Common Exclusion Patterns

### Always Exclude
```
# Build artifacts
build/
dist/
*.egg-info/
target/  # Rust/Java

# Caches
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Virtual environments
.venv/
venv/
env/
.env/

# Version control
.git/
.svn/
.hg/
```

### Usually Exclude
```
# Documentation
docs/
*.md
*.rst
*.txt

# Config files
*.ini
*.cfg
*.conf
*.yaml
*.yml
*.toml
*.json

# Test data
fixtures/
test_data/
mock_data/
```

### Context-Dependent
```
# Might contain real code or just examples
examples/
demo/
samples/
tutorials/

# Might be production or experimental
scripts/
tools/
utils/
```

## CLI Integration

### Commands for Managing Exclusions
```bash
# Show what would be scanned
codex --dry-run

# List all excluded files with reasons
codex --show-excluded

# List files matching specific exclusion pattern
codex --show-excluded-by "*_backup_*/"

# Scan including normally excluded files
codex --no-exclusions

# Scan with custom exclusion file
codex --exclude-from .codexignore.custom

# Add exclusion interactively
codex exclude add "pattern"

# Test if a file would be excluded
codex exclude test "path/to/file.py"
```

### Debug Exclusions
```bash
# Verbose mode shows exclusion decisions
codex --explain

# Output:
# ❌ FILE_EXCLUDED: quality_enforcement_backup_20250819_194047/cli.py
#   Reason: Matched exclusion pattern
#   Pattern: *_backup_*/
#   Source: .codex.toml

# ✅ FILE_INCLUDED: codex/scanner.py
#   Reason: Passed all filters
#   Checked: .gitignore (pass), .codexignore (pass), config (pass)
```

## Migration Path

### Step 1: Audit Current State
```bash
# See what's currently being scanned
codex --dry-run --list-files > current-files.txt

# See what's excluded
codex --dry-run --show-excluded > excluded-files.txt
```

### Step 2: Create `.codexignore`
```bash
# Start with common patterns
cat > .codexignore << 'EOF'
# Backup directories
*_backup_*/
*backup*/
*.backup/

# Build artifacts not in .gitignore
build/

# Experimental code
experiments/
scratch/
EOF
```

### Step 3: Update Configuration
```toml
# .codex.toml
[scan]
use_gitignore = true
use_codexignore = true

# Additional runtime exclusions
exclude = [
    "demo_*.py",
    "test_*.py",
]
```

### Step 4: Verify
```bash
# Check reduction in files scanned
codex --dry-run

# Before: Scanning 237 files
# After:  Scanning 95 files
```

## Benefits of This System

1. **Layered Control**: Different exclusion reasons at different levels
2. **Version Controlled**: `.codexignore` can be committed and shared
3. **Override Capability**: Can include specific files despite exclusions
4. **Pattern-Specific**: Different patterns can have different exclusions
5. **Debuggable**: Clear reporting of why files are excluded
6. **Performance**: Fewer files to scan = faster scanning
7. **Accuracy**: Excludes intentionally bad code (examples, fixtures)

## Example: Codex Project Itself

```toml
# .codex.toml for the Codex project
[scan]
use_gitignore = true

exclude = [
    # Backup directories (major issue we discovered)
    "*_backup_*/",
    "quality_enforcement_backup_*/",
    "codex_backup_*/",

    # Build artifacts
    "build/",
    "dist/",

    # Experimental files in root
    "demo_*.py",
    "test_*.py",
    "experiment_*.py",
    "extract_*.py",
    "enhanced_*.py",
]

# Pattern-specific exclusions
[[tool.codex.pattern_exclude]]
pattern = "mock-code-naming"
paths = ["tests/fixtures/"]

[[tool.codex.pattern_exclude]]
pattern = "no-hardcoded-secrets"
paths = ["tests/test_data/", "examples/"]
```

This would reduce Codex's violations from 1,146 to ~450, making the real issues visible and actionable.

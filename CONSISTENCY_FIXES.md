# Consistency Fixes Required

## Root Cause Analysis
The fundamental problem is that we have THREE different database implementations, each with its own hardcoded path instead of using the centralized Pydantic settings. This violates the DRY principle and creates confusion.

## Current State Problems

### 1. Multiple Database Implementations
- **database.py**: SQLModel, hardcoded to `data/patterns.db`
- **fts_database.py**: SQLite FTS5, hardcoded to `patterns_fts.db`  
- **unified_database.py**: Unified SQLite, CORRECTLY uses settings!

### 2. Inconsistent Imports
- Some files import multiple database modules
- No clear guidance on which to use
- Mixed usage even within same file (cli.py)

### 3. Path Inconsistency
- database.py: `./data/patterns.db` (project relative)
- fts_database.py: `./patterns_fts.db` (cwd relative)
- unified_database.py: `~/.local/share/codex/codex.db` (XDG compliant)

## Solution

### Step 1: Use ONLY unified_database.py
- It's the only one using Pydantic settings correctly
- Has FTS5 support built-in
- Uses proper XDG paths

### Step 2: Delete Other Database Modules
- Remove database.py
- Remove fts_database.py
- Update ALL imports to use unified_database

### Step 3: Ensure Settings Usage
Every module that needs configuration MUST:
```python
from .settings import settings

# Then use settings.database_path, settings.config_dir, etc.
```

### Step 4: Create Migration Script
- Move data from old databases to new unified one
- Delete old database files
- Ensure no data loss

## Why This Keeps Happening

1. **No Architectural Documentation**: Developers don't know which module to use
2. **Multiple Working Solutions**: Each database "works" so there's no immediate error
3. **Copy-Paste Development**: New features copy from different existing files
4. **No Code Review Process**: Multiple implementations get merged without review
5. **Missing Integration Tests**: Tests don't catch when different modules use different databases

## Prevention

1. **Single Source of Truth**: ONE database module, ONE settings module
2. **Documentation**: Clear README on which modules to use
3. **Linting Rules**: Custom rule to prevent multiple database imports
4. **Settings Validation**: Fail fast if settings aren't used
5. **Import Guards**: Prevent importing deprecated modules
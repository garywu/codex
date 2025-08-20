# Database Consistency Audit

## Current State (INCONSISTENT)

### Database Modules (3 different modules!)
1. **database.py** - SQLModel-based, uses patterns.db
2. **fts_database.py** - SQLite FTS5, uses patterns_fts.db
3. **unified_database.py** - New unified approach, uses codex.db in ~/.local/share

### Database Files (3 different files!)
1. `/Users/admin/Work/codex/codex/data/patterns.db` (12KB) - Old SQLModel database
2. `/Users/admin/Work/codex/codex/data/patterns_fts.db` (41KB) - FTS database
3. `/Users/admin/.local/share/codex/codex.db` (123KB) - New unified database (ACTIVE)

### Module Usage Analysis

#### Files using database.py (OLD - NEEDS MIGRATION)
- cli.py (mixed - also uses unified_database!)
- client.py
- pattern_importer.py

#### Files using fts_database.py (OLD - NEEDS MIGRATION)
- mcp_server.py
- ai_query.py
- pattern_extractor.py
- sqlite_scanner.py

#### Files using unified_database.py (CORRECT)
- scanner.py
- pattern_cli.py
- cli.py (partially)

## Issues Found

1. **Multiple Database Files**: 3 separate database files with potentially different data
2. **Mixed Imports**: cli.py imports BOTH database.py AND unified_database.py
3. **Inconsistent Data Location**: Some in project folder, some in XDG location
4. **No Backup System**: Patterns only in database, not in source control
5. **MCP Server Using Wrong DB**: Still using old FTS database

## Recommended Actions

1. Migrate ALL modules to use unified_database.py
2. Remove database.py and fts_database.py
3. Delete old database files after migration
4. Create pattern backup system in source code
5. Ensure all patterns are versioned in git

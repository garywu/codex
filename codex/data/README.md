# Codex Data Directory

This directory contains the pattern database and related data files.

## Files

- `patterns.db` - SQLite database containing all code patterns and best practices
  - Created automatically on first run
  - Populated from project-init.json or other pattern sources
  - Tracks pattern usage and success rates

## Note

The `patterns.db` file is gitignored by default since it's generated from source patterns.
To share patterns across a team, commit the pattern source files (e.g., project-init.json)
rather than the database itself.
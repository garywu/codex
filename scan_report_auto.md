# Executive Summary Report
Generated: 2025-08-20 08:20:25

## Current Status
- **Latest Scan**: 2025-08-20T08:17:01.157373
- **Total Violations**: 307
- **Files Scanned**: 79
- **Fix Rate**: 0.0% (0 fixed / 921 total)

## Trend
- **Current**: 307 violations
- **Previous**: 307 violations
- **Change**: +0 (→)

## Top Issues
1. `mock-code-naming`: 46 occurrences
1. `minimum-test`: 42 occurrences
1. `no-cors-wildcard`: 36 occurrences


---

# Detailed Scan Report
Generated: 2025-08-20 08:20:25
Database: /Users/admin/Work/codex/.codex/scans.db

## Module Health Scores

| Module | Files | Violations | Pattern Diversity | Health Score |
|--------|-------|------------|-------------------|-------------|
| experiments | 7 | 20 | 8 | 75/100 |
| root | 7 | 17 | 10 | 75/100 |
| scripts | 5 | 15 | 8 | 75/100 |
| tests | 10 | 43 | 11 | 50/100 |
| codex | 50 | 212 | 18 | 10/100 |

## Hotspot Files

| File | Total Violations | Scan Appearances | Unique Patterns |
|------|-----------------|------------------|----------------|
| codex/interactive_fixer.py | 24 | 3 | 8 |
| codex/scan_rules.py | 24 | 3 | 8 |
| codex/ai_query.py | 21 | 3 | 7 |
| codex/cli.py | 21 | 3 | 7 |
| codex/scanner.py | 21 | 3 | 7 |
| codex/sqlite_scanner.py | 21 | 3 | 7 |
| tests/test_fts_direct.py | 21 | 3 | 7 |
| tests/test_safe_fixing.py | 21 | 3 | 7 |
| codex/fix_orchestrator.py | 18 | 3 | 6 |
| codex/mcp_server.py | 18 | 3 | 6 |

## Pattern Analysis

| Pattern | Total | Scans | Files |
|---------|-------|-------|-------|
| mock-code-naming | 138 | 3 | 46 |
| minimum-test | 126 | 3 | 42 |
| no-cors-wildcard | 108 | 3 | 36 |
| structured-logging | 90 | 3 | 30 |
| no-cors | 72 | 3 | 24 |
| use-pydantic | 45 | 3 | 15 |
| use-db-context | 42 | 3 | 14 |
| mock-code | 39 | 3 | 13 |
| sanitize-production | 39 | 3 | 13 |
| structured | 39 | 3 | 13 |

## Weekly Activity

| Date | Scans | Avg Violations | Min | Max |
|------|-------|----------------|-----|-----|
| 2025-08-20 | 3 | 307 | 307 | 307 |

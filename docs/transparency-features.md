# Codex Scanner Transparency Features

## Overview

The Codex scanner now provides complete transparency into its decision-making process, allowing users to understand exactly what files are being scanned, why certain files are excluded, and how violations are detected.

## Key Features

### 1. Pre-Scan Discovery (`--dry-run`)

Shows what would be scanned without actually performing the scan:

```bash
codex --dry-run

# Output:
# 🔍 Dry-run Discovery for /Users/admin/Work/codex:
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
# ┃ Metric                        ┃ Value ┃
# ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━┫
# ┃ Total Files Found             ┃  2926 ┃
# ┃ Files to Scan                 ┃    99 ┃
# ┃ Files Excluded                ┃  2827 ┃
# ┃ Exclusion Rate                ┃ 96.6% ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━┛
# Would scan 99 files
# Would exclude 2827 files
```

### 2. List Files Mode (`--list-files`)

Lists all files that would be scanned:

```bash
codex --list-files

# Output:
# 📄 Files that would be scanned in /Users/admin/Work/codex:
#   /Users/admin/Work/codex/codex/__init__.py
#   /Users/admin/Work/codex/codex/ai_query.py
#   /Users/admin/Work/codex/codex/analyzer.py
#   ...
```

### 3. Explain Mode (`--explain`)

Provides verbose, real-time explanations of every decision:

```bash
codex --explain

# Output with color-coded decisions:
# [14:23:45.123] ✅ FILE_INCLUDED
#   Context: Processing file: scanner.py
#   Reason: File successfully loaded (15234 bytes)
#   File: /Users/admin/Work/codex/codex/scanner.py
#   Time: 2.34ms
#
# [14:23:45.156] 🔍 PATTERN_MATCHED
#   Context: Checking pattern 'no-cors-wildcard' against scanner.py
#   Reason: Violation detected
#   Pattern: no-cors-wildcard
#   Confidence: 90.0%
#   Time: 5.67ms
```

### 4. JSON Output (`--json`)

Machine-readable output for CI/CD integration:

```bash
codex --json > results.json

# Output format:
{
  "scan_summary": {
    "total_violations": 123,
    "files_scanned": 45,
    "exit_code": 1,
    "scan_duration_ms": 2500.0
  },
  "violations": [
    {
      "file_path": "src/main.py",
      "line_number": 42,
      "pattern_name": "no-cors-wildcard",
      "priority": "CRITICAL",
      "matched_code": "origins = ['*']",
      "suggestion": "Replace with specific origins",
      "confidence": 0.9
    }
  ]
}
```

### 5. Export Detailed Reports

#### Violation Report (`--export-json`)

```bash
codex --export-json violations.json

# Exports detailed violation report with statistics
```

#### Audit Trail (`--export-audit`)

```bash
codex --export-audit audit.json

# Exports complete decision history for debugging
```

## Decision Types Tracked

The scanner tracks and can explain the following decision types:

| Decision Type | Symbol | Description |
|--------------|--------|-------------|
| FILE_INCLUDED | ✅ | File was included in scan |
| FILE_EXCLUDED | ❌ | File was excluded from scan |
| PATTERN_MATCHED | 🔍 | Pattern found a match |
| PATTERN_SKIPPED | • | Pattern found no match |
| VIOLATION_DETECTED | ⚠️ | Violation was identified |
| SCAN_ERROR | ❗ | Error encountered during scan |

## Exclusion Transparency

The scanner now clearly shows why files are excluded:

```
Exclusion Reasons:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Reason                                 ┃ Count ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━┫
┃ Matched exclusion pattern              ┃  2812 ┃
┃ Matched .gitignore pattern             ┃    10 ┃
┃ Outside scan root                      ┃     5 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━┛
```

## Performance Metrics

Every scan includes performance metrics:

```
Performance Summary:
- Total Duration: 2345.6ms
- Files/Second: 185.7
- Patterns/Second: 2847.3
- Avg per File: 23.7ms
```

## Use Cases

### 1. Debugging False Positives

```bash
# See exactly why a violation was detected
codex --explain src/api.py
```

### 2. CI/CD Integration

```bash
# Get machine-readable results with exit code
codex --json --quiet
if [ $? -eq 1 ]; then
  echo "Violations found"
fi
```

### 3. Pre-commit Verification

```bash
# Check what would be scanned before committing
codex --dry-run --list-files
```

### 4. Audit and Compliance

```bash
# Generate complete audit trail for compliance
codex --export-audit scan-audit-$(date +%Y%m%d).json
```

### 5. Performance Optimization

```bash
# Identify slow patterns or files
codex --explain --export-audit perf-analysis.json
# Analyze the audit trail for processing times
```

## Best Practices

1. **Use `--dry-run` first** to verify your exclusion patterns are working correctly
2. **Use `--explain` when debugging** unexpected violations or missing detections
3. **Export audit trails in CI/CD** for troubleshooting failed builds
4. **Use JSON output for automation** to integrate with other tools
5. **Review exclusion rates** - very high rates might indicate overly broad patterns

## Implementation Details

The transparency features are implemented through:

- **ScanDiscovery**: Handles file discovery with complete audit trail
- **ScanContext**: Tracks all decisions with timestamps and reasons
- **ViolationReporter**: Provides clean, structured violation reporting
- **Decision enum**: Categorizes all scanner decisions for clarity

All output respects the MCP protocol by:
- Sending status messages to stderr
- Sending data output to stdout
- Using structured logging with Logfire
- Avoiding stdout pollution in library code
# Making Codex Settings Discoverable

## The Problem
Users don't know:
1. What settings exist
2. Where to configure them
3. What values are valid
4. What the current settings are
5. Why certain files are excluded/included

## Solution: Multi-Layer Discoverability

### 1. 🔍 **Interactive Discovery Commands**

#### `codex config` - Main configuration command
```bash
# Show all current settings and their sources
$ codex config show
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Setting               ┃ Value                       ┃ Source          ┃
┣━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━┫
┃ exclude               ┃ ["*.pyc", "__pycache__",    ┃ .codex.toml     ┃
┃                       ┃  ".venv", "*_backup_*/"]    ┃                 ┃
┃ use_gitignore         ┃ true                        ┃ defaults        ┃
┃ max_file_size         ┃ 1MB                         ┃ defaults        ┃
┃ run_tools             ┃ false                       ┃ .env            ┃
┃ pattern_priorities    ┃ ["CRITICAL", "HIGH"]        ┃ pyproject.toml  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┛

# Show where settings come from
$ codex config sources
Configuration loaded from (in order of precedence):
1. ✓ Default settings (built-in)
2. ✗ User config (~/.config/codex/settings.toml) - not found
3. ✓ Project config (.codex.toml)
4. ✓ Environment variables (CODEX_RUN_TOOLS)
5. ✗ Command line arguments (none)

# List all available settings with descriptions
$ codex config list
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Setting               ┃ Description                                 ┃ Type     ┃
┣━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━┫
┃ exclude               ┃ Patterns to exclude from scanning          ┃ list[str]┃
┃ use_gitignore         ┃ Also exclude .gitignore patterns           ┃ bool     ┃
┃ max_file_size         ┃ Skip files larger than this                ┃ size     ┃
┃ run_tools             ┃ Run external tools (ruff, mypy, typos)     ┃ bool     ┃
┃ pattern_priorities    ┃ Which pattern priorities to enforce        ┃ list[str]┃
┃ auto_fix              ┃ Automatically apply fixes                  ┃ bool     ┃
┃ output_format         ┃ Output format (human|json|markdown)        ┃ enum     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━┛

# Search for specific settings
$ codex config search exclude
Found 3 settings matching 'exclude':
• exclude - Patterns to exclude from scanning
• use_gitignore - Also exclude .gitignore patterns  
• pattern_exclusions - Exclude specific patterns from paths
```

#### `codex config init` - Interactive configuration wizard
```bash
$ codex config init
Welcome to Codex configuration wizard!

? Where should we save the configuration? › 
❯ .codex.toml (project-specific)
  pyproject.toml (in [tool.codex] section)
  ~/.config/codex/settings.toml (user-global)

? What should be excluded from scanning? › 
✓ Python artifacts (*.pyc, __pycache__)
✓ Virtual environments (.venv, venv)
✓ Version control (.git)
✓ Build artifacts (build/, dist/)
☐ Documentation (docs/, *.md)
☐ Tests (tests/)
✓ Backup directories (*_backup_*/)

? Enable external tools? (Y/n) › Yes

? Which tools should run? ›
✓ ruff (linting)
✓ mypy (type checking)
✓ typos (spell checking)

Creating .codex.toml with your settings...
✓ Configuration saved to .codex.toml

Run 'codex config validate' to test your configuration
```

#### `codex config validate` - Test configuration
```bash
$ codex config validate
Validating configuration...

✓ Configuration file is valid TOML
✓ All exclude patterns are valid
⚠ Pattern '*_backup_*/' will exclude 3 directories (576 files)
✓ External tools are available: ruff, mypy, typos
✓ No conflicting settings detected

Configuration is valid and ready to use!
```

### 2. 📊 **Diagnostic Commands**

#### `codex explain` - Explain decisions
```bash
$ codex explain path/to/file.py
File: path/to/file.py

Would this file be scanned? NO ❌

Exclusion chain:
1. ✓ Not binary file
2. ✓ Size: 1.2KB (under 1MB limit)
3. ✗ Matches .gitignore pattern: build/**
4. (Stopped here - file excluded)

To include this file:
- Remove 'build/**' from .gitignore, OR
- Add to .codex.toml: include_despite_gitignore = ["path/to/file.py"]
```

#### `codex why-excluded` - Bulk exclusion analysis
```bash
$ codex why-excluded
Analyzing exclusions...

Top exclusion reasons:
1. "*_backup_*/" pattern → 576 files (3 directories)
2. ".venv/**" from .gitignore → 2,104 files  
3. "build/" pattern → 107 files
4. "__pycache__" pattern → 89 files
5. "*.pyc" pattern → 67 files

Directories fully excluded:
• quality_enforcement_backup_20250819_200552/ (192 files)
• quality_enforcement_backup_20250819_194047/ (192 files)
• codex_backup_20250819_185515/ (192 files)
• .venv/ (2,104 files)
• build/ (107 files)

Tip: These 5 directories contain 60% of all excluded files.
Consider moving them outside the project or to .gitignore.
```

### 3. 📝 **Self-Documenting Config Files**

#### Generated `.codex.toml` with comments
```toml
# Codex Configuration File
# Generated by: codex config init
# Date: 2024-01-15
# Docs: https://codex.docs/configuration

[codex]
# Patterns to exclude from scanning
# Use glob patterns: *, **, ?, [abc]
# Default: ["*.pyc", "__pycache__", ".git", ".venv", "venv"]
exclude = [
    # Python artifacts
    "*.pyc",
    "__pycache__",
    
    # Virtual environments
    ".venv",
    "venv",
    "env",
    
    # Build artifacts
    "build/",
    "dist/",
    "*.egg-info",
    
    # Backup directories (fixes duplicate scanning issue)
    "*_backup_*/",      # Added to fix 576 duplicate violations
    
    # Project-specific
    "experiments/",     # Experimental code with known issues
    "legacy/",          # Old code being phased out
]

# Use .gitignore patterns as additional exclusions
# Default: true
use_gitignore = true

# Maximum file size to scan (examples: "1MB", "500KB", "2GB")
# Default: "1MB"
max_file_size = "1MB"

# Run external tools during scan
# Default: true
run_tools = true

# Which external tools to run
[codex.tools]
ruff = true    # Fast Python linter
mypy = true    # Static type checker
typos = false  # Spell checker (disabled - too many false positives)

# Pattern-specific exclusions
# Some patterns shouldn't apply to certain directories
[codex.pattern_exclusions]
# Don't check mock naming in test fixtures
"mock-code-naming" = ["tests/fixtures/", "tests/data/"]

# Don't check for secrets in example code
"no-hardcoded-secrets" = ["examples/", "docs/tutorials/"]

# Legacy code doesn't use uv yet
"use-uv-package-manager" = ["legacy/", "vendor/"]
```

### 4. 🎯 **First-Run Experience**

#### Automatic config detection on first run
```bash
$ codex
No configuration found. Would you like to:

1. Quick setup (recommended) - Sensible defaults for Python projects
2. Custom setup - Choose your own settings
3. Skip - Use built-in defaults

Choice [1]: 1

Creating .codex.toml with recommended settings...

✓ Created .codex.toml
✓ Detected 3 backup directories - added to exclusions
✓ Found .gitignore - will use those exclusions too
✓ Found pyproject.toml - detected Python project

Ready to scan! Found 95 Python files to check.
Run 'codex config show' to see your settings.
```

### 5. 🔧 **IDE/Editor Integration**

#### VS Code Extension
```json
// .vscode/settings.json - Auto-generated
{
  "codex.exclude": [
    "*_backup_*/",
    "build/"
  ],
  "codex.showExcludedInExplorer": true,
  "codex.decorateExcludedFiles": true
}
```

Visual indicators in file explorer:
- 🚫 Excluded files (grayed out)
- ✅ Included files (normal)
- ⚠️ Large files (warning icon)

### 6. 📖 **Built-in Documentation**

#### `codex help config`
```bash
$ codex help config
CONFIGURATION GUIDE

Codex looks for configuration in this order:
1. Command line arguments (--exclude, --no-tools)
2. Environment variables (CODEX_*)
3. Project config (.codex.toml or pyproject.toml)
4. User config (~/.config/codex/settings.toml)
5. Built-in defaults

COMMON PATTERNS:

Exclude backup directories:
  exclude = ["*_backup_*/", "*.backup"]

Exclude by extension:
  exclude = ["*.tmp", "*.log", "*.cache"]

Exclude by directory:
  exclude = ["vendor/", "third_party/", "legacy/"]

EXAMPLES:

Minimal .codex.toml:
  [codex]
  exclude = ["*_backup_*/", "build/"]

With pattern exclusions:
  [codex.pattern_exclusions]
  "mock-code-naming" = ["tests/"]

Environment variable:
  export CODEX_EXCLUDE='["vendor/", "legacy/"]'
  
MORE HELP:
  codex config --help     Configuration commands
  codex config examples   Show example configurations
  codex config migrate    Migrate old config to new format
```

### 7. 🚨 **Proactive Warnings**

#### Detect common issues
```bash
$ codex
⚠️ Warning: Found 3 backup directories with 576 duplicate files:
  • quality_enforcement_backup_20250819_200552/
  • quality_enforcement_backup_20250819_194047/
  • codex_backup_20250819_185515/

These will be scanned and create duplicate violations.
Add to .codex.toml to exclude:

  exclude = ["*_backup_*/"]

Or run: codex config add-exclude "*_backup_*/"
```

### 8. 💡 **Smart Suggestions**

#### Context-aware recommendations
```bash
$ codex --dry-run
Scanning 237 files...

💡 Optimization opportunity detected:
You're scanning 142 files in backup directories that duplicate your main code.

Quick fix:
  codex config add-exclude "*_backup_*/"

This would reduce files scanned from 237 to 95 (-60%)
```

### 9. 🔄 **Config Migration**

#### Help users upgrade
```bash
$ codex config migrate
Found old configuration format in .codexrc

Would you like to migrate to the new format? (Y/n) Y

Migrating settings:
✓ exclude_patterns → exclude
✓ enable_tools → run_tools  
✓ priorities → pattern_priorities

✓ Migration complete! Old config backed up to .codexrc.backup
✓ New config saved to .codex.toml
```

### 10. 📊 **Web UI Dashboard**

#### `codex ui` - Visual configuration
```bash
$ codex ui
Starting Codex configuration UI at http://localhost:8080

[Web browser opens with visual config editor]
```

Features:
- Visual exclude pattern builder
- Live preview of what files will be scanned
- Pattern testing playground
- Settings history/undo
- Export/import configurations

## Implementation Priority

### Phase 1: Immediate (High Impact, Low Effort)
1. ✅ Add `codex config show` command
2. ✅ Add `codex config init` wizard  
3. ✅ Generate commented `.codex.toml` files
4. ✅ Add warnings for backup directories

### Phase 2: Short-term (High Value)
5. Add `codex explain <file>` command
6. Add `codex why-excluded` analysis
7. Improve `--dry-run` output
8. Add config validation

### Phase 3: Long-term (Nice to Have)
9. VS Code extension
10. Web UI dashboard
11. Config migration tool
12. Smart suggestions

## Success Metrics

Settings are discoverable when:
1. **New users** can configure Codex in <2 minutes
2. **Users understand** why files are excluded/included
3. **Configuration errors** drop by 80%
4. **Support questions** about settings decrease
5. **Users discover** optimization opportunities themselves

## Key Insight

The current issue (1,146 violations with 60% false positives) would have been automatically prevented with:
- Proactive warning about backup directories
- Config wizard suggesting exclusions
- `why-excluded` showing the impact

Make the tool teach users how to use it!
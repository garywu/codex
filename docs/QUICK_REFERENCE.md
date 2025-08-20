# Codex Quick Reference Card

## 🚀 Essential Commands

```bash
# Query patterns with natural language
codex query "HTTP client best practices"

# Get file-specific recommendations
codex context --file src/api.py --ai

# Validate code snippets
codex validate --code "import requests"

# Scan project for violations
codex --fix
```

## 🤖 AI Assistant Commands

```bash
# Core AI workflow commands
codex query "<search>" --ai           # Natural language pattern search
codex context --file <path> --ai      # File-specific patterns
codex explain <pattern> --ai          # Pattern details
codex validate --code "<code>"        # Code validation
```

## 📊 Common Use Cases

### Error Resolution
```bash
codex query "ruff TRY401" --ai        # Fix specific ruff errors
codex explain ruff-TRY401 --ai        # Detailed explanation
```

### Technology Guidance
```bash
codex query "HTTP client" --ai        # → httpx recommendations
codex query "async database" --ai     # → SQLModel patterns
codex query "dependency injection"    # → DI patterns
```

### File Context
```bash
codex context --file src/api.py --ai     # → API patterns
codex context --file tests/test_*.py     # → Testing patterns
codex context --file setup.py            # → Package management
```

## 🔧 Setup Commands

```bash
# Quick installation
./install_codex_mcp.sh install

# Check status
codex startup-status

# Import patterns
codex import-patterns project-init.json
```

## 📈 Pattern Categories

- **package_management** - UV vs pip/poetry
- **core_libraries** - httpx, pydantic, typer
- **quality_tools** - ruff, mypy, pytest
- **security** - SQL injection prevention
- **error_handling** - Exception patterns
- **testing** - pytest, dependency injection

## 🎯 Exit Codes

- `0` - Clean (no violations)
- `1` - Violations found
- `2` - Error (file not found, etc.)

## 🔍 Output Formats

```bash
--ai           # AI-friendly markdown
--format json  # Machine-readable
--quiet        # CI/CD mode
```

## 📱 Quick Examples

```bash
# Developer workflow
codex query "async patterns" --limit 5
codex validate src/main.py
codex --fix && git commit

# AI integration
codex context --intent "making HTTP requests" --ai
codex validate --code "generated_code_here"

# Team compliance
codex scan --format json > report.json
codex export --format markdown > standards.md
```

---
**Get started:** `./install_codex_mcp.sh install && codex query "HTTP client"`

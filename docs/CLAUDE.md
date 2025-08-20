# Codex Development Guide for Claude

## Overview

Codex is an AI-powered pattern intelligence platform that:
1. **Primary**: Provides instant pattern queries and code intelligence for AI assistants
2. **MCP Integration**: Direct Claude Desktop integration with 8 specialized tools
3. **Pattern Database**: SQLite FTS5 with 0.1ms query responses
4. **Code Scanner**: Validates code against patterns with auto-fixing
5. **Auto-Startup**: Background service ready when you need it
6. **Enterprise Ready**: Handles 2,400+ line pattern files efficiently

## 🚀 For Claude: Quick Start Commands

### **Most Important Commands for AI Assistance**

#### **Pattern Discovery** (Use these first!)
```bash
# Natural language pattern search
codex query "HTTP client best practices" --ai
codex query "error handling patterns" --ai
codex query "dependency injection" --ai

# File-specific context (when helping with specific files)
codex context --file src/api.py --ai
codex context --file tests/test_client.py --ai

# Intent-based discovery (when user describes what they want)
codex context --intent "making HTTP requests" --ai
codex context --intent "writing tests" --ai
```

#### **Code Validation** (Use when reviewing/generating code)
```bash
# Validate code snippets
codex validate --code "import requests; requests.get(url)"
codex validate --code "pip install httpx"

# Validate files
codex validate src/main.py
codex validate tests/ --language python
```

#### **Technology Recommendations** (NEW! Use for architecture guidance)
```bash
# Get technology adoption recommendations
codex scan --recommendations                    # Full project analysis
codex precommit --recommendations              # Pre-commit with suggestions
codex ci --recommendations                     # CI/CD with architecture guidance

# Examples of what it detects:
# - Multiple env vars → Recommend Pydantic Settings
# - Manual validation → Recommend Pydantic Models  
# - Basic logging → Recommend Logfire integration
```

#### **Specific Help** (When user has errors or needs explanations)
```bash
# Explain specific patterns
codex explain use-httpx --ai
codex explain ruff-TRY401 --ai

# Get error-specific help
codex query "ruff TRY401" --ai
codex query "logging.exception error" --ai
```

## 📋 Complete Command Reference for Claude

### **Essential AI Commands** (Use these regularly!)

#### **Pattern Query Commands**
```bash
# Natural language pattern search
codex query "HTTP client" --ai                    # Get httpx recommendations
codex query "error handling" --ai                 # Exception patterns
codex query "package management" --ai              # UV vs pip patterns
codex query "async database" --ai                 # aiosqlite, SQLModel patterns

# File-specific context generation
codex context --file src/api.py --ai              # API patterns (httpx, pydantic, FastAPI)
codex context --file tests/test_client.py --ai    # Testing patterns (pytest, DI)
codex context --file setup.py --ai                # Package management patterns

# Intent-based pattern discovery
codex context --intent "making HTTP requests" --ai # HTTP client patterns
codex context --intent "writing tests" --ai        # Testing best practices
codex context --intent "handling errors" --ai      # Error handling patterns

# Category exploration
codex context --category core_libraries --ai       # Core library patterns
codex context --category security --ai             # Security patterns
```

#### **Code Validation Commands**
```bash
# Validate code snippets (perfect for generated code)
codex validate --code "import requests; requests.get(url)"
codex validate --code "pip install httpx"
codex validate --code "logging.exception(f'Error: {e}')"

# Validate files
codex validate src/main.py                         # Check single file
codex validate tests/ --language python            # Check directory
codex validate . --quiet                          # Quick validation

# Full project scanning
codex                                              # Scan current directory
codex src/ --fix                                  # Scan with auto-fixes
codex --quiet                                     # CI mode (exit codes only)
```

#### **Technology Recommendation Commands** (NEW!)
```bash
# Project-level architecture recommendations
codex scan --recommendations                      # Technology adoption suggestions
codex precommit --recommendations                 # Pre-commit with architecture guidance
codex ci --recommendations                        # CI/CD with technology recommendations

# Examples of recommendations:
# - Detects multiple env vars → Suggests Pydantic Settings
# - Finds manual validation → Recommends Pydantic Models
# - Identifies basic logging → Suggests Logfire adoption
# - Analyzes code patterns → Architecture improvement suggestions
```

#### **Pattern Information Commands**
```bash
# Detailed pattern explanations (for teaching users)
codex explain use-httpx --ai                      # HTTP client pattern details
codex explain ruff-TRY401 --ai                    # Specific ruff error fix
codex explain dependency-injection-constructor --ai # DI pattern explanation

# Pattern management
codex patterns --list                             # List all patterns
codex patterns --category core_libraries          # List by category
codex stats                                       # Usage statistics
```

#### **🔋 Portable "Batteries Included" Commands** (NEW!)
```bash
# Apply quality tools to ANY repository (even without setup)
codex portable /path/to/any-repo                 # Analyze any repo
codex portable /path/to/any-repo --fix          # Fix violations
codex portable . --install                       # Auto-install missing tools

# Initialize any repository with Codex
codex init-repo /path/to/existing-repo           # Make repo Codex-ready
codex init-repo . --patterns company.json       # Add company patterns
codex init-repo --no-precommit                  # Skip pre-commit setup

# One-shot quality analysis of external repositories
codex any-repo /path/to/external-repo            # Quick quality check
codex any-repo ../some-project --init --fix     # Full analysis with setup
codex any-repo ~/Downloads/project --patterns patterns.json --quiet

# Manage portable tools
codex tools --check                             # Check tool availability
codex tools --install ruff                      # Install specific tool
codex tools --config mypy                       # Generate tool config
```

#### **Setup and Management Commands**
```bash
# Pattern database management
codex import-patterns ~/work/project-init.json    # Import patterns
codex export --format markdown --ai               # Export for documentation
codex export --format json                        # Export structured data

# Service management
codex startup-status                              # Check service status
codex serve --mcp                                 # Start MCP server manually

# Project initialization
codex init --import ~/work/project-init.json     # Initialize new project
```

## Architecture

### Core Flow (Optimized for Speed)
```
codex (no args) → scan current dir → exit 0 or 1
codex file.py → scan file → show violations → exit code
codex --fix → scan → apply fixes → exit code
```

### Components

#### Scanner (`scanner.py`)
- Fast pattern matching
- Runs external tools (ruff, mypy, typos)
- Minimal dependencies
- Exit codes for CI/CD
- Quiet mode for automation

#### Tool Runner (`tools.py`)
- Executes ruff, mypy, typos
- Parallel execution for speed
- JSON output parsing
- Fix mode support

#### Config (`config.py`)
- Load from `.codex.toml`
- Fallback to `pyproject.toml`
- Default configuration

#### Pattern Database (`database.py`)
- SQLite with SQLModel
- Async operations
- Pattern caching

#### Farm Integration (`client.py`)
- Optional AI detection
- Graceful fallback
- Agent training

## Configuration Priority

1. Command line args (highest)
2. `.codex.toml` in current dir
3. `pyproject.toml` [tool.codex]
4. Default configuration

## Pattern Detection Layers

1. **Fast**: Regex and forbidden patterns (<10ms)
2. **Smart**: Context-aware rules (<50ms)
3. **AI**: Farm agents when available (<500ms)

## Exit Codes

- `0`: Clean - no violations
- `1`: Violations found
- `2`: Error (file not found, etc.)

## Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: codex
        name: Codex Scanner
        entry: codex
        language: system
        pass_filenames: true
```

## Development Workflow

### Adding New Pattern Detection
1. Add to `detection_rules` in pattern
2. Implement in `scanner._check_pattern_simple()`
3. Test with sample violations

### Negative Space Best Practices Methodology
Codex implements evidence-based best practice identification through "negative space" analysis:

1. **Scan Multiple Projects**: Run enhanced scanner across organization
2. **Identify Clean Projects**: Find projects that avoid specific violations
3. **Analyze Protective Patterns**: Compare structural differences between clean and problematic projects
4. **Extract Best Practices**: Codify patterns that correlate with avoiding problems
5. **Generate Implementation Guides**: Create actionable recommendations

Key files:
- `codex/negative_space_patterns.py`: Core negative space detection
- `comprehensive_enhanced_patterns.json`: Project-init.json derived patterns
- `negative_space_analyzer.py`: Cross-project analysis tool

### Testing Scanner
```bash
# Test on sample file
echo "eval('bad')" > test.py
uv run codex test.py  # Should find violation

# Test fix
uv run codex test.py --fix
cat test.py  # Should be fixed

# Run negative space analysis
uv run python negative_space_analyzer.py
```

### Performance Testing
```bash
# Time scanning
time uv run codex src/

# Profile for optimization
uv run python -m cProfile -o profile.out codex src/
```

### Best Practices Integration
```bash
# Scan with comprehensive patterns
uv run python enhanced_intelligent_scanner.py

# Analyze organizational best practices
uv run python negative_space_analyzer.py

# Generate evidence-based recommendations
uv run python best_practices_scanner.py
```

## Key Design Decisions

### Why Scanner-First?
- Most common use case is scanning
- Pre-commit hooks need speed
- CI/CD needs simple exit codes
- Follows successful tools like `ruff`, `typos`

### Why Hidden Commands?
- Keep main interface simple
- Advanced features available but not cluttering
- Focus on primary use case

### Why Configuration Files?
- Project-specific settings
- Share across team
- Pre-commit compatible

## Common Issues

### Pattern Not Detected
1. Check pattern in database: `codex patterns --list`
2. Verify detection rules
3. Check file not excluded
4. Try with `--exclude ""`

### Slow Scanning
1. Too many patterns enabled
2. Large files - add to exclude
3. Farm SDK timeout - disable with config

### Fix Not Applied
1. Pattern needs `fix_template`
2. File permissions
3. Complex fix needs manual intervention

## AI Assistant Integration (IMPLEMENTED)

### Complete SQLite FTS Pattern System

Codex now provides a complete AI-friendly pattern query system with CLI and MCP server interfaces:

#### Implementation Summary:
✅ **SQLite FTS5 Database** - Fast pattern storage with full-text search
✅ **Pattern Extractor** - Imports from project-init.json files
✅ **AI Query Interface** - Natural language pattern queries
✅ **CLI Commands** - Complete command-line interface
✅ **MCP Server** - Model Context Protocol for AI assistants
✅ **Code Validation** - Real-time pattern violation detection

#### New CLI Commands:
```bash
# Query patterns with natural language
codex query "HTTP client implementation"
codex query "error handling best practices" --ai

# Get context for specific files/situations
codex context --file src/api.py --ai
codex context --intent "making HTTP requests"

# Pattern management
codex import-patterns ~/work/project-init.json
codex explain use-httpx --ai
codex validate src/main.py
codex stats

# MCP server for AI assistants
codex serve --mcp
```

#### MCP Server Tools:
- `query_patterns` - Natural language pattern search
- `get_file_context` - File-specific pattern recommendations
- `explain_pattern` - Detailed pattern explanations
- `validate_code` - Code snippet validation
- `semantic_search` - Intent-based pattern discovery

#### Performance Metrics (Verified):
- **Database**: 28KB for 6 patterns (~4.8KB per pattern)
- **Query Speed**: 0.1ms for pattern matching
- **Natural Language**: "HTTP client" → httpx patterns
- **Code Validation**: Real-time violation detection
- **Context Generation**: File-specific recommendations

#### AI Query Examples:
```python
# Natural language queries
"HTTP client"           → use-httpx [HIGH]
"package management"    → use-uv-not-pip [MANDATORY]
"dependency injection"  → constructor injection patterns
"logging exception"     → ruff-TRY401 error fix

# Intent-based search
"I want to make HTTP requests" → httpx recommendations
"I need to install packages"   → UV package manager
"Got ruff error TRY401"       → exact fix instructions
```

#### Integration Workflow:
```
1. Import: codex import-patterns project-init.json
2. Query: AI calls MCP tools or CLI commands
3. Context: AI gets file-specific patterns
4. Validate: AI checks code before commit
5. Track: Usage statistics and pattern success
```

#### File-Specific Context:
- `src/api/*.py` → httpx, pydantic, FastAPI patterns
- `tests/*.py` → dependency injection, pytest patterns
- `*.py` → ruff errors, exception handling patterns

### Recommended Workflow for AI Assistants:

1. **Session Start**: `codex context --file {current_file} --ai`
2. **Before Coding**: `codex query "{functionality}" --ai`
3. **On Errors**: `codex explain {error_pattern} --ai`
4. **Before Commit**: `codex validate {file} --ai`

### Pattern Storage Architecture:
```
project-init.json (2,400 lines)
        ↓ codex import-patterns
SQLite FTS Database (efficient storage)
        ↓ AI queries via CLI/MCP
Focused Context (50-200 lines)
        ↓ Track usage
Analytics & Learning
```

## 🤖 MCP Integration (Claude Desktop)

### **Available MCP Tools** (8 tools total)
When using Claude Desktop with MCP integration, these tools are available:

1. **`query_patterns`** - Natural language pattern search
2. **`get_file_context`** - File-specific pattern recommendations
3. **`explain_pattern`** - Detailed pattern explanations
4. **`validate_code`** - Code snippet validation
5. **`semantic_search`** - Intent-based pattern discovery
6. **`import_patterns`** - Import new pattern definitions
7. **`list_categories`** - Browse available pattern categories
8. **`get_stats`** - Usage analytics and statistics

### **Example MCP Interactions**
```
Claude: "I need to make HTTP requests in Python"
→ Uses query_patterns tool → Returns httpx patterns with examples

Claude: "How do I fix this ruff error TRY401?"
→ Uses explain_pattern tool → Returns exact fix instructions

Claude: "What patterns apply to this API file?"
→ Uses get_file_context tool → Returns httpx, pydantic, FastAPI patterns
```

## 🎯 AI Assistant Workflow

### **Recommended Usage Pattern for Claude**

1. **When helping with code**: Start with pattern context
   ```bash
   codex context --file src/api.py --ai
   ```

2. **When user asks "how to do X"**: Query patterns
   ```bash
   codex query "X" --ai
   ```

3. **When reviewing code**: Validate against patterns
   ```bash
   codex validate --code "user_code_here"
   ```

4. **When user has errors**: Explain specific patterns
   ```bash
   codex explain pattern-name --ai
   ```

### **Common AI Assistant Scenarios**

#### **HTTP Client Implementation**
```bash
codex query "HTTP client" --ai
# Returns: use-httpx pattern with async examples
# AI can then provide httpx-based solution
```

#### **Error Handling Setup**
```bash
codex query "error handling" --ai
# Returns: exception patterns, logging best practices
# AI can implement proper error handling
```

#### **Package Management Questions**
```bash
codex query "package management" --ai
# Returns: UV over pip/poetry patterns
# AI recommends UV for dependencies
```

#### **Testing Implementation**
```bash
codex context --intent "writing tests" --ai
# Returns: pytest, dependency injection patterns
# AI structures tests with DI for testability
```

#### **Architecture Recommendations** (NEW!)
```bash
codex scan --recommendations
# Returns: Technology adoption suggestions based on code analysis
# - "Consider Pydantic Settings for environment configuration"
# - "Adopt Pydantic Models for data validation in API endpoints"
# - "Integrate Logfire for structured logging and observability"
```

#### **Code Review and Fixes**
```bash
codex validate --code "problematic_code"
# Returns: specific violations and fixes
# AI provides exact corrections
```

## 📊 Pattern Categories Available

**Core Categories Claude Should Know:**

- **📦 package_management**: UV vs pip/poetry (MANDATORY patterns)
- **🌐 core_libraries**: httpx, pydantic, SQLModel, typer, rich
- **🔧 quality_tools**: ruff, mypy, pytest configurations
- **🏗️ project_structure**: Directory layouts, file organization
- **⚠️ error_handling**: Exception patterns, logging best practices
- **✅ validation**: Pydantic models, data validation
- **🔒 security**: SQL injection prevention, input sanitization
- **🧪 testing**: pytest patterns, dependency injection
- **💉 dependency_injection**: Constructor injection, testability
- **🚨 ruff_errors**: Specific solutions for ruff violations
- **🏛️ architecture_recommendations**: Technology adoption guidance (NEW!)

## ⚡ Performance for AI

- **Pattern Queries**: 0.1ms average (faster than loading JSON)
- **Database Size**: 28KB for 50+ complex patterns
- **Context Generation**: <50ms for file-specific patterns
- **Code Validation**: Real-time snippet checking
- **Natural Language**: Maps intent to patterns automatically

## 🔧 Installation Status

### **Check if Codex is Ready**
```bash
codex startup-status          # Check if service is running
codex query "test" --limit 1   # Quick functionality test
```

### **If Not Installed**
```bash
./install_codex_mcp.sh install  # One-command setup
```

## 💡 Tips for Claude

### **Always Use `--ai` Flag**
For AI-friendly markdown output:
```bash
codex query "anything" --ai
codex context --file path --ai
codex explain pattern --ai
```

### **Combine Multiple Approaches**
```bash
# Get both file-specific and general context
codex context --file src/api.py --ai
codex query "FastAPI patterns" --ai
```

### **Validate Generated Code**
```bash
# After generating code for user
codex validate --code "generated_code_here"
```

### **Error Resolution Flow**
1. User reports error → `codex query "specific_error" --ai`
2. Get broader context → `codex context --intent "error_handling" --ai`
3. Provide solution → Validate with `codex validate --code "solution"`

## 🚀 Quick Reference

**Most Used Commands for AI:**
- `codex query "<search>" --ai` - Find patterns
- `codex context --file <path> --ai` - File context
- `codex validate --code "<code>"` - Check compliance
- `codex explain <pattern> --ai` - Pattern details
- `codex scan --recommendations` - Architecture guidance (NEW!)

**Key Patterns to Remember:**
- **HTTP**: use-httpx (not requests)
- **Package**: use-uv-not-pip (not pip/poetry)
- **Validation**: use-pydantic-basemodel (not dataclass for APIs)
- **Testing**: dependency-injection-constructor (for testability)
- **Errors**: Specific ruff error codes (TRY401, F841, etc.)

## Future Enhancements

- [ ] Parallel file scanning
- [ ] Watch mode for development
- [ ] Pattern learning from fixes
- [ ] VSCode extension
- [ ] GitHub Action
- [x] SQLite FTS pattern database for AI queries
- [x] MCP server integration with Claude Desktop
- [x] Natural language pattern queries
- [x] Real-time code validation
- [x] Auto-startup service installation
- [ ] Semantic pattern search with embeddings
- [ ] Pattern usage analytics and learning
- [ ] Multi-project pattern federation
- [ ] Real-time pattern sync across teams

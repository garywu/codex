# Codex - AI-Powered Pattern Intelligence Platform

**Codex** is a sophisticated pattern-based code scanner and AI assistant integration platform that enforces coding standards, best practices, and provides real-time pattern intelligence.

## 🚀 Quick Start

```bash
# Install everything (auto-startup + AI integration)
./install_codex_mcp.sh install

# Query patterns with natural language
codex query "HTTP client best practices"

# 🔋 PORTABLE: Apply to ANY repository (batteries included!)
codex portable /path/to/any-repo --fix

# 🎯 ONE-SHOT: Complete quality check on external repo
codex any-repo ~/Downloads/some-project --init --patterns company.json
```

## 🎯 Core Features

### 🔍 **Pattern Intelligence**
- **Natural Language Queries**: Ask "HTTP client" → Get httpx recommendations
- **File-Specific Context**: Smart pattern suggestions based on file type/location
- **Intent-Based Search**: "I want to handle errors" → Exception handling patterns
- **Real-Time Validation**: Instant code compliance checking
- **Pattern Evolution**: Learn from usage and improve recommendations

### 🤖 **AI Assistant Integration**
- **MCP Protocol Server**: Direct integration with Claude Desktop, Cursor, Copilot
- **8 Specialized Tools**: Pattern queries, code validation, context generation
- **Sub-millisecond Responses**: SQLite FTS5 for instant pattern retrieval
- **Semantic Understanding**: Maps AI intent to relevant coding patterns
- **Usage Analytics**: Track which patterns work best

### ⚡ **Performance**
- **0.1ms Pattern Queries**: Faster than loading JSON files
- **28KB Database**: Stores thousands of patterns efficiently
- **Auto-Startup**: Background service ready when you need it
- **Parallel Scanning**: Fast file processing with async operations

### 🔋 **Portable "Batteries Included" Mode** (NEW!)
- **Apply to ANY Repository**: Works on repositories without any existing tool setup
- **Auto-Install Tools**: Automatically installs ruff, mypy, typos if missing
- **Generate Configurations**: Creates working configs for all tools
- **Cross-Repository Patterns**: Apply your organization's standards anywhere
- **One-Shot Analysis**: Complete quality audit of external codebases
- **Zero Configuration**: Just point and scan - everything else is handled

Perfect for:
- 🔍 **Auditing unknown codebases**: `codex any-repo /path/to/external-project`
- 🏢 **Applying company standards**: `codex portable . --patterns company.json --fix`
- 🚀 **Legacy project modernization**: `codex init-repo /old/project --precommit`
- 📊 **Code quality assessments**: `codex portable --quiet` (exit codes for CI/CD)

## 📋 Complete CLI Reference

### **🔋 Portable Commands** (NEW!)

#### `codex portable [dir]` - Run Quality Tools on Any Repository
```bash
# Analyze any repository (auto-detects tools, generates configs)
codex portable /path/to/any-repo
codex portable . --fix                          # Apply fixes
codex portable ~/project --install              # Auto-install missing tools
codex portable --no-config                      # Don't generate configs
```

#### `codex any-repo <path>` - One-Shot Quality Analysis
```bash
# Complete analysis of external repositories
codex any-repo /path/to/external-repo
codex any-repo ../some-project --init --fix     # Initialize and fix
codex any-repo ~/Downloads/project --patterns patterns.json --quiet
```

#### `codex init-repo [path]` - Initialize Repository with Codex
```bash
# Make any repository Codex-ready
codex init-repo /path/to/existing-repo
codex init-repo . --patterns company.json       # Add company patterns
codex init-repo --no-precommit                  # Skip pre-commit setup
```

#### `codex tools` - Manage Portable Tools
```bash
# Check tool availability
codex tools --check

# Install specific tools
codex tools --install ruff
codex tools --install mypy

# Generate tool configurations
codex tools --config ruff --dir /path/to/project
```

### **Pattern Query Commands**

#### `codex query "<search>"` - Natural Language Pattern Search
```bash
# Basic queries
codex query "HTTP client"
codex query "error handling"
codex query "dependency injection"
codex query "package management"

# Specific error codes
codex query "ruff TRY401"
codex query "mypy errors"

# With options
codex query "async patterns" --limit 10 --ai
codex query "security" --priority MANDATORY
```

#### `codex context` - Contextual Pattern Recommendations
```bash
# File-specific context
codex context --file src/api.py
codex context --file tests/test_client.py --ai
codex context --file setup.py --limit 5

# Intent-based context
codex context --intent "making HTTP requests"
codex context --intent "writing tests"
codex context --intent "handling errors"

# Category-specific
codex context --category package_management
codex context --category core_libraries --ai
```

#### `codex explain <pattern>` - Detailed Pattern Information
```bash
# Pattern explanations
codex explain use-httpx
codex explain ruff-TRY401
codex explain dependency-injection-constructor

# AI-friendly format
codex explain use-pydantic-basemodel --ai
```

### **Code Validation Commands**

#### `codex validate` - Code Compliance Checking
```bash
# Validate files
codex validate src/main.py
codex validate tests/ --language python

# Validate code snippets
codex validate --code "import requests; requests.get(url)"
codex validate --code "pip install httpx" --language bash

# Validate with output formats
codex validate src/ --format json
codex validate . --quiet
```

#### `codex scan` - Full Project Scanning (Default Command)
```bash
# Basic scanning
codex
codex src/
codex --fix
codex --quiet

# Advanced options
codex --no-tools --exclude "*.pyc"
codex --diff --config .codex.toml
```

### **Pattern Management Commands**

#### `codex import-patterns` - Import Pattern Definitions
```bash
# Import from project-init files
codex import-patterns ~/work/project-init.json
codex import-patterns /path/to/company-standards.json --db custom.db

# Import multiple files
codex import-patterns patterns/*.json
```

#### `codex patterns` - Pattern Database Management
```bash
# List patterns
codex patterns --list
codex patterns --category core_libraries
codex patterns --add new-patterns.json
```

#### `codex export` - Export Patterns
```bash
# Export to different formats
codex export --format markdown
codex export --format json --output patterns.json
codex export --format yaml > company-patterns.yaml
```

### **Service Management Commands**

#### `codex serve` - Start MCP Server
```bash
# Start MCP server for AI assistants
codex serve --mcp
codex serve --stdio

# Background service (use installer instead)
./install_codex_mcp.sh install
```

#### `codex install-startup` - Auto-Startup Installation
```bash
# Install user service (recommended)
codex install-startup --user

# Install system service (requires sudo)
codex install-startup --system
```

#### `codex startup-status` - Service Status
```bash
# Check service status
codex startup-status

# Shows:
# - Installation status (user/system)
# - Running status (active/inactive)
# - Log locations and sizes
# - Database information
```

#### `codex uninstall-startup` - Remove Auto-Startup
```bash
# Remove user service
codex uninstall-startup

# Remove system service
codex uninstall-startup --system
```

### **Analytics and Monitoring Commands**

#### `codex stats` - Usage Statistics
```bash
# Pattern usage analytics
codex stats

# Shows:
# - Total patterns in database
# - Most used patterns
# - Usage by AI assistant
# - Success rates
```

### **Initialization Commands**

#### `codex init` - Project Setup
```bash
# Initialize new project
codex init --import ~/work/project-init.json
codex init --farm-url http://localhost:8001
```

#### `codex check` - Pattern-Specific Validation
```bash
# Check specific patterns
codex check use-httpx src/
codex check dependency-injection tests/
```

#### `codex train` - AI Agent Training
```bash
# Train Farm agents for pattern detection
codex train http-agent core_libraries
codex train security-agent security
```

## 🔧 Installation & Setup

### **Method 1: Complete Auto-Installation (Recommended)**
```bash
# Install everything with one command
./install_codex_mcp.sh install

# This installs:
# ✅ Auto-startup service (launchd/systemd)
# ✅ Claude Desktop MCP integration
# ✅ Pattern database from project-init.json
# ✅ Logging and monitoring
```

### **Method 2: Manual CLI Installation**
```bash
# Initialize Codex
codex init --import ~/work/project-init.json

# Install auto-startup
codex install-startup --user

# Check status
codex startup-status
```

### **Method 3: Development Setup**
```bash
# Install dependencies
uv sync --dev

# Import patterns
codex import-patterns project-init.json

# Start MCP server manually
codex serve --mcp
```

## 🤖 AI Assistant Integration

### **Claude Desktop MCP Integration**
```json
{
  "mcpServers": {
    "codex-patterns": {
      "command": "python3",
      "args": ["-m", "codex.mcp_server"],
      "cwd": "/Users/admin/Work/codex"
    }
  }
}
```

### **Available MCP Tools for AI Assistants**
1. **`query_patterns`** - Natural language pattern search
2. **`get_file_context`** - File-specific pattern recommendations
3. **`explain_pattern`** - Detailed pattern explanations
4. **`validate_code`** - Code snippet validation
5. **`semantic_search`** - Intent-based pattern discovery
6. **`import_patterns`** - Import new pattern definitions
7. **`list_categories`** - Browse available pattern categories
8. **`get_stats`** - Usage analytics and statistics

### **Example AI Interactions**
```
AI: "I need to make HTTP requests in Python"
→ Codex returns: use-httpx pattern with async examples

AI: "How do I handle this ruff error TRY401?"
→ Codex returns: Exact fix for logging.exception redundancy

AI: "What patterns apply to this API file?"
→ Codex returns: httpx, pydantic, FastAPI patterns
```

## 📁 Project Structure

```
codex/
├── 📁 codex/                    # Main package
│   ├── cli.py                   # Command-line interface
│   ├── scanner.py               # Pattern scanning engine
│   ├── fts_database.py          # SQLite FTS5 database
│   ├── ai_query.py              # AI query interface
│   ├── pattern_extractor.py     # Pattern import from JSON
│   ├── mcp_server.py            # MCP protocol server
│   └── models.py                # Data models
├── 📁 config/                   # Service configurations
│   ├── com.codex.mcp-server.plist    # macOS launchd
│   ├── codex-mcp.service             # Linux systemd
│   └── claude_desktop_config.json    # Claude Desktop MCP
├── 📁 scripts/                  # Service scripts
│   └── startup_wrapper.sh       # Service startup wrapper
├── 📁 logs/                     # Service logs
├── 📁 data/                     # Pattern database
│   └── patterns_fts.db          # SQLite FTS database
├── 📁 docs/                     # Documentation
├── install_codex_mcp.sh         # Complete installer
├── README.md                    # This file
├── INSTALLATION.md              # Detailed setup guide
└── CLAUDE.md                    # AI assistant instructions
```

## 🎨 Usage Examples

### **For Developers**
```bash
# Quick pattern lookup
codex query "async database"

# Validate before commit
codex validate src/ --quiet && git commit

# Get context while coding
codex context --file $(pwd)/api.py --ai
```

### **For AI Assistants**
```bash
# File-specific recommendations
codex context --file src/api.py --ai

# Validate generated code
codex validate --code "generated_code_here"

# Explain specific patterns
codex explain use-httpx --ai
```

### **For Teams**
```bash
# Import company standards
codex import-patterns company-patterns.json

# Check compliance across project
codex scan --format json > compliance-report.json

# Export current patterns
codex export --format markdown > team-standards.md
```

### **For CI/CD**
```bash
# Pre-commit validation
codex --quiet || exit 1

# Generate compliance report
codex scan --format json > artifacts/violations.json

# Check specific patterns
codex check security-patterns src/
```

## 🔍 Pattern Categories

Codex includes patterns for:

- **📦 Package Management**: UV vs pip/poetry, dependency management
- **🌐 Core Libraries**: httpx, pydantic, SQLModel, typer, rich
- **🔧 Quality Tools**: ruff, mypy, pytest, bandit configurations
- **🏗️ Project Structure**: Directory layouts, file organization
- **⚠️ Error Handling**: Exception patterns, logging best practices
- **✅ Validation**: Pydantic models, data validation strategies
- **🔒 Security**: SQL injection prevention, input sanitization
- **🧪 Testing**: pytest patterns, dependency injection for tests
- **📚 Documentation**: Docstring standards, README templates
- **🎯 API Design**: FastAPI patterns, REST best practices
- **💉 Dependency Injection**: Constructor injection, testability
- **🚨 Ruff Error Fixes**: Specific solutions for ruff violations

## ⚡ Performance Benchmarks

- **Pattern Queries**: 0.1ms average response time
- **Database Size**: 28KB for 50+ complex patterns
- **Startup Time**: <2 seconds for MCP server
- **Memory Usage**: <50MB resident memory
- **File Scanning**: 1000+ files/second
- **Pattern Matching**: 10,000+ patterns/second

## 🛠️ Configuration

### **Project Configuration (`.codex.toml`)**
```toml
[codex]
patterns = ["all"]
exclude = ["*.pyc", "__pycache__", ".git"]
auto_fix = false
enforce = ["mandatory", "critical", "high"]

[ai_integration]
enable_mcp_server = true
mcp_port = 8080
default_query_limit = 5

[patterns]
database_path = ".codex/patterns.db"
auto_import = ["~/work/project-init.json"]
```

### **Environment Variables**
```bash
export CODEX_LOG_LEVEL=INFO
export CODEX_DATABASE_PATH=/custom/path/patterns.db
export PYTHONPATH=/Users/admin/Work/codex
```

## 🔄 Workflow Integration

### **Pre-commit Hook**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: codex
        name: Codex Pattern Scanner
        entry: codex
        language: system
        pass_filenames: true
```

### **GitHub Actions**
```yaml
# .github/workflows/codex.yml
- name: Run Codex Pattern Check
  run: |
    codex --quiet
    codex export --format json > pattern-report.json
```

### **VS Code Integration**
```json
{
  "tasks": [
    {
      "label": "Codex: Query Patterns",
      "type": "shell",
      "command": "codex query '${input:query}' --ai"
    }
  ]
}
```

## 📊 Monitoring & Logging

### **Service Logs**
```bash
# Real-time logs
tail -f logs/codex-mcp.log

# Error logs
tail -f logs/codex-mcp-error.log

# Service status
./install_codex_mcp.sh status
```

### **Usage Analytics**
```bash
# Pattern statistics
codex stats

# Database metrics
sqlite3 data/patterns_fts.db "SELECT COUNT(*) FROM patterns;"

# Query performance
grep "Query.*ms" logs/codex-mcp.log
```

## 🤝 Contributing

### **Adding New Patterns**
1. Update `project-init.json` with new patterns
2. Import with `codex import-patterns`
3. Test with `codex query "new pattern"`
4. Validate with `codex validate test-code`

### **Extending CLI**
1. Add commands to `codex/cli.py`
2. Update this README with examples
3. Test with `codex command --help`
4. Document in `CLAUDE.md` for AI assistants

## 🐛 Troubleshooting

### **Common Issues**

**Service won't start:**
```bash
# Check dependencies
python3 -c "import codex.mcp_server"

# Check permissions
ls -la scripts/startup_wrapper.sh

# Restart service
./install_codex_mcp.sh uninstall && ./install_codex_mcp.sh install
```

**Patterns not found:**
```bash
# Check database
ls -la data/patterns_fts.db

# Reimport patterns
codex import-patterns ~/work/project-init.json

# Test queries
codex query "test" --limit 1
```

**AI integration not working:**
```bash
# Check MCP server
./install_codex_mcp.sh test

# Check Claude Desktop config
cat "$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Restart Claude Desktop
```

## 📚 Documentation

- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation guide
- **[CLAUDE.md](CLAUDE.md)** - AI assistant instructions
- **[docs/](docs/)** - Technical documentation
- **[config/](config/)** - Configuration examples

## 🏆 Key Benefits

✅ **Instant Pattern Intelligence** - Sub-millisecond pattern queries
✅ **AI Assistant Ready** - Direct MCP integration with Claude Desktop
✅ **Zero Configuration** - Auto-startup service with one-command install
✅ **Production Proven** - Handles 2,400+ line pattern files efficiently
✅ **Cross-Platform** - macOS launchd and Linux systemd support
✅ **Extensible** - Easy pattern addition and custom rule creation
✅ **Team Friendly** - Shared pattern databases and compliance reporting
✅ **Developer Focused** - CLI-first design with comprehensive tooling

---

**Get started in 30 seconds:**
```bash
./install_codex_mcp.sh install
codex query "HTTP client"
```

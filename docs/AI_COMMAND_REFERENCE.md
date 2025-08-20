# Codex CLI - AI Assistant Command Reference

This reference is optimized for AI assistants to quickly discover and use Codex commands effectively.

## 🤖 Quick AI Discovery

**When an AI assistant needs to help with coding patterns, use these commands:**

### **Instant Pattern Lookup**
```bash
codex query "<what you need>"
```
Examples:
- `codex query "HTTP client"` → httpx recommendations
- `codex query "error handling"` → exception patterns  
- `codex query "ruff TRY401"` → exact fix for ruff error

### **File-Specific Context**
```bash
codex context --file <filepath> --ai
```
Examples:
- `codex context --file src/api.py --ai` → API patterns (httpx, pydantic, FastAPI)
- `codex context --file tests/test_client.py --ai` → Testing patterns (pytest, DI)
- `codex context --file setup.py --ai` → Package management (UV, dependencies)

### **Code Validation**
```bash
codex validate --code "<code snippet>"
```
Examples:
- `codex validate --code "import requests"` → Suggests httpx instead
- `codex validate --code "pip install httpx"` → Suggests UV instead
- `codex validate --code "logging.exception(f'Error: {e}')"` → Shows TRY401 fix

## 📋 Complete Command Matrix

### **Pattern Discovery Commands**

| Command | Purpose | AI Use Case | Example |
|---------|---------|-------------|---------|
| `codex query "<search>"` | Natural language pattern search | Find relevant patterns for any coding task | `codex query "async database"` |
| `codex context --file <path>` | File-specific recommendations | Get patterns for current file being edited | `codex context --file src/api.py` |
| `codex context --intent "<intent>"` | Intent-based discovery | Find patterns based on what user wants to do | `codex context --intent "handle errors"` |
| `codex context --category <cat>` | Browse by category | Explore specific pattern categories | `codex context --category security` |
| `codex explain <pattern>` | Detailed pattern info | Get comprehensive pattern explanation | `codex explain use-httpx` |

### **Code Quality Commands**

| Command | Purpose | AI Use Case | Example |
|---------|---------|-------------|---------|
| `codex validate <file>` | File validation | Check if file follows patterns | `codex validate src/main.py` |
| `codex validate --code "<code>"` | Snippet validation | Validate generated code | `codex validate --code "import requests"` |
| `codex scan` | Full project scan | Check entire project compliance | `codex --quiet` |
| `codex scan --fix` | Auto-fix violations | Fix pattern violations automatically | `codex --fix src/` |

### **Pattern Management Commands**

| Command | Purpose | AI Use Case | Example |
|---------|---------|-------------|---------|
| `codex import-patterns <file>` | Import new patterns | Add organization's patterns | `codex import-patterns company.json` |
| `codex export --format <fmt>` | Export patterns | Share or backup patterns | `codex export --format markdown` |
| `codex patterns --list` | List all patterns | Browse available patterns | `codex patterns --category tools` |
| `codex stats` | Usage statistics | See pattern usage analytics | `codex stats` |

### **Service Management Commands**

| Command | Purpose | AI Use Case | Example |
|---------|---------|-------------|---------|
| `codex startup-status` | Check service status | Troubleshoot integration issues | `codex startup-status` |
| `codex serve --mcp` | Start MCP server | Manual server startup | `codex serve --mcp` |
| `codex install-startup` | Install auto-startup | Set up automatic service | `codex install-startup --user` |

## 🎯 AI Assistant Use Cases

### **1. Code Generation Support**
**Scenario**: AI is writing code and needs to follow best practices

```bash
# Before generating HTTP client code
codex query "HTTP client best practices" --ai

# Before writing error handling
codex query "error handling patterns" --ai

# Before adding dependencies  
codex query "package management" --ai
```

### **2. Code Review and Validation**
**Scenario**: AI is reviewing or validating user's code

```bash
# Check specific code snippet
codex validate --code "import requests; r = requests.get(url)"

# Validate entire file
codex validate src/client.py

# Get patterns for file type
codex context --file src/api.py --ai
```

### **3. Error Resolution**
**Scenario**: User has linting errors or wants to fix code issues

```bash
# Specific ruff error
codex explain ruff-TRY401 --ai

# General error type
codex query "logging exception errors" --ai

# Pattern-specific help
codex explain use-httpx --ai
```

### **4. Learning and Discovery**
**Scenario**: User wants to learn about patterns or best practices

```bash
# Explore category
codex context --category core_libraries --ai

# Intent-based discovery
codex context --intent "writing tests" --ai

# See what's available
codex patterns --list
```

### **5. Project Setup**
**Scenario**: Setting up new project or adding features

```bash
# Initialize with patterns
codex init --import ~/company-standards.json

# Check current project status
codex scan --format json

# Get project-wide context
codex context --category package_management --ai
```

## 🔍 Pattern Query Strategies for AI

### **Effective Query Patterns**

#### **Technology-Specific Queries**
```bash
codex query "HTTP client"        # → httpx patterns
codex query "async database"     # → aiosqlite, SQLModel patterns  
codex query "CLI interface"      # → typer patterns
codex query "API validation"     # → pydantic patterns
```

#### **Problem-Specific Queries**
```bash
codex query "error handling"     # → exception patterns
codex query "dependency injection" # → DI patterns
codex query "testing async code" # → pytest-asyncio patterns
codex query "security patterns" # → SQL injection prevention
```

#### **Tool-Specific Queries**
```bash
codex query "ruff configuration" # → ruff setup patterns
codex query "mypy strict mode"   # → mypy patterns
codex query "pytest fixtures"    # → test patterns
```

#### **Error-Code Queries**
```bash
codex query "ruff TRY401"       # → exact fix for TRY401
codex query "mypy type errors"  # → typing patterns
codex query "B008 errors"       # → ruff B008 fixes
```

### **Context Query Strategies**

#### **File-Type Context**
```bash
codex context --file src/api.py          # → API patterns
codex context --file tests/test_*.py     # → testing patterns
codex context --file setup.py            # → packaging patterns
codex context --file Dockerfile          # → deployment patterns
```

#### **Intent-Based Context**
```bash
codex context --intent "making HTTP requests"    # → httpx patterns
codex context --intent "handling user input"     # → validation patterns
codex context --intent "storing data"            # → database patterns
codex context --intent "deploying application"   # → deployment patterns
```

#### **Category-Based Context**
```bash
codex context --category package_management   # → UV, dependencies
codex context --category core_libraries       # → httpx, pydantic, etc.
codex context --category quality_tools        # → ruff, mypy, pytest
codex context --category security             # → security patterns
```

## 💡 AI Integration Tips

### **Response Formatting**
Always use `--ai` flag for AI-friendly markdown output:
```bash
codex query "HTTP client" --ai
codex context --file src/api.py --ai  
codex explain use-httpx --ai
```

### **Contextual Awareness**
Combine multiple approaches for comprehensive context:
```bash
# Get file-specific + general patterns
codex context --file src/api.py --ai
codex query "FastAPI best practices" --ai
```

### **Error Resolution Flow**
1. **Identify error**: User provides error message or code
2. **Query specific fix**: `codex query "ruff TRY401" --ai`
3. **Get broader context**: `codex context --intent "error handling" --ai`
4. **Validate solution**: `codex validate --code "fixed_code"`

### **Code Generation Flow**
1. **Get context**: `codex context --file current_file.py --ai`
2. **Query specific patterns**: `codex query "specific_need" --ai`
3. **Generate code**: Apply patterns to code generation
4. **Validate result**: `codex validate --code "generated_code"`

## 🚀 Quick Reference for Common Tasks

### **HTTP Client Implementation**
```bash
codex query "HTTP client" --ai
# Returns: use-httpx with async examples
```

### **Error Handling Setup**
```bash
codex query "error handling" --ai
# Returns: exception patterns, logging best practices
```

### **Package Management**
```bash
codex query "package management" --ai
# Returns: UV over pip/poetry patterns
```

### **API Development**
```bash
codex context --intent "building API" --ai
# Returns: FastAPI, pydantic, httpx patterns
```

### **Testing Setup**
```bash
codex context --intent "writing tests" --ai
# Returns: pytest, dependency injection patterns
```

### **Code Quality Check**
```bash
codex validate src/main.py
# Returns: violations with specific fixes
```

### **Project Standards**
```bash
codex export --format markdown
# Returns: all patterns in readable format
```

## 🔧 Advanced AI Usage

### **Batch Operations**
```bash
# Check multiple files
for file in src/*.py; do codex validate "$file"; done

# Query multiple patterns
codex query "HTTP" --ai && codex query "database" --ai
```

### **Integration with Code Generation**
```python
# Pseudo-code for AI integration
def generate_code_with_patterns(intent):
    # Get relevant patterns
    patterns = run_command(f"codex context --intent '{intent}' --ai")
    
    # Generate code using patterns
    code = generate_with_patterns(patterns)
    
    # Validate against patterns
    validation = run_command(f"codex validate --code '{code}'")
    
    return code, validation
```

### **Pipeline Integration**
```bash
# Pre-commit validation
codex --quiet || exit 1

# CI/CD compliance check  
codex scan --format json > compliance.json

# Pattern export for team
codex export --format markdown > team-standards.md
```

## 📊 Output Formats

### **AI-Friendly Format (`--ai` flag)**
- Clean markdown output
- Structured sections (Rule, Why, Fix, Examples)
- No color codes or special formatting
- Optimized for parsing and understanding

### **Human Format (default)**
- Rich terminal output with colors
- Emojis and visual formatting
- Interactive-friendly display

### **JSON Format (`--format json`)**
- Machine-readable structured data
- Perfect for programmatic processing
- Includes all metadata and details

### **Validation Output**
- Clear violation descriptions
- Specific line numbers
- Exact fix recommendations
- Compliance scores

This reference enables AI assistants to effectively use Codex for pattern discovery, code validation, and best practice enforcement in real-time coding assistance.
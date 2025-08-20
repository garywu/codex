# Codex Usage Examples

This document provides practical examples of using Codex for different scenarios and user types.

## 🧑‍💻 Developer Examples

### Daily Development Workflow

#### 1. Starting a New Feature
```bash
# Get context for the file you're working on
codex context --file src/api/users.py --ai

# Query specific patterns you need
codex query "FastAPI dependency injection" --ai
codex query "pydantic validation" --ai

# Validate your implementation
codex validate src/api/users.py
```

#### 2. Fixing Linting Errors
```bash
# Get specific fix for ruff error
codex query "ruff TRY401" --ai
# Returns: Use `logging.exception` without redundant message

# Explain the pattern in detail
codex explain ruff-TRY401 --ai

# Validate the fix
codex validate --code "logging.exception('Database error occurred')"
```

#### 3. Refactoring HTTP Client Code
```bash
# Query best practices
codex query "HTTP client best practices" --ai

# Get specific httpx patterns
codex explain use-httpx --ai

# Validate refactored code
codex validate --code "
import httpx

async def fetch_user(user_id: int) -> User:
    async with httpx.AsyncClient() as client:
        response = await client.get(f'/api/users/{user_id}')
        response.raise_for_status()
        return User.model_validate(response.json())
"
```

#### 4. Setting Up Testing
```bash
# Get testing patterns
codex context --intent "writing tests" --ai

# Query dependency injection for tests
codex query "pytest dependency injection" --ai

# Validate test structure
codex context --file tests/test_api.py --ai
```

### Pre-Commit Workflow
```bash
# Quick scan before commit
codex --quiet && git commit -m "Add user API endpoints" || echo "Fix violations first"

# Fix violations automatically
codex --fix

# Validate specific files
codex validate $(git diff --name-only --cached | grep '\.py$')
```

## 🤖 AI Assistant Examples

### Code Generation Support

#### 1. HTTP Client Implementation
**AI Request**: "I need to make HTTP requests in Python"

**Codex Query**:
```bash
codex query "HTTP client" --ai
```

**Result**: Returns use-httpx pattern with async examples, performance benefits, and error handling.

#### 2. Error Handling Implementation
**AI Request**: "How should I handle exceptions in this API endpoint?"

**Codex Query**:
```bash
codex context --file src/api/endpoint.py --ai
codex query "error handling patterns" --ai
```

**Result**: Returns exception handling patterns, logging best practices, and HTTP error responses.

#### 3. Database Integration
**AI Request**: "What's the best way to work with databases in Python?"

**Codex Query**:
```bash
codex query "async database" --ai
codex explain use-sqlmodel --ai
```

**Result**: Returns SQLModel patterns, async database operations, and connection management.

### Code Review and Validation

#### 1. Reviewing Generated Code
**AI Generated Code**:
```python
import requests

def get_user(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()
```

**Codex Validation**:
```bash
codex validate --code "import requests

def get_user(user_id):
    response = requests.get(f\"https://api.example.com/users/{user_id}\")
    return response.json()"
```

**Result**: Suggests using httpx instead of requests, adds error handling, type hints.

#### 2. Pattern-Specific Validation
```bash
# Check for specific anti-patterns
codex validate --code "eval(user_input)" 
# Returns: Security violation - never use eval() with user input

codex validate --code "pip install httpx"
# Returns: Use UV instead of pip for package management
```

### Intent-Based Discovery

#### 1. Building an API
**AI Intent**: "I want to build a REST API"

**Codex Query**:
```bash
codex context --intent "building API" --ai
```

**Result**: Returns FastAPI patterns, pydantic models, dependency injection, error handling.

#### 2. Adding Security
**AI Intent**: "I need to secure my application"

**Codex Query**:
```bash
codex context --category security --ai
codex query "SQL injection prevention" --ai
```

**Result**: Returns input validation, parameterized queries, authentication patterns.

## 👥 Team Examples

### Onboarding New Developers

#### 1. Learning Project Standards
```bash
# Export current patterns as documentation
codex export --format markdown > team-standards.md

# Get overview of all patterns
codex patterns --list

# Explore specific categories
codex context --category package_management --ai
codex context --category core_libraries --ai
```

#### 2. Setting Up Development Environment
```bash
# Initialize project with patterns
codex init --import company-patterns.json

# Check what patterns apply to current work
codex context --file src/main.py --ai

# Validate understanding with examples
codex validate examples/good_practices.py
```

### Code Review Process

#### 1. Automated Pattern Checking
```bash
# Pre-commit hook integration
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

#### 2. Review Guidelines
```bash
# Generate compliance report
codex scan --format json > pr-compliance.json

# Check specific patterns
codex check use-httpx src/
codex check dependency-injection tests/

# Export violations summary
codex scan --quiet || codex scan --format markdown > violations.md
```

### Pattern Evolution

#### 1. Adding New Patterns
```bash
# Import from multiple sources
codex import-patterns company-standards.json
codex import-patterns team-specific.json
codex import-patterns project-init.json

# Test new patterns
codex query "new pattern" --limit 1
codex validate test-file.py
```

#### 2. Usage Analytics
```bash
# Track pattern usage
codex stats

# Monitor most violated patterns
grep "violation" logs/codex-mcp.log | sort | uniq -c | sort -nr

# Export usage data
codex export --format json --stats > pattern-usage.json
```

## 🚀 CI/CD Examples

### GitHub Actions Integration

#### 1. Pattern Compliance Check
```yaml
# .github/workflows/codex.yml
name: Codex Pattern Check
on: [push, pull_request]

jobs:
  pattern-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Codex
        run: |
          pip install -e .
          codex import-patterns .github/patterns.json
          
      - name: Run Pattern Check
        run: codex --quiet
        
      - name: Generate Compliance Report
        if: failure()
        run: |
          codex scan --format json > compliance-report.json
          
      - name: Upload Report
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: compliance-report
          path: compliance-report.json
```

#### 2. Pattern-Specific Checks
```yaml
- name: Check Security Patterns
  run: codex check security-patterns src/
  
- name: Check HTTP Client Usage
  run: codex check use-httpx src/

- name: Validate Dependencies
  run: codex validate requirements.txt
```

### Pre-Commit Integration

#### 1. Basic Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: codex-scan
        name: Codex Pattern Scanner
        entry: codex
        language: system
        pass_filenames: true
        args: ['--quiet']
        
      - id: codex-fix
        name: Codex Auto-Fix
        entry: codex
        language: system
        pass_filenames: true
        args: ['--fix', '--quiet']
```

#### 2. Staged Files Only
```bash
# Custom pre-commit script
#!/bin/bash
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
if [ ! -z "$staged_files" ]; then
    codex validate $staged_files --quiet
fi
```

### Docker Integration

#### 1. Container with Codex
```dockerfile
FROM python:3.11-slim

# Install Codex
COPY . /app/codex
RUN pip install -e /app/codex

# Import patterns
COPY patterns.json /app/patterns.json
RUN codex import-patterns /app/patterns.json

# Set up entry point
WORKDIR /app
ENTRYPOINT ["codex"]
```

#### 2. CI Container Usage
```bash
# Build pattern-checking container
docker build -t codex-checker .

# Use in CI
docker run --rm -v $(pwd):/code codex-checker scan /code --format json
```

## 📱 IDE Integration Examples

### VS Code Integration

#### 1. Task Configuration
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Codex: Query Patterns",
      "type": "shell",
      "command": "codex",
      "args": ["query", "${input:query}", "--ai"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Codex: Validate Current File",
      "type": "shell",
      "command": "codex",
      "args": ["validate", "${file}"],
      "group": "build"
    },
    {
      "label": "Codex: Get File Context",
      "type": "shell",
      "command": "codex",
      "args": ["context", "--file", "${file}", "--ai"],
      "group": "build"
    }
  ],
  "inputs": [
    {
      "id": "query",
      "description": "Pattern search query",
      "default": "HTTP client",
      "type": "promptString"
    }
  ]
}
```

#### 2. Keyboard Shortcuts
```json
{
  "key": "ctrl+shift+p",
  "command": "workbench.action.tasks.runTask",
  "args": "Codex: Query Patterns"
},
{
  "key": "ctrl+shift+v",
  "command": "workbench.action.tasks.runTask", 
  "args": "Codex: Validate Current File"
}
```

### Neovim Integration

#### 1. Lua Configuration
```lua
-- ~/.config/nvim/lua/codex.lua
local M = {}

function M.query_patterns()
  local query = vim.fn.input("Pattern query: ")
  if query ~= "" then
    local result = vim.fn.systemlist("codex query '" .. query .. "' --ai")
    vim.api.nvim_buf_set_lines(0, -1, -1, false, result)
  end
end

function M.validate_file()
  local file = vim.fn.expand("%:p")
  local result = vim.fn.systemlist("codex validate '" .. file .. "'")
  print(table.concat(result, "\n"))
end

function M.get_context()
  local file = vim.fn.expand("%:p")
  local result = vim.fn.systemlist("codex context --file '" .. file .. "' --ai")
  vim.api.nvim_buf_set_lines(0, -1, -1, false, result)
end

-- Key mappings
vim.keymap.set('n', '<leader>cq', M.query_patterns, {desc = 'Codex query patterns'})
vim.keymap.set('n', '<leader>cv', M.validate_file, {desc = 'Codex validate file'})
vim.keymap.set('n', '<leader>cc', M.get_context, {desc = 'Codex get context'})

return M
```

## 🔍 Advanced Usage Examples

### Custom Pattern Development

#### 1. Creating New Patterns
```json
{
  "name": "use-custom-logger",
  "description": "Use company's custom logging framework",
  "category": "logging",
  "priority": "mandatory",
  "detection_rules": [
    {
      "type": "import_forbidden",
      "pattern": "import logging",
      "message": "Use company.logging instead of standard logging"
    }
  ],
  "fix_template": "from company.logging import get_logger\nlogger = get_logger(__name__)",
  "examples": [
    {
      "good": "from company.logging import get_logger\nlogger = get_logger(__name__)",
      "bad": "import logging\nlogger = logging.getLogger(__name__)"
    }
  ]
}
```

#### 2. Testing New Patterns
```bash
# Add to patterns file
codex import-patterns custom-patterns.json

# Test detection
codex validate --code "import logging"

# Test query
codex query "custom logger" --ai

# Verify fix template
codex explain use-custom-logger --ai
```

### Batch Operations

#### 1. Bulk File Processing
```bash
# Validate all Python files
find src/ -name "*.py" -exec codex validate {} \;

# Apply fixes to all files
find src/ -name "*.py" -exec codex --fix {} \;

# Generate reports for each directory
for dir in src/ tests/ scripts/; do
  codex scan "$dir" --format json > "report-$(basename "$dir").json"
done
```

#### 2. Pattern Migration
```bash
# Export old patterns
codex export --format json > old-patterns.json

# Import new patterns
codex import-patterns new-patterns.json

# Validate migration
codex scan --diff old-patterns.json
```

### Performance Optimization

#### 1. Large Codebase Scanning
```bash
# Parallel scanning
find src/ -name "*.py" | xargs -P 8 -I {} codex validate {}

# Exclude large files
codex scan --exclude "*.min.js" --exclude "vendor/*"

# Focus on specific patterns
codex check security-patterns src/ --parallel
```

#### 2. Monitoring Usage
```bash
# Monitor query performance
tail -f logs/codex-mcp.log | grep "Query time"

# Track database growth
watch -n 60 'ls -lh data/patterns_fts.db'

# Memory usage monitoring
ps aux | grep codex.mcp_server
```

## 🎓 Learning Examples

### Pattern Discovery Workshop

#### 1. Explore Available Patterns
```bash
# Get overview
codex patterns --list | head -20

# Explore by category
codex context --category core_libraries --ai
codex context --category quality_tools --ai
codex context --category security --ai

# Search for specific topics
codex query "async" --limit 10
codex query "testing" --limit 10
codex query "security" --limit 10
```

#### 2. Interactive Learning
```bash
# Learn about specific patterns
codex explain use-httpx --ai
codex explain dependency-injection-constructor --ai
codex explain ruff-TRY401 --ai

# Compare approaches
codex query "HTTP client" --ai
codex query "requests vs httpx" --ai

# Understand violations
codex validate --code "import requests" 
codex validate --code "eval(user_input)"
```

### Team Training Scenarios

#### 1. Code Review Training
```bash
# Create examples of good/bad code
echo "import requests\nresponse = requests.get(url)" > bad_example.py
echo "import httpx\nasync with httpx.AsyncClient() as client:\n    response = await client.get(url)" > good_example.py

# Show violations
codex validate bad_example.py

# Show compliance
codex validate good_example.py

# Explain the differences
codex explain use-httpx --ai
```

#### 2. Pattern Adoption Tracking
```bash
# Track pattern usage over time
codex stats > "stats-$(date +%Y%m%d).json"

# Monitor compliance trends
codex scan --format json > "compliance-$(date +%Y%m%d).json"

# Generate team reports
codex export --format markdown > "team-patterns-$(date +%Y%m%d).md"
```

These examples demonstrate the versatility and power of Codex across different use cases, from individual development to enterprise-scale pattern management.
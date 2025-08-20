"""
import logging
Default patterns for Codex - Version controlled backup.

This module contains all default patterns that should be loaded into
the database on initialization. This ensures patterns are:
1. Version controlled in git
2. Consistent across installations
3. Easily reviewable in code reviews
"""

DEFAULT_PATTERNS = [
    # ============ MANDATORY PATTERNS ============
    {
        "name": "flat-module-structure",
        "category": "organization",
        "priority": "MANDATORY",
        "description": "Use flat module structure with no subdirectories in main package",
        "rule": "Keep all modules in flat structure under main package directory",
        "rationale": "Documented architectural decision for simplicity and maintainability",
        "detection": {
            "keywords": ["__init__.py", "nested", "subdirectory"],
            "regex": ".*/__init__\\.py"
        },
        "fix": {
            "template": "Move modules to flat structure under main package directory",
            "complexity": "medium"
        },
        "examples": {
            "good": "hepha/component.py, hepha/server.py",
            "bad": "hepha/utils/helper.py, hepha/models/user.py"
        },
        "tags": ["architecture", "organization", "flat"]
    },
    {
        "name": "uv-package-manager",
        "category": "dependencies",
        "priority": "MANDATORY",
        "description": "Use UV package manager instead of pip or poetry",
        "rule": "Always use uv commands for package management",
        "rationale": "UV provides faster, more reliable package management",
        "detection": {
            "keywords": ["pip install", "poetry add", "requirements.txt"],
            "regex": "pip\\s+install|poetry\\s+add"
        },
        "fix": {
            "template": "Replace with: uv add <package>",
            "complexity": "simple"
        },
        "examples": {
            "good": "uv add fastapi[all]",
            "bad": "pip install fastapi"
        },
        "tags": ["uv", "dependencies", "package-manager"]
    },
    {
        "name": "zero-tolerance-precommit",
        "category": "ci_cd",
        "priority": "MANDATORY",
        "description": "All pre-commit hook errors must be fixed before commit",
        "rule": "Fix all pre-commit issues, no temporary workarounds allowed",
        "rationale": "Maintains code quality and prevents broken builds",
        "detection": {
            "keywords": ["TODO: fix this later", "FIXME", "HACK", "noqa", "type: ignore"],
            "regex": "#\\s*(TODO|FIXME|HACK):|#\\s*noqa|#\\s*type:\\s*ignore"
        },
        "fix": {
            "template": "Fix all issues before committing",
            "complexity": "medium"
        },
        "examples": {
            "good": "Clean code that passes all hooks",
            "bad": "# TODO: fix this later\\n# noqa: F401"
        },
        "tags": ["quality", "precommit", "ci"]
    },
    {
        "name": "no-bare-except",
        "category": "error_handling",
        "priority": "MANDATORY",
        "description": "Never use bare except: clauses",
        "rule": "Always specify exception types",
        "rationale": "Bare except catches system exits and keyboard interrupts",
        "detection": {
            "keywords": ["except:", "bare except"],
            "regex": "except\\s*:"
        },
        "fix": {
            "template": "except Exception:",
            "complexity": "simple",
            "auto_fixable": True
        },
        "examples": {
            "good": "except ValueError:\\n    handle_error()",
            "bad": "except:\\n    pass"
        },
        "tags": ["error-handling", "python", "mandatory"]
    },
    {
        "name": "secure-jwt-storage",
        "category": "security",
        "priority": "MANDATORY",
        "description": "Store JWT secrets in secure credential manager, never hardcode",
        "rule": "JWT secrets must be in environment variables or secret manager",
        "rationale": "Hardcoded secrets are a critical security vulnerability",
        "detection": {
            "keywords": ["jwt_secret", "JWT_SECRET", "secret_key", "SECRET_KEY"],
            "regex": "(jwt_secret|JWT_SECRET|secret_key|SECRET_KEY)\\s*=\\s*[\"']"
        },
        "fix": {
            "template": "Use os.environ.get('JWT_SECRET')",
            "complexity": "simple"
        },
        "examples": {
            "good": "jwt_secret = os.environ.get('JWT_SECRET')",
            "bad": "jwt_secret = 'hardcoded-secret-key'"
        },
        "tags": ["security", "jwt", "secrets"]
    },
    
    # ============ HIGH PRIORITY PATTERNS ============
    {
        "name": "gh-cli-operations",
        "category": "git",
        "priority": "HIGH",
        "description": "Use gh CLI for GitHub operations instead of git commands",
        "rule": "Use gh CLI for all GitHub operations (PRs, issues, repos)",
        "rationale": "Better integration with GitHub API and consistent workflow",
        "detection": {
            "keywords": ["git push origin", "git pull request"],
            "regex": "git\\s+push\\s+origin|git\\s+pull-request"
        },
        "fix": {
            "template": "Use: gh pr create, gh issue create, gh repo clone",
            "complexity": "simple"
        },
        "examples": {
            "good": "gh pr create --title 'Feature: Add component'",
            "bad": "git push origin feature-branch"
        },
        "tags": ["github", "cli", "workflow"]
    },
    {
        "name": "mock-naming-convention",
        "category": "testing",
        "priority": "HIGH",
        "description": "Mock code must use mock_ prefix for clear identification",
        "rule": "All mock objects and functions must have mock_ prefix",
        "rationale": "Distinguishes test mocks from production code",
        "detection": {
            "keywords": ["def fake_", "class Mock", "def stub_"],
            "regex": "def\\s+(fake_|stub_)|class\\s+Mock(?!_)"
        },
        "fix": {
            "template": "Rename to mock_ prefix: mock_user_data, mock_api_response",
            "complexity": "simple"
        },
        "examples": {
            "good": "mock_user_data = {...}",
            "bad": "fake_user_data = {...}"
        },
        "tags": ["testing", "mocks", "naming"]
    },
    {
        "name": "use-pydantic-validation",
        "category": "validation",
        "priority": "HIGH",
        "description": "Use Pydantic for all API input validation",
        "rule": "All API endpoints must use Pydantic models for validation",
        "rationale": "Provides automatic validation, serialization, and documentation",
        "detection": {
            "keywords": ["fastapi", "request", "validation", "dict", "json.loads"],
            "regex": "@(app|router)\\.(post|put|patch).*dict\\[|json\\.loads"
        },
        "fix": {
            "template": "Create Pydantic model for request body",
            "complexity": "medium"
        },
        "examples": {
            "good": "async def create_user(user: UserCreate):",
            "bad": "async def create_user(data: dict):"
        },
        "tags": ["validation", "api", "pydantic", "fastapi"]
    },
    {
        "name": "structured-logging",
        "category": "logging",
        "priority": "HIGH",
        "description": "Use JSON structured logs with consistent schema",
        "rule": "Use structured logging with key-value pairs",
        "rationale": "Enables better log aggregation and searching",
        "detection": {
            "keywords": ["logger", "logging", "logging.info("],
            "regex": "logger\\.(info|debug|warning|error)\\([^{]|print\\("
        },
        "fix": {
            "template": "logger.info({'event': 'action', 'details': data})",
            "complexity": "medium"
        },
        "examples": {
            "good": "logger.info({'event': 'user_login', 'user_id': user.id})",
            "bad": "logger.info(f'User {user.id} logged in')"
        },
        "tags": ["logging", "structured", "json"]
    },
    {
        "name": "no-print-production",
        "category": "logging",
        "priority": "HIGH",
        "description": "Replace print() with proper logging",
        "rule": "Never use print() in production code",
        "rationale": "Print statements bypass logging infrastructure",
        "detection": {
            "keywords": ["logging.info("],
            "regex": "^\\s*print\\("
        },
        "fix": {
            "template": "logger.info(...)",
            "complexity": "simple",
            "auto_fixable": True
        },
        "examples": {
            "good": "logger.info('Processing started')",
            "bad": "logging.info('Processing started')"
        },
        "tags": ["logging", "production", "quality"]
    }
]

def get_default_patterns():
    """Return a copy of default patterns."""
    import copy
    return copy.deepcopy(DEFAULT_PATTERNS)

def get_patterns_by_priority(priority: str):
    """Get patterns filtered by priority."""
    return [p for p in DEFAULT_PATTERNS if p.get("priority") == priority]

def get_patterns_by_category(category: str):
    """Get patterns filtered by category."""
    return [p for p in DEFAULT_PATTERNS if p.get("category") == category]
"""
Codex Scan Rules - Custom scanning rules based on collected patterns.

This module defines Codex's own scanning rules that enforce best practices
we've learned from analyzing codebases. These are first-class rules that
complement external tools like Ruff, ty, and typos.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .pattern_models import PatternMatch
from .scan_registry import BaseScan, ScanCategory, ScanDefinition, ScanResult, ScanSeverity


class CodexRuleCategory(str, Enum):
    """Categories for Codex-specific rules."""

    SETTINGS = "settings"  # Pydantic settings, configuration
    DATABASE = "database"  # Database patterns
    DEPENDENCIES = "dependencies"  # Package management
    SECURITY = "security"  # Security patterns
    ARCHITECTURE = "architecture"  # Code structure
    TESTING = "testing"  # Test patterns
    LOGGING = "logging"  # Logging patterns
    API = "api"  # API patterns


@dataclass
class CodexRule:
    """Definition of a Codex scanning rule."""

    code: str  # Rule code (e.g., CDX001)
    name: str  # Short name
    category: CodexRuleCategory  # Rule category
    severity: ScanSeverity  # Severity level
    description: str  # What this rule detects
    rationale: str  # Why this matters
    detection_patterns: list[tuple[str, str]]  # (pattern, message) pairs
    fix_template: str | None = None
    examples: dict[str, str] = field(default_factory=dict)  # good/bad examples
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


class CodexRuleRegistry:
    """Registry of all Codex scanning rules."""

    # Define all Codex rules based on patterns we've collected
    RULES = [
        # Settings Rules (CDX001-CDX010)
        CodexRule(
            code="CDX001",
            name="use-pydantic-settings",
            category=CodexRuleCategory.SETTINGS,
            severity=ScanSeverity.HIGH,
            description="Use Pydantic Settings for configuration management",
            rationale="Pydantic Settings provides type-safe configuration with validation",
            detection_patterns=[
                (r"config\s*=\s*\{.*\}", "Hardcoded config dict - use Pydantic Settings"),
                (r'os\.environ\.get\(["\']', "Direct environ access - use Pydantic Settings"),
                (r"config\s*=\s*ConfigParser\(\)", "ConfigParser - use Pydantic Settings"),
            ],
            fix_template="from pydantic_settings import BaseSettings\n\nclass Settings(BaseSettings):\n    ...",
            examples={
                "good": "from pydantic_settings import BaseSettings\nclass Settings(BaseSettings):\n    api_key: str",
                "bad": "config = {'api_key': os.environ.get('API_KEY', 'default')}",
            },
            tags=["configuration", "pydantic", "settings"],
        ),
        CodexRule(
            code="CDX002",
            name="single-settings-source",
            category=CodexRuleCategory.SETTINGS,
            severity=ScanSeverity.HIGH,
            description="Use single settings instance across codebase",
            rationale="Multiple settings instances lead to inconsistency",
            detection_patterns=[
                (r"Settings\(\)", "Creating new Settings instance - use shared settings"),
                (r"BaseSettings\(\)", "Direct BaseSettings instantiation"),
            ],
            fix_template="from .settings import settings  # Use shared instance",
            examples={
                "good": "from .settings import settings\ndb_path = settings.database_path",
                "bad": "settings = Settings()\ndb_path = settings.database_path",
            },
            tags=["configuration", "singleton", "consistency"],
        ),
        CodexRule(
            code="CDX003",
            name="no-hardcoded-paths",
            category=CodexRuleCategory.SETTINGS,
            severity=ScanSeverity.HIGH,
            description="Don't hardcode file paths",
            rationale="Hardcoded paths break portability and deployment",
            detection_patterns=[
                (r'Path\(["\']/', "Hardcoded absolute path"),
                (r'["\']~/\.', "Hardcoded home directory path"),
                (r'\.db["\']', "Hardcoded database file"),
                (r'data_dir\s*=\s*["\']', "Hardcoded data directory"),
            ],
            fix_template="Use settings.data_dir / settings.config_dir / etc.",
            tags=["paths", "portability"],
        ),
        # Database Rules (CDX011-CDX020)
        CodexRule(
            code="CDX011",
            name="use-context-managers",
            category=CodexRuleCategory.DATABASE,
            severity=ScanSeverity.HIGH,
            description="Always use context managers for database sessions",
            rationale="Prevents connection leaks and ensures proper cleanup",
            detection_patterns=[
                (r"session\s*=.*Session\(\)(?!\s*with)", "Session without context manager"),
                (r"conn\s*=.*connect\(\)(?!\s*with)", "Connection without context manager"),
            ],
            fix_template="with get_db_session() as session:\n    ...",
            examples={
                "good": "with get_db_session() as session:\n    result = session.query(User).all()",
                "bad": "session = SessionLocal()\nresult = session.query(User).all()",
            },
            tags=["database", "context-manager", "resource-management"],
        ),
        CodexRule(
            code="CDX012",
            name="single-database-module",
            category=CodexRuleCategory.DATABASE,
            severity=ScanSeverity.HIGH,
            description="Use single database module for consistency",
            rationale="Multiple database modules lead to inconsistent state",
            detection_patterns=[
                (r"from\s+\.\s*database\s+import", "Using old database module"),
                (r"from\s+\.\s*fts_database\s+import", "Using old FTS database module"),
            ],
            fix_template="from .unified_database import UnifiedDatabase",
            tags=["database", "consistency"],
        ),
        # Dependency Rules (CDX021-CDX030)
        CodexRule(
            code="CDX021",
            name="pin-production-deps",
            category=CodexRuleCategory.DEPENDENCIES,
            severity=ScanSeverity.HIGH,
            description="Pin exact versions for production dependencies",
            rationale="Ensures reproducible deployments",
            detection_patterns=[
                (r'["\'][\w-]+>=\d+\.', "Unpinned dependency version"),
                (r'["\'][\w-]+~=\d+\.', "Range dependency version"),
            ],
            fix_template="package==1.2.3  # Pin exact version",
            tags=["dependencies", "reproducibility"],
        ),
        CodexRule(
            code="CDX022",
            name="use-uv-package-manager",
            category=CodexRuleCategory.DEPENDENCIES,
            severity=ScanSeverity.MEDIUM,
            description="Use uv for package management",
            rationale="uv is 10-100x faster than pip",
            detection_patterns=[
                (r"pip install", "Using pip instead of uv"),
                (r"pip freeze", "Using pip freeze instead of uv"),
            ],
            fix_template="uv pip install ...",
            tags=["dependencies", "performance", "uv"],
        ),
        # Security Rules (CDX031-CDX040)
        CodexRule(
            code="CDX031",
            name="no-eval-exec",
            category=CodexRuleCategory.SECURITY,
            severity=ScanSeverity.CRITICAL,
            description="Never use eval() or exec()",
            rationale="Code injection vulnerability",
            detection_patterns=[
                (r"eval\s*\(", "eval() is dangerous"),
                (r"exec\s*\(", "exec() is dangerous"),
            ],
            fix_template="Use ast.literal_eval() or refactor",
            tags=["security", "injection"],
        ),
        CodexRule(
            code="CDX032",
            name="no-hardcoded-secrets",
            category=CodexRuleCategory.SECURITY,
            severity=ScanSeverity.CRITICAL,
            description="Don't hardcode secrets or API keys",
            rationale="Secrets in code are security vulnerabilities",
            detection_patterns=[
                (r'api_key\s*=\s*["\'][A-Za-z0-9]{20,}', "Hardcoded API key"),
                (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
                (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
                (r'token\s*=\s*["\'][A-Za-z0-9]{20,}', "Hardcoded token"),
            ],
            fix_template="Use environment variables or secrets management",
            tags=["security", "secrets"],
        ),
        # Architecture Rules (CDX041-CDX050)
        CodexRule(
            code="CDX041",
            name="no-circular-imports",
            category=CodexRuleCategory.ARCHITECTURE,
            severity=ScanSeverity.HIGH,
            description="Avoid circular imports",
            rationale="Circular imports cause initialization problems",
            detection_patterns=[
                (r"from\s+\.\s+import.*#.*circular", "Possible circular import"),
            ],
            fix_template="Refactor to remove circular dependency",
            tags=["architecture", "imports"],
        ),
        CodexRule(
            code="CDX042",
            name="consistent-imports",
            category=CodexRuleCategory.ARCHITECTURE,
            severity=ScanSeverity.MEDIUM,
            description="Use consistent import style",
            rationale="Consistency improves readability",
            detection_patterns=[
                (r"from\s+\w+\s+import\s+\*", "Avoid wildcard imports"),
            ],
            fix_template="Import specific names: from module import name1, name2",
            tags=["architecture", "imports", "style"],
        ),
        # Testing Rules (CDX051-CDX060)
        CodexRule(
            code="CDX051",
            name="use-pytest-fixtures",
            category=CodexRuleCategory.TESTING,
            severity=ScanSeverity.MEDIUM,
            description="Use pytest fixtures for test setup",
            rationale="Fixtures provide better test isolation",
            detection_patterns=[
                (r"def\s+setUp\s*\(self\)", "Use pytest fixtures instead of setUp"),
                (r"unittest\.TestCase", "Use pytest instead of unittest"),
            ],
            fix_template="@pytest.fixture\ndef setup():\n    ...",
            tags=["testing", "pytest"],
        ),
        # Logging Rules (CDX061-CDX070)
        CodexRule(
            code="CDX061",
            name="centralized-logging",
            category=CodexRuleCategory.LOGGING,
            severity=ScanSeverity.MEDIUM,
            description="Use centralized logging configuration",
            rationale="Ensures consistent logging across application",
            detection_patterns=[
                (r"logging\.basicConfig\(", "Use centralized logging config"),
                (r"logging\.getLogger\(\)\.setLevel", "Setting logger level directly"),
            ],
            fix_template="from .logging_config import logger",
            tags=["logging", "configuration"],
        ),
        CodexRule(
            code="CDX062",
            name="structured-logging",
            category=CodexRuleCategory.LOGGING,
            severity=ScanSeverity.LOW,
            description="Use structured logging",
            rationale="Structured logs are easier to query and analyze",
            detection_patterns=[
                (r"print\s*\(", "Use logger instead of print"),
                (r'logger\.info\s*\(f["\']', "Use structured logging with extra"),
            ],
            fix_template='logger.info("message", extra={"key": "value"})',
            tags=["logging", "observability"],
        ),
        # API Rules (CDX071-CDX080)
        CodexRule(
            code="CDX071",
            name="use-pydantic-validation",
            category=CodexRuleCategory.API,
            severity=ScanSeverity.HIGH,
            description="Use Pydantic for API input validation",
            rationale="Pydantic provides automatic validation with clear errors",
            detection_patterns=[
                (r"request\.json\[", "Direct JSON access - use Pydantic model"),
                (r"if\s+not\s+.*in\s+request\.json", "Manual validation - use Pydantic"),
            ],
            fix_template="class RequestModel(BaseModel):\n    field: str",
            tags=["api", "validation", "pydantic"],
        ),
        CodexRule(
            code="CDX072",
            name="explicit-status-codes",
            category=CodexRuleCategory.API,
            severity=ScanSeverity.MEDIUM,
            description="Use explicit HTTP status codes",
            rationale="Magic numbers reduce readability",
            detection_patterns=[
                (r"return.*,\s*200\)", "Use HTTPStatus.OK"),
                (r"return.*,\s*404\)", "Use HTTPStatus.NOT_FOUND"),
                (r"return.*,\s*500\)", "Use HTTPStatus.INTERNAL_SERVER_ERROR"),
            ],
            fix_template="from http import HTTPStatus\nreturn data, HTTPStatus.OK",
            tags=["api", "http", "readability"],
        ),
    ]

    @classmethod
    def get_rule(cls, code: str) -> CodexRule | None:
        """Get a rule by its code."""
        for rule in cls.RULES:
            if rule.code == code:
                return rule
        return None

    @classmethod
    def get_rules_by_category(cls, category: CodexRuleCategory) -> list[CodexRule]:
        """Get all rules in a category."""
        return [r for r in cls.RULES if r.category == category]

    @classmethod
    def get_enabled_rules(cls) -> list[CodexRule]:
        """Get all enabled rules."""
        return [r for r in cls.RULES if r.enabled]


class CodexRuleScan(BaseScan):
    """Scanner that checks Codex-specific rules."""

    def __init__(self, rule: CodexRule, definition: ScanDefinition):
        super().__init__(definition)
        self.rule = rule

    async def scan_file(self, file_path: Path, content: str) -> list[PatternMatch]:
        """Scan a file for rule violations."""
        violations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Skip comments and docstrings
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue

            # Check each detection pattern
            for pattern, message in self.rule.detection_patterns:
                if re.search(pattern, line):
                    violations.append(
                        self.create_match(
                            file_path=file_path,
                            line_number=line_num,
                            matched_code=line.strip(),
                            message=f"{self.rule.code}: {message}",
                            fix_suggestion=self.rule.fix_template,
                        )
                    )
                    break  # Only report first match per line

        return violations

    async def scan_directory(self, directory: Path) -> ScanResult:
        """Scan directory for rule violations."""
        from datetime import datetime

        self.start_time = datetime.utcnow()
        all_violations = []
        files_scanned = 0

        # Scan Python files
        for py_file in directory.rglob("*.py"):
            # Skip test files if not testing rule
            if "test" in py_file.name and self.rule.category != CodexRuleCategory.TESTING:
                continue

            # Skip migrations
            if "migration" in py_file.name:
                continue

            # Skip virtual environments
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                violations = await self.scan_file(py_file, content)
                all_violations.extend(violations)
                files_scanned += 1
            except (OSError, UnicodeDecodeError):
                continue

        self.end_time = datetime.utcnow()
        duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

        return ScanResult(
            scan_id=self.scan_id,
            timestamp=self.start_time,
            repository_path=str(directory),
            files_scanned=files_scanned,
            patterns_checked=len(self.rule.detection_patterns),
            violations=all_violations,
            duration_ms=duration_ms,
            confidence_avg=1.0 if all_violations else None,
        )


class CodexScanManager:
    """Manager for Codex-specific scans."""

    @classmethod
    def create_scan_definitions(cls) -> list[ScanDefinition]:
        """Create scan definitions for all Codex rules."""
        definitions = []

        for rule in CodexRuleRegistry.get_enabled_rules():
            # Map category to scan category
            category_map = {
                CodexRuleCategory.SETTINGS: ScanCategory.CONSISTENCY,
                CodexRuleCategory.DATABASE: ScanCategory.CONSISTENCY,
                CodexRuleCategory.DEPENDENCIES: ScanCategory.QUALITY,
                CodexRuleCategory.SECURITY: ScanCategory.SECURITY,
                CodexRuleCategory.ARCHITECTURE: ScanCategory.ARCHITECTURE,
                CodexRuleCategory.TESTING: ScanCategory.QUALITY,
                CodexRuleCategory.LOGGING: ScanCategory.QUALITY,
                CodexRuleCategory.API: ScanCategory.QUALITY,
            }

            definition = ScanDefinition(
                id=f"codex-{rule.code.lower()}",
                name=rule.name,
                description=rule.description,
                category=category_map[rule.category],
                severity=rule.severity,
                enabled=rule.enabled,
                tags=rule.tags,
            )
            definitions.append(definition)

        return definitions

    @classmethod
    def create_scan(cls, rule_code: str) -> CodexRuleScan | None:
        """Create a scan for a specific rule."""
        rule = CodexRuleRegistry.get_rule(rule_code)
        if not rule:
            return None

        # Create scan definition
        category_map = {
            CodexRuleCategory.SETTINGS: ScanCategory.CONSISTENCY,
            CodexRuleCategory.DATABASE: ScanCategory.CONSISTENCY,
            CodexRuleCategory.DEPENDENCIES: ScanCategory.QUALITY,
            CodexRuleCategory.SECURITY: ScanCategory.SECURITY,
            CodexRuleCategory.ARCHITECTURE: ScanCategory.ARCHITECTURE,
            CodexRuleCategory.TESTING: ScanCategory.QUALITY,
            CodexRuleCategory.LOGGING: ScanCategory.QUALITY,
            CodexRuleCategory.API: ScanCategory.QUALITY,
        }

        definition = ScanDefinition(
            id=f"codex-{rule.code.lower()}",
            name=rule.name,
            description=rule.description,
            category=category_map[rule.category],
            severity=rule.severity,
            enabled=rule.enabled,
            tags=rule.tags,
        )

        return CodexRuleScan(rule, definition)

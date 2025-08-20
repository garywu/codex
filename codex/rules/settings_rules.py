"""
Settings and configuration management rules (SET prefix).

Following Ruff's pattern of organizing related rules in dedicated modules.
"""

import ast
import re
from pathlib import Path

from .registry import (
    ASTChecker,
    Fix,
    FixApplicability,
    Location,
    PatternChecker,
    Rule,
    RuleChecker,
    Severity,
    Violation,
)

# Rule definitions
USE_PYDANTIC_SETTINGS = Rule(
    code="SET001",
    name="use-pydantic-settings",
    message_template="Use Pydantic Settings instead of {method}",
    severity=Severity.WARNING,
    description="Configuration should use Pydantic Settings for type safety",
    rationale="Pydantic Settings provides validation, type safety, and environment variable support",
    tags=["settings", "pydantic", "configuration"],
    examples={
        "good": """
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str
    debug: bool = False
""",
        "bad": """
config = {
    'api_key': os.environ.get('API_KEY'),
    'debug': os.environ.get('DEBUG', 'false') == 'true'
}
""",
    },
)


SINGLE_SETTINGS_INSTANCE = Rule(
    code="SET002",
    name="single-settings-instance",
    message_template="Creating new Settings instance - use shared 'settings' object",
    severity=Severity.ERROR,
    description="Use a single shared settings instance",
    rationale="Multiple settings instances can lead to inconsistent configuration",
    tags=["settings", "singleton"],
)


NO_HARDCODED_PATHS = Rule(
    code="SET003",
    name="no-hardcoded-paths",
    message_template="Hardcoded path '{path}' - use settings.{setting}",
    severity=Severity.WARNING,
    description="Paths should come from settings, not hardcoded",
    rationale="Hardcoded paths break portability and make deployment difficult",
    tags=["paths", "configuration"],
)


NO_CONFIG_GET_WITH_DEFAULT = Rule(
    code="SET004",
    name="no-config-get-with-default",
    message_template="Using .get() with default for required config - use direct access",
    severity=Severity.WARNING,
    description="Required configuration should fail explicitly if missing",
    rationale="Silent defaults can hide configuration errors in production",
    tags=["configuration", "error-handling"],
)


# Checker implementations
class PydanticSettingsChecker(PatternChecker):
    """Check for non-Pydantic configuration patterns."""

    def __init__(self):
        patterns = [
            (r"config\s*=\s*\{", "dict configuration"),
            (r"ConfigParser\(\)", "ConfigParser"),
            (r'os\.environ\.get\(["\'](?!CODEX_)', "direct environ access"),
            (r"json\.load.*config", "JSON config file"),
            (r"yaml\.load.*config", "YAML config file"),
        ]
        super().__init__(USE_PYDANTIC_SETTINGS, patterns)


class SingleSettingsChecker(ASTChecker):
    """Check for multiple Settings instantiations."""

    def __init__(self):
        super().__init__(SINGLE_SETTINGS_INSTANCE)

    def check_ast(self, tree: ast.AST, file_path: Path) -> list[Violation]:
        """Find Settings() instantiations."""
        violations = []

        class SettingsVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                # Check for Settings() or BaseSettings() calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("Settings", "BaseSettings", "CodexSettings"):
                        # Skip if it's in a settings module
                        if "settings" not in str(file_path):
                            location = Location(file_path, node.lineno, node.col_offset)
                            violation = SINGLE_SETTINGS_INSTANCE.create_violation(
                                location=location, class_name=node.func.id
                            )
                            violations.append(violation)
                self.generic_visit(node)

        visitor = SettingsVisitor()
        visitor.visit(tree)
        return violations


class HardcodedPathChecker(RuleChecker):
    """Check for hardcoded file paths."""

    PATH_PATTERNS = [
        (re.compile(r'Path\(["\']\/'), "absolute path", "data_dir"),
        (re.compile(r'["\']~\/\.config'), "config directory", "config_dir"),
        (re.compile(r'["\']~\/\.local\/share'), "data directory", "data_dir"),
        (re.compile(r'["\']~\/\.cache'), "cache directory", "cache_dir"),
        (re.compile(r'\.db["\']'), "database file", "database_path"),
        (re.compile(r"\/tmp\/"), "temp directory", "temp_dir"),
    ]

    def __init__(self):
        super().__init__(NO_HARDCODED_PATHS)

    def check_file(self, file_path: Path, content: str) -> list[Violation]:
        """Check for hardcoded paths."""
        violations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue

            for pattern, path_type, setting_name in self.PATH_PATTERNS:
                match = pattern.search(line)
                if match:
                    location = Location(file_path, line_num, match.start())

                    # Create fix suggestion
                    fix = Fix(
                        description=f"Use settings.{setting_name}",
                        replacements=[(location, f"settings.{setting_name}")],
                        applicability=FixApplicability.SOMETIMES,
                    )

                    violation = self.rule.create_violation(
                        location=location, path=path_type, setting=setting_name, context=line.strip()
                    )
                    violation.fix = fix
                    violations.append(violation)
                    break

        return violations


class ConfigGetChecker(PatternChecker):
    """Check for config.get() with defaults."""

    def __init__(self):
        patterns = [
            (r'config\.get\(["\'](\w+)["\']\s*,\s*["\']?\w+', "config.get with default"),
            (r'settings\.get\(["\'](\w+)["\']\s*,', "settings.get with default"),
        ]
        super().__init__(NO_CONFIG_GET_WITH_DEFAULT, patterns)


# Register all rules
def register_settings_rules(registry):
    """Register all settings rules with the registry."""
    registry.register(USE_PYDANTIC_SETTINGS, PydanticSettingsChecker())
    registry.register(SINGLE_SETTINGS_INSTANCE, SingleSettingsChecker())
    registry.register(NO_HARDCODED_PATHS, HardcodedPathChecker())
    registry.register(NO_CONFIG_GET_WITH_DEFAULT, ConfigGetChecker())

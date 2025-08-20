"""
Rule registry system inspired by Ruff's architecture.

This module provides the core infrastructure for managing and executing rules.
"""

import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .categories import RulePrefix, get_prefix_from_code


class Severity(str, Enum):
    """Rule severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class FixApplicability(str, Enum):
    """Applicability of automatic fixes."""

    ALWAYS = "always"  # Fix is always safe
    SOMETIMES = "sometimes"  # Fix may need review
    NEVER = "never"  # No automatic fix available


@dataclass
class Location:
    """Location of a violation in source code."""

    file: Path
    line: int
    column: int = 0
    end_line: int | None = None
    end_column: int | None = None

    def __str__(self) -> str:
        """Format as file:line:column."""
        return f"{self.file}:{self.line}:{self.column}"


@dataclass
class Fix:
    """Automatic fix for a violation."""

    description: str
    replacements: list[tuple[Location, str]]  # (location, new_text)
    applicability: FixApplicability = FixApplicability.SOMETIMES


@dataclass
class Violation:
    """A rule violation found in code."""

    rule: "Rule"
    location: Location
    message: str
    context: str | None = None  # Code snippet
    fix: Fix | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def code(self) -> str:
        """Get the rule code."""
        return self.rule.code

    @property
    def severity(self) -> Severity:
        """Get the severity."""
        return self.rule.severity

    def format(self, style: str = "default") -> str:
        """Format the violation for output."""
        if style == "json":
            return self._format_json()
        elif style == "github":
            return self._format_github()
        else:
            return self._format_default()

    def _format_default(self) -> str:
        """Default format: file:line:col: CODE message."""
        return f"{self.location}: {self.code} {self.message}"

    def _format_github(self) -> str:
        """GitHub Actions format."""
        level = "error" if self.severity == Severity.ERROR else "warning"
        return f"::{level} file={self.location.file},line={self.location.line}::{self.code}: {self.message}"

    def _format_json(self) -> str:
        """JSON format for machine parsing."""
        import json

        return json.dumps(
            {
                "code": self.code,
                "severity": self.severity.value,
                "file": str(self.location.file),
                "line": self.location.line,
                "column": self.location.column,
                "message": self.message,
                "fix_available": self.fix is not None,
            }
        )


@dataclass
class Rule:
    """Definition of a scanning rule."""

    code: str  # Unique code (e.g., SET001)
    name: str  # Short name
    message_template: str  # Message template with {placeholders}
    severity: Severity = Severity.WARNING
    description: str | None = None
    rationale: str | None = None
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    examples: dict[str, str] = field(default_factory=dict)  # good/bad examples

    @property
    def prefix(self) -> RulePrefix:
        """Get the rule's prefix category."""
        return get_prefix_from_code(self.code)

    def create_violation(self, location: Location, message: str | None = None, **kwargs) -> Violation:
        """Create a violation of this rule."""
        if message is None:
            message = self.message_template.format(**kwargs)

        return Violation(rule=self, location=location, message=message, metadata=kwargs)


class RuleChecker(ABC):
    """Base class for rule checkers."""

    def __init__(self, rule: Rule):
        self.rule = rule
        self.violations: list[Violation] = []

    @abstractmethod
    def check_file(self, file_path: Path, content: str) -> list[Violation]:
        """Check a file for violations of this rule."""
        pass

    def check_line(self, line: str, line_num: int, file_path: Path) -> Violation | None:
        """Check a single line for violations."""
        return None

    def check_ast(self, tree: ast.AST, file_path: Path) -> list[Violation]:
        """Check an AST for violations."""
        return []


class PatternChecker(RuleChecker):
    """Checker that uses regex patterns."""

    def __init__(self, rule: Rule, patterns: list[tuple[str, str]]):
        super().__init__(rule)
        self.patterns = [(re.compile(p), msg) for p, msg in patterns]

    def check_file(self, file_path: Path, content: str) -> list[Violation]:
        """Check file using patterns."""
        violations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Skip comments and docstrings
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue

            for pattern, message in self.patterns:
                if pattern.search(line):
                    location = Location(file_path, line_num, 0)
                    violation = self.rule.create_violation(location=location, message=message, context=line.strip())
                    violations.append(violation)
                    break  # Only report first match per line

        return violations


class ASTChecker(RuleChecker):
    """Checker that analyzes Python AST."""

    def check_file(self, file_path: Path, content: str) -> list[Violation]:
        """Parse and check AST."""
        try:
            tree = ast.parse(content, filename=str(file_path))
            return self.check_ast(tree, file_path)
        except SyntaxError:
            return []


class RuleRegistry:
    """Central registry for all rules."""

    def __init__(self):
        self._rules: dict[str, Rule] = {}
        self._checkers: dict[str, RuleChecker] = {}
        self._by_prefix: dict[RulePrefix, list[Rule]] = {}

    def register(self, rule: Rule, checker: RuleChecker | None = None) -> None:
        """Register a rule and its checker."""
        self._rules[rule.code] = rule

        if checker:
            self._checkers[rule.code] = checker

        # Index by prefix
        prefix = rule.prefix
        if prefix not in self._by_prefix:
            self._by_prefix[prefix] = []
        self._by_prefix[prefix].append(rule)

    def get_rule(self, code: str) -> Rule | None:
        """Get a rule by its code."""
        return self._rules.get(code)

    def get_checker(self, code: str) -> RuleChecker | None:
        """Get a checker for a rule."""
        return self._checkers.get(code)

    def get_rules_by_prefix(self, prefix: RulePrefix) -> list[Rule]:
        """Get all rules with a given prefix."""
        return self._by_prefix.get(prefix, [])

    def get_enabled_rules(self) -> list[Rule]:
        """Get all enabled rules."""
        return [r for r in self._rules.values() if r.enabled]

    def select_rules(self, selectors: list[str]) -> set[Rule]:
        """Select rules based on selectors (codes or prefixes)."""
        selected = set()

        for selector in selectors:
            # Check if it's a full code
            if selector in self._rules:
                selected.add(self._rules[selector])
            else:
                # Try as prefix
                try:
                    prefix = RulePrefix(selector)
                    selected.update(self.get_rules_by_prefix(prefix))
                except ValueError:
                    # Try partial match (e.g., "SET" for all SET rules)
                    for code, rule in self._rules.items():
                        if code.startswith(selector):
                            selected.add(rule)

        return selected

    def check_file(self, file_path: Path, content: str, selected_rules: set[str] | None = None) -> list[Violation]:
        """Check a file against selected rules."""
        violations = []

        # Determine which rules to check
        if selected_rules:
            rules_to_check = [
                self._rules[code] for code in selected_rules if code in self._rules and self._rules[code].enabled
            ]
        else:
            rules_to_check = self.get_enabled_rules()

        # Run each checker
        for rule in rules_to_check:
            checker = self._checkers.get(rule.code)
            if checker:
                rule_violations = checker.check_file(file_path, content)
                violations.extend(rule_violations)

        return violations


# Global registry instance
registry = RuleRegistry()

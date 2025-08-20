#!/usr/bin/env python3
"""
Integration of Ensemble Scanner into Main Scanner

This module provides the bridge between the existing scanner and the new ensemble-based
pattern matching with voting mechanism.
"""

import ast
from typing import Any

from .ensemble_scanner import (
    ASTPatternRule,
    ContextAwareRule,
    EnsembleScanner,
    FunctionNameRule,
    RegexPatternRule,
    RuleContext,
)
from .models import PatternMatch
from .unified_database import UnifiedDatabase


class IntegratedEnsembleScanner:
    """Integrates ensemble scanner with existing Codex scanner."""

    def __init__(self, quiet: bool = False, verbose: bool = False):
        self.quiet = quiet
        self.verbose = verbose
        self.ensemble_scanner = EnsembleScanner()
        self.db = UnifiedDatabase()
        self._register_all_patterns()

    def _register_all_patterns(self):
        """Register all pattern rules with the ensemble scanner."""

        # Load all patterns with ensemble rules from database
        with self.db.get_connection() as conn:
            pattern_names = [
                row[0] for row in conn.execute("SELECT DISTINCT pattern_name FROM ensemble_rules").fetchall()
            ]

        for pattern_name in pattern_names:
            db_rules = self.db.get_ensemble_rules(pattern_name)
            if db_rules:
                # Convert database rules to ensemble rules
                rules = self._convert_db_rules_to_ensemble(pattern_name, db_rules)
                if rules:
                    self.ensemble_scanner.register_pattern(pattern_name, rules)

        # Fallback to hardcoded rules if database is empty
        if not any(pattern_name in self.ensemble_scanner.rule_sets for pattern_name in pattern_names):
            self._register_fallback_patterns()

    def _convert_db_rules_to_ensemble(self, pattern_name: str, db_rules: list[dict]) -> list:
        """Convert database rules to ensemble scanner rules."""
        rules = []

        for rule_config in db_rules:
            rule_type = rule_config["type"]
            # Handle nested config structure from database
            if "config" in rule_config["config"]:
                config = rule_config["config"]["config"]
            else:
                config = rule_config["config"]

            try:
                if rule_type == "function_name":
                    rules.append(
                        FunctionNameRule(
                            patterns=config["patterns"],
                            prefix_required=config["prefix_required"],
                            category=config["category"],
                        )
                    )

                elif rule_type == "regex":
                    rules.append(
                        RegexPatternRule(
                            regex=config["pattern"], message=config["message"], category=config["category"]
                        )
                    )

                elif rule_type == "ast_pattern":
                    # Create AST rule based on configuration
                    if config.get("node_type") == "Call":
                        rules.append(
                            ASTPatternRule(
                                node_type=ast.Call,
                                condition_fn=self._get_ast_condition_function(config.get("condition")),
                                message=config.get("message", ""),
                                category=config.get("category", "general"),
                            )
                        )
                    elif config.get("node_type") == "Assign":
                        rules.append(
                            ASTPatternRule(
                                node_type=ast.Assign,
                                condition_fn=self._get_ast_condition_function(config.get("condition")),
                                message=config.get("message", ""),
                                category=config.get("category", "general"),
                            )
                        )
                    elif config.get("node_type") == "FunctionDef":
                        rules.append(
                            ASTPatternRule(
                                node_type=ast.FunctionDef,
                                condition_fn=self._get_ast_condition_function(config.get("condition")),
                                message=config.get("message", ""),
                                category=config.get("category", "general"),
                            )
                        )

                elif rule_type == "context_aware":
                    rules.append(
                        ContextAwareRule(
                            rule_id=config.get("rule_id", "unknown"),
                            check_fn=self._get_context_check_function(config.get("rule_id")),
                            message=config.get("message", ""),
                            category=config.get("category", "general"),
                        )
                    )

            except Exception as e:
                if self.verbose:  # Only show in verbose mode, not normal operation
                    print(f"Warning: Failed to convert rule {rule_type} for {pattern_name}: {e}")

        return rules

    def _get_ast_condition_function(self, condition_name: str):
        """Get AST condition function by name."""
        conditions = {
            "cors_assignment_with_wildcard": self._check_cors_assignment,
            "subprocess_pip_call": self._check_subprocess_pip,
            "print_statement_non_test": self._check_print_statement,
            "basic_logging_without_structure": self._check_basic_logging,
            "fake_function_without_prefix_in_tests": lambda node, ctx: (
                any(word in node.name.lower() for word in ["fake", "mock", "stub"])
                and not any(node.name.startswith(prefix) for prefix in ["mock_", "fake_", "Mock", "Fake"])
                and ctx.is_test_file
            ),
        }
        return conditions.get(condition_name, lambda node, ctx: False)

    def _get_context_check_function(self, rule_id: str):
        """Get context check function by rule ID."""
        functions = {
            "not_in_string": self._check_not_in_string,
            "cors_context": self._check_cors_context,
            "not_glob_pattern": self._check_not_glob,
            "test_coverage_check": self._check_test_coverage,
            "not_example_code": self._check_not_example_code,
            "not_pattern_file": self._check_not_pattern_file,
            "not_script_file": self._check_not_script_file,
            "test_file_only": self._check_test_file_only,
            "test_file_required": self._check_test_file_required,
            "api_context": self._check_api_context,
        }
        return functions.get(rule_id, lambda ctx: [])

    def _register_fallback_patterns(self):
        """Fallback registration using hardcoded rules."""

        # Mock/Test patterns
        self.ensemble_scanner.register_pattern(
            "mock-code-naming",
            [
                FunctionNameRule(
                    patterns=["mock", "fake", "stub", "dummy"], prefix_required="mock_", category="testing"
                ),
                ASTPatternRule(
                    node_type=ast.FunctionDef,
                    condition_fn=lambda node, ctx: (
                        any(word in node.name.lower() for word in ["fake", "mock", "stub"])
                        and not any(node.name.startswith(prefix) for prefix in ["mock_", "fake_", "Mock", "Fake"])
                        and ctx.is_test_file
                    ),
                    message="Test mock functions should follow naming convention",
                    category="testing",
                ),
                # Negative evidence - reduces false positives for string literals
                ContextAwareRule(
                    rule_id="not_in_string", check_fn=self._check_not_in_string, message="", category="testing"
                ),
            ],
        )

        # CORS patterns
        self.ensemble_scanner.register_pattern(
            "no-cors-wildcard",
            [
                # Check for CORS-related variable assignments
                ASTPatternRule(
                    node_type=ast.Assign,
                    condition_fn=self._check_cors_assignment,
                    message="CORS configuration should not use wildcard",
                    category="security",
                ),
                # Check for CORS in dictionary keys
                ContextAwareRule(
                    rule_id="cors_context",
                    check_fn=self._check_cors_context,
                    message="CORS wildcard in configuration",
                    category="security",
                ),
                # Negative evidence - not a glob pattern
                ContextAwareRule(
                    rule_id="not_glob_pattern", check_fn=self._check_not_glob, message="", category="security"
                ),
            ],
        )

        # Package manager patterns
        self.ensemble_scanner.register_pattern(
            "use-uv-package-manager",
            [
                RegexPatternRule(
                    regex=r"\bpip\s+install\b", message="Use uv instead of pip install", category="package_management"
                ),
                RegexPatternRule(
                    regex=r"\bpip3\s+install\b", message="Use uv instead of pip3 install", category="package_management"
                ),
                RegexPatternRule(
                    regex=r"\bpoetry\s+(add|install)\b",
                    message="Use uv instead of poetry",
                    category="package_management",
                ),
                ASTPatternRule(
                    node_type=ast.Call,
                    condition_fn=self._check_subprocess_pip,
                    message="Use uv in subprocess calls instead of pip",
                    category="package_management",
                ),
            ],
        )

        # Structured logging patterns
        self.ensemble_scanner.register_pattern(
            "structured-logging",
            [
                ASTPatternRule(
                    node_type=ast.Call,
                    condition_fn=self._check_print_statement,
                    message="Use structured logging instead of print()",
                    category="logging",
                ),
                ASTPatternRule(
                    node_type=ast.Call,
                    condition_fn=self._check_basic_logging,
                    message="Use structured logging with key=value pairs or JSON",
                    category="logging",
                ),
            ],
        )

        # Test coverage patterns
        self.ensemble_scanner.register_pattern(
            "minimum-test-coverage",
            [
                ContextAwareRule(
                    rule_id="test_coverage_check",
                    check_fn=self._check_test_coverage,
                    message="Insufficient test coverage",
                    category="testing",
                )
            ],
        )

    def _check_not_in_string(self, context: RuleContext) -> list:
        """Check if 'test' appears outside of string literals."""
        if not context.ast_tree:
            return []

        from .ensemble_scanner import RuleViolation

        violations = []
        for node in ast.walk(context.ast_tree):
            # Look for non-string occurrences of test-related words
            if isinstance(node, ast.Name) and "test" in node.id.lower():
                # This is a variable/function name, not a string
                violations.append(
                    RuleViolation(
                        rule_id="not_in_string",
                        line_number=node.lineno,
                        column=node.col_offset,
                        message="",
                        confidence=0.3,  # Low confidence as negative evidence
                    )
                )

        return violations if not violations else []  # Return empty if no real violations

    def _check_cors_assignment(self, node, context: RuleContext) -> bool:
        """Check if this is a CORS-related assignment with wildcard."""
        if not hasattr(node, "targets"):
            return False

        # Check if target name contains CORS-related keywords
        for target in node.targets:
            if hasattr(target, "id"):
                name = target.id.lower()
                if any(word in name for word in ["cors", "origin", "access"]):
                    # Check if value is a wildcard
                    if isinstance(node.value, ast.Constant) and node.value.value == "*":
                        return True

        return False

    def _check_cors_context(self, context: RuleContext) -> list:
        """Check for CORS wildcards in context."""
        from .ensemble_scanner import RuleViolation

        violations = []

        for i, line in enumerate(context.lines, 1):
            line_lower = line.lower()
            # Check if line contains CORS-related keywords AND a wildcard
            if "cors" in line_lower or "origin" in line_lower or "access-control" in line_lower:
                if '"*"' in line or "'*'" in line:
                    violations.append(
                        RuleViolation(
                            rule_id="cors_context",
                            line_number=i,
                            column=0,
                            message="CORS wildcard detected",
                            confidence=0.8,
                        )
                    )

        return violations

    def _check_not_glob(self, context: RuleContext) -> list:
        """Negative evidence: check if wildcards are glob patterns."""
        from .ensemble_scanner import RuleViolation

        penalties = []

        for i, line in enumerate(context.lines, 1):
            # If line contains glob-related functions, reduce confidence
            if any(pattern in line for pattern in ["glob.glob", "rglob", "*.py", "*.txt", "fnmatch"]):
                penalties.append(
                    RuleViolation(
                        rule_id="not_glob_pattern",
                        line_number=i,
                        column=0,
                        message="",
                        confidence=-0.5,  # Negative confidence as counter-evidence
                    )
                )

        return penalties

    def _check_subprocess_pip(self, node, context: RuleContext) -> bool:
        """Check for pip/poetry in subprocess calls."""
        if not (isinstance(node.func, ast.Attribute) and node.func.attr in ["run", "call", "check_call", "Popen"]):
            return False

        # Check first argument for pip/poetry commands
        if node.args:
            first_arg = node.args[0]

            # Check for list of command parts
            if isinstance(first_arg, ast.List) and first_arg.elts:
                if isinstance(first_arg.elts[0], ast.Constant):
                    cmd = first_arg.elts[0].value
                    if cmd in ["pip", "pip3", "poetry"]:
                        return True

            # Check for string command
            elif isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                cmd = first_arg.value
                if any(tool in cmd for tool in ["pip install", "pip3 install", "poetry add"]):
                    return True

        return False

    def _check_print_statement(self, node, context: RuleContext) -> bool:
        """Check for print statements in non-test code."""
        if context.is_test_file:
            return False

        return isinstance(node.func, ast.Name) and node.func.id == "print"

    def _check_basic_logging(self, node, context: RuleContext) -> bool:
        """Check for basic logging without structure."""
        if not (isinstance(node.func, ast.Attribute) and node.func.attr in ["info", "warning", "error", "debug"]):
            return False

        # Check if it's a logger call
        if isinstance(node.func.value, ast.Name) and node.func.value.id in ["logging", "logger", "log"]:
            # Check if message has structure
            if node.args and isinstance(node.args[0], ast.Constant):
                msg = str(node.args[0].value)
                # Simple heuristic: structured logs have key=value or JSON-like format
                if not any(pattern in msg for pattern in ["=", "{", "%", "json"]):
                    return True

        return False

    def _check_test_coverage(self, context: RuleContext) -> list:
        """Check test coverage in test files."""
        if not context.is_test_file or not context.ast_tree:
            return []

        from .ensemble_scanner import RuleViolation

        # Count test and non-test functions
        test_functions = 0
        regular_functions = 0

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    test_functions += 1
                elif not node.name.startswith("_"):
                    regular_functions += 1

        # Check coverage ratio
        if regular_functions > 0 and test_functions < regular_functions * 0.8:
            return [
                RuleViolation(
                    rule_id="test_coverage_check",
                    line_number=1,
                    column=0,
                    message=f"Low test coverage: {test_functions} tests for {regular_functions} functions",
                    confidence=0.7,
                )
            ]

        return []

    def _check_not_example_code(self, context: RuleContext) -> list:
        """Negative evidence: reduce confidence if this appears to be example code."""
        from .ensemble_scanner import RuleViolation

        penalties = []

        # Check for example indicators in file path
        example_indicators = ["example", "demo", "sample", "test", "experiment"]
        if any(indicator in context.file_path.lower() for indicator in example_indicators):
            penalties.append(
                RuleViolation(
                    rule_id="not_example_code",
                    line_number=1,
                    column=0,
                    message="Example/demo file",
                    confidence=-0.4,  # Strong negative evidence
                )
            )

        return penalties

    def _check_not_pattern_file(self, context: RuleContext) -> list:
        """Negative evidence: reduce confidence if this is a pattern definition file."""
        from .ensemble_scanner import RuleViolation

        penalties = []

        # Check file path
        pattern_indicators = ["pattern", "rule", "ensemble", "populate", "validate"]
        if any(indicator in context.file_path.lower() for indicator in pattern_indicators):
            penalties.append(
                RuleViolation(
                    rule_id="not_pattern_file",
                    line_number=1,
                    column=0,
                    message="Pattern definition file",
                    confidence=-0.5,  # Very strong negative evidence
                )
            )

        return penalties

    def _check_not_script_file(self, context: RuleContext) -> list:
        """Negative evidence: reduce confidence for script files."""
        from .ensemble_scanner import RuleViolation

        penalties = []

        # Check if it's a script (not in main codex module)
        if (
            "script" in context.file_path.lower()
            or "experiment" in context.file_path.lower()
            or (context.file_path.endswith(".py") and "codex/" not in context.file_path)
        ):
            penalties.append(
                RuleViolation(
                    rule_id="not_script_file",
                    line_number=1,
                    column=0,
                    message="Script file - relaxed rules",
                    confidence=-0.3,
                )
            )

        return penalties

    def _check_test_file_only(self, context: RuleContext) -> list:
        """Positive evidence: only applies to test files."""
        from .ensemble_scanner import RuleViolation

        if not context.is_test_file:
            return [
                RuleViolation(
                    rule_id="test_file_only",
                    line_number=1,
                    column=0,
                    message="Rule only applies to test files",
                    confidence=-0.8,  # Very strong negative evidence
                )
            ]

        return []

    def _check_test_file_required(self, context: RuleContext) -> list:
        """Requirement: must be in test file context."""
        if not context.is_test_file:
            return []  # No violation if not in test file

        return []

    def _check_api_context(self, context: RuleContext) -> list:
        """Positive evidence: check if in API context."""
        from .ensemble_scanner import RuleViolation

        violations = []

        # Look for API framework indicators
        api_indicators = ["fastapi", "flask", "django", "api", "endpoint", "router"]
        has_api_context = any(indicator in context.content.lower() for indicator in api_indicators)

        if has_api_context:
            violations.append(
                RuleViolation(
                    rule_id="api_context",
                    line_number=1,
                    column=0,
                    message="API context detected",
                    confidence=0.3,  # Positive evidence
                )
            )

        return violations

    def check_pattern(self, pattern: Any, context_dict: dict) -> PatternMatch | None:
        """
        Check a pattern using ensemble voting.

        This is the main integration point that replaces _check_pattern_simple.
        """
        # Convert context to RuleContext
        rule_context = RuleContext.from_file(
            file_path=context_dict.get("file_path", ""), content=context_dict.get("content", "")
        )

        # Get pattern name
        pattern_name = (
            pattern.get("name", "unknown") if isinstance(pattern, dict) else getattr(pattern, "name", "unknown")
        )

        # Check if we have ensemble rules for this pattern
        if pattern_name not in self.ensemble_scanner.rule_sets:
            # Fall back to simple checking for unregistered patterns
            return None

        # Run ensemble scan
        violations = self.ensemble_scanner.scan_file(rule_context.file_path, rule_context.content, [pattern_name])

        # Convert ensemble violations to PatternMatch
        if violations:
            # Take the highest confidence violation
            best_violation = max(violations, key=lambda v: v.confidence)

            # Only report if confidence is above threshold
            if best_violation.confidence >= 0.6:  # 60% confidence threshold
                return PatternMatch(
                    pattern_id=pattern.get("id", 0) if isinstance(pattern, dict) else getattr(pattern, "id", 0),
                    pattern_name=pattern_name,
                    category=pattern.get("category", "unknown")
                    if isinstance(pattern, dict)
                    else getattr(pattern, "category", "unknown"),
                    priority=pattern.get("priority", "MEDIUM")
                    if isinstance(pattern, dict)
                    else getattr(pattern, "priority", "MEDIUM"),
                    file_path=rule_context.file_path,
                    line_number=best_violation.line_number,
                    matched_code=rule_context.lines[best_violation.line_number - 1].strip()
                    if best_violation.line_number <= len(rule_context.lines)
                    else "",
                    confidence=best_violation.confidence,
                    suggestion=best_violation.message,
                    auto_fixable=bool(pattern.get("fix_template", False)) if isinstance(pattern, dict) else False,
                    fix_code=pattern.get("fix_template") if isinstance(pattern, dict) else None,
                )

        return None

    def get_statistics(self) -> list[dict]:
        """Get performance statistics for all rules."""
        return self.ensemble_scanner.get_rule_performance()

#!/usr/bin/env python3
"""
Improved Scanner with Context-Aware Pattern Matching

Reduces false positives by:
1. Using AST parsing for Python code
2. Distinguishing between strings, comments, and code
3. Understanding context (test files, glob patterns, etc.)
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CodeContext:
    """Enhanced context with AST information."""

    file_path: str
    content: str
    lines: list[str] = None
    ast_tree: ast.AST | None = None
    is_test_file: bool = False
    is_config_file: bool = False

    def __post_init__(self):
        """Parse AST and determine file type."""
        self.lines = self.content.split("\n")

        # Determine file type
        path = Path(self.file_path)
        self.is_test_file = "test" in path.name or path.parts and "test" in path.parts
        self.is_config_file = path.suffix in [".toml", ".yaml", ".json", ".ini", ".cfg"]

        # Try to parse AST for Python files
        if path.suffix == ".py":
            try:
                self.ast_tree = ast.parse(self.content)
            except:
                self.ast_tree = None


class ImprovedPatternMatcher:
    """Context-aware pattern matcher that reduces false positives."""

    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def check_mock_pattern(self, context: CodeContext) -> list[dict[str, Any]]:
        """Check for mock-related patterns with proper context."""
        violations = []

        if not context.ast_tree:
            return violations

        # Look for function definitions that should follow mock naming
        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name

                # Check if it's a mock/fake function that doesn't follow convention
                if (
                    "fake" in func_name.lower()
                    or "mock" in func_name.lower()
                    or "stub" in func_name.lower()
                    or "dummy" in func_name.lower()
                ):
                    # Should start with mock_ or fake_
                    if not (
                        func_name.startswith("mock_") or func_name.startswith("fake_") or func_name.startswith("Mock")
                    ):  # Allow classes
                        violations.append(
                            {
                                "line": node.lineno,
                                "code": f"def {func_name}(...)",
                                "message": f"Mock/fake function '{func_name}' should start with 'mock_' or 'fake_' prefix",
                                "pattern": "mock-code-naming",
                            }
                        )

        return violations

    def check_cors_pattern(self, context: CodeContext) -> list[dict[str, Any]]:
        """Check for CORS wildcards with proper context."""
        violations = []

        # Skip non-Python files
        if context.is_config_file or not context.ast_tree:
            return violations

        for node in ast.walk(context.ast_tree):
            # Look for string literals that might be CORS configurations
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value

                # Check if it's actually CORS-related
                if value == "*":
                    # Get the line and check context
                    line_num = node.lineno
                    if line_num <= len(context.lines):
                        line = context.lines[line_num - 1].lower()

                        # Check if it's actually CORS-related
                        cors_indicators = ["cors", "origin", "access-control", "allowed_origins", "allow_origin"]
                        if any(indicator in line for indicator in cors_indicators):
                            violations.append(
                                {
                                    "line": line_num,
                                    "code": context.lines[line_num - 1].strip(),
                                    "message": "CORS should not use wildcard '*' in production",
                                    "pattern": "no-cors-wildcard",
                                }
                            )

            # Check for CORS configuration in dictionaries
            elif isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str) and "cors" in key.value.lower():
                        if isinstance(value, ast.Constant) and value.value == "*":
                            violations.append(
                                {
                                    "line": value.lineno,
                                    "code": f'"{key.value}": "*"',
                                    "message": "CORS configuration should not use wildcard",
                                    "pattern": "no-cors-wildcard",
                                }
                            )

        return violations

    def check_test_coverage(self, context: CodeContext) -> list[dict[str, Any]]:
        """Check for test coverage with proper context."""
        violations = []

        # Only check test files
        if not context.is_test_file or not context.ast_tree:
            return violations

        # Count test functions
        test_functions = []
        regular_functions = []

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    test_functions.append(node.name)
                elif not node.name.startswith("_"):
                    regular_functions.append(node.name)

        # Check if there are untested functions in the same file
        if regular_functions and len(test_functions) < len(regular_functions):
            violations.append(
                {
                    "line": 1,
                    "code": f"{len(test_functions)} tests for {len(regular_functions)} functions",
                    "message": f"Low test coverage: {len(test_functions)} tests for {len(regular_functions)} functions",
                    "pattern": "minimum-test-coverage",
                }
            )

        return violations

    def check_package_manager(self, context: CodeContext) -> list[dict[str, Any]]:
        """Check for package manager usage."""
        violations = []

        # Look for pip/poetry usage that should be uv
        pip_patterns = [
            (r"pip\s+install", "pip install"),
            (r"pip3\s+install", "pip3 install"),
            (r"python\s+-m\s+pip", "python -m pip"),
            (r"poetry\s+add", "poetry add"),
            (r"poetry\s+install", "poetry install"),
        ]

        for i, line in enumerate(context.lines, 1):
            # Skip comments and strings
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Check for pip/poetry patterns
            for pattern, name in pip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Make sure it's not in a string
                    if not ('"' in line and name in line.split('"')[1::2]):
                        violations.append(
                            {
                                "line": i,
                                "code": line.strip(),
                                "message": f"Use 'uv' instead of '{name}'",
                                "pattern": "use-uv-package-manager",
                            }
                        )
                        break

        return violations

    def check_structured_logging(self, context: CodeContext) -> list[dict[str, Any]]:
        """Check for structured logging usage."""
        violations = []

        if not context.ast_tree:
            return violations

        for node in ast.walk(context.ast_tree):
            # Look for print statements in non-test code
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print" and not context.is_test_file:
                    violations.append(
                        {
                            "line": node.lineno,
                            "code": context.lines[node.lineno - 1].strip()
                            if node.lineno <= len(context.lines)
                            else "print(...)",
                            "message": "Use structured logging instead of print()",
                            "pattern": "structured-logging",
                        }
                    )

                # Check for basic logging without structure
                elif (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in ["info", "warning", "error", "debug"]
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in ["logging", "logger"]
                ):
                    # Check if it's using structured format
                    if node.args and isinstance(node.args[0], ast.Constant):
                        msg = str(node.args[0].value)
                        # Simple heuristic: structured logs often have key=value or JSON-like format
                        if not ("=" in msg or "{" in msg or "%" in msg):
                            violations.append(
                                {
                                    "line": node.lineno,
                                    "code": context.lines[node.lineno - 1].strip()
                                    if node.lineno <= len(context.lines)
                                    else "logger.info(...)",
                                    "message": "Use structured logging with key=value pairs or JSON",
                                    "pattern": "structured-logging",
                                }
                            )

        return violations

    def check_patterns(self, context: CodeContext, patterns: list[str]) -> list[dict[str, Any]]:
        """Check multiple patterns with context awareness."""
        all_violations = []

        pattern_checkers = {
            "mock-code-naming": self.check_mock_pattern,
            "no-cors-wildcard": self.check_cors_pattern,
            "no-cors": self.check_cors_pattern,
            "minimum-test-coverage": self.check_test_coverage,
            "use-uv-package-manager": self.check_package_manager,
            "structured-logging": self.check_structured_logging,
        }

        for pattern in patterns:
            if pattern in pattern_checkers:
                violations = pattern_checkers[pattern](context)
                all_violations.extend(violations)

        return all_violations


def compare_scanners(file_path: str, content: str):
    """Compare old vs new scanner results."""
    context = CodeContext(file_path=file_path, content=content)
    matcher = ImprovedPatternMatcher()

    patterns = [
        "mock-code-naming",
        "no-cors-wildcard",
        "minimum-test-coverage",
        "use-uv-package-manager",
        "structured-logging",
    ]

    violations = matcher.check_patterns(context, patterns)

    return violations


def test_improved_scanner():
    """Test the improved scanner with sample code."""

    # Test case 1: False positive for "test" in string
    test_code1 = """
def process_file(path):
    if "test" in path:  # This should NOT be flagged
        return "test file"
    return "regular file"
"""

    # Test case 2: Real mock function issue
    test_code2 = """
def fake_database_connection():  # This SHOULD be flagged
    return {"connected": True}

def mock_api_call():  # This should NOT be flagged (correct prefix)
    return {"status": 200}
"""

    # Test case 3: Glob pattern vs CORS
    test_code3 = """
import glob

files = glob.glob("*.py")  # This should NOT be flagged

CORS_ORIGINS = "*"  # This SHOULD be flagged
"""

    print("=== Test Case 1: String literal 'test' ===")
    violations = compare_scanners("test1.py", test_code1)
    print(f"Violations found: {len(violations)}")
    for v in violations:
        print(f"  Line {v['line']}: {v['message']}")

    print("\n=== Test Case 2: Mock functions ===")
    violations = compare_scanners("test2.py", test_code2)
    print(f"Violations found: {len(violations)}")
    for v in violations:
        print(f"  Line {v['line']}: {v['message']}")

    print("\n=== Test Case 3: Glob vs CORS ===")
    violations = compare_scanners("test3.py", test_code3)
    print(f"Violations found: {len(violations)}")
    for v in violations:
        print(f"  Line {v['line']}: {v['message']}")


if __name__ == "__main__":
    test_improved_scanner()

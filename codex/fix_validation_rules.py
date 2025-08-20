#!/usr/bin/env python3
"""
Fix Validation Rules

CRITICAL: These rules determine what fixes are safe to apply.
ANY modification to these rules should be carefully reviewed.
"""

# Patterns that should NEVER be auto-fixed
NEVER_AUTO_FIX = {
    "secure-jwt-storage",  # Security critical
    "no-cors-wildcard",  # Security critical
    "sql-injection",  # Security critical
    "xss-vulnerability",  # Security critical
    "path-traversal",  # Security critical
    "command-injection",  # Security critical
    "unsafe-deserialization",  # Security critical
}

# Patterns that require human review even with automation
REQUIRE_HUMAN_REVIEW = {
    "use-pydantic-validation",  # Requires understanding data structure
    "business-logic-in-cli",  # Architectural decision
    "database-migrations",  # Can break database
    "api-versioning",  # Can break clients
    "authentication-logic",  # Security sensitive
    "authorization-checks",  # Security sensitive
}

# Patterns safe for automated fixing with validation
SAFE_WITH_VALIDATION = {
    "mock-code-naming",  # Simple rename
    "use-uv-package-manager",  # Tool substitution
    "standard-import-order",  # Formatting only
    "trailing-whitespace",  # Formatting only
    "missing-docstring",  # Addition only
}

# Files that should NEVER be auto-modified
PROTECTED_FILES = {
    "__init__.py",  # Package initialization
    "setup.py",  # Package configuration
    "pyproject.toml",  # Project configuration
    ".env",  # Environment variables
    "requirements.txt",  # Dependencies (use uv)
    "poetry.lock",  # Lock files
    "Pipfile.lock",  # Lock files
}

# Patterns in file paths that indicate critical code
CRITICAL_PATH_PATTERNS = {
    "auth",  # Authentication
    "security",  # Security
    "crypto",  # Cryptography
    "payment",  # Payment processing
    "billing",  # Billing
    "migration",  # Database migrations
    "deploy",  # Deployment scripts
    "prod",  # Production code
}


class FixSafetyAnalyzer:
    """Analyze if a fix is safe to apply."""

    @staticmethod
    def is_fix_safe(pattern_name: str, file_path: str, line_content: str) -> tuple[bool, str]:
        """
        Determine if a fix is safe to apply.

        Returns:
            Tuple of (is_safe, reason)
        """
        # Check if pattern is in never-fix list
        if pattern_name in NEVER_AUTO_FIX:
            return False, f"Pattern '{pattern_name}' is security-critical and requires manual review"

        # Check if file is protected
        import os

        file_name = os.path.basename(file_path)
        if file_name in PROTECTED_FILES:
            return False, f"File '{file_name}' is protected and should not be auto-modified"

        # Check for critical path patterns
        file_path_lower = file_path.lower()
        for critical_pattern in CRITICAL_PATH_PATTERNS:
            if critical_pattern in file_path_lower:
                return False, f"File path contains critical pattern '{critical_pattern}'"

        # Check for test files - generally safer
        if "test" in file_path_lower:
            # Test files are generally safer to modify
            if pattern_name in SAFE_WITH_VALIDATION:
                return True, "Test file with safe pattern"

        # Check if pattern requires human review
        if pattern_name in REQUIRE_HUMAN_REVIEW:
            return False, f"Pattern '{pattern_name}' requires human review for context"

        # Check line content for dangerous patterns
        dangerous_keywords = [
            "eval(",
            "exec(",
            "compile(",
            "__import__",
            "subprocess",
            "os.system",
            "DELETE FROM",
            "DROP TABLE",
            "TRUNCATE",
            "sudo",
        ]

        for keyword in dangerous_keywords:
            if keyword in line_content:
                return False, f"Line contains dangerous keyword '{keyword}'"

        # Check if pattern is in safe list
        if pattern_name in SAFE_WITH_VALIDATION:
            return True, "Pattern is in safe list with validation"

        # Default to unsafe
        return False, "Pattern not in any safe list"

    @staticmethod
    def get_required_validations(pattern_name: str) -> list[str]:
        """Get list of required validations for a pattern."""
        validations = ["syntax"]  # Always validate syntax

        if pattern_name in ["mock-code-naming", "standard-import-order"]:
            validations.append("imports")

        if pattern_name in ["use-pydantic-validation", "use-db-context-managers"]:
            validations.append("type_checking")

        if pattern_name in ["structured-logging", "sanitize-production-errors"]:
            validations.append("runtime_behavior")

        if pattern_name in REQUIRE_HUMAN_REVIEW:
            validations.append("human_review")

        return validations

    @staticmethod
    def estimate_risk_level(pattern_name: str, file_path: str) -> str:
        """
        Estimate risk level of applying a fix.

        Returns: 'low', 'medium', 'high', 'critical'
        """
        if pattern_name in NEVER_AUTO_FIX:
            return "critical"

        if pattern_name in REQUIRE_HUMAN_REVIEW:
            return "high"

        # Check file importance
        if any(critical in file_path.lower() for critical in CRITICAL_PATH_PATTERNS):
            return "high"

        if "test" in file_path.lower():
            return "low"

        if pattern_name in SAFE_WITH_VALIDATION:
            return "low"

        return "medium"


def validate_fix_safety_rules():
    """Validate that safety rules are consistent."""
    all_patterns = NEVER_AUTO_FIX | REQUIRE_HUMAN_REVIEW | SAFE_WITH_VALIDATION

    # Check for overlaps
    never_and_review = NEVER_AUTO_FIX & REQUIRE_HUMAN_REVIEW
    if never_and_review:
        raise ValueError(f"Patterns in both NEVER_AUTO_FIX and REQUIRE_HUMAN_REVIEW: {never_and_review}")

    never_and_safe = NEVER_AUTO_FIX & SAFE_WITH_VALIDATION
    if never_and_safe:
        raise ValueError(f"Patterns in both NEVER_AUTO_FIX and SAFE_WITH_VALIDATION: {never_and_safe}")

    review_and_safe = REQUIRE_HUMAN_REVIEW & SAFE_WITH_VALIDATION
    if review_and_safe:
        raise ValueError(f"Patterns in both REQUIRE_HUMAN_REVIEW and SAFE_WITH_VALIDATION: {review_and_safe}")

    print(f"✓ Safety rules validated: {len(all_patterns)} patterns configured")
    print(f"  - Never auto-fix: {len(NEVER_AUTO_FIX)}")
    print(f"  - Require review: {len(REQUIRE_HUMAN_REVIEW)}")
    print(f"  - Safe with validation: {len(SAFE_WITH_VALIDATION)}")
    print(f"  - Protected files: {len(PROTECTED_FILES)}")
    print(f"  - Critical paths: {len(CRITICAL_PATH_PATTERNS)}")


if __name__ == "__main__":
    # Validate rules on module load
    validate_fix_safety_rules()

    # Example usage
    analyzer = FixSafetyAnalyzer()

    test_cases = [
        ("mock-code-naming", "tests/test_example.py", "def fake_function():"),
        ("secure-jwt-storage", "auth/jwt_handler.py", "JWT_SECRET = 'hardcoded'"),
        ("use-uv-package-manager", "scripts/install.py", "pip install requests"),
    ]

    for pattern, file_path, line in test_cases:
        is_safe, reason = analyzer.is_fix_safe(pattern, file_path, line)
        risk = analyzer.estimate_risk_level(pattern, file_path)
        print(f"\n{pattern} in {file_path}:")
        print(f"  Safe: {is_safe}")
        print(f"  Reason: {reason}")
        print(f"  Risk: {risk}")
        print(f"  Validations: {analyzer.get_required_validations(pattern)}")

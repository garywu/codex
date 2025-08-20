#!/usr/bin/env python3
"""
Populate database with ensemble rules for improved pattern detection.

This script migrates the hardcoded ensemble rules from IntegratedEnsembleScanner
to the database for better maintainability and configurability.
"""

import sys
from pathlib import Path

# Add codex to Python path
sys.path.insert(0, str(Path(__file__).parent / "codex"))

from codex.unified_database import UnifiedDatabase


def populate_ensemble_rules():
    """Populate database with ensemble rules for key patterns."""

    db = UnifiedDatabase()

    # Mock/Test pattern rules
    mock_rules = [
        {
            "type": "function_name",
            "config": {
                "patterns": ["mock", "fake", "stub", "dummy"],
                "prefix_required": "mock_",
                "category": "testing",
            },
            "priority": 100,
            "enabled": True,
        },
        {
            "type": "ast_pattern",
            "config": {
                "node_type": "FunctionDef",
                "condition": "fake_function_without_prefix_in_tests",
                "message": "Test mock functions should follow naming convention",
                "category": "testing",
            },
            "priority": 90,
            "enabled": True,
        },
        {
            "type": "context_aware",
            "config": {
                "rule_id": "not_in_string",
                "check_type": "negative_evidence",
                "reduces_false_positives": True,
                "category": "testing",
            },
            "priority": 80,
            "enabled": True,
        },
    ]

    # CORS pattern rules
    cors_rules = [
        {
            "type": "ast_pattern",
            "config": {
                "node_type": "Assign",
                "condition": "cors_assignment_with_wildcard",
                "message": "CORS configuration should not use wildcard",
                "category": "security",
            },
            "priority": 100,
            "enabled": True,
        },
        {
            "type": "context_aware",
            "config": {
                "rule_id": "cors_context",
                "check_type": "context_keywords",
                "keywords": ["cors", "origin", "access-control"],
                "wildcard_patterns": ['"*"', "'*'"],
                "message": "CORS wildcard in configuration",
                "category": "security",
            },
            "priority": 90,
            "enabled": True,
        },
        {
            "type": "context_aware",
            "config": {
                "rule_id": "not_glob_pattern",
                "check_type": "negative_evidence",
                "glob_indicators": ["glob.glob", "rglob", "*.py", "*.txt", "fnmatch"],
                "reduces_confidence": True,
                "category": "security",
            },
            "priority": 80,
            "enabled": True,
        },
    ]

    # Package manager rules
    uv_rules = [
        {
            "type": "regex",
            "config": {
                "pattern": r"\\bpip\\s+install\\b",
                "message": "Use uv instead of pip install",
                "category": "package_management",
            },
            "priority": 100,
            "enabled": True,
        },
        {
            "type": "regex",
            "config": {
                "pattern": r"\\bpip3\\s+install\\b",
                "message": "Use uv instead of pip3 install",
                "category": "package_management",
            },
            "priority": 100,
            "enabled": True,
        },
        {
            "type": "regex",
            "config": {
                "pattern": r"\\bpoetry\\s+(add|install)\\b",
                "message": "Use uv instead of poetry",
                "category": "package_management",
            },
            "priority": 100,
            "enabled": True,
        },
        {
            "type": "ast_pattern",
            "config": {
                "node_type": "Call",
                "condition": "subprocess_pip_call",
                "message": "Use uv in subprocess calls instead of pip",
                "category": "package_management",
            },
            "priority": 90,
            "enabled": True,
        },
    ]

    # Structured logging rules
    logging_rules = [
        {
            "type": "ast_pattern",
            "config": {
                "node_type": "Call",
                "condition": "print_statement_non_test",
                "message": "Use structured logging instead of print()",
                "category": "logging",
            },
            "priority": 100,
            "enabled": True,
        },
        {
            "type": "ast_pattern",
            "config": {
                "node_type": "Call",
                "condition": "basic_logging_without_structure",
                "message": "Use structured logging with key=value pairs or JSON",
                "category": "logging",
            },
            "priority": 90,
            "enabled": True,
        },
    ]

    # Test coverage rules
    coverage_rules = [
        {
            "type": "context_aware",
            "config": {
                "rule_id": "test_coverage_check",
                "check_type": "test_file_analysis",
                "min_coverage_ratio": 0.8,
                "message": "Insufficient test coverage",
                "category": "testing",
            },
            "priority": 100,
            "enabled": True,
        }
    ]

    # Add rules to database
    print("🔧 Populating ensemble rules in database...")

    patterns_to_update = [
        ("mock-code-naming", mock_rules, 2, 0.7),  # min_votes=2, threshold=0.7
        ("no-cors-wildcard", cors_rules, 2, 0.6),  # min_votes=2, threshold=0.6
        ("use-uv-package-manager", uv_rules, 1, 0.6),  # min_votes=1, threshold=0.6
        ("structured-logging", logging_rules, 1, 0.7),  # min_votes=1, threshold=0.7
        ("minimum-test-coverage", coverage_rules, 1, 0.7),  # min_votes=1, threshold=0.7
    ]

    for pattern_name, rules, min_votes, threshold in patterns_to_update:
        print(f"  ✅ Adding {len(rules)} rules for '{pattern_name}'")
        db.add_ensemble_rules(pattern_name, rules)
        db.update_pattern_ensemble_config(pattern_name, min_votes, threshold)

    print(f"\n🎉 Successfully populated {sum(len(rules) for _, rules, _, _ in patterns_to_update)} ensemble rules!")
    print("   These rules will reduce false positives through voting mechanisms.")


if __name__ == "__main__":
    populate_ensemble_rules()

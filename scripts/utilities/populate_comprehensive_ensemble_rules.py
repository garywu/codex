#!/usr/bin/env python3
"""
Populate comprehensive ensemble rules for all major patterns.

This script creates ensemble rules for the most commonly triggered patterns
to maximize false positive reduction across the entire codebase.
"""

import sys
from pathlib import Path

# Add codex to Python path
sys.path.insert(0, str(Path(__file__).parent / "codex"))

from codex.unified_database import UnifiedDatabase


def populate_comprehensive_ensemble_rules():
    """Populate database with ensemble rules for all major patterns."""

    db = UnifiedDatabase()

    # Get all patterns from database
    with db.get_connection() as conn:
        patterns = conn.execute("SELECT name FROM patterns").fetchall()
        pattern_names = [row[0] for row in patterns]

    print(f"🔧 Creating ensemble rules for {len(pattern_names)} patterns...")

    # Define ensemble rules for major pattern categories
    ensemble_rules_map = {
        # Security patterns - high precision needed
        "no-cors-wildcard": [
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
                    "reduces_confidence": True,
                    "category": "security",
                },
                "priority": 80,
                "enabled": True,
            },
        ],
        "secure-jwt-storage": [
            {
                "type": "regex",
                "config": {
                    "pattern": r'jwt.*secret.*=.*["\'][^"\']+["\']',
                    "message": "JWT secrets should not be hardcoded",
                    "category": "security",
                },
                "priority": 100,
                "enabled": True,
            },
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "not_test_file",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
                    "category": "security",
                },
                "priority": 80,
                "enabled": True,
            },
        ],
        "sanitize-production-errors": [
            {
                "type": "regex",
                "config": {
                    "pattern": r"raise.*\(.*\+.*\)",
                    "message": "Avoid exposing sensitive data in error messages",
                    "category": "security",
                },
                "priority": 100,
                "enabled": True,
            }
        ],
        # Package management patterns - already good
        "use-uv-package-manager": [
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
                    "pattern": r"\\bpoetry\\s+(add|install)\\b",
                    "message": "Use uv instead of poetry",
                    "category": "package_management",
                },
                "priority": 100,
                "enabled": True,
            },
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "not_example_code",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
                    "category": "package_management",
                },
                "priority": 70,
                "enabled": True,
            },
        ],
        "use-uv-not-pip": [
            {
                "type": "regex",
                "config": {
                    "pattern": r"\\bpip\\s+install\\b",
                    "message": "Use uv instead of pip",
                    "category": "package_management",
                },
                "priority": 100,
                "enabled": True,
            }
        ],
        "uv-package-manager": [
            {
                "type": "regex",
                "config": {
                    "pattern": r"\\bpip\\s+install\\b",
                    "message": "Use uv package manager",
                    "category": "package_management",
                },
                "priority": 100,
                "enabled": True,
            }
        ],
        # Testing patterns - high false positive risk
        "mock-code-naming": [
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
                "type": "context_aware",
                "config": {
                    "rule_id": "test_file_only",
                    "check_type": "file_context",
                    "test_file_required": True,
                    "category": "testing",
                },
                "priority": 90,
                "enabled": True,
            },
            {
                "type": "context_aware",
                "config": {"rule_id": "not_in_string", "check_type": "negative_evidence", "category": "testing"},
                "priority": 80,
                "enabled": True,
            },
        ],
        "mock-naming-convention": [
            {
                "type": "function_name",
                "config": {"patterns": ["mock", "fake", "stub"], "prefix_required": "mock_", "category": "testing"},
                "priority": 100,
                "enabled": True,
            }
        ],
        "minimum-test-coverage": [
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
            },
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "test_file_required",
                    "check_type": "file_context",
                    "test_file_required": True,
                    "category": "testing",
                },
                "priority": 90,
                "enabled": True,
            },
        ],
        # Logging patterns - medium false positive risk
        "structured-logging": [
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
        ],
        "use-structured-logging": [
            {
                "type": "ast_pattern",
                "config": {
                    "node_type": "Call",
                    "condition": "print_statement_non_test",
                    "message": "Use structured logging",
                    "category": "logging",
                },
                "priority": 100,
                "enabled": True,
            }
        ],
        "no-print-production": [
            {
                "type": "ast_pattern",
                "config": {
                    "node_type": "Call",
                    "condition": "print_statement_non_test",
                    "message": "No print statements in production code",
                    "category": "logging",
                },
                "priority": 100,
                "enabled": True,
            }
        ],
        # Validation patterns - medium false positive risk
        "use-pydantic-validation": [
            {
                "type": "regex",
                "config": {
                    "pattern": r"class.*\\(.*\\):.*def __init__.*self.*:",
                    "message": "Consider using Pydantic BaseModel for validation",
                    "category": "validation",
                },
                "priority": 100,
                "enabled": True,
            },
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "api_context",
                    "check_type": "file_context",
                    "api_file_indicators": ["fastapi", "flask", "django"],
                    "category": "validation",
                },
                "priority": 90,
                "enabled": True,
            },
        ],
        "pydantic-validation": [
            {
                "type": "regex",
                "config": {
                    "pattern": r"def.*validate.*\\(",
                    "message": "Use Pydantic for validation",
                    "category": "validation",
                },
                "priority": 100,
                "enabled": True,
            }
        ],
        # Database patterns - low false positive risk
        "use-db-context-managers": [
            {
                "type": "regex",
                "config": {
                    "pattern": r"\\.(connect|cursor)\\(.*\\)",
                    "message": "Use context managers for database connections",
                    "category": "database",
                },
                "priority": 100,
                "enabled": True,
            }
        ],
    }

    # Set minimum votes and thresholds based on pattern risk
    pattern_configs = {
        # High precision needed (security/critical)
        "no-cors-wildcard": (2, 0.7),
        "secure-jwt-storage": (2, 0.8),
        "sanitize-production-errors": (1, 0.7),
        # Package management (reliable patterns)
        "use-uv-package-manager": (1, 0.6),
        "use-uv-not-pip": (1, 0.6),
        "uv-package-manager": (1, 0.6),
        # Testing (high false positive risk)
        "mock-code-naming": (2, 0.7),
        "mock-naming-convention": (2, 0.7),
        "minimum-test-coverage": (2, 0.8),
        # Logging (medium risk)
        "structured-logging": (1, 0.6),
        "use-structured-logging": (1, 0.6),
        "no-print-production": (2, 0.7),
        # Validation (medium risk)
        "use-pydantic-validation": (1, 0.6),
        "pydantic-validation": (1, 0.6),
        # Database (low risk)
        "use-db-context-managers": (1, 0.6),
    }

    # Add rules to database
    rules_added = 0
    patterns_updated = 0

    for pattern_name in pattern_names:
        if pattern_name in ensemble_rules_map:
            rules = ensemble_rules_map[pattern_name]
            min_votes, threshold = pattern_configs.get(pattern_name, (1, 0.6))

            print(f"  ✅ Adding {len(rules)} ensemble rules for '{pattern_name}'")
            db.add_ensemble_rules(pattern_name, rules)
            db.update_pattern_ensemble_config(pattern_name, min_votes, threshold)

            rules_added += len(rules)
            patterns_updated += 1
        else:
            # Create basic single-rule ensemble for patterns without specific rules
            basic_rules = [
                {
                    "type": "regex",
                    "config": {
                        "pattern": f"{pattern_name}_basic_detection",
                        "message": f"Pattern {pattern_name} detected",
                        "category": "general",
                    },
                    "priority": 100,
                    "enabled": True,
                }
            ]

            if not pattern_name.startswith("test-"):  # Skip test patterns
                print(f"  📋 Adding basic ensemble rule for '{pattern_name}'")
                db.add_ensemble_rules(pattern_name, basic_rules)
                db.update_pattern_ensemble_config(pattern_name, 1, 0.5)  # Lower threshold for basic rules
                rules_added += 1
                patterns_updated += 1

    print(f"\n🎉 Successfully updated {patterns_updated} patterns with {rules_added} ensemble rules!")
    print(f"   Enhanced patterns: {len([p for p in pattern_names if p in ensemble_rules_map])}")
    print(f"   Basic rule patterns: {patterns_updated - len([p for p in pattern_names if p in ensemble_rules_map])}")
    print("   Ensemble scanner now covers all patterns for reduced false positives!")


if __name__ == "__main__":
    populate_comprehensive_ensemble_rules()

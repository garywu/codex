#!/usr/bin/env python3
"""
Update ensemble rules with improved context awareness and negative evidence.
"""

import sys
from pathlib import Path

# Add codex to Python path
sys.path.insert(0, str(Path(__file__).parent / "codex"))

from codex.unified_database import UnifiedDatabase


def update_ensemble_rules_with_context():
    """Update existing ensemble rules with better context awareness."""

    db = UnifiedDatabase()

    print("🔧 Updating ensemble rules with improved context awareness...")

    # Enhanced rules with negative evidence for common false positive patterns
    enhanced_rules = {
        # Package management patterns - add script file detection
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
                    "rule_id": "not_pattern_file",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
                    "category": "package_management",
                },
                "priority": 80,
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
        # Print production patterns - add script detection
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
            },
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "not_script_file",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
                    "category": "logging",
                },
                "priority": 80,
                "enabled": True,
            },
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "not_example_code",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
                    "category": "logging",
                },
                "priority": 70,
                "enabled": True,
            },
        ],
        # Mock naming patterns - improve test file detection
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
                    "rule_id": "not_pattern_file",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
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
        # CORS patterns - add stronger negative evidence
        "no-cors-wildcard": [
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "cors_context",
                    "check_type": "context_keywords",
                    "message": "CORS wildcard in configuration",
                    "category": "security",
                },
                "priority": 100,
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
                "priority": 90,
                "enabled": True,
            },
            {
                "type": "context_aware",
                "config": {
                    "rule_id": "not_pattern_file",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
                    "category": "security",
                },
                "priority": 80,
                "enabled": True,
            },
        ],
        # JWT storage - add pattern file detection
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
                    "rule_id": "not_pattern_file",
                    "check_type": "negative_evidence",
                    "reduces_false_positives": True,
                    "category": "security",
                },
                "priority": 80,
                "enabled": True,
            },
        ],
    }

    # Update voting thresholds for better accuracy
    pattern_configs = {
        "use-uv-package-manager": (2, 0.7),  # Require 2 votes, higher threshold
        "no-print-production": (2, 0.7),  # Require 2 votes, higher threshold
        "mock-code-naming": (2, 0.8),  # Require 2 votes, high threshold
        "no-cors-wildcard": (2, 0.7),  # Require 2 votes, higher threshold
        "secure-jwt-storage": (2, 0.8),  # Require 2 votes, high threshold
    }

    # Update rules in database
    rules_updated = 0

    for pattern_name, rules in enhanced_rules.items():
        print(f"  ✅ Updating {len(rules)} rules for '{pattern_name}'")
        db.add_ensemble_rules(pattern_name, rules)

        if pattern_name in pattern_configs:
            min_votes, threshold = pattern_configs[pattern_name]
            db.update_pattern_ensemble_config(pattern_name, min_votes, threshold)

        rules_updated += len(rules)

    print(f"\n🎉 Successfully updated {rules_updated} ensemble rules!")
    print("   Enhanced negative evidence for:")
    print("   • Pattern definition files")
    print("   • Example/demo code")
    print("   • Script vs production detection")
    print("   • Increased voting thresholds for accuracy")


if __name__ == "__main__":
    update_ensemble_rules_with_context()

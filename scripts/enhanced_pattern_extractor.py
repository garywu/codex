#!/usr/bin/env python3
"""
Enhanced pattern extractor from project-init.json with more comprehensive rules.

This version captures more nuanced patterns and anti-patterns from the
organizational principles.
"""

import json
from pathlib import Path
from typing import Any


def extract_comprehensive_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract all patterns from project-init with enhanced detection."""
    patterns = []

    # ========== NAMING PATTERNS ==========

    # Anti-pattern: Redundant package prefixes
    patterns.append(
        {
            "name": "no-package-stutter",
            "category": "naming",
            "priority": "HIGH",
            "description": "Avoid repeating package name in module or class names",
            "rule": "Within heimdall package, use daemon.py not heimdall_daemon.py",
            "detect": r"class\s+(\w*Heimdall\w+)|class\s+(\w*Circle\w+)|class\s+(\w*Hermes\w+)",
            "fix": "Remove package name from class/file name",
            "why": "Package context is already established by import path",
            "good_example": "from heimdall import Daemon  # Not HeimdallDaemon",
            "bad_example": "from heimdall import HeimdallDaemon  # Redundant",
        }
    )

    # Anti-pattern: Version numbers in filenames
    patterns.append(
        {
            "name": "no-version-in-filename",
            "category": "naming",
            "priority": "MANDATORY",
            "description": "Never use version numbers in production filenames",
            "rule": "Maintain single canonical implementation without v1, v2, etc.",
            "detect": r"[\w_]+(v\d+|_v\d+|_version\d+)\.(py|js|ts|go)$",
            "fix": "Consolidate to single canonical file",
            "why": "Version suffixes indicate unresolved technical debt",
            "good_example": "cache_manager.py",
            "bad_example": "cache_manager_v2.py",
        }
    )

    # Anti-pattern: Implementation details in names
    patterns.append(
        {
            "name": "no-impl-details-in-name",
            "category": "naming",
            "priority": "HIGH",
            "description": "Don't include implementation details in names",
            "rule": "Use functional names, not implementation specifics",
            "detect": r"(_simple|_complex|_fast|_slow|_impl|_base|_abstract)\.(py|js|ts)$",
            "fix": "Rename based on purpose, not implementation",
            "why": "Implementation may change but purpose remains",
            "good_example": "processor.py",
            "bad_example": "processor_simple.py",
        }
    )

    # ========== ERROR HANDLING PATTERNS ==========

    # Anti-pattern: Bare except clauses
    patterns.append(
        {
            "name": "no-bare-except",
            "category": "error_handling",
            "priority": "MANDATORY",
            "description": "Never use bare except: clauses",
            "rule": "Always catch specific exception types",
            "detect": r"except\s*:\s*$|except\s*:\s*#",
            "fix": "Specify exception type: except SpecificError:",
            "why": "Bare except catches SystemExit, KeyboardInterrupt, and hides bugs",
            "good_example": "except ValueError as e:\n    logger.error('Invalid value', error=e)",
            "bad_example": "except:\n    pass  # Silently swallows all errors",
        }
    )

    # Anti-pattern: Broad Exception catching
    patterns.append(
        {
            "name": "no-broad-exception",
            "category": "error_handling",
            "priority": "HIGH",
            "description": "Avoid catching Exception without re-raising",
            "rule": "Catch specific exceptions or re-raise after logging",
            "detect": r"except\s+Exception\s*:|except\s+Exception\s+as\s+\w+:",
            "fix": "Use specific exception types or re-raise",
            "why": "Broad exception handling masks programming errors",
            "good_example": "except RequestException as e:\n    logger.error('Request failed', error=e)\n    raise",
            "bad_example": "except Exception:\n    return None  # Hides errors",
        }
    )

    # Pattern: Fail-fast validation
    patterns.append(
        {
            "name": "fail-fast-validation",
            "category": "validation",
            "priority": "HIGH",
            "description": "Validate inputs immediately and fail with clear errors",
            "rule": "Check required parameters at function entry",
            "detect": r"if\s+not\s+\w+:\s*return\s+None",
            "fix": "Raise ValueError with descriptive message",
            "why": "Early validation prevents cascading errors",
            "good_example": "if not user_id:\n    raise ValueError('user_id is required')",
            "bad_example": "if not user_id:\n    return None  # Silent failure",
        }
    )

    # Anti-pattern: Silent defaults
    patterns.append(
        {
            "name": "no-silent-defaults",
            "category": "error_handling",
            "priority": "HIGH",
            "description": "Don't use .get() with defaults for required config",
            "rule": "Required parameters should fail if missing",
            "detect": r"config\.get\(['\"](\w+)['\"]\s*,\s*['\"]?[\w\d]+['\"]?\)",
            "fix": "Use direct access: config['key']",
            "why": "Silent defaults hide configuration errors",
            "good_example": "api_key = config['api_key']  # Fails if missing",
            "bad_example": "api_key = config.get('api_key', 'default')  # Hides missing config",
        }
    )

    # ========== LOGGING PATTERNS ==========

    # Anti-pattern: Print statements in production
    patterns.append(
        {
            "name": "no-print-production",
            "category": "logging",
            "priority": "HIGH",
            "description": "Replace print() with proper logging",
            "rule": "Use logger instead of print in all production code",
            "detect": r"^\s*print\s*\(",
            "fix": "Use logger.info() or appropriate level",
            "why": "Print statements can't be controlled or filtered in production",
            "good_example": "logger.info('Processing', item_id=item_id)",
            "bad_example": "print(f'Processing {item_id}')",
        }
    )

    # Pattern: Structured logging
    patterns.append(
        {
            "name": "use-structured-logging",
            "category": "logging",
            "priority": "MEDIUM",
            "description": "Use key-value pairs in logging",
            "rule": "Log with structured data, not string formatting",
            "detect": r"logger\.\w+\(f['\"].*\{.*\}|logger\.\w+\(['\"].*%s",
            "fix": "Use key-value parameters",
            "why": "Structured logs are searchable and parseable",
            "good_example": "logger.info('user_login', user_id=123, ip=request.ip)",
            "bad_example": "logger.info(f'User {user_id} logged in from {ip}')",
        }
    )

    # Pattern: Centralized logging config
    patterns.append(
        {
            "name": "centralized-logging-config",
            "category": "logging",
            "priority": "HIGH",
            "description": "Configure logging in one central module",
            "rule": "Single logging configuration imported everywhere",
            "detect": r"logging\.basicConfig\(|logging\.getLogger\(\)\.setLevel",
            "fix": "Create logging_config.py module",
            "why": "Ensures consistent logging configuration",
            "good_example": "from .logging_config import logger",
            "bad_example": "logging.basicConfig(level=logging.INFO)  # In multiple files",
        }
    )

    # ========== FILE ORGANIZATION PATTERNS ==========

    # Anti-pattern: Backup files in repo
    patterns.append(
        {
            "name": "no-backup-files",
            "category": "organization",
            "priority": "MANDATORY",
            "description": "Remove backup/temporary files from version control",
            "rule": "No _backup, _old, _tmp, .bak files in repository",
            "detect": r"(_backup|_old|_tmp|_copy|\.bak|~|\.(swp|swo))$",
            "fix": "Delete or add to .gitignore",
            "why": "Backup files create confusion and security risks",
            "good_example": ".gitignore contains *.bak",
            "bad_example": "config_backup.py tracked in git",
        }
    )

    # Pattern: Proper test naming
    patterns.append(
        {
            "name": "test-naming-convention",
            "category": "testing",
            "priority": "MEDIUM",
            "description": "Follow test_{component}_{aspect}.py naming",
            "rule": "Test files should clearly indicate what they test",
            "detect": r"test\.py$|tests\.py$|_test\.py$",
            "fix": "Rename to test_{component}_{aspect}.py",
            "why": "Clear test names improve discoverability",
            "good_example": "test_auth_validation.py",
            "bad_example": "auth_tests.py",
        }
    )

    # Pattern: Documentation structure
    patterns.append(
        {
            "name": "organized-documentation",
            "category": "organization",
            "priority": "MEDIUM",
            "description": "Keep documentation in organized structure",
            "rule": "Use docs/ with api/, guides/, architecture/ subdirs",
            "detect": r"(README_\w+\.md|NOTES\.md|TODO\.md|CHANGELOG\d+\.md)$",
            "fix": "Move to appropriate docs/ subdirectory",
            "why": "Organized docs are easier to maintain and find",
            "good_example": "docs/architecture/design.md",
            "bad_example": "README_OLD.md in root",
        }
    )

    # ========== IMPORT PATTERNS ==========

    # Pattern: Import ordering
    patterns.append(
        {
            "name": "standard-import-order",
            "category": "imports",
            "priority": "LOW",
            "description": "Follow standard library, third-party, local import order",
            "rule": "Group imports: stdlib, third-party, local",
            "detect": r"^from \.|^import (?!sys|os|re|json|time|datetime)",
            "fix": "Reorder imports according to convention",
            "why": "Consistent import order improves readability",
            "good_example": "import os\\nimport sys\\n\\nimport requests\\n\\nfrom .config import settings",
            "bad_example": "from .config import settings\\nimport os",
        }
    )

    # Pattern: Relative imports in packages
    patterns.append(
        {
            "name": "prefer-relative-imports",
            "category": "imports",
            "priority": "MEDIUM",
            "description": "Use relative imports within packages",
            "rule": "Use from . imports for internal package modules",
            "detect": r"from\s+(heimdall|circle|hermes|codex)\.",
            "fix": "Convert to relative import",
            "why": "Makes packages more portable and refactorable",
            "good_example": "from .utils import helper",
            "bad_example": "from mypackage.utils import helper",
        }
    )

    # ========== DEPENDENCY PATTERNS ==========

    # Pattern: Use modern tooling
    patterns.append(
        {
            "name": "use-uv-not-pip",
            "category": "dependencies",
            "priority": "HIGH",
            "description": "Use uv for Python package management",
            "rule": "Replace pip with uv for 10-100x faster installs",
            "detect": r"pip\s+install|python\s+-m\s+pip",
            "fix": "Use uv add or uv pip install",
            "why": "uv is significantly faster and more reliable",
            "good_example": "uv add requests",
            "bad_example": "pip install requests",
        }
    )

    # Pattern: Version pinning strategy
    patterns.append(
        {
            "name": "pin-production-dependencies",
            "category": "dependencies",
            "priority": "HIGH",
            "description": "Pin exact versions for production",
            "rule": "Use == for production, >= only for libraries",
            "detect": r"['\"][\w-]+>=\d+\.|['\"][\w-]+~=\d+\.",
            "fix": "Pin to exact version for production",
            "why": "Ensures reproducible deployments",
            "good_example": "requests==2.31.0",
            "bad_example": "requests>=2.28.0",
        }
    )

    # ========== VALIDATION PATTERNS ==========

    # Pattern: Use Pydantic for validation
    patterns.append(
        {
            "name": "pydantic-validation",
            "category": "validation",
            "priority": "HIGH",
            "description": "Use Pydantic models for data validation",
            "rule": "Replace manual validation with Pydantic models",
            "detect": r"if\s+isinstance\(.*,\s*(dict|list|str|int)\)|type\(\w+\)\s*==",
            "fix": "Create Pydantic model",
            "why": "Pydantic provides automatic validation with clear errors",
            "good_example": "class UserInput(BaseModel):\n    name: str\n    age: int",
            "bad_example": "if not isinstance(data, dict):\n    raise ValueError",
        }
    )

    # ========== COMMIT PATTERNS ==========

    # Pattern: Structured commits
    patterns.append(
        {
            "name": "conventional-commits",
            "category": "git",
            "priority": "MEDIUM",
            "description": "Use conventional commit messages",
            "rule": "Format: type(scope): description",
            "detect": r"^(Updated?|Fixed?|Added?|Changed?|Removed?)",
            "fix": "Use: feat:, fix:, docs:, refactor:, test:",
            "why": "Enables automatic changelog generation",
            "good_example": "feat(auth): add OAuth2 support",
            "bad_example": "Updated authentication system",
        }
    )

    return patterns


def add_pattern_metadata(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add consistent metadata to all patterns."""
    for i, pattern in enumerate(patterns):
        pattern.update(
            {
                "id": 2000 + i,  # Start from 2000 for v2 patterns
                "source": "project-init-v2-enhanced",
                "enabled": True,
                "auto_fixable": bool(pattern.get("fix")),
                "confidence": {"MANDATORY": 1.0, "CRITICAL": 0.95, "HIGH": 0.9, "MEDIUM": 0.8, "LOW": 0.7}.get(
                    pattern["priority"], 0.8
                ),
                "tags": f"{pattern['category']} {pattern['priority'].lower()}",
            }
        )
    return patterns


def generate_pattern_documentation(patterns: list[dict[str, Any]]) -> str:
    """Generate markdown documentation for patterns."""
    doc = ["# Codex Patterns from Project-Init v2\n"]
    doc.append("## Overview\n")
    doc.append("These patterns enforce the organizational principles from project-init.json v2.\n\n")

    # Group by category
    categories = {}
    for pattern in patterns:
        cat = pattern["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(pattern)

    # Document each category
    for category in sorted(categories.keys()):
        doc.append(f"## {category.title()} Patterns\n")
        for pattern in categories[category]:
            doc.append(f"### {pattern['name']}\n")
            doc.append(f"**Priority**: {pattern['priority']}\n")
            doc.append(f"**Description**: {pattern['description']}\n")
            doc.append(f"**Rule**: {pattern['rule']}\n")
            doc.append(f"**Why**: {pattern['why']}\n")
            if pattern.get("good_example"):
                doc.append(f"\n**Good Example**:\n```python\n{pattern['good_example']}\n```\n")
            if pattern.get("bad_example"):
                doc.append(f"\n**Bad Example**:\n```python\n{pattern['bad_example']}\n```\n")
            doc.append("\n---\n\n")

    return "\n".join(doc)


def main():
    """Main function to extract enhanced patterns."""
    print("🚀 Enhanced Pattern Extraction from project-init.json v2")
    print("=" * 55)

    # Load project-init
    project_init_path = "/Users/admin/work/project-init.json"
    with open(project_init_path) as f:
        project_init = json.load(f)

    # Extract comprehensive patterns
    patterns = extract_comprehensive_patterns(project_init)
    patterns = add_pattern_metadata(patterns)

    # Statistics
    print("\n📊 Pattern Statistics:")
    print(f"Total patterns: {len(patterns)}")

    # By category
    categories = {}
    for p in patterns:
        categories[p["category"]] = categories.get(p["category"], 0) + 1

    print("\n📁 By Category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat:15} {count:2} patterns")

    # By priority
    priorities = {}
    for p in patterns:
        priorities[p["priority"]] = priorities.get(p["priority"], 0) + 1

    print("\n🎯 By Priority:")
    for prio in ["MANDATORY", "CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if prio in priorities:
            print(f"  • {prio:10} {priorities[prio]:2} patterns")

    # Save patterns
    output_file = "codex_patterns_v2_enhanced.json"
    output = {
        "version": "2.0.0",
        "source": "project-init.json",
        "generated": str(Path(output_file).resolve()),
        "description": "Enhanced patterns from project organization principles",
        "statistics": {"total_patterns": len(patterns), "categories": categories, "priorities": priorities},
        "patterns": patterns,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Saved {len(patterns)} patterns to {output_file}")

    # Generate documentation
    doc_file = "PATTERNS_V2_DOCUMENTATION.md"
    documentation = generate_pattern_documentation(patterns)
    Path(doc_file).write_text(documentation)
    print(f"📚 Generated documentation: {doc_file}")

    # Show high-priority patterns
    print("\n🔴 MANDATORY Patterns:")
    mandatory = [p for p in patterns if p["priority"] == "MANDATORY"]
    for p in mandatory:
        print(f"  • {p['name']}: {p['description']}")

    print("\n🎯 Next Steps:")
    print("1. Review patterns in codex_patterns_v2_enhanced.json")
    print("2. Import: codex import-patterns codex_patterns_v2_enhanced.json")
    print("3. Test: codex scan --patterns project-init-v2")
    print("4. Apply: codex scan --fix")


if __name__ == "__main__":
    main()

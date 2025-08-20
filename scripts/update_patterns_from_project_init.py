#!/usr/bin/env python3
"""
Update Codex patterns from the enhanced project-init.json

This script extracts the new organizational principles and converts them
into actionable Codex patterns.
"""

import json
from typing import Any


def load_project_init(file_path: str) -> dict[str, Any]:
    """Load the project-init.json file."""
    with open(file_path) as f:
        return json.load(f)


def extract_naming_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract naming convention patterns."""
    patterns = []

    # Pattern: Remove redundant package prefixes
    patterns.append(
        {
            "name": "no-redundant-package-prefix",
            "category": "naming",
            "priority": "HIGH",
            "description": "Remove redundant package name prefixes from files and classes",
            "rule": "Don't repeat package name in file or class names within that package",
            "detect": r"class\s+(\w*Package\w+)|(\w+_package\w+\.py)",
            "fix": "Remove the package name prefix/suffix",
            "why": "Reduces redundancy and improves clarity - the package context is already known",
            "good_example": "# In heimdall package\nclass Daemon:  # Not HeimdallDaemon",
            "bad_example": "# In heimdall package\nclass HeimdallDaemon:  # Redundant prefix",
        }
    )

    # Pattern: No version suffixes
    patterns.append(
        {
            "name": "no-version-suffixes",
            "category": "naming",
            "priority": "MANDATORY",
            "description": "Remove version suffixes from canonical implementations",
            "rule": "Use single canonical version without v1, v2, _simple, _new suffixes",
            "detect": r"(_v\d+|_simple|_new|_old|_backup)\.(py|js|ts|go)$",
            "fix": "Consolidate to single canonical implementation",
            "why": "Version suffixes indicate technical debt and unclear ownership",
            "good_example": "server.py  # Single canonical implementation",
            "bad_example": "server_v2.py  # Multiple versions create confusion",
        }
    )

    # Pattern: Descriptive purpose-based naming
    patterns.append(
        {
            "name": "purpose-based-naming",
            "category": "naming",
            "priority": "HIGH",
            "description": "Use purpose-based suffixes instead of implementation details",
            "rule": "Name components by their purpose (manager, handler, client, config)",
            "detect": r"(_impl|_base|_abstract|_concrete)\.(py|js|ts)$",
            "fix": "Rename to describe purpose, not implementation",
            "why": "Purpose-based names are more maintainable and self-documenting",
            "good_example": "cache_manager.py  # Clear purpose",
            "bad_example": "cache_impl_v2.py  # Implementation detail in name",
        }
    )

    return patterns


def extract_fail_fast_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract fail-fast principle patterns."""
    patterns = []

    # Pattern: No silent defaults
    patterns.append(
        {
            "name": "no-silent-defaults",
            "category": "error_handling",
            "priority": "HIGH",
            "description": "Avoid .get() with defaults for required parameters",
            "rule": "Don't use dict.get() with defaults for required configuration",
            "detect": r"\.get\(['\"][\w_]+['\"]\s*,\s*[^)]+\)",
            "fix": "Use direct access and handle KeyError explicitly",
            "why": "Silent defaults hide configuration errors and make debugging harder",
            "good_example": "port = config['port']  # Fails fast if missing",
            "bad_example": "port = config.get('port', 8080)  # Hides missing config",
        }
    )

    # Pattern: Specific exception handling
    patterns.append(
        {
            "name": "specific-exceptions",
            "category": "error_handling",
            "priority": "MANDATORY",
            "description": "Catch specific exceptions, never bare except",
            "rule": "Always catch specific exception types",
            "detect": r"except\s*:|except\s+Exception\s*:",
            "fix": "Replace with specific exception types",
            "why": "Broad exceptions hide bugs and make debugging difficult",
            "good_example": "except FileNotFoundError:",
            "bad_example": "except:  # Catches everything including SystemExit",
        }
    )

    # Pattern: Validate with Pydantic
    patterns.append(
        {
            "name": "use-pydantic-validation",
            "category": "validation",
            "priority": "HIGH",
            "description": "Use Pydantic models for data validation",
            "rule": "Replace manual validation with Pydantic models",
            "detect": r"if\s+not\s+isinstance\(|if\s+type\(.*\)\s*!=",
            "fix": "Create Pydantic model for validation",
            "why": "Pydantic provides automatic validation, serialization, and clear error messages",
            "good_example": "class Config(BaseModel):\n    port: int\n    host: str",
            "bad_example": "if not isinstance(port, int):\n    port = 8080",
        }
    )

    return patterns


def extract_logging_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract logging and observability patterns."""
    patterns = []

    # Pattern: No print statements
    patterns.append(
        {
            "name": "no-print-statements",
            "category": "logging",
            "priority": "HIGH",
            "description": "Replace print statements with structured logging",
            "rule": "Use logging module instead of print() in production code",
            "detect": r"print\s*\(",
            "fix": "Replace with logger.info() or appropriate log level",
            "why": "Print statements can't be controlled, filtered, or structured",
            "good_example": "logger.info('Processing request', user_id=user_id)",
            "bad_example": "print(f'Processing request for {user_id}')",
        }
    )

    # Pattern: Structured logging
    patterns.append(
        {
            "name": "structured-logging",
            "category": "logging",
            "priority": "MEDIUM",
            "description": "Use structured logging with key-value pairs",
            "rule": "Log with structured data instead of string formatting",
            "detect": r"logger\.\w+\(f['\"]|logger\.\w+\(['\"].*%",
            "fix": "Use structured logging with key-value pairs",
            "why": "Structured logs are searchable, parseable, and integrable with monitoring",
            "good_example": "logger.info('user_action', action='login', user_id=123)",
            "bad_example": "logger.info(f'User {user_id} logged in')",
        }
    )

    # Pattern: Centralized logging config
    patterns.append(
        {
            "name": "centralized-logging",
            "category": "logging",
            "priority": "HIGH",
            "description": "Use centralized logging configuration",
            "rule": "Configure logging in one place, import everywhere",
            "detect": r"logging\.basicConfig\(|logging\.getLogger\(__name__\)\.setLevel",
            "fix": "Create central logging config module",
            "why": "Centralized configuration ensures consistent logging across the application",
            "good_example": "from .logging_config import get_logger\nlogger = get_logger(__name__)",
            "bad_example": "import logging\nlogging.basicConfig(level=logging.INFO)",
        }
    )

    return patterns


def extract_file_organization_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract file and folder organization patterns."""
    patterns = []

    # Pattern: Proper documentation structure
    patterns.append(
        {
            "name": "documentation-structure",
            "category": "organization",
            "priority": "MEDIUM",
            "description": "Organize documentation in standard folders",
            "rule": "Use docs/api/, docs/architecture/, docs/guides/ structure",
            "detect": r"(README_.*\.md|NOTES\.md|TODO\.md)$",
            "fix": "Move to appropriate docs/ subfolder",
            "why": "Organized documentation is easier to maintain and discover",
            "good_example": "docs/architecture/system-design.md",
            "bad_example": "README_OLD.md in root directory",
        }
    )

    # Pattern: Test organization
    patterns.append(
        {
            "name": "test-file-naming",
            "category": "testing",
            "priority": "MEDIUM",
            "description": "Use consistent test file naming",
            "rule": "Name tests as test_{component}_{aspect}.py",
            "detect": r"test_.*\.py$",
            "fix": "Rename to follow pattern: test_{component}_{aspect}.py",
            "why": "Consistent naming makes tests discoverable and their purpose clear",
            "good_example": "test_auth_validation.py",
            "bad_example": "auth_tests.py",
        }
    )

    # Pattern: No backup files in production
    patterns.append(
        {
            "name": "no-backup-files",
            "category": "organization",
            "priority": "MANDATORY",
            "description": "Remove backup and temporary files from version control",
            "rule": "No _backup, _old, _tmp files in production code",
            "detect": r"(_backup|_old|_tmp|\.bak|~)$",
            "fix": "Delete or move to archive if needed",
            "why": "Backup files create confusion and potential security risks",
            "good_example": "config.py  # Current version only",
            "bad_example": "config_backup.py  # Should not be in repo",
        }
    )

    return patterns


def extract_import_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract import organization patterns."""
    patterns = []

    # Pattern: Import order
    patterns.append(
        {
            "name": "import-order",
            "category": "imports",
            "priority": "LOW",
            "description": "Follow standard import ordering",
            "rule": "Standard library, third-party, then local imports",
            "detect": r"^import|^from\s+\w+\s+import",
            "fix": "Reorder imports: stdlib, third-party, local",
            "why": "Consistent import order improves readability",
            "good_example": "import os\nimport sys\n\nimport requests\n\nfrom .config import settings",
            "bad_example": "from .config import settings\nimport requests\nimport os",
        }
    )

    # Pattern: Relative imports within package
    patterns.append(
        {
            "name": "use-relative-imports",
            "category": "imports",
            "priority": "MEDIUM",
            "description": "Use relative imports within packages",
            "rule": "Prefer relative imports for internal package modules",
            "detect": r"from\s+mypackage\.",
            "fix": "Replace with relative import",
            "why": "Relative imports make packages more portable and refactorable",
            "good_example": "from .utils import helper",
            "bad_example": "from mypackage.utils import helper",
        }
    )

    return patterns


def extract_dependency_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract dependency management patterns."""
    patterns = []

    # Pattern: Use modern tools
    patterns.append(
        {
            "name": "use-modern-tools",
            "category": "dependencies",
            "priority": "HIGH",
            "description": "Use uv for Python dependency management",
            "rule": "Prefer uv over pip for faster, more reliable dependency management",
            "detect": r"pip\s+install|requirements\.txt",
            "fix": "Migrate to uv and pyproject.toml",
            "why": "uv is 10-100x faster than pip and more reliable",
            "good_example": "uv add requests",
            "bad_example": "pip install requests",
        }
    )

    # Pattern: Pin versions in production
    patterns.append(
        {
            "name": "pin-production-versions",
            "category": "dependencies",
            "priority": "HIGH",
            "description": "Pin exact versions in production",
            "rule": "Use exact version pins for production dependencies",
            "detect": r"['\"][\w-]+>=|['\"][\w-]+~=",
            "fix": "Pin to exact version for production",
            "why": "Exact versions ensure reproducible deployments",
            "good_example": "requests==2.31.0",
            "bad_example": "requests>=2.0.0",
        }
    )

    return patterns


def create_codex_patterns(project_init: dict[str, Any]) -> list[dict[str, Any]]:
    """Create comprehensive Codex patterns from project-init."""
    all_patterns = []

    # Extract patterns from each category
    all_patterns.extend(extract_naming_patterns(project_init))
    all_patterns.extend(extract_fail_fast_patterns(project_init))
    all_patterns.extend(extract_logging_patterns(project_init))
    all_patterns.extend(extract_file_organization_patterns(project_init))
    all_patterns.extend(extract_import_patterns(project_init))
    all_patterns.extend(extract_dependency_patterns(project_init))

    # Add metadata to each pattern
    for i, pattern in enumerate(all_patterns):
        pattern["id"] = i + 1000  # Start from 1000 to avoid conflicts
        pattern["source"] = "project-init-v2"
        pattern["enabled"] = True
        pattern["auto_fixable"] = pattern.get("fix", "") != ""

    return all_patterns


def save_patterns(patterns: list[dict[str, Any]], output_file: str):
    """Save patterns to JSON file."""
    output = {
        "version": "2.0.0",
        "source": "project-init.json",
        "description": "Patterns extracted from updated project organization principles",
        "patterns": patterns,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Saved {len(patterns)} patterns to {output_file}")


def main():
    """Main function to extract and convert patterns."""
    print("🚀 Extracting patterns from updated project-init.json")
    print("=" * 50)

    # Load project-init
    project_init_path = "/Users/admin/work/project-init.json"
    project_init = load_project_init(project_init_path)

    # Extract patterns
    patterns = create_codex_patterns(project_init)

    # Display summary
    print("\n📊 Pattern Summary:")
    print(f"Total patterns extracted: {len(patterns)}")

    # Group by category
    categories = {}
    for pattern in patterns:
        cat = pattern["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("\nPatterns by category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count} patterns")

    # Group by priority
    priorities = {}
    for pattern in patterns:
        prio = pattern["priority"]
        priorities[prio] = priorities.get(prio, 0) + 1

    print("\nPatterns by priority:")
    for prio in ["MANDATORY", "CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if prio in priorities:
            print(f"  • {prio}: {priorities[prio]} patterns")

    # Save patterns
    output_file = "patterns_from_project_init_v2.json"
    save_patterns(patterns, output_file)

    # Show some examples
    print("\n🔍 Sample Patterns:")
    for pattern in patterns[:3]:
        print(f"\n[{pattern['priority']}] {pattern['name']}")
        print(f"  Description: {pattern['description']}")
        print(f"  Rule: {pattern['rule']}")
        print(f"  Why: {pattern['why']}")

    print("\n✨ Pattern extraction complete!")
    print(f"📁 Patterns saved to: {output_file}")
    print("\nNext steps:")
    print("1. Review the generated patterns")
    print("2. Import into Codex: codex import-patterns patterns_from_project_init_v2.json")
    print("3. Run scan with new patterns: codex scan --patterns project-init-v2")


if __name__ == "__main__":
    main()

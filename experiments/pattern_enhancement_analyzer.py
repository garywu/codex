#!/usr/bin/env python3
"""
Pattern Enhancement Analyzer - Extract new patterns from project-init.json

Uses Claude intelligence to analyze the updated project-init.json and identify
new pattern opportunities for Codex scanning and fixing.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class PatternEnhancementAnalyzer:
    """Intelligently analyzes project-init.json for new pattern opportunities."""

    def __init__(self, project_init_path: Path):
        self.project_init_path = project_init_path
        self.project_init = self._load_project_init()
        self.new_patterns = []

    def _load_project_init(self) -> dict[str, Any]:
        """Load and parse project-init.json."""
        with open(self.project_init_path) as f:
            return json.load(f)

    def analyze_zombie_code_patterns(self) -> list[dict[str, Any]]:
        """Extract zombie code detection patterns."""
        zombie_config = self.project_init.get("project_organization", {}).get("zombie_code_management", {})

        patterns = []

        # Pattern 1: Versioned Files
        patterns.append(
            {
                "name": "zombie_versioned_files",
                "category": "code_quality",
                "priority": "HIGH",
                "description": "Detect files with version suffixes that indicate zombie code",
                "detection_rules": {
                    "file_patterns": [
                        r".*_v[0-9]+\.py$",
                        r".*_v[0-9]+_[0-9]+\.py$",
                        r".*_simple\.py$",
                        r".*_legacy\.py$",
                        r".*_backup\.py$",
                        r".*_old\.py$",
                        r".*_new\.py$",
                        r".*_original\.py$",
                        r".*_copy\.py$",
                    ],
                    "excludes": [
                        r"test_.*",  # Test files can have versions
                        r".*_test\.py$",
                        r"migrations/.*",  # Migration files legitimately versioned
                    ],
                },
                "rationale": zombie_config.get("detection_principles", {}).get("pattern_recognition", ""),
                "fix_strategy": "consolidate_to_canonical",
                "severity": "WARNING",
            }
        )

        # Pattern 2: Duplicate Class Names
        patterns.append(
            {
                "name": "zombie_duplicate_classes",
                "category": "code_quality",
                "priority": "HIGH",
                "description": "Detect multiple implementations of the same class",
                "detection_rules": {
                    "content_patterns": [
                        r"class\s+(\w+)Handler\s*\(",
                        r"class\s+(\w+)Manager\s*\(",
                        r"class\s+(\w+)Service\s*\(",
                        r"class\s+(\w+)Client\s*\(",
                    ],
                    "analysis_type": "cross_file_duplicate_detection",
                },
                "rationale": "Multiple implementations indicate zombie code needing consolidation",
                "fix_strategy": "establish_canonical_implementation",
                "severity": "WARNING",
            }
        )

        return patterns

    def analyze_mock_code_patterns(self) -> list[dict[str, Any]]:
        """Extract mock code policy enforcement patterns."""
        mock_config = self.project_init.get("mock_code_policy", {})

        patterns = []

        # Pattern 1: Mock Naming Compliance
        patterns.append(
            {
                "name": "mock_naming_compliance",
                "category": "security",
                "priority": "MANDATORY",
                "description": "Enforce strict mock code naming requirements",
                "detection_rules": {
                    "content_patterns": [
                        # Functions that look like mocks but don't follow naming
                        r"def\s+((?!mock_)\w*mock\w*)\s*\(",
                        r"def\s+((?!mock_)\w*fake\w*)\s*\(",
                        r"def\s+((?!mock_)\w*dummy\w*)\s*\(",
                        r"def\s+((?!mock_)\w*stub\w*)\s*\(",
                        # Classes that look like mocks but don't follow naming
                        r"class\s+((?!Mock)\w*Mock\w*)\s*\(",
                        r"class\s+((?!Mock)\w*Fake\w*)\s*\(",
                        r"class\s+((?!Mock)\w*Dummy\w*)\s*\(",
                    ],
                    "file_patterns": [
                        # Files that look like mocks but don't start with mock_
                        r"(?!mock_).*mock.*\.py$",
                        r"(?!mock_).*fake.*\.py$",
                        r"(?!mock_).*dummy.*\.py$",
                    ],
                },
                "rationale": mock_config.get("strict_requirements", {}).get("naming", {}),
                "fix_strategy": "rename_to_mock_prefix",
                "severity": "ERROR",
            }
        )

        # Pattern 2: Mock Warning Requirements
        patterns.append(
            {
                "name": "mock_warning_requirements",
                "category": "security",
                "priority": "MANDATORY",
                "description": "Ensure all mock functions log warnings",
                "detection_rules": {
                    "content_patterns": [
                        # Mock functions without warning logs
                        r"def\s+mock_\w+\s*\([^)]*\):[^}]*?(?!.*warning.*mock).*?(?=def|\Z)",
                    ],
                    "required_patterns": [
                        r"logfire\.warning.*⚠️\s*MOCK",
                        r"logging\.warning.*⚠️\s*MOCK",
                        r"logger\.warning.*⚠️\s*MOCK",
                    ],
                },
                "rationale": "All mock functions must log warnings for visibility",
                "fix_strategy": "add_mock_warnings",
                "severity": "ERROR",
            }
        )

        return patterns

    def analyze_architectural_patterns(self) -> list[dict[str, Any]]:
        """Extract architectural separation validation patterns."""
        arch_config = self.project_init.get("project_organization", {}).get("architectural_separation", {})

        patterns = []

        # Pattern 1: Business Logic in CLI
        patterns.append(
            {
                "name": "business_logic_in_cli",
                "category": "architecture",
                "priority": "HIGH",
                "description": "Detect business logic that should be in core package",
                "detection_rules": {
                    "file_patterns": [r".*cli\.py$", r"cli/.*\.py$"],
                    "content_patterns": [
                        # Complex business logic indicators in CLI files
                        r"class\s+\w+(?:Service|Manager|Handler|Engine|Processor)\s*\(",
                        r"def\s+(?:process|calculate|analyze|generate|transform)_\w+",
                        r"(?:for|while)\s+\w+\s+in.*:.*(?:for|while)",  # Nested loops
                        r"try:\s*\n.*except\s+\w+.*:\s*\n.*(?:raise|return)",  # Complex error handling
                    ],
                    "excludes": [
                        r"def\s+.*(?:parse|format|display|print|show).*",  # UI operations
                        r"typer\.",  # Typer CLI framework usage
                        r"click\.",  # Click CLI framework usage
                    ],
                },
                "rationale": arch_config.get("core_business_logic", {}).get("principle", ""),
                "fix_strategy": "move_to_core_package",
                "severity": "WARNING",
            }
        )

        # Pattern 2: Package Name Redundancy
        patterns.append(
            {
                "name": "redundant_package_naming",
                "category": "architecture",
                "priority": "MEDIUM",
                "description": "Detect redundant naming within packages",
                "detection_rules": {
                    "analysis_type": "package_scoping_analysis",
                    "patterns": [
                        # Files repeating package name
                        r"codex/codex_\w+\.py$",
                        r"hepha/hepha_\w+\.py$",
                        # Classes repeating package name
                        r"class\s+Codex\w+.*:",
                        r"class\s+Hepha\w+.*:",
                        # Functions repeating package name
                        r"def\s+codex_\w+",
                        r"def\s+hepha_\w+",
                    ],
                },
                "rationale": "Package scoping eliminates need for redundant naming",
                "fix_strategy": "remove_redundant_prefixes",
                "severity": "INFO",
            }
        )

        return patterns

    def analyze_security_patterns(self) -> list[dict[str, Any]]:
        """Extract security best practice patterns."""
        security_config = self.project_init.get("security_best_practices", {})

        patterns = []

        # Pattern 1: Never Wildcard CORS
        patterns.append(
            {
                "name": "cors_never_wildcard",
                "category": "security",
                "priority": "MANDATORY",
                "description": "NEVER use wildcard (*) in production CORS origins",
                "detection_rules": {
                    "content_patterns": [
                        r'allow_origins\s*=\s*\[\s*["\']?\*["\']?\s*\]',
                        r'origins\s*=\s*\[\s*["\']?\*["\']?\s*\]',
                        r"Access-Control-Allow-Origin.*\*",
                        r"CORS.*origins.*\*",
                    ],
                    "excludes": [
                        r"#.*test",  # Test configuration comments
                        r"development",  # Development environment
                        r"local",  # Local development
                    ],
                },
                "rationale": security_config.get("cors_configuration", {}).get("never_wildcard", ""),
                "fix_strategy": "specify_exact_origins",
                "severity": "ERROR",
            }
        )

        # Pattern 2: Hardcoded Secrets
        patterns.append(
            {
                "name": "hardcoded_secrets",
                "category": "security",
                "priority": "CRITICAL",
                "description": "Detect hardcoded secrets and credentials",
                "detection_rules": {
                    "content_patterns": [
                        r'(?:password|secret|key|token)\s*=\s*["\'][^"\']{8,}["\']',
                        r'(?:api_key|auth_token|jwt_secret)\s*=\s*["\'][^"\']+["\']',
                        r"Bearer\s+[A-Za-z0-9_-]{20,}",
                        r"(?:sk-|pk_)[A-Za-z0-9_-]{32,}",
                    ],
                    "excludes": [r"test_.*", r"example", r"placeholder", r"your_.*_here"],
                },
                "rationale": "Never commit secrets to version control",
                "fix_strategy": "use_environment_variables",
                "severity": "CRITICAL",
            }
        )

        return patterns

    def analyze_pre_commit_patterns(self) -> list[dict[str, Any]]:
        """Extract pre-commit compliance patterns."""
        ci_config = self.project_init.get("continuous_integration", {}).get("pre_commit_workflow", {})

        patterns = []

        # Pattern 1: Skip Flag Usage
        patterns.append(
            {
                "name": "pre_commit_skip_usage",
                "category": "code_quality",
                "priority": "HIGH",
                "description": "Detect usage of SKIP flags in commits",
                "detection_rules": {
                    "git_patterns": [r"SKIP=.*git\s+commit", r"git\s+commit.*--no-verify", r"pre-commit.*--no-verify"],
                    "commit_message_patterns": [r"SKIP=", r"skip.*pre-commit", r"ignore.*linting", r"will.*fix.*later"],
                },
                "rationale": ci_config.get("zero_tolerance_policy", {}).get("fundamental_rule", ""),
                "fix_strategy": "enforce_pre_commit_compliance",
                "severity": "ERROR",
            }
        )

        return patterns

    def analyze_all_pattern_opportunities(self) -> list[dict[str, Any]]:
        """Analyze all sections for new pattern opportunities."""
        print("=== ANALYZING PROJECT-INIT.JSON FOR PATTERN OPPORTUNITIES ===")

        all_patterns = []

        # Analyze each section
        zombie_patterns = self.analyze_zombie_code_patterns()
        mock_patterns = self.analyze_mock_code_patterns()
        arch_patterns = self.analyze_architectural_patterns()
        security_patterns = self.analyze_security_patterns()
        pre_commit_patterns = self.analyze_pre_commit_patterns()

        all_patterns.extend(zombie_patterns)
        all_patterns.extend(mock_patterns)
        all_patterns.extend(arch_patterns)
        all_patterns.extend(security_patterns)
        all_patterns.extend(pre_commit_patterns)

        print(f"Found {len(all_patterns)} new pattern opportunities:")
        for pattern in all_patterns:
            print(f"  - {pattern['name']}: {pattern['description']}")

        return all_patterns

    def create_pattern_enhancement_report(self, patterns: list[dict[str, Any]]) -> str:
        """Create comprehensive report of pattern enhancements."""
        timestamp = datetime.now().isoformat()

        report = f"""
PATTERN ENHANCEMENT ANALYSIS REPORT ({timestamp})

PROJECT-INIT.JSON ANALYSIS COMPLETE:
- Source: {self.project_init_path}
- Version: {self.project_init.get('project_organization', {}).get('version', 'unknown')}
- Last Updated: {self.project_init.get('project_organization', {}).get('last_updated', 'unknown')}

NEW PATTERN OPPORTUNITIES IDENTIFIED:
- Total patterns: {len(patterns)}
- Critical/Mandatory: {len([p for p in patterns if p['priority'] in ['CRITICAL', 'MANDATORY']])}
- High priority: {len([p for p in patterns if p['priority'] == 'HIGH'])}
- Medium/Low priority: {len([p for p in patterns if p['priority'] in ['MEDIUM', 'LOW', 'INFO']])}

PATTERNS BY CATEGORY:
"""

        by_category = {}
        for pattern in patterns:
            category = pattern["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(pattern)

        for category, cat_patterns in sorted(by_category.items()):
            report += f"\n{category.upper()} ({len(cat_patterns)} patterns):\n"
            for pattern in cat_patterns:
                report += f"  - {pattern['name']} ({pattern['priority']}): {pattern['description']}\n"

        report += f"""
HIGH-IMPACT PATTERNS FOR IMMEDIATE IMPLEMENTATION:

1. ZOMBIE CODE DETECTION:
   - Systematic detection of versioned files (v1, v2, legacy, backup)
   - Cross-file duplicate class detection
   - Consolidation workflow automation

2. SECURITY ENFORCEMENT:
   - CORS wildcard prevention (MANDATORY)
   - Hardcoded secrets detection (CRITICAL)
   - Mock code policy compliance (MANDATORY)

3. ARCHITECTURAL VALIDATION:
   - Business logic separation enforcement
   - Package naming redundancy elimination
   - Core-interface layer validation

4. QUALITY ASSURANCE:
   - Pre-commit compliance monitoring
   - Zero tolerance policy enforcement
   - Systematic technical debt prevention

INTEGRATION WITH EXISTING INTELLIGENCE:
✅ Patterns designed for Claude intelligence analysis
✅ Context-aware detection with exclude rules
✅ Severity-based prioritization for smart fixing
✅ Compatible with existing modular fixer architecture

NEXT STEPS:
1. Implement high-priority patterns in Codex scanner
2. Create intelligent fixers for MANDATORY/CRITICAL issues
3. Test patterns on Codex codebase for validation
4. Apply systematic fixing with enhanced pattern set

PATTERN ENHANCEMENT PHILOSOPHY:
These patterns embody the project-init.json principles:
- Zero tolerance for technical debt accumulation
- Systematic quality improvement over time
- Intelligence-driven analysis over blind automation
- Context-aware decision making with exclude rules
"""

        return report


def main():
    """Analyze project-init.json for pattern enhancement opportunities."""
    project_init_path = Path("/Users/admin/work/project-init.json")

    if not project_init_path.exists():
        print(f"Error: {project_init_path} not found")
        return

    analyzer = PatternEnhancementAnalyzer(project_init_path)
    patterns = analyzer.analyze_all_pattern_opportunities()

    report = analyzer.create_pattern_enhancement_report(patterns)
    print(report)

    # Save patterns to JSON for integration
    patterns_file = Path(__file__).parent / "enhanced_patterns.json"
    with open(patterns_file, "w") as f:
        json.dump(patterns, f, indent=2, default=str)

    print(f"\n=== ANALYSIS COMPLETE ===")
    print(f"Enhanced patterns saved to: {patterns_file}")
    print(f"Ready for systematic implementation in Codex scanner")


if __name__ == "__main__":
    main()

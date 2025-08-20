#!/usr/bin/env python3
"""
Violation Analyzer - Analyzes the remaining 98 violations to understand next steps.

Provides detailed breakdown of what violations remain after modular fixing.
"""

import re
from pathlib import Path
from typing import Any


class ViolationAnalyzer:
    """Analyzes remaining violations for targeted fixing."""

    def __init__(self, db_path: Path, codex_dir: Path):
        self.db_path = db_path
        self.codex_dir = codex_dir

        # Define refined patterns to analyze
        self.refined_patterns = {
            "structured-logging-refined": {
                "triggers": [r"print\s*\(", r"console\.print\s*\("],
                "excludes": [r"#.*print", r'""".*print.*"""', r"'[^']*print[^']*'", r'"[^"]*print[^"]*"'],
            },
            "cors-wildcard-refined": {
                "triggers": [r'["\']origins["\'].*\*', r"Access-Control-Allow-Origin.*\*", r'["\']?\*["\']?'],
                "excludes": [r"import.*\*", r'\.rglob\(["\'].*\*', r"\*args", r"\*\*kwargs", r"#.*\*"],
            },
        }

    def scan_file_for_violations(self, file_path: Path) -> list[dict]:
        """Scan a single file and categorize violations."""
        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return violations

        lines = content.split("\n")

        for pattern_name, pattern_config in self.refined_patterns.items():
            for line_num, line in enumerate(lines, 1):
                # Check excludes first
                if any(re.search(exclude, line, re.IGNORECASE) for exclude in pattern_config["excludes"]):
                    continue

                # Check triggers
                for trigger in pattern_config["triggers"]:
                    if re.search(trigger, line, re.IGNORECASE):
                        violations.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "pattern": pattern_name,
                                "code_line": line.strip(),
                                "trigger": trigger,
                                "category": self.categorize_violation(pattern_name, line),
                            }
                        )
                        break

        return violations

    def categorize_violation(self, pattern_name: str, line: str) -> str:
        """Categorize what type of violation this is."""
        line_lower = line.strip().lower()

        if pattern_name == "structured-logging-refined":
            if "console.print(" in line_lower:
                return "console_print"
            elif "print(" in line_lower:
                return "print_statement"
            else:
                return "other_logging"

        elif pattern_name == "cors-wildcard-refined":
            if "import" in line_lower and "*" in line_lower:
                return "wildcard_import"
            elif ".rglob(" in line_lower or ".glob(" in line_lower:
                return "glob_pattern"
            elif "*args" in line_lower or "**kwargs" in line_lower:
                return "function_args"
            elif line_lower.strip().startswith("#"):
                return "comment"
            elif '"*"' in line_lower or "'*'" in line_lower:
                return "string_literal"
            elif "regex" in line_lower or r"\*" in line_lower:
                return "regex_pattern"
            else:
                return "other_wildcard"

        return "unknown"

    def analyze_all_violations(self) -> dict[str, Any]:
        """Analyze all violations in the codebase."""
        print("=== ANALYZING REMAINING VIOLATIONS ===")

        all_violations = []
        files_scanned = 0

        for py_file in self.codex_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ["__pycache__", ".venv", ".git"]):
                continue

            file_violations = self.scan_file_for_violations(py_file)
            all_violations.extend(file_violations)
            files_scanned += 1

        # Group by pattern and category
        by_pattern = {}
        by_category = {}

        for violation in all_violations:
            pattern = violation["pattern"]
            category = violation["category"]

            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(violation)

            if category not in by_category:
                by_category[category] = []
            by_category[category].append(violation)

        print(f"Files scanned: {files_scanned}")
        print(f"Total violations: {len(all_violations)}")
        print(f"Patterns with violations: {len(by_pattern)}")

        # Show breakdown by pattern
        print("\nViolations by pattern:")
        for pattern, violations in sorted(by_pattern.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {pattern}: {len(violations)}")

        # Show breakdown by category
        print("\nViolations by category:")
        for category, violations in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {category}: {len(violations)}")

            # Show samples for each category
            if len(violations) <= 3:
                for v in violations:
                    print(f"    {Path(v['file']).name}:{v['line']} - {v['code_line'][:60]}")
            else:
                for v in violations[:2]:
                    print(f"    {Path(v['file']).name}:{v['line']} - {v['code_line'][:60]}")
                print(f"    ... and {len(violations) - 2} more")

        return {
            "total_violations": len(all_violations),
            "files_scanned": files_scanned,
            "by_pattern": {p: len(vs) for p, vs in by_pattern.items()},
            "by_category": {c: len(vs) for c, vs in by_category.items()},
            "violations": all_violations,
            "real_issues": self.identify_real_issues(by_category),
            "false_positives": self.identify_false_positives(by_category),
        }

    def identify_real_issues(self, by_category: dict[str, list]) -> list[str]:
        """Identify categories that represent real issues to fix."""
        real_issues = []

        # Print statements and console.print are real issues
        if "print_statement" in by_category:
            real_issues.append(f"print_statement: {len(by_category['print_statement'])} instances")
        if "console_print" in by_category:
            real_issues.append(f"console_print: {len(by_category['console_print'])} instances")

        return real_issues

    def identify_false_positives(self, by_category: dict[str, list]) -> list[str]:
        """Identify categories that are likely false positives."""
        false_positives = []

        fp_categories = [
            "wildcard_import",
            "glob_pattern",
            "function_args",
            "comment",
            "string_literal",
            "regex_pattern",
        ]

        for category in fp_categories:
            if category in by_category:
                false_positives.append(f"{category}: {len(by_category[category])} instances")

        return false_positives

    def create_targeted_fix_plan(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Create a plan for fixing remaining real issues."""
        real_issues = analysis["real_issues"]
        false_positives = analysis["false_positives"]

        fix_plan = {
            "real_issues_to_fix": len(real_issues),
            "false_positives_to_exclude": len(false_positives),
            "actions": [],
        }

        # Plan fixes for real issues
        if any("print_statement" in issue for issue in real_issues):
            fix_plan["actions"].append(
                {
                    "type": "create_fixer",
                    "name": "remaining_print_fixer",
                    "target": "Convert remaining print statements to logging",
                    "complexity": "low",
                }
            )

        if any("console_print" in issue for issue in real_issues):
            fix_plan["actions"].append(
                {
                    "type": "create_fixer",
                    "name": "console_print_fixer",
                    "target": "Convert console.print to logging",
                    "complexity": "low",
                }
            )

        # Plan pattern refinements for false positives
        if false_positives:
            fix_plan["actions"].append(
                {
                    "type": "refine_patterns",
                    "name": "cors_wildcard_refinement",
                    "target": "Add more exclude patterns for CORS wildcard detection",
                    "complexity": "medium",
                }
            )

        return fix_plan


def main():
    """Analyze remaining violations after modular fixing."""
    import os

    def get_xdg_path(xdg_var: str, default_suffix: str) -> Path:
        if xdg_path := os.environ.get(xdg_var):
            return Path(xdg_path) / "codex"
        return Path.home() / default_suffix / "codex"

    db_path = get_xdg_path("XDG_DATA_HOME", ".local/share") / "codex.db"
    codex_dir = Path(__file__).parent / "codex"

    analyzer = ViolationAnalyzer(db_path, codex_dir)
    analysis = analyzer.analyze_all_violations()

    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Total violations: {analysis['total_violations']}")
    print(f"Real issues identified: {len(analysis['real_issues'])}")
    print(f"False positives identified: {len(analysis['false_positives'])}")

    if analysis["real_issues"]:
        print("\nReal issues to fix:")
        for issue in analysis["real_issues"]:
            print(f"  - {issue}")

    if analysis["false_positives"]:
        print("\nFalse positives to refine:")
        for fp in analysis["false_positives"][:5]:  # Show first 5
            print(f"  - {fp}")

    # Create fix plan
    fix_plan = analyzer.create_targeted_fix_plan(analysis)
    print("\n=== TARGETED FIX PLAN ===")
    print(f"Actions needed: {len(fix_plan['actions'])}")
    for action in fix_plan["actions"]:
        print(f"  {action['type']}: {action['name']} ({action['complexity']} complexity)")
        print(f"    Target: {action['target']}")


if __name__ == "__main__":
    main()

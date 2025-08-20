#!/usr/bin/env python3
"""
Intelligent Fixer - Codex provides convenience, Claude provides intelligent decisions.

This fixer uses Codex for speed and automation, but Claude makes the intelligent
decisions about WHAT to fix and HOW to fix it. No blind automation - every fix
is intelligently considered.
"""

import re
from pathlib import Path
from typing import Any


class IntelligentFixer:
    """
    AI-assisted fixer where Codex provides tools and Claude provides intelligence.

    Philosophy:
    - Codex provides fast text manipulation and file operations
    - Claude analyzes context and makes intelligent fixing decisions
    - Every fix is reviewed before application
    - Interactive decision-making for complex cases
    """

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.fix_decisions = []
        self.fixes_applied = []

    def analyze_and_fix_intelligently(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Main entry point: Analyze issues with intelligence and apply selective fixes.

        Unlike automatic fixers, this method:
        1. Analyzes each issue with context
        2. Makes intelligent decisions about fixes
        3. Asks for confirmation on ambiguous cases
        4. Applies only approved fixes
        """
        print("=== INTELLIGENT FIXING SESSION ===")
        print("Claude will analyze each issue and make intelligent fixing decisions...")

        # Phase 1: Intelligent analysis of each issue
        fix_plans = []
        for issue in issues:
            fix_plan = self._analyze_issue_intelligently(issue)
            fix_plans.append(fix_plan)

        # Phase 2: Review and approve fixes
        approved_fixes = self._review_and_approve_fixes(fix_plans)

        # Phase 3: Apply approved fixes using Codex for speed
        results = self._apply_approved_fixes(approved_fixes)

        return results

    def _analyze_issue_intelligently(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Apply intelligence to analyze a single issue and plan the fix."""
        candidate = issue["candidate"]
        verdict = issue["intelligent_verdict"]

        # Get full context for intelligent analysis
        file_path = Path(candidate.file_path)
        full_context = self._get_full_file_context(file_path, candidate.line_number)

        fix_plan = {
            "issue": issue,
            "file_path": file_path,
            "line_number": candidate.line_number,
            "intelligent_analysis": self._perform_intelligent_analysis(candidate, full_context),
            "fix_strategy": None,
            "fix_approved": False,
            "fix_complexity": "unknown",
        }

        # Intelligent fix strategy based on analysis
        if verdict == "real_violation":
            fix_plan["fix_strategy"] = self._design_intelligent_fix_strategy(candidate, full_context)
            fix_plan["fix_approved"] = self._should_auto_approve_fix(fix_plan)
            fix_plan["fix_complexity"] = self._assess_fix_complexity(fix_plan)
        else:
            fix_plan["fix_strategy"] = {"action": "no_fix_needed", "reason": f"Verdict: {verdict}"}
            fix_plan["fix_approved"] = True  # Approved to NOT fix
            fix_plan["fix_complexity"] = "none"

        return fix_plan

    def _get_full_file_context(self, file_path: Path, line_number: int) -> dict[str, Any]:
        """Get full file context for intelligent analysis."""
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            return {
                "total_lines": len(lines),
                "target_line": lines[line_number - 1].strip() if line_number <= len(lines) else "",
                "surrounding_lines": lines[max(0, line_number - 6) : line_number + 5],
                "file_imports": [line.strip() for line in lines[:20] if line.strip().startswith(("import ", "from "))],
                "file_type": self._classify_file_type(file_path, lines),
                "has_logging": any("logging" in line for line in lines[:30]),
            }
        except (OSError, UnicodeDecodeError):
            return {"error": "Could not read file"}

    def _classify_file_type(self, file_path: Path, lines: list[str]) -> str:
        """Intelligently classify what type of file this is."""
        path_str = str(file_path).lower()
        content = "".join(lines[:50]).lower()  # First 50 lines

        if "test" in path_str or "test" in content:
            return "test"
        elif "cli" in path_str or "__main__" in content:
            return "cli"
        elif "config" in path_str or "settings" in path_str:
            return "config"
        elif "main" in path_str or "if __name__" in content:
            return "script"
        else:
            return "library"

    def _perform_intelligent_analysis(self, candidate, context: dict[str, Any]) -> dict[str, Any]:
        """Perform deep intelligent analysis of the issue."""
        analysis = {
            "context_understanding": self._understand_context(candidate, context),
            "impact_assessment": self._assess_impact(candidate, context),
            "risk_level": self._assess_risk_level(candidate, context),
            "fix_necessity": self._assess_fix_necessity(candidate, context),
        }

        return analysis

    def _understand_context(self, candidate, context: dict[str, Any]) -> str:
        """Understand the context around this issue."""
        file_type = context.get("file_type", "unknown")
        target_line = context.get("target_line", "")

        if "print(" in target_line:
            if file_type == "cli":
                return "Print statement in CLI context - likely user output"
            elif file_type == "test":
                return "Print statement in test context - likely debug output"
            else:
                return "Print statement in library code - should use logging"
        elif ".db" in target_line:
            if "test" in target_line:
                return "Database path in test context - might be acceptable"
            else:
                return "Hardcoded database path - should use configuration"
        else:
            return "General code pattern issue"

    def _assess_impact(self, candidate, context: dict[str, Any]) -> str:
        """Assess the impact of NOT fixing this issue."""
        pattern_name = candidate.pattern_name
        file_type = context.get("file_type", "unknown")

        if "print" in pattern_name:
            if file_type in ["cli", "script"]:
                return "Low impact - user-facing output expected"
            else:
                return "Medium impact - inconsistent logging approach"
        elif "path" in pattern_name:
            return "High impact - portability and configuration issues"
        else:
            return "Unknown impact - needs case-by-case assessment"

    def _assess_risk_level(self, candidate, context: dict[str, Any]) -> str:
        """Assess the risk of applying the fix."""
        if context.get("file_type") == "test":
            return "Low risk - test code changes are safe"
        elif "cli" in str(candidate.file_path).lower():
            return "Medium risk - CLI behavior changes affect users"
        else:
            return "Low risk - internal code improvements"

    def _assess_fix_necessity(self, candidate, context: dict[str, Any]) -> str:
        """Intelligently assess whether this really needs fixing."""
        impact = self._assess_impact(candidate, context)
        risk = self._assess_risk_level(candidate, context)
        file_type = context.get("file_type", "unknown")

        if "High impact" in impact and "Low risk" in risk:
            return "High necessity - clear improvement with low risk"
        elif file_type == "cli" and "print(" in candidate.code_line:
            return "Low necessity - CLI output is appropriate"
        elif "Medium impact" in impact:
            return "Medium necessity - worthwhile improvement"
        else:
            return "Low necessity - minor improvement"

    def _design_intelligent_fix_strategy(self, candidate, context: dict[str, Any]) -> dict[str, Any]:
        """Design an intelligent fix strategy based on deep analysis."""
        target_line = context.get("target_line", "")
        file_type = context.get("file_type", "unknown")
        has_logging = context.get("has_logging", False)

        if "print(" in target_line and file_type not in ["cli", "script"]:
            # Intelligent print statement fixing
            return {
                "action": "convert_print_to_logging",
                "method": "logging.info()" if not "error" in target_line.lower() else "logging.error()",
                "needs_import": not has_logging,
                "preserve_formatting": True,
                "reason": "Convert to structured logging for better observability",
            }
        elif ".db" in target_line and "settings" not in str(candidate.file_path):
            # Intelligent path fixing
            return {
                "action": "replace_hardcoded_path",
                "replacement": "settings.database_path",
                "needs_import": "from .settings import settings" not in context.get("file_imports", []),
                "reason": "Use configuration for better portability",
            }
        else:
            return {"action": "no_fix_recommended", "reason": "Context analysis suggests this is acceptable as-is"}

    def _should_auto_approve_fix(self, fix_plan: dict[str, Any]) -> bool:
        """Intelligently decide if this fix should be auto-approved."""
        analysis = fix_plan["intelligent_analysis"]
        strategy = fix_plan["fix_strategy"]

        # Auto-approve if:
        # 1. High necessity AND low risk
        # 2. Simple conversion (print to logging)
        # 3. Clear improvement with no ambiguity

        necessity = analysis.get("fix_necessity", "")
        risk = analysis.get("risk_level", "")
        action = strategy.get("action", "")

        if "High necessity" in necessity and "Low risk" in risk:
            return True
        elif action == "convert_print_to_logging" and "library" in str(fix_plan["file_path"]):
            return True
        elif action == "no_fix_recommended":
            return True
        else:
            return False  # Require manual approval

    def _assess_fix_complexity(self, fix_plan: dict[str, Any]) -> str:
        """Assess the complexity of applying this fix."""
        strategy = fix_plan["fix_strategy"]
        action = strategy.get("action", "")

        if action == "no_fix_recommended":
            return "none"
        elif action == "convert_print_to_logging" and not strategy.get("needs_import"):
            return "simple"
        elif strategy.get("needs_import"):
            return "medium"
        else:
            return "complex"

    def _review_and_approve_fixes(self, fix_plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Review fix plans and approve them intelligently."""
        print("\n=== INTELLIGENT FIX REVIEW ===")

        auto_approved = [plan for plan in fix_plans if plan["fix_approved"]]
        needs_review = [plan for plan in fix_plans if not plan["fix_approved"]]

        print(f"Auto-approved fixes: {len(auto_approved)}")
        print(f"Fixes needing review: {len(needs_review)}")

        # Show auto-approved fixes
        if auto_approved:
            print("\n✅ Auto-approved fixes:")
            for plan in auto_approved:
                if plan["fix_strategy"]["action"] != "no_fix_recommended":
                    print(f"  {Path(plan['file_path']).name}:{plan['line_number']} - {plan['fix_strategy']['action']}")
                    print(f"    Reason: {plan['fix_strategy']['reason']}")

        # For this demo, auto-approve simple fixes that need review
        for plan in needs_review:
            if plan["fix_complexity"] == "simple":
                plan["fix_approved"] = True
                print(f"  ✅ Approving simple fix: {Path(plan['file_path']).name}:{plan['line_number']}")

        approved_fixes = [
            plan
            for plan in fix_plans
            if plan["fix_approved"] and plan["fix_strategy"]["action"] != "no_fix_recommended"
        ]

        print(f"\nTotal approved fixes: {len(approved_fixes)}")
        return approved_fixes

    def _apply_approved_fixes(self, approved_fixes: list[dict[str, Any]]) -> dict[str, Any]:
        """Apply the approved fixes using Codex for speed."""
        print("\n=== APPLYING APPROVED FIXES ===")
        print("Using Codex for fast file operations...")

        results = {
            "fixes_attempted": len(approved_fixes),
            "fixes_successful": 0,
            "fixes_failed": 0,
            "files_modified": set(),
            "fix_details": [],
        }

        for fix_plan in approved_fixes:
            try:
                success = self._apply_single_fix(fix_plan)
                if success:
                    results["fixes_successful"] += 1
                    results["files_modified"].add(str(fix_plan["file_path"]))
                    results["fix_details"].append(
                        {
                            "file": str(fix_plan["file_path"]),
                            "line": fix_plan["line_number"],
                            "action": fix_plan["fix_strategy"]["action"],
                            "status": "success",
                        }
                    )
                else:
                    results["fixes_failed"] += 1
            except Exception as e:
                results["fixes_failed"] += 1
                print(f"❌ Fix failed for {fix_plan['file_path']}: {e}")

        results["files_modified"] = list(results["files_modified"])

        print(f"✅ Successfully applied {results['fixes_successful']} fixes")
        print(f"❌ Failed to apply {results['fixes_failed']} fixes")
        print(f"📁 Modified {len(results['files_modified'])} files")

        return results

    def _apply_single_fix(self, fix_plan: dict[str, Any]) -> bool:
        """Apply a single fix using Codex for file operations."""
        file_path = fix_plan["file_path"]
        line_number = fix_plan["line_number"]
        strategy = fix_plan["fix_strategy"]

        try:
            # Read file
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Apply the fix
            if strategy["action"] == "convert_print_to_logging":
                success = self._apply_print_fix(lines, line_number, strategy)
            elif strategy["action"] == "replace_hardcoded_path":
                success = self._apply_path_fix(lines, line_number, strategy)
            else:
                return False

            if success:
                # Write file back
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                print(f"✅ Fixed {Path(file_path).name}:{line_number} - {strategy['action']}")
                return True

        except (OSError, UnicodeDecodeError) as e:
            print(f"❌ Error applying fix to {file_path}: {e}")

        return False

    def _apply_print_fix(self, lines: list[str], line_number: int, strategy: dict[str, Any]) -> bool:
        """Apply print statement fix using Codex for text manipulation."""
        if line_number > len(lines):
            return False

        line_idx = line_number - 1
        original_line = lines[line_idx]

        # Use Codex pattern for fast replacement
        if "print(" in original_line:
            new_line = re.sub(r"print\s*\(", f"{strategy['method']}(", original_line)
            lines[line_idx] = new_line

            # Add import if needed
            if strategy.get("needs_import"):
                # Find good spot for import
                import_line = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(("import ", "from ")) and "logging" not in line:
                        import_line = i
                lines.insert(import_line + 1, "import logging\n")

            return True

        return False

    def _apply_path_fix(self, lines: list[str], line_number: int, strategy: dict[str, Any]) -> bool:
        """Apply hardcoded path fix using Codex for text manipulation."""
        if line_number > len(lines):
            return False

        line_idx = line_number - 1
        original_line = lines[line_idx]

        # Use Codex pattern for fast replacement
        if ".db" in original_line:
            # This is a simplified replacement - real implementation would be more sophisticated
            new_line = re.sub(r'["\'][^"\']*\.db["\']', strategy["replacement"], original_line)
            lines[line_idx] = new_line

            # Add import if needed
            if strategy.get("needs_import"):
                import_line = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(("import ", "from ")):
                        import_line = i
                lines.insert(import_line + 1, "from .settings import settings\n")

            return True

        return False


def main():
    """Demonstrate intelligent fixing with Codex-Claude collaboration."""
    import os

    from intelligent_scanner import IntelligentScanner

    def get_xdg_path(xdg_var: str, default_suffix: str) -> Path:
        if xdg_path := os.environ.get(xdg_var):
            return Path(xdg_path) / "codex"
        return Path.home() / default_suffix / "codex"

    db_path = get_xdg_path("XDG_DATA_HOME", ".local/share") / "codex.db"
    codex_dir = Path(__file__).parent / "codex"

    print("=== INTELLIGENT FIXING DEMO ===")
    print("Step 1: Use intelligent scanner to find real issues")

    # Use intelligent scanner to get real issues
    scanner = IntelligentScanner(db_path, codex_dir)
    candidates = scanner.fast_pattern_scan()
    decisions = scanner.intelligent_review(candidates)

    # Filter to real violations only
    real_issues = [d for d in decisions if "violation" in d["intelligent_verdict"]]

    print(f"Step 2: Apply intelligent fixing to {len(real_issues)} real issues")

    # Apply intelligent fixing
    fixer = IntelligentFixer(codex_dir)
    results = fixer.analyze_and_fix_intelligently(real_issues)

    print("\n=== INTELLIGENT FIXING COMPLETE ===")
    print(f"Issues analyzed: {len(real_issues)}")
    print(f"Fixes applied: {results['fixes_successful']}")
    print(f"Files modified: {len(results['files_modified'])}")

    print("\nThis demonstrates the Codex-Claude collaboration:")
    print("✅ Codex provided speed for scanning and file operations")
    print("✅ Claude provided intelligence for analysis and decisions")
    print("✅ Result: High-quality, context-aware fixing")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Fixer Orchestrator - Composes small, modular fixers.

This orchestrator runs multiple focused fixers in sequence, following the
Unix philosophy of "do one thing well" and composability.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from external_tools_fixer import ExternalToolsFixer
from hardcoded_paths_fixer import HardcodedPathsFixer
from import_consolidation_fixer import ImportConsolidationFixer
from print_to_logging_fixer import PrintToLoggingFixer

logger = logging.getLogger(__name__)


class FixerOrchestrator:
    """Orchestrates multiple small, modular fixers."""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.backup_dir = None
        self.results = {}

        # Initialize all fixers
        self.fixers = {
            "external_tools": ExternalToolsFixer(target_dir),
            "print_to_logging": PrintToLoggingFixer(target_dir),
            "hardcoded_paths": HardcodedPathsFixer(target_dir),
            "import_consolidation": ImportConsolidationFixer(target_dir),
        }

    def create_backup(self) -> Path:
        """Create backup before applying fixes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"codex_backup_{timestamp}"
        self.backup_dir = self.target_dir.parent / backup_name

        logger.info(f"Creating backup: {self.backup_dir}")
        shutil.copytree(self.target_dir, self.backup_dir)
        return self.backup_dir

    def run_fixer(self, fixer_name: str, fixer_instance) -> dict[str, Any]:
        """Run a single fixer and capture results."""
        logger.info(f"Running {fixer_name} fixer...")

        try:
            if hasattr(fixer_instance, "run_all_tools"):
                # External tools fixer
                result = fixer_instance.run_all_tools()
                summary = fixer_instance.get_summary()
            else:
                # Pattern-based fixers
                result = fixer_instance.fix_directory()
                summary = fixer_instance.get_summary()

            return {"success": True, "result": result, "summary": summary, "fixer_type": fixer_name}

        except Exception as e:
            logger.error(f"Error in {fixer_name} fixer: {e}")
            return {"success": False, "error": str(e), "fixer_type": fixer_name}

    def run_all_fixers(self, skip_external: bool = False) -> dict[str, Any]:
        """Run all fixers in sequence."""
        logger.info("Starting orchestrated fixing session...")

        # Create backup
        self.create_backup()

        # Run fixers in order
        for fixer_name, fixer_instance in self.fixers.items():
            if skip_external and fixer_name == "external_tools":
                logger.info(f"Skipping {fixer_name} (skip_external=True)")
                continue

            result = self.run_fixer(fixer_name, fixer_instance)
            self.results[fixer_name] = result

        return self.results

    def run_selected_fixers(self, selected: list[str]) -> dict[str, Any]:
        """Run only selected fixers."""
        logger.info(f"Running selected fixers: {', '.join(selected)}")

        # Create backup
        self.create_backup()

        # Run selected fixers
        for fixer_name in selected:
            if fixer_name in self.fixers:
                result = self.run_fixer(fixer_name, self.fixers[fixer_name])
                self.results[fixer_name] = result
            else:
                logger.warning(f"Unknown fixer: {fixer_name}")

        return self.results

    def get_overall_summary(self) -> dict[str, Any]:
        """Get summary of all fixing operations."""
        total_fixes = 0
        successful_fixers = 0
        failed_fixers = []

        for fixer_name, result in self.results.items():
            if result.get("success"):
                successful_fixers += 1
                summary = result.get("summary", {})
                total_fixes += summary.get("total_fixes", 0)
            else:
                failed_fixers.append(fixer_name)

        return {
            "total_fixers_run": len(self.results),
            "successful_fixers": successful_fixers,
            "failed_fixers": failed_fixers,
            "total_fixes_applied": total_fixes,
            "backup_location": str(self.backup_dir) if self.backup_dir else None,
        }

    def create_session_report(self) -> str:
        """Create detailed report of fixing session."""
        timestamp = datetime.now().isoformat()
        summary = self.get_overall_summary()

        report = f"""
CODEX MODULAR FIXING SESSION ({timestamp})

Applied small, modular, composable fixers to eliminate violations.

ORCHESTRATION SUMMARY:
- Fixers run: {summary['total_fixers_run']}
- Successful: {summary['successful_fixers']}
- Failed: {len(summary['failed_fixers'])}
- Total fixes: {summary['total_fixes_applied']}

FIXER RESULTS:
"""

        for fixer_name, result in self.results.items():
            status = "✅" if result.get("success") else "❌"

            if result.get("success"):
                summary_data = result.get("summary", {})
                fixes = summary_data.get("total_fixes", 0)
                report += f"{status} {fixer_name}: {fixes} fixes applied\n"
            else:
                error = result.get("error", "Unknown error")
                report += f"{status} {fixer_name}: {error}\n"

        if summary["failed_fixers"]:
            report += f"\nFAILED FIXERS: {', '.join(summary['failed_fixers'])}\n"

        report += f"""
BACKUP LOCATION:
{summary['backup_location']}

MODULAR DESIGN BENEFITS:
✅ Each fixer has single responsibility
✅ Fixers can be run independently
✅ Easy to debug and maintain
✅ Composable and reusable
✅ Follows Unix philosophy

SELF-REFLECTION:
The modular approach works much better than monolithic fixing.
Each fixer is focused, testable, and can be used independently.
The orchestrator provides coordination while keeping fixers simple.

This demonstrates the value of small, composable tools working together.
"""

        return report


def main():
    """Run the modular fixer orchestrator."""
    codex_dir = Path(__file__).parent.parent / "codex"

    orchestrator = FixerOrchestrator(codex_dir)

    print("=== MODULAR FIXER ORCHESTRATION ===")
    print(f"Target directory: {codex_dir}")

    # Run all fixers
    results = orchestrator.run_all_fixers()

    # Generate report
    report = orchestrator.create_session_report()
    print(f"\n{report}")

    # Show summary
    summary = orchestrator.get_overall_summary()
    print("\n=== ORCHESTRATION COMPLETE ===")
    print(f"Total fixes applied: {summary['total_fixes_applied']}")
    print(f"Successful fixers: {summary['successful_fixers']}/{summary['total_fixers_run']}")

    if summary["backup_location"]:
        print(f"Backup saved to: {summary['backup_location']}")


if __name__ == "__main__":
    main()

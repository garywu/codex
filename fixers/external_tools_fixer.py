#!/usr/bin/env python3
"""
External Tools Fixer - Runs external tools like ruff and typos to fix violations.

Small, focused fixer that handles external tool execution only.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExternalToolsFixer:
    """Runs external tools with automatic fixes."""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.results = {}

    def fix_with_ruff(self, select_rules: list[str] = None) -> dict[str, Any]:
        """Run ruff with fixes."""
        logger.info("Running ruff with fixes...")

        cmd = ["ruff", "check", str(self.target_dir), "--fix"]

        if select_rules:
            cmd.extend(["--select", ",".join(select_rules)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "fixes_applied": "Applied fixes" if result.returncode == 0 else "Some issues remain",
            }

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"Ruff execution failed: {e}")
            return {"success": False, "error": str(e)}

    def fix_with_typos(self) -> dict[str, Any]:
        """Run typos with fixes."""
        logger.info("Running typos with fixes...")

        try:
            result = subprocess.run(
                ["typos", str(self.target_dir), "--write-changes"], capture_output=True, text=True, timeout=30
            )

            typo_count = len(result.stdout.splitlines()) if result.stdout else 0

            return {
                "success": result.returncode == 0,
                "fixes_applied": typo_count,
                "output": result.stdout,
                "errors": result.stderr,
            }

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"Typos execution failed: {e}")
            return {"success": False, "error": str(e)}

    def run_all_tools(self) -> dict[str, Any]:
        """Run all external tools."""
        results = {}

        # Run ruff
        results["ruff"] = self.fix_with_ruff()

        # Run typos
        results["typos"] = self.fix_with_typos()

        self.results = results
        return results

    def get_summary(self) -> dict[str, Any]:
        """Get summary of fixes applied."""
        if not self.results:
            return {"tools_run": 0, "successful_tools": 0}

        successful_tools = sum(1 for r in self.results.values() if r.get("success"))

        return {
            "tools_run": len(self.results),
            "successful_tools": successful_tools,
            "ruff_success": self.results.get("ruff", {}).get("success", False),
            "typos_fixes": self.results.get("typos", {}).get("fixes_applied", 0),
        }


def main():
    """Test external tools fixer."""
    codex_dir = Path(__file__).parent.parent / "codex"

    fixer = ExternalToolsFixer(codex_dir)
    results = fixer.run_all_tools()

    print("=== EXTERNAL TOOLS FIXER RESULTS ===")
    for tool, result in results.items():
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {tool}: {result.get('fixes_applied', result.get('error', 'Unknown'))}")

    summary = fixer.get_summary()
    print(f"\nSummary: {summary['successful_tools']}/{summary['tools_run']} tools successful")


if __name__ == "__main__":
    main()

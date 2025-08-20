#!/usr/bin/env python3
"""
Pre-commit hook script for organization checking.

Returns exit code 0 if organization score >= 80, otherwise 1.
"""

import sys
from pathlib import Path

# Add parent directory to path to import codex
sys.path.insert(0, str(Path(__file__).parent.parent))

from codex.organization_scanner import OrganizationScanner


def main():
    """Run organization check for pre-commit."""

    MIN_SCORE = 80  # Minimum acceptable organization score

    scanner = OrganizationScanner()
    results = scanner.scan()

    # Calculate score
    total_issues = len(results["issues"])
    score = max(0, 100 - (total_issues * 2))

    # Print summary
    print(f"Organization Score: {score}/100")

    if score < MIN_SCORE:
        print(f"\n❌ Organization score too low (minimum: {MIN_SCORE}/100)")
        print("\nTop issues:")

        # Show high priority issues
        high_issues = [i for i in results["issues"] if i.get("severity") == "high"]
        for issue in high_issues[:3]:
            print(f"  • {issue['message']}")

        # Show recommendations
        if results["recommendations"]:
            print("\nQuick fixes:")
            for rec in results["recommendations"][:2]:
                if "command" in rec:
                    print(f"  • {rec['action']}: {rec['command']}")

        print("\nRun 'uv run python -m codex.organization_scanner' for full report")
        return 1
    else:
        print("✅ Organization check passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

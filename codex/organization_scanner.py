#!/usr/bin/env python3
"""
File Organization Scanner for Codex

Detects and reports file organization issues:
- Files in wrong locations
- Duplicate implementations
- Missing standard directories
- Naming inconsistencies
- Backup directories that should be removed
"""

import re
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table


class OrganizationScanner:
    """Scans project for file organization issues."""

    def __init__(self, root_path: Path = Path.cwd()):
        self.root = root_path
        self.console = Console()
        self.issues = []

        # Define expected structure
        # Note: File patterns for organization, not CORS configuration
        self.expected_structure = {
            "tests": ["test_*.py", "*_test.py"],
            "docs": ["*.md", "*.rst", "*.txt"],
            "examples": ["demo_*.py", "example_*.py"],
            "scripts": ["*.sh", "install_*.py", "migrate_*.py"],
            "config": ["*.toml", "*.yaml", "*.json", "*.ini"],
        }

        # Files that should be in root
        self.allowed_root_files = {
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            ".gitignore",
            ".env.example",
            "Makefile",
            "requirements.txt",
            "requirements-dev.txt",
            "uv.lock",  # UV package manager lock file
            "poetry.lock",
            "Pipfile.lock",
        }

        # Patterns indicating problems
        self.problem_patterns = {
            "backup_dirs": r".*_backup_\d+.*",
            "old_versions": r".*_(OLD|DEPRECATED|old|backup)\.py$",
            "numbered_versions": r".*_v\d+\..*",
            "temp_files": r".*\.(tmp|temp|bak|swp)$",
            "build_artifacts": r"(build|dist|.*\.egg-info)",
        }

        # Duplicate detection patterns
        self.duplicate_patterns = {
            "scanners": r".*scanner.*\.py$",
            "fixers": r".*fixer.*\.py$",
            "databases": r".*database.*\.py$",
            "analyzers": r".*analyzer.*\.py$",
        }

    def scan(self) -> dict:
        """Perform comprehensive organization scan."""

        results = {
            "total_files": 0,
            "issues": [],
            "statistics": {},
            "duplicates": defaultdict(list),
            "misplaced_files": defaultdict(list),
            "structure_issues": [],
            "recommendations": [],
        }

        # Collect all files
        all_files = list(self.root.rglob("*"))
        results["total_files"] = len([f for f in all_files if f.is_file()])

        # Check for backup directories
        self._check_backup_dirs(results)

        # Check root directory organization
        self._check_root_organization(results)

        # Check for duplicate implementations
        self._check_duplicates(results)

        # Check for missing standard directories
        self._check_missing_dirs(results)

        # Check for old/deprecated files
        self._check_old_files(results)

        # Check test organization
        self._check_test_organization(results)

        # Generate recommendations
        self._generate_recommendations(results)

        return results

    def _check_backup_dirs(self, results: dict):
        """Check for backup directories that should be removed."""

        backup_dirs = []
        for item in self.root.iterdir():
            if item.is_dir() and re.match(self.problem_patterns["backup_dirs"], item.name):
                file_count = len(list(item.rglob("*")))
                backup_dirs.append({"path": str(item), "name": item.name, "file_count": file_count})
                results["issues"].append(
                    {
                        "type": "backup_directory",
                        "severity": "high",
                        "path": str(item),
                        "message": f"Backup directory contains {file_count} files - should be removed",
                    }
                )

        results["statistics"]["backup_directories"] = len(backup_dirs)
        results["statistics"]["files_in_backups"] = sum(d["file_count"] for d in backup_dirs)

    def _check_root_organization(self, results: dict):
        """Check if root directory has too many files."""

        root_files = [f for f in self.root.iterdir() if f.is_file()]
        python_files = [f for f in root_files if f.suffix == ".py"]
        markdown_files = [f for f in root_files if f.suffix == ".md"]

        # Check Python files in root
        misplaced_python = []
        for py_file in python_files:
            if py_file.name not in self.allowed_root_files:
                # Determine where it should go
                if py_file.name.startswith("test_"):
                    target = "tests/"
                    results["misplaced_files"]["tests"].append(py_file.name)
                elif py_file.name.startswith("demo_") or py_file.name.startswith("example_"):
                    target = "examples/"
                    results["misplaced_files"]["examples"].append(py_file.name)
                elif "scanner" in py_file.name or "fixer" in py_file.name:
                    target = "examples/ or delete if experimental"
                    results["misplaced_files"]["experimental"].append(py_file.name)
                else:
                    target = "scripts/ or codex/"
                    results["misplaced_files"]["utilities"].append(py_file.name)

                misplaced_python.append(py_file.name)
                results["issues"].append(
                    {
                        "type": "misplaced_file",
                        "severity": "medium",
                        "path": str(py_file),
                        "message": f"Python file in root should be in {target}",
                    }
                )

        # Check markdown files
        docs_in_root = [f for f in markdown_files if f.name not in {"README.md", "LICENSE", "CHANGELOG.md"}]

        for doc in docs_in_root:
            results["misplaced_files"]["docs"].append(doc.name)
            results["issues"].append(
                {
                    "type": "misplaced_file",
                    "severity": "low",
                    "path": str(doc),
                    "message": "Documentation file should be in docs/",
                }
            )

        results["statistics"]["root_python_files"] = len(python_files)
        results["statistics"]["root_markdown_files"] = len(markdown_files)
        results["statistics"]["misplaced_root_files"] = len(misplaced_python) + len(docs_in_root)

    def _check_duplicates(self, results: dict):
        """Check for duplicate implementations."""

        for category, pattern in self.duplicate_patterns.items():
            matches = []
            for py_file in self.root.rglob("*.py"):
                if re.match(pattern, py_file.name):
                    matches.append(str(py_file.relative_to(self.root)))

            if len(matches) > 3:  # More than 3 similar files is suspicious
                results["duplicates"][category] = matches
                results["issues"].append(
                    {
                        "type": "duplicate_implementations",
                        "severity": "high",
                        "category": category,
                        "count": len(matches),
                        "message": f"Found {len(matches)} {category} implementations - consolidate?",
                    }
                )

        results["statistics"]["duplicate_categories"] = len(results["duplicates"])

    def _check_missing_dirs(self, results: dict):
        """Check for missing standard directories."""

        expected_dirs = ["tests", "docs", "examples", "scripts"]
        missing_dirs = []

        for dir_name in expected_dirs:
            dir_path = self.root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                results["structure_issues"].append(
                    {
                        "type": "missing_directory",
                        "name": dir_name,
                        "message": f"Standard directory '{dir_name}/' is missing",
                    }
                )

        results["statistics"]["missing_directories"] = len(missing_dirs)

    def _check_old_files(self, results: dict):
        """Check for old/deprecated files."""

        old_files = []
        for py_file in self.root.rglob("*.py"):
            if re.match(self.problem_patterns["old_versions"], py_file.name):
                old_files.append(str(py_file.relative_to(self.root)))
                results["issues"].append(
                    {
                        "type": "old_file",
                        "severity": "medium",
                        "path": str(py_file),
                        "message": "Old/deprecated file should be removed",
                    }
                )

        results["statistics"]["old_files"] = len(old_files)

    def _check_test_organization(self, results: dict):
        """Check test file organization."""

        # Find all test files
        test_files_root = list(self.root.glob("test_*.py"))
        test_files_tests_dir = list((self.root / "tests").glob("test_*.py")) if (self.root / "tests").exists() else []

        if test_files_root:
            results["issues"].append(
                {
                    "type": "test_organization",
                    "severity": "medium",
                    "count": len(test_files_root),
                    "message": f"{len(test_files_root)} test files in root should be in tests/",
                }
            )

        results["statistics"]["tests_in_root"] = len(test_files_root)
        results["statistics"]["tests_in_tests_dir"] = len(test_files_tests_dir)

    def _generate_recommendations(self, results: dict):
        """Generate actionable recommendations."""

        recs = []

        # Backup directories
        if results["statistics"].get("backup_directories", 0) > 0:
            recs.append(
                {
                    "priority": "HIGH",
                    "action": "Remove backup directories",
                    "command": "rm -rf *_backup_*",
                    "impact": f"Removes {results['statistics']['files_in_backups']} duplicate files",
                }
            )

        # Root organization
        if results["statistics"].get("misplaced_root_files", 0) > 10:
            recs.append(
                {
                    "priority": "HIGH",
                    "action": "Organize root directory",
                    "command": "mkdir -p tests docs examples scripts && mv test_*.py tests/ && mv *.md docs/",
                    "impact": f"Organizes {results['statistics']['misplaced_root_files']} misplaced files",
                }
            )

        # Duplicates
        for category, files in results["duplicates"].items():
            if len(files) > 3:
                recs.append(
                    {
                        "priority": "MEDIUM",
                        "action": f"Consolidate {category}",
                        "files": files[:5],  # Show first 5
                        "impact": f"Reduces {len(files)} implementations to 1",
                    }
                )

        # Missing directories
        if results["statistics"].get("missing_directories", 0) > 0:
            recs.append(
                {
                    "priority": "LOW",
                    "action": "Create standard directories",
                    "command": "mkdir -p tests docs examples scripts",
                    "impact": "Establishes proper project structure",
                }
            )

        results["recommendations"] = recs

    def print_report(self, results: dict):
        """Print a formatted report of findings."""

        self.console.print("\n[bold cyan]📁 File Organization Scan Report[/bold cyan]\n")

        # Summary statistics
        stats_table = Table(title="Organization Statistics", border_style="blue")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", justify="right")

        for key, value in results["statistics"].items():
            stats_table.add_row(key.replace("_", " ").title(), str(value))

        self.console.print(stats_table)

        # Issues by severity
        high_issues = [i for i in results["issues"] if i.get("severity") == "high"]
        medium_issues = [i for i in results["issues"] if i.get("severity") == "medium"]
        low_issues = [i for i in results["issues"] if i.get("severity") == "low"]

        if high_issues:
            self.console.print("\n[bold red]🔴 High Priority Issues:[/bold red]")
            for issue in high_issues[:5]:
                self.console.print(f"  • {issue['message']}")

        if medium_issues:
            self.console.print("\n[bold yellow]🟡 Medium Priority Issues:[/bold yellow]")
            for issue in medium_issues[:5]:
                self.console.print(f"  • {issue['message']}")

        # Misplaced files
        if results["misplaced_files"]:
            self.console.print("\n[bold]📂 Misplaced Files by Category:[/bold]")
            for category, files in results["misplaced_files"].items():
                if files:
                    self.console.print(f"\n  [cyan]{category}[/cyan] ({len(files)} files):")
                    for f in files[:3]:
                        self.console.print(f"    • {f}")
                    if len(files) > 3:
                        self.console.print(f"    ... and {len(files)-3} more")

        # Duplicates
        if results["duplicates"]:
            self.console.print("\n[bold]🔄 Duplicate Implementations:[/bold]")
            for category, files in results["duplicates"].items():
                self.console.print(f"\n  [cyan]{category}[/cyan] ({len(files)} files):")
                for f in files[:3]:
                    self.console.print(f"    • {f}")
                if len(files) > 3:
                    self.console.print(f"    ... and {len(files)-3} more")

        # Recommendations
        if results["recommendations"]:
            self.console.print("\n[bold green]✅ Recommendations:[/bold green]")
            for rec in results["recommendations"]:
                priority_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}.get(rec["priority"], "white")
                self.console.print(f"\n  [{priority_color}]{rec['priority']}[/{priority_color}]: {rec['action']}")
                if "command" in rec:
                    self.console.print(f"    Command: [dim]{rec['command']}[/dim]")
                if "impact" in rec:
                    self.console.print(f"    Impact: {rec['impact']}")

        # Overall score
        total_issues = len(results["issues"])
        score = max(0, 100 - (total_issues * 2))

        color = "green" if score > 80 else "yellow" if score > 60 else "red"
        self.console.print(f"\n[bold]Organization Score: [{color}]{score}/100[/{color}][/bold]")

        if score < 60:
            self.console.print("[red]⚠️  Significant organization issues detected - cleanup recommended![/red]")


def main():
    """Run organization scan."""
    scanner = OrganizationScanner()
    results = scanner.scan()
    scanner.print_report(results)

    # Return exit code based on severity
    high_issues = [i for i in results["issues"] if i.get("severity") == "high"]
    return 1 if high_issues else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

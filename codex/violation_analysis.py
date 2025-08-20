#!/usr/bin/env python3
"""
Violation Analysis Tool for Codex

Provides comprehensive analysis of violations by:
1. Location (file, folder, module)
2. Category (error type, pattern)
3. Severity and priority
4. Trends and patterns
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree


@dataclass
class Violation:
    """Represents a single violation."""

    file_path: str
    line_number: int
    pattern_name: str
    message: str
    severity: str = "medium"
    category: str = ""
    module: str = ""
    folder: str = ""

    def __post_init__(self):
        """Extract module and folder from file path."""
        path = Path(self.file_path)
        parts = path.parts

        # Determine module (top-level package)
        if len(parts) > 0:
            if parts[0] == "codex":
                self.module = "codex"
            elif parts[0] == "tests":
                self.module = "tests"
            elif parts[0] == "scripts":
                self.module = "scripts"
            elif parts[0] == "examples":
                self.module = "examples"
            elif parts[0] == "experiments":
                self.module = "experiments"
            elif parts[0] == "docs":
                self.module = "docs"
            else:
                self.module = "root"

        # Determine folder (immediate parent)
        if len(parts) > 1:
            self.folder = str(Path(*parts[:-1]))
        else:
            self.folder = "."

        # Categorize by pattern name
        self.category = self._categorize_pattern(self.pattern_name)

    def _categorize_pattern(self, pattern: str) -> str:
        """Categorize violation by pattern name."""
        categories = {
            "Package Management": ["use-uv", "uv-package", "pip", "poetry", "requirements"],
            "Type Safety": ["type-annotation", "no-untyped", "mypy", "typing"],
            "Security": ["jwt", "cors", "auth", "password", "secret", "token", "security"],
            "Testing": ["test", "coverage", "mock", "assert", "pytest"],
            "Code Quality": ["complexity", "duplicate", "naming", "style", "format"],
            "Performance": ["async", "cache", "optimize", "performance", "memory"],
            "Documentation": ["docstring", "comment", "readme", "doc"],
            "Best Practices": ["best-practice", "pattern", "anti-pattern", "code-smell"],
            "Dependencies": ["import", "dependency", "module", "package"],
            "Configuration": ["config", "settings", "env", "toml", "yaml"],
        }

        pattern_lower = pattern.lower()
        for category, keywords in categories.items():
            if any(keyword in pattern_lower for keyword in keywords):
                return category

        return "Other"


@dataclass
class AnalysisReport:
    """Complete violation analysis report."""

    total_violations: int = 0
    total_files: int = 0
    by_module: dict[str, list[Violation]] = field(default_factory=dict)
    by_folder: dict[str, list[Violation]] = field(default_factory=dict)
    by_category: dict[str, list[Violation]] = field(default_factory=dict)
    by_pattern: dict[str, list[Violation]] = field(default_factory=dict)
    by_severity: dict[str, list[Violation]] = field(default_factory=dict)
    by_file: dict[str, list[Violation]] = field(default_factory=dict)
    hotspots: list[tuple[str, int]] = field(default_factory=list)  # (file, count)
    patterns_frequency: dict[str, int] = field(default_factory=dict)


class ViolationAnalyzer:
    """Analyzes violations comprehensively."""

    def __init__(self):
        self.console = Console()
        self.violations: list[Violation] = []
        self.report = AnalysisReport()

    def parse_scan_output(self, scan_output: str) -> list[Violation]:
        """Parse scan output to extract violations."""
        violations = []

        # Pattern to match violation lines
        # Example: "/Users/admin/Work/codex/cli.py:123: use-uv-package-manager - Use uv for speed"
        pattern = r"^(.+?):(\d+):\s*([a-z-]+)\s*-\s*(.+)$"

        for line in scan_output.split("\n"):
            line = line.strip()
            # Skip empty lines and headers
            if not line or line.startswith("┏") or line.startswith("┃") or line.startswith("━"):
                continue

            match = re.match(pattern, line)
            if match:
                file_path, line_num, pattern_name, message = match.groups()
                # Make path relative if it's absolute
                if file_path.startswith("/"):
                    try:
                        file_path = str(Path(file_path).relative_to(Path.cwd()))
                    except:
                        pass  # Keep absolute if can't make relative

                violations.append(
                    Violation(
                        file_path=file_path, line_number=int(line_num), pattern_name=pattern_name, message=message
                    )
                )

        return violations

    def analyze(self, violations: list[Violation]) -> AnalysisReport:
        """Perform comprehensive analysis of violations."""
        self.violations = violations
        self.report = AnalysisReport()

        # Basic counts
        self.report.total_violations = len(violations)
        self.report.total_files = len(set(v.file_path for v in violations))

        # Group by different dimensions
        for violation in violations:
            # By module
            if violation.module not in self.report.by_module:
                self.report.by_module[violation.module] = []
            self.report.by_module[violation.module].append(violation)

            # By folder
            if violation.folder not in self.report.by_folder:
                self.report.by_folder[violation.folder] = []
            self.report.by_folder[violation.folder].append(violation)

            # By category
            if violation.category not in self.report.by_category:
                self.report.by_category[violation.category] = []
            self.report.by_category[violation.category].append(violation)

            # By pattern
            if violation.pattern_name not in self.report.by_pattern:
                self.report.by_pattern[violation.pattern_name] = []
            self.report.by_pattern[violation.pattern_name].append(violation)

            # By severity
            if violation.severity not in self.report.by_severity:
                self.report.by_severity[violation.severity] = []
            self.report.by_severity[violation.severity].append(violation)

            # By file
            if violation.file_path not in self.report.by_file:
                self.report.by_file[violation.file_path] = []
            self.report.by_file[violation.file_path].append(violation)

        # Calculate hotspots (files with most violations)
        file_counts = [(file, len(viols)) for file, viols in self.report.by_file.items()]
        self.report.hotspots = sorted(file_counts, key=lambda x: x[1], reverse=True)[:10]

        # Pattern frequency
        self.report.patterns_frequency = {pattern: len(viols) for pattern, viols in self.report.by_pattern.items()}

        return self.report

    def print_location_analysis(self):
        """Print analysis by location (module/folder/file)."""
        self.console.print("\n[bold cyan]📍 LOCATION ANALYSIS[/bold cyan]\n")

        # Module breakdown
        module_table = Table(title="By Module", border_style="blue", box=box.ROUNDED)
        module_table.add_column("Module", style="cyan")
        module_table.add_column("Violations", justify="right")
        module_table.add_column("Files", justify="right")
        module_table.add_column("Avg/File", justify="right")

        for module, viols in sorted(self.report.by_module.items(), key=lambda x: len(x[1]), reverse=True):
            files = len(set(v.file_path for v in viols))
            avg = len(viols) / files if files > 0 else 0
            module_table.add_row(module, str(len(viols)), str(files), f"{avg:.1f}")

        self.console.print(module_table)

        # Folder tree view
        self.console.print("\n[bold]Folder Distribution:[/bold]")
        tree = Tree("📁 Project")

        # Group folders hierarchically
        folder_tree = defaultdict(list)
        for folder, viols in self.report.by_folder.items():
            parts = Path(folder).parts
            if len(parts) == 1:
                folder_tree["root"].append((folder, len(viols)))
            else:
                parent = parts[0]
                folder_tree[parent].append((folder, len(viols)))

        for parent, children in sorted(folder_tree.items()):
            if parent == "root":
                for folder, count in sorted(children, key=lambda x: x[1], reverse=True):
                    if folder != ".":
                        tree.add(f"[yellow]{folder}[/yellow] ({count} violations)")
            else:
                branch = tree.add(f"[cyan]{parent}/[/cyan]")
                for folder, count in sorted(children, key=lambda x: x[1], reverse=True):
                    if folder != parent:
                        subfolder = str(Path(folder).relative_to(parent)) if parent != "." else folder
                        branch.add(f"[yellow]{subfolder}[/yellow] ({count})")

        self.console.print(tree)

        # Hotspot files
        self.console.print("\n[bold]🔥 Hotspot Files (Top 10):[/bold]")
        hotspot_table = Table(border_style="red", box=box.SIMPLE)
        hotspot_table.add_column("File", style="red")
        hotspot_table.add_column("Violations", justify="right")
        hotspot_table.add_column("Top Patterns")

        for file_path, count in self.report.hotspots:
            # Get top patterns for this file
            file_viols = self.report.by_file[file_path]
            pattern_counts = defaultdict(int)
            for v in file_viols:
                pattern_counts[v.pattern_name] += 1
            top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            patterns_str = ", ".join(f"{p}({c})" for p, c in top_patterns)

            hotspot_table.add_row(file_path, str(count), patterns_str)

        self.console.print(hotspot_table)

    def print_category_analysis(self):
        """Print analysis by error category."""
        self.console.print("\n[bold cyan]📊 CATEGORY ANALYSIS[/bold cyan]\n")

        # Category breakdown
        cat_table = Table(title="By Category", border_style="green", box=box.ROUNDED)
        cat_table.add_column("Category", style="green")
        cat_table.add_column("Count", justify="right")
        cat_table.add_column("Percentage", justify="right")
        cat_table.add_column("Top Patterns")

        total = self.report.total_violations
        for category, viols in sorted(self.report.by_category.items(), key=lambda x: len(x[1]), reverse=True):
            # Get top patterns in this category
            pattern_counts = defaultdict(int)
            for v in viols:
                pattern_counts[v.pattern_name] += 1
            top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            patterns_str = ", ".join(f"{p}" for p, c in top_patterns)

            percentage = (len(viols) / total * 100) if total > 0 else 0
            cat_table.add_row(category, str(len(viols)), f"{percentage:.1f}%", patterns_str)

        self.console.print(cat_table)

        # Pattern frequency
        self.console.print("\n[bold]Pattern Frequency (Top 15):[/bold]")
        pattern_table = Table(border_style="yellow", box=box.SIMPLE)
        pattern_table.add_column("Pattern", style="yellow")
        pattern_table.add_column("Count", justify="right")
        pattern_table.add_column("Category")
        pattern_table.add_column("Example Message")

        for pattern, count in sorted(self.report.patterns_frequency.items(), key=lambda x: x[1], reverse=True)[:15]:
            # Get category and example message
            example = self.report.by_pattern[pattern][0]
            pattern_table.add_row(
                pattern,
                str(count),
                example.category,
                example.message[:50] + "..." if len(example.message) > 50 else example.message,
            )

        self.console.print(pattern_table)

    def print_cross_analysis(self):
        """Print cross-dimensional analysis."""
        self.console.print("\n[bold cyan]🔄 CROSS-DIMENSIONAL ANALYSIS[/bold cyan]\n")

        # Module vs Category matrix
        self.console.print("[bold]Module × Category Matrix:[/bold]")

        # Build matrix data
        matrix_data = defaultdict(lambda: defaultdict(int))
        for violation in self.violations:
            matrix_data[violation.module][violation.category] += 1

        # Get all categories
        all_categories = sorted(self.report.by_category.keys())

        # Create matrix table
        matrix_table = Table(border_style="magenta", box=box.ROUNDED)
        matrix_table.add_column("Module", style="magenta")
        for cat in all_categories[:6]:  # Limit to 6 most common categories
            matrix_table.add_column(cat[:8], justify="center")  # Truncate long names

        for module in sorted(matrix_data.keys()):
            row = [module]
            for cat in all_categories[:6]:
                count = matrix_data[module][cat]
                row.append(str(count) if count > 0 else "-")
            matrix_table.add_row(*row)

        self.console.print(matrix_table)

        # Correlation insights
        self.console.print("\n[bold]Key Insights:[/bold]")
        insights = []

        # Find module with most diverse violations
        module_diversity = {
            module: len(set(v.category for v in viols)) for module, viols in self.report.by_module.items()
        }
        most_diverse = max(module_diversity.items(), key=lambda x: x[1])
        insights.append(
            f"• Most diverse module: [cyan]{most_diverse[0]}[/cyan] ({most_diverse[1]} different categories)"
        )

        # Find most concentrated category
        category_concentration = {
            cat: len(set(v.module for v in viols)) for cat, viols in self.report.by_category.items()
        }
        most_spread = max(category_concentration.items(), key=lambda x: x[1])
        insights.append(f"• Most spread category: [green]{most_spread[0]}[/green] (across {most_spread[1]} modules)")

        # Find files with single type of violation
        single_pattern_files = [
            file
            for file, viols in self.report.by_file.items()
            if len(set(v.pattern_name for v in viols)) == 1 and len(viols) > 3
        ]
        if single_pattern_files:
            insights.append(f"• Files with single pattern repeated: {len(single_pattern_files)}")

        for insight in insights:
            self.console.print(insight)

    def print_summary(self):
        """Print executive summary."""
        summary = Panel.fit(
            f"""[bold cyan]VIOLATION ANALYSIS SUMMARY[/bold cyan]

📊 Total Violations: [bold red]{self.report.total_violations}[/bold red]
📁 Affected Files: [bold yellow]{self.report.total_files}[/bold yellow]
📦 Affected Modules: [bold]{len(self.report.by_module)}[/bold]
🏷️ Unique Patterns: [bold]{len(self.report.by_pattern)}[/bold]
📂 Affected Folders: [bold]{len(self.report.by_folder)}[/bold]

🎯 Top Issues:
1. [yellow]{list(self.report.by_category.keys())[0]}[/yellow]: {len(self.report.by_category[list(self.report.by_category.keys())[0]])} violations
2. [yellow]{list(self.report.patterns_frequency.keys())[0]}[/yellow]: {self.report.patterns_frequency[list(self.report.patterns_frequency.keys())[0]]} occurrences
3. Hotspot: [red]{self.report.hotspots[0][0] if self.report.hotspots else 'N/A'}[/red] ({self.report.hotspots[0][1] if self.report.hotspots else 0} violations)
""",
            border_style="bold blue",
            box=box.DOUBLE,
        )
        self.console.print(summary)

    def export_json(self, output_path: Path):
        """Export analysis to JSON."""
        export_data = {
            "summary": {
                "total_violations": self.report.total_violations,
                "total_files": self.report.total_files,
                "total_modules": len(self.report.by_module),
                "total_patterns": len(self.report.by_pattern),
            },
            "by_module": {module: len(viols) for module, viols in self.report.by_module.items()},
            "by_category": {cat: len(viols) for cat, viols in self.report.by_category.items()},
            "by_pattern": self.report.patterns_frequency,
            "hotspots": self.report.hotspots,
            "details": [
                {
                    "file": v.file_path,
                    "line": v.line_number,
                    "pattern": v.pattern_name,
                    "category": v.category,
                    "module": v.module,
                    "message": v.message,
                }
                for v in self.violations
            ],
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        self.console.print(f"\n✅ Analysis exported to: [green]{output_path}[/green]")


def main():
    """Run violation analysis."""
    import subprocess

    analyzer = ViolationAnalyzer()

    # Run scan and capture output
    console = Console()
    console.print("[bold]Running Codex scan to collect violations...[/bold]")

    try:
        result = subprocess.run(["uv", "run", "codex", "scan"], capture_output=True, text=True, cwd=Path.cwd())
        scan_output = result.stdout + result.stderr
    except Exception as e:
        console.print(f"[red]Error running scan: {e}[/red]")
        return 1

    # Parse violations
    violations = analyzer.parse_scan_output(scan_output)

    if not violations:
        console.print("[yellow]No violations found or unable to parse scan output.[/yellow]")
        return 0

    # Analyze
    report = analyzer.analyze(violations)

    # Print reports
    analyzer.print_summary()
    analyzer.print_location_analysis()
    analyzer.print_category_analysis()
    analyzer.print_cross_analysis()

    # Export to JSON
    output_path = Path("violation_analysis_report.json")
    analyzer.export_json(output_path)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

#!/usr/bin/env python3
"""
Transparent File Discovery for Codex Scanner

Provides complete transparency about which files are discovered, included, and excluded
with detailed reasoning for each decision.
"""

import fnmatch
import logging
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.tree import Tree


@dataclass
class FileDecision:
    """Record of a decision about whether to include/exclude a file."""

    file_path: Path
    included: bool
    reason: str
    matched_pattern: str | None = None
    file_size: int = 0
    last_modified: str | None = None


@dataclass
class ScanDiscoveryResult:
    """Complete result of file discovery process."""

    scan_root: Path
    total_files_found: int
    files_to_scan: list[Path]
    excluded_files: list[FileDecision]
    inclusion_decisions: list[FileDecision]
    patterns_used: list[str]
    exclusion_patterns: list[str] = field(default_factory=list)
    discovery_time_ms: float = 0.0
    gitignore_patterns: set[str] = field(default_factory=set)

    @property
    def exclusion_rate(self) -> float:
        """Percentage of files excluded."""
        if self.total_files_found == 0:
            return 0.0
        return len(self.excluded_files) / self.total_files_found * 100

    @property
    def files_by_extension(self) -> dict[str, int]:
        """Count files by extension."""
        counts = {}
        for file_path in self.files_to_scan:
            ext = file_path.suffix.lower() or "no_extension"
            counts[ext] = counts.get(ext, 0) + 1
        return counts


class ScanDiscovery:
    """
    Transparent file discovery with complete audit trail.

    This class handles file discovery with full transparency about:
    - Which files are found
    - Which files are included/excluded
    - Why each decision was made
    - Performance metrics
    """

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)

    def discover_files(
        self,
        scan_root: Path,
        patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        respect_gitignore: bool = True,
        follow_symlinks: bool = False,
    ) -> ScanDiscoveryResult:
        """
        Discover files to scan with complete transparency.

        Args:
            scan_root: Root directory to scan
            patterns: File patterns to include (default: ["*.py", "*.js", "*.ts"])
            exclude_patterns: Patterns to exclude
            respect_gitignore: Whether to respect .gitignore files
            follow_symlinks: Whether to follow symbolic links

        Returns:
            Complete discovery result with audit trail
        """
        import time

        start_time = time.time()

        # Default patterns
        if patterns is None:
            patterns = ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java"]

        # Default exclusions
        default_excludes = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            "*.pyo",
            "*backup*",
            "build",
            "dist",
            "*.egg-info",
            "demo_repository",
            ".DS_Store",
            "*.log",
            "*.tmp",
        ]

        if exclude_patterns is None:
            exclude_patterns = default_excludes
        else:
            exclude_patterns = default_excludes + exclude_patterns

        self.logger.info(f"Starting file discovery in: {scan_root}")
        self.logger.info(f"Include patterns: {patterns}")
        self.logger.info(f"Exclude patterns: {exclude_patterns}")

        # Load gitignore patterns if requested
        gitignore_patterns = set()
        if respect_gitignore:
            gitignore_patterns = self._load_gitignore_patterns(scan_root)
            self.logger.info(f"Loaded {len(gitignore_patterns)} gitignore patterns")

        # Discovery process
        all_files = []
        files_to_scan = []
        excluded_files = []
        inclusion_decisions = []

        # Find all files matching patterns
        for pattern in patterns:
            for file_path in scan_root.rglob(pattern):
                if not follow_symlinks and file_path.is_symlink():
                    decision = FileDecision(
                        file_path=file_path, included=False, reason="Symbolic link (follow_symlinks=False)"
                    )
                    excluded_files.append(decision)
                    continue

                if not file_path.is_file():
                    continue

                all_files.append(file_path)

                # Check exclusions
                decision = self._evaluate_file(file_path, scan_root, exclude_patterns, gitignore_patterns)

                if decision.included:
                    files_to_scan.append(file_path)
                    inclusion_decisions.append(decision)
                else:
                    excluded_files.append(decision)

        discovery_time = (time.time() - start_time) * 1000

        result = ScanDiscoveryResult(
            scan_root=scan_root,
            total_files_found=len(all_files),
            files_to_scan=files_to_scan,
            excluded_files=excluded_files,
            inclusion_decisions=inclusion_decisions,
            patterns_used=patterns,
            exclusion_patterns=exclude_patterns,
            discovery_time_ms=discovery_time,
            gitignore_patterns=gitignore_patterns,
        )

        self.logger.info(f"Discovery complete: {len(files_to_scan)}/{len(all_files)} files to scan")
        return result

    def _evaluate_file(
        self, file_path: Path, scan_root: Path, exclude_patterns: list[str], gitignore_patterns: set[str]
    ) -> FileDecision:
        """Evaluate whether a file should be included or excluded."""

        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(scan_root)
        except ValueError:
            # File is outside scan root
            return FileDecision(file_path=file_path, included=False, reason="Outside scan root")

        rel_path_str = str(rel_path)
        file_path_str = str(file_path)

        # Check gitignore patterns first
        for pattern in gitignore_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(file_path_str, pattern):
                return FileDecision(
                    file_path=file_path, included=False, reason="Matched .gitignore pattern", matched_pattern=pattern
                )

        # Check exclusion patterns
        for pattern in exclude_patterns:
            # Check if pattern matches any part of the path
            if (
                fnmatch.fnmatch(file_path_str, f"*{pattern}*")
                or fnmatch.fnmatch(rel_path_str, f"*{pattern}*")
                or fnmatch.fnmatch(file_path.name, pattern)
            ):
                return FileDecision(
                    file_path=file_path, included=False, reason="Matched exclusion pattern", matched_pattern=pattern
                )

        # File is included
        try:
            file_size = file_path.stat().st_size
            last_modified = file_path.stat().st_mtime
        except (OSError, PermissionError):
            file_size = 0
            last_modified = None

        return FileDecision(
            file_path=file_path,
            included=True,
            reason="Passed all filters",
            file_size=file_size,
            last_modified=str(last_modified) if last_modified else None,
        )

    def _load_gitignore_patterns(self, scan_root: Path) -> set[str]:
        """Load patterns from .gitignore files."""
        patterns = set()

        # Look for .gitignore files in the scan root and parent directories
        current_dir = scan_root
        while current_dir.parent != current_dir:  # Stop at filesystem root
            gitignore_file = current_dir / ".gitignore"
            if gitignore_file.exists():
                try:
                    with open(gitignore_file, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                patterns.add(line)
                except (UnicodeDecodeError, PermissionError):
                    self.logger.warning(f"Could not read {gitignore_file}")
            current_dir = current_dir.parent

        return patterns

    def print_discovery_summary(self, result: ScanDiscoveryResult) -> None:
        """Print a detailed summary of the discovery process."""

        # Main summary table
        table = Table(title="File Discovery Summary", border_style="cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Scan Root", str(result.scan_root))
        table.add_row("Total Files Found", str(result.total_files_found))
        table.add_row("Files to Scan", f"[green]{len(result.files_to_scan)}[/green]")
        table.add_row("Files Excluded", f"[red]{len(result.excluded_files)}[/red]")
        table.add_row("Exclusion Rate", f"{result.exclusion_rate:.1f}%")
        table.add_row("Discovery Time", f"{result.discovery_time_ms:.1f}ms")
        table.add_row("Gitignore Patterns", str(len(result.gitignore_patterns)))

        self.console.print(table)

        # Files by extension
        if result.files_by_extension:
            ext_table = Table(title="Files by Extension", border_style="blue")
            ext_table.add_column("Extension", style="bold")
            ext_table.add_column("Count", justify="right")

            for ext, count in sorted(result.files_by_extension.items()):
                ext_table.add_row(ext, str(count))

            self.console.print(ext_table)

        # Exclusion reasons
        if result.excluded_files:
            exclusion_reasons = {}
            for decision in result.excluded_files:
                reason = decision.reason
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1

            reason_table = Table(title="Exclusion Reasons", border_style="yellow")
            reason_table.add_column("Reason", style="bold")
            reason_table.add_column("Count", justify="right")

            for reason, count in sorted(exclusion_reasons.items(), key=lambda x: x[1], reverse=True):
                reason_table.add_row(reason, str(count))

            self.console.print(reason_table)

    def print_file_tree(self, result: ScanDiscoveryResult, max_files: int = 50) -> None:
        """Print a tree view of discovered files."""
        tree = Tree(f"📁 {result.scan_root}", style="bold blue")

        # Group files by directory
        dirs = {}
        for file_path in result.files_to_scan[:max_files]:
            rel_path = file_path.relative_to(result.scan_root)
            parent = rel_path.parent

            if parent not in dirs:
                dirs[parent] = []
            dirs[parent].append(rel_path.name)

        # Build tree
        for directory, files in sorted(dirs.items()):
            if str(directory) == ".":
                dir_node = tree
            else:
                dir_node = tree.add(f"📁 {directory}", style="blue")

            for file_name in sorted(files):
                dir_node.add(f"📄 {file_name}", style="green")

        if len(result.files_to_scan) > max_files:
            tree.add(f"... and {len(result.files_to_scan) - max_files} more files", style="dim")

        self.console.print(tree)

    def export_discovery_report(self, result: ScanDiscoveryResult, output_path: Path) -> None:
        """Export a complete discovery report to JSON."""
        import json
        from datetime import datetime

        report = {
            "discovery_report": {
                "timestamp": datetime.now().isoformat(),
                "scan_root": str(result.scan_root),
                "summary": {
                    "total_files_found": result.total_files_found,
                    "files_to_scan": len(result.files_to_scan),
                    "files_excluded": len(result.excluded_files),
                    "exclusion_rate_percent": result.exclusion_rate,
                    "discovery_time_ms": result.discovery_time_ms,
                },
                "configuration": {
                    "patterns_used": result.patterns_used,
                    "exclusion_patterns": result.exclusion_patterns,
                    "gitignore_patterns": list(result.gitignore_patterns),
                },
                "files_to_scan": [str(f) for f in result.files_to_scan],
                "excluded_files": [
                    {
                        "path": str(decision.file_path),
                        "reason": decision.reason,
                        "matched_pattern": decision.matched_pattern,
                        "file_size": decision.file_size,
                    }
                    for decision in result.excluded_files
                ],
                "files_by_extension": result.files_by_extension,
            }
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        self.console.print(f"[green]Discovery report exported to: {output_path}[/green]")


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Transparent file discovery")
    parser.add_argument("path", type=Path, help="Directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scanned")
    parser.add_argument("--export", type=Path, help="Export report to JSON file")
    parser.add_argument("--tree", action="store_true", help="Show file tree")

    args = parser.parse_args()

    discovery = ScanDiscovery()
    result = discovery.discover_files(args.path)

    discovery.print_discovery_summary(result)

    if args.tree:
        discovery.print_file_tree(result)

    if args.export:
        discovery.export_discovery_report(result, args.export)

    if args.dry_run:
        print(f"\nWould scan {len(result.files_to_scan)} files:")
        for file_path in result.files_to_scan:
            print(f"  {file_path}")

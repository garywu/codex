"""
Scanner module for detecting pattern violations in code.

Optimized for pre-commit hook usage and CI integration.
"""

import fnmatch
from pathlib import Path
from typing import Any

from rich.console import Console

from .models import AnalysisResult, CodeContext, PatternMatch
from .tools import ToolRunner
from .unified_database import UnifiedDatabase
import logging


class Scanner:
    """Fast pattern scanner for code files."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        quiet: bool = False,
        fix: bool = False,
        show_diff: bool = False,
        exclude_pattern: str | None = None,
    ):
        """Initialize scanner with configuration."""
        self.config = config or {}
        self.quiet = quiet
        self.fix = fix
        self.show_diff = show_diff
        self.exclude_pattern = exclude_pattern
        self.console = Console(quiet=quiet)
        self.db = UnifiedDatabase()
        self.tool_runner = ToolRunner(quiet=quiet, fix=fix, config=config)

    async def scan_file(self, file_path: Path) -> AnalysisResult:
        """Scan a single file for pattern violations."""
        if not file_path.exists():
            return AnalysisResult(file_path=str(file_path))

        # Skip excluded files
        if self._is_excluded(file_path):
            return AnalysisResult(file_path=str(file_path))

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return AnalysisResult(file_path=str(file_path))

        context = CodeContext(
            project_root=str(file_path.parent),
            file_path=str(file_path),
            content=content,
            language=self._detect_language(file_path),
        )

        result = AnalysisResult(
            file_path=str(file_path),
            violations=[],
            score=1.0,
        )

        # Get patterns to check
        patterns = await self._get_patterns_to_check()

        # Check each pattern
        for pattern in patterns:
            violation = self._check_pattern_simple(pattern, context)
            if violation:
                result.violations.append(violation)
                if not self.quiet:
                    self._print_violation(violation)

        # Apply fixes if requested
        if self.fix and result.violations:
            await self._apply_fixes(file_path, result.violations)

        return result

    async def scan_directory(self, directory: Path) -> list[AnalysisResult]:
        """Scan all files in a directory recursively."""
        results = []
        
        # Get all Python files (extend for other languages)
        patterns_to_scan = ["*.py", "*.js", "*.ts", "*.go", "*.rs"]
        
        for pattern in patterns_to_scan:
            for file_path in directory.rglob(pattern):
                if not self._is_excluded(file_path):
                    result = await self.scan_file(file_path)
                    if result.violations:
                        results.append(result)

        # Run external tools on the directory if enabled
        if self.config.get("run_tools", True):
            tool_results = await self.tool_runner.run_all_tools([directory])
            
            # Convert tool results to violations
            for tool, tool_result in tool_results.items():
                if tool_result.violations > 0:
                    # Create synthetic result for tool violations
                    tool_analysis = AnalysisResult(
                        file_path=f"[{tool.value}]",
                        violations=[
                            PatternMatch(
                                pattern_id=0,
                                pattern_name=f"{tool.value}_check",
                                category="QUALITY_TOOLS",  # type: ignore[arg-type]
                                priority="HIGH",  # type: ignore[arg-type]
                                file_path=str(directory),
                                line_number=0,
                                matched_code="",
                                confidence=1.0,
                                suggestion=f"{tool_result.violations} {tool.value} issue(s) found",
                                auto_fixable=tool_result.fixed > 0,
                            )
                        ],
                        score=0.9,
                    )
                    results.append(tool_analysis)
            
            # Print tool results
            if not self.quiet and tool_results:
                self.tool_runner.print_results(tool_results)

        return results

    async def check_pattern(
        self, pattern_name: str, paths: list[Path]
    ) -> list[PatternMatch]:
        """Check specific pattern across files."""
        violations = []
        
        # Get the specific pattern
        patterns = await self.db.search_patterns_async(pattern_name)
        if not patterns:
            return violations

        pattern = patterns[0]

        for path in paths:
            if path.is_file():
                context = self._create_context(path)
                if context:
                    violation = self._check_pattern_simple(pattern, context)
                    if violation:
                        violations.append(violation)
            elif path.is_dir():
                for file_path in path.rglob("*.py"):
                    context = self._create_context(file_path)
                    if context:
                        violation = self._check_pattern_simple(pattern, context)
                        if violation:
                            violations.append(violation)

        return violations

    def _check_pattern_simple(self, pattern: Any, context: CodeContext) -> PatternMatch | None:
        """Simple pattern checking logic."""
        # Handle both old and new pattern formats
        detection_rules = None
        
        # Debug: print pattern info
        if not self.quiet:
            pattern_name = pattern.get('name', 'unknown') if isinstance(pattern, dict) else getattr(pattern, 'name', 'unknown')
            logging.info(f"Checking pattern: {pattern_name}", file=__import__('sys').stderr)
            logging.info(f"Pattern type: {type(pattern)}", file=__import__('sys').stderr)
            if isinstance(pattern, dict):
                logging.info(f"Pattern detection field: {pattern.get('detection')}", file=__import__('sys').stderr)
        
        if hasattr(pattern, 'detection_rules') and pattern.detection_rules:
            detection_rules = pattern.detection_rules
        elif hasattr(pattern, 'detection') and pattern.detection:
            # Convert new format to old format for compatibility
            detection_rules = {}
            if 'keywords' in pattern.detection:
                detection_rules['forbidden'] = pattern.detection['keywords']
        elif isinstance(pattern, dict) and pattern.get('detection'):
            # Handle dict format with JSON detection
            import json
            try:
                detection_data = json.loads(pattern['detection']) if isinstance(pattern['detection'], str) else pattern['detection']
                detection_rules = {}
                if 'keywords' in detection_data:
                    detection_rules['forbidden'] = detection_data['keywords']
                if not self.quiet:
                    logging.info(f"Parsed detection rules: {detection_rules}", file=__import__('sys').stderr)
            except (json.JSONDecodeError, TypeError) as e:
                if not self.quiet:
                    logging.info(f"Failed to parse detection: {e}", file=__import__('sys').stderr)
        
        if not detection_rules:
            if not self.quiet:
                logging.info(f"No detection rules for pattern", file=__import__('sys').stderr)
            return None

        # Check for forbidden patterns
        if "forbidden" in detection_rules:
            for forbidden in detection_rules["forbidden"]:
                if forbidden in context.content:
                    # Find line number
                    lines = context.content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if forbidden in line:
                            return PatternMatch(
                                pattern_id=pattern.get('id', 0),
                                pattern_name=pattern.get('name', 'unknown'),
                                category=pattern.get('category', 'unknown'),
                                priority=pattern.get('priority', 'MEDIUM'),
                                file_path=context.file_path,
                                line_number=i,
                                matched_code=line.strip(),
                                confidence=0.9,
                                suggestion=pattern.get('description', ''),
                                auto_fixable=bool(pattern.get('fix_template')),
                                fix_code=pattern.get('fix_template'),
                            )

        # Check for missing required patterns
        if "required" in detection_rules:
            for required in detection_rules["required"]:
                if required not in context.content:
                    return PatternMatch(
                        pattern_id=pattern.id,
                        pattern_name=pattern.name,
                        category=pattern.category,
                        priority=pattern.priority,
                        file_path=context.file_path,
                        line_number=1,
                        matched_code="",
                        confidence=0.9,
                        suggestion=f"Missing required: {required}",
                        auto_fixable=False,
                    )

        return None

    async def _get_patterns_to_check(self) -> list[Any]:
        """Get patterns based on configuration."""
        enforce_priorities = self.config.get("enforce", ["mandatory", "critical", "high"])
        
        all_patterns = []
        for priority in enforce_priorities:
            patterns = await self.db.get_patterns(priority=priority.upper())
            all_patterns.extend(patterns)
        
        if not self.quiet:
            logging.info(f"Found {len(all_patterns)} patterns for priorities: {enforce_priorities}", file=__import__('sys').stderr)
            if not all_patterns:
                # Try getting all patterns to debug
                all_db_patterns = await self.db.get_patterns()
                logging.info(f"Total patterns in database: {len(all_db_patterns)}", file=__import__('sys').stderr)
                if all_db_patterns:
                    logging.info(f"Sample pattern: {all_db_patterns[0]}", file=__import__('sys').stderr)
        
        return all_patterns

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded."""
        # Default excludes
        default_excludes = [
            "__pycache__", ".git", ".venv", "venv", "node_modules",
            ".pytest_cache", ".mypy_cache", "*.pyc", "*.pyo"
        ]
        
        excludes = self.config.get("exclude", default_excludes)
        if self.exclude_pattern:
            excludes.append(self.exclude_pattern)

        for pattern in excludes:
            if fnmatch.fnmatch(str(file_path), f"*{pattern}*"):
                return True
        
        return False

    def _detect_language(self, file_path: Path) -> str | None:
        """Detect programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
        }
        return extension_map.get(file_path.suffix)

    def _create_context(self, file_path: Path) -> CodeContext | None:
        """Create context from file."""
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            
            return CodeContext(
                project_root=str(file_path.parent),
                file_path=str(file_path),
                content=content,
                language=self._detect_language(file_path),
            )
        except (UnicodeDecodeError, PermissionError):
            return None

    def _print_violation(self, violation: PatternMatch) -> None:
        """Print violation in readable format."""
        priority_colors = {
            "MANDATORY": "red",
            "CRITICAL": "red",
            "HIGH": "yellow",
            "MEDIUM": "cyan",
            "LOW": "blue",
        }
        color = priority_colors.get(violation.priority, "white")
        
        self.console.logging.info(
            f"{violation.file_path}:{violation.line_number}: "
            f"[{color}]{violation.pattern_name}[/{color}] - {violation.suggestion}"
        )

    async def _apply_fixes(self, file_path: Path, violations: list[PatternMatch]) -> int:
        """Apply automatic fixes to violations."""
        fixed = 0
        
        if not file_path.exists():
            return fixed

        with open(file_path) as f:
            content = f.read()
        
        original = content
        
        for violation in violations:
            if violation.auto_fixable and violation.fix_code and violation.matched_code:
                if violation.matched_code in content:
                    content = content.replace(violation.matched_code, violation.fix_code)
                    fixed += 1

        if fixed > 0:
            if self.show_diff:
                self._show_diff(original, content, file_path)
            
            with open(file_path, "w") as f:
                f.write(content)
            
            if not self.quiet:
                self.console.logging.info(f"[green]Fixed {fixed} violation(s) in {file_path}[/green]")
        
        return fixed

    def _show_diff(self, original: str, fixed: str, file_path: Path) -> None:
        """Show diff between original and fixed content."""
        import difflib
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (fixed)",
        )
        
        for line in diff:
            if line.startswith("+"):
                self.console.logging.info(f"[green]{line}[/green]", end="")
            elif line.startswith("-"):
                self.console.logging.info(f"[red]{line}[/red]", end="")
            else:
                self.console.print(line, end="")
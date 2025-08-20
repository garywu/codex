"""
Scanner module for detecting pattern violations in code.

Optimized for pre-commit hook usage and CI integration.
Includes negative space pattern detection for evidence-based best practices.
"""

import fnmatch
import logging
import time
from pathlib import Path
from typing import Any

from rich.console import Console

from .ensemble_integration import IntegratedEnsembleScanner
from .models import AnalysisResult, CodeContext, PatternCategory, PatternMatch, PatternPriority
from .negative_space_patterns import NegativeSpaceDetector
from .scan_context import DecisionType, ScanContext
from .tools import ToolRunner
from .unified_database import UnifiedDatabase
from .violation_reporter import ViolationReporter


class Scanner:
    """Fast pattern scanner for code files."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        quiet: bool = False,
        fix: bool = False,
        show_diff: bool = False,
        exclude_pattern: str | None = None,
        enable_negative_space: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize scanner with configuration.

        Args:
            config: Scanner configuration dictionary
            quiet: Suppress output for CI/automation
            fix: Enable automatic fixes where possible
            show_diff: Show diff for fixes applied
            exclude_pattern: Pattern to exclude files from scanning
            enable_negative_space: Enable negative space pattern detection for best practices
            verbose: Enable verbose decision explanations
        """
        self.config = config or {}
        self.quiet = quiet
        self.fix = fix
        self.show_diff = show_diff
        self.exclude_pattern = exclude_pattern
        self.enable_negative_space = enable_negative_space
        self.verbose = verbose
        self.console = Console(quiet=quiet)
        self.violation_reporter = ViolationReporter(console=self.console, quiet=quiet)
        self.scan_context: ScanContext | None = None
        self.db = UnifiedDatabase()
        self.tool_runner = ToolRunner(quiet=quiet, fix=fix, config=config)

        # Initialize negative space detector for best practices analysis
        self.negative_space_detector = NegativeSpaceDetector() if enable_negative_space else None

        # Initialize ensemble scanner for reduced false positives
        self.ensemble_scanner = IntegratedEnsembleScanner(quiet=quiet, verbose=verbose)

    async def scan_file(self, file_path: Path) -> AnalysisResult:
        """Scan a single file for pattern violations."""

        # Initialize scan context if not exists
        if not self.scan_context:
            self.scan_context = ScanContext(file_path.parent, verbose=self.verbose)
            self.scan_context.set_configuration(self.config)

        # Start timing this file
        start_time = time.time()

        if not file_path.exists():
            self.scan_context.record_decision(
                DecisionType.FILE_EXCLUDED, f"File check: {file_path.name}", "File does not exist", file_path=file_path
            )
            return AnalysisResult(file_path=str(file_path))

        # Skip excluded files
        if self._is_excluded(file_path):
            self.scan_context.record_file_excluded(
                file_path, "Matched exclusion pattern", matched_pattern=self._get_exclusion_reason(file_path)
            )
            return AnalysisResult(file_path=str(file_path))

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            self.scan_context.record_error(f"Reading file: {file_path.name}", str(e), file_path=file_path)
            return AnalysisResult(file_path=str(file_path))

        # Record successful file inclusion
        file_size = len(content)
        language = self._detect_language(file_path)
        self.scan_context.record_file_included(
            file_path, f"File successfully loaded ({file_size} bytes)", file_size=file_size, language=language
        )

        context = CodeContext(
            project_root=str(file_path.parent),
            file_path=str(file_path),
            content=content,
            language=language,
        )

        result = AnalysisResult(
            file_path=str(file_path),
            violations=[],
            score=1.0,
        )

        # Report file scan start
        self.violation_reporter.report_file_start(file_path)

        # Get patterns to check
        patterns = await self._get_patterns_to_check()

        # Check each pattern with context tracking
        for pattern in patterns:
            pattern_start_time = time.time()
            # Try ensemble scanner first, fall back to simple if not supported
            violation = self._check_pattern_ensemble(pattern, context)
            pattern_duration = (time.time() - pattern_start_time) * 1000  # ms

            pattern_name = (
                pattern.get("name", "unknown") if isinstance(pattern, dict) else getattr(pattern, "name", "unknown")
            )

            if violation:
                result.violations.append(violation)

                # Record violation in context
                self.scan_context.record_violation(
                    pattern_name,
                    file_path,
                    violation.line_number or 0,
                    violation.matched_code or "",
                    violation.confidence or 0.0,
                )

                if not self.quiet:
                    self._print_violation(violation)

            # Record pattern check result
            self.scan_context.record_pattern_check(
                pattern_name,
                file_path,
                violation is not None,
                "Violation detected" if violation else "No violation found",
                pattern_duration,
                violation.confidence if violation else None,
            )

        # Report file scan completion
        self.violation_reporter.report_file_complete(file_path, len(result.violations))

        # Apply fixes if requested
        if self.fix and result.violations:
            await self._apply_fixes(file_path, result.violations)

        return result

    def get_scan_context(self) -> ScanContext | None:
        """Get the current scan context for reporting."""
        return self.scan_context

    def finalize_scan(self) -> None:
        """Finalize the scan and close context."""
        if self.scan_context:
            self.scan_context.finalize_scan()

    async def scan_directory(self, directory: Path) -> list[AnalysisResult]:
        """Scan all files in a directory recursively."""

        # Initialize scan context for directory scan
        if not self.scan_context:
            self.scan_context = ScanContext(directory, verbose=self.verbose)
            self.scan_context.set_configuration(self.config)

        # Start directory scan phase
        self.scan_context.start_phase(f"Directory Scan: {directory.name}")

        results = []

        # Get all Python files (extend for other languages)
        patterns_to_scan = ["*.py", "*.js", "*.ts", "*.go", "*.rs"]

        for pattern in patterns_to_scan:
            for file_path in directory.rglob(pattern):
                if not self._is_excluded(file_path):
                    result = await self.scan_file(file_path)
                    if result.violations:
                        results.append(result)

        # End directory scan phase
        self.scan_context.end_phase()

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
                                category=PatternCategory.QUALITY_TOOLS,
                                priority=PatternPriority.HIGH,
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

    async def check_pattern(self, pattern_name: str, paths: list[Path]) -> list[PatternMatch]:
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
                    # Try ensemble scanner first, fall back to simple if not supported
                    violation = self._check_pattern_ensemble(pattern, context)
                    if violation:
                        violations.append(violation)
            elif path.is_dir():
                for file_path in path.rglob("*.py"):
                    context = self._create_context(file_path)
                    if context:
                        # Try ensemble scanner first, fall back to simple if not supported
                        violation = self._check_pattern_ensemble(pattern, context)
                        if violation:
                            violations.append(violation)

        return violations

    def _check_pattern_simple(self, pattern: Any, context: CodeContext) -> PatternMatch | None:
        """Simple pattern checking logic."""
        # Handle both old and new pattern formats
        detection_rules = None

        # Debug: print pattern info
        if not self.quiet:
            pattern_name = (
                pattern.get("name", "unknown") if isinstance(pattern, dict) else getattr(pattern, "name", "unknown")
            )
            logging.info(f"Checking pattern: {pattern_name}", file=__import__("sys").stderr)
            logging.info(f"Pattern type: {type(pattern)}", file=__import__("sys").stderr)
            if isinstance(pattern, dict):
                logging.info(f"Pattern detection field: {pattern.get('detection')}", file=__import__("sys").stderr)

        if hasattr(pattern, "detection_rules") and pattern.detection_rules:
            detection_rules = pattern.detection_rules
        elif hasattr(pattern, "detection") and pattern.detection:
            # Convert new format to old format for compatibility
            detection_rules = {}
            if "keywords" in pattern.detection:
                detection_rules["forbidden"] = pattern.detection["keywords"]
        elif isinstance(pattern, dict) and pattern.get("detection"):
            # Handle dict format with JSON detection
            import json

            try:
                detection_data = (
                    json.loads(pattern["detection"]) if isinstance(pattern["detection"], str) else pattern["detection"]
                )
                detection_rules = {}
                if "keywords" in detection_data:
                    detection_rules["forbidden"] = detection_data["keywords"]
                if not self.quiet:
                    logging.info(f"Parsed detection rules: {detection_rules}", file=__import__("sys").stderr)
            except (json.JSONDecodeError, TypeError) as e:
                if not self.quiet:
                    logging.info(f"Failed to parse detection: {e}", file=__import__("sys").stderr)

        if not detection_rules:
            if not self.quiet:
                logging.info("No detection rules for pattern", file=__import__("sys").stderr)
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
                                pattern_id=pattern.get("id", 0),
                                pattern_name=pattern.get("name", "unknown"),
                                category=pattern.get("category", "unknown"),
                                priority=pattern.get("priority", "MEDIUM"),
                                file_path=context.file_path,
                                line_number=i,
                                matched_code=line.strip(),
                                confidence=0.9,
                                suggestion=pattern.get("description", ""),
                                auto_fixable=bool(pattern.get("fix_template")),
                                fix_code=pattern.get("fix_template"),
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

    def _check_pattern_ensemble(self, pattern: Any, context: CodeContext) -> PatternMatch | None:
        """Check pattern using ensemble voting system with fallback."""
        # Create context dict for ensemble scanner
        context_dict = {"file_path": context.file_path, "content": context.content}

        # Try ensemble scanner first
        ensemble_result = self.ensemble_scanner.check_pattern(pattern, context_dict)
        if ensemble_result:
            return ensemble_result

        # Fall back to simple pattern checking for patterns not in ensemble
        return self._check_pattern_simple(pattern, context)

    async def _get_patterns_to_check(self) -> list[Any]:
        """Get patterns based on configuration."""
        enforce_priorities = self.config.get("enforce", ["mandatory", "critical", "high"])

        all_patterns = []
        for priority in enforce_priorities:
            patterns = await self.db.get_patterns(priority=priority.upper())
            all_patterns.extend(patterns)

        if not self.quiet:
            logging.info(
                f"Found {len(all_patterns)} patterns for priorities: {enforce_priorities}",
                file=__import__("sys").stderr,
            )
            if not all_patterns:
                # Try getting all patterns to debug
                all_db_patterns = await self.db.get_patterns()
                logging.info(f"Total patterns in database: {len(all_db_patterns)}", file=__import__("sys").stderr)
                if all_db_patterns:
                    logging.info(f"Sample pattern: {all_db_patterns[0]}", file=__import__("sys").stderr)

        return all_patterns

    def _is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded."""
        # Default excludes
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
        ]

        excludes = self.config.get("exclude", default_excludes)
        if self.exclude_pattern:
            excludes.append(self.exclude_pattern)

        for pattern in excludes:
            if fnmatch.fnmatch(str(file_path), f"*{pattern}*"):
                return True

        return False

    def _get_exclusion_reason(self, file_path: Path) -> str:
        """Get the specific reason why a file was excluded."""
        # Default excludes
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
        ]

        excludes = self.config.get("exclude", default_excludes)
        if self.exclude_pattern:
            excludes.append(self.exclude_pattern)

        for pattern in excludes:
            if fnmatch.fnmatch(str(file_path), f"*{pattern}*"):
                return pattern

        return "unknown"

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
        self.violation_reporter.report_violation(violation)

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
                logging.info(f"Fixed {fixed} violation(s) in {file_path}")

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
            if not self.quiet:
                logging.info(line.rstrip())

    async def analyze_project_negative_space(self, project_path: Path) -> dict[str, Any]:
        """
        Analyze project for negative space patterns (evidence-based best practices).

        This method identifies structural patterns that correlate with avoiding
        common code quality violations, providing evidence-based recommendations.

        Args:
            project_path: Path to the project root directory

        Returns:
            Dictionary containing negative space analysis results:
            - structural_features: Project organization characteristics
            - protective_patterns: Patterns that prevent common violations
            - recommendations: Evidence-based improvement suggestions
            - excellence_score: Overall project organization score (0.0-1.0)
        """
        if not self.negative_space_detector:
            return {"error": "Negative space analysis not enabled"}

        if not self.quiet:
            logging.info("🔍 Analyzing project structure for best practices...")

        # First, run regular violation scan to understand what problems exist
        scan_results = await self.scan_directory(project_path)

        # Convert scan results to violation data format
        violation_data = {"fix_plans": [], "total_violations": len(scan_results)}

        for result in scan_results:
            for violation in result.violations:
                violation_data["fix_plans"].append(
                    {
                        "violation": {
                            "pattern": violation.pattern_name,
                            "category": violation.category,
                            "priority": violation.priority,
                            "file": violation.file_path,
                            "line": violation.line_number,
                            "description": violation.suggestion,
                        }
                    }
                )

        # Analyze project structure using negative space detector
        project_analysis = self.negative_space_detector.analyze_project_negative_space(project_path, violation_data)

        # Generate recommendations based on structural features
        recommendations = self._generate_negative_space_recommendations(project_analysis)

        if not self.quiet:
            self._print_negative_space_analysis(project_analysis, recommendations)

        return {
            "project_name": project_analysis.name,
            "structural_features": project_analysis.structural_features,
            "violations_by_pattern": project_analysis.violations_by_pattern,
            "organization_score": project_analysis.organization_score,
            "recommendations": recommendations,
            "excellence_level": self._get_excellence_level(project_analysis.organization_score),
        }

    def _generate_negative_space_recommendations(self, project_analysis) -> list[str]:
        """
        Generate evidence-based recommendations from negative space analysis.

        Args:
            project_analysis: ProjectAnalysis object from negative space detector

        Returns:
            List of actionable recommendations based on structural patterns
        """
        recommendations = []
        features = project_analysis.structural_features

        # Architecture recommendations based on missing protective structures
        if not features.get("has_core_package"):
            recommendations.append("📦 Create core/ package to separate business logic from interface layers")

        if not features.get("has_api_package") and features.get("has_cli_package"):
            recommendations.append("🔌 Add api/ package to enable multiple interface types (CLI, web, SDK)")

        if not features.get("has_settings_file"):
            recommendations.append("⚙️ Create unified settings module with Pydantic BaseSettings for configuration")

        if not features.get("has_tests"):
            recommendations.append("🧪 Add tests/ directory with proper pytest structure for quality assurance")

        # Organization recommendations based on complexity indicators
        if features.get("package_depth", 0) > 5:
            recommendations.append("📁 Reduce package nesting depth to 2-4 levels for better maintainability")

        if features.get("has_monolithic_files"):
            recommendations.append("📄 Break down large files (>15KB) into focused, single-responsibility modules")

        # Security recommendations based on protective patterns
        if project_analysis.violations_by_pattern.get("hardcoded_secrets", 0) > 0:
            recommendations.append("🔒 Implement environment variable pattern to avoid hardcoded secrets")

        if project_analysis.violations_by_pattern.get("cors_never_wildcard", 0) > 0:
            recommendations.append("🌐 Configure specific CORS origins instead of wildcard for security")

        return recommendations[:5]  # Top 5 recommendations

    def _get_excellence_level(self, score: float) -> str:
        """
        Convert organization score to excellence level description.

        Args:
            score: Organization score between 0.0 and 1.0

        Returns:
            Excellence level description
        """
        if score >= 0.8:
            return "EXCEPTIONAL"
        elif score >= 0.6:
            return "EXCELLENT"
        elif score >= 0.4:
            return "GOOD"
        elif score >= 0.2:
            return "DEVELOPING"
        else:
            return "NEEDS_IMPROVEMENT"

    def _print_negative_space_analysis(self, project_analysis, recommendations: list[str]) -> None:
        """
        Log negative space analysis results in MCP-compatible format.

        Args:
            project_analysis: ProjectAnalysis object with structural data
            recommendations: List of actionable recommendations
        """
        if self.quiet:
            return

        logging.info(f"📊 NEGATIVE SPACE ANALYSIS: {project_analysis.name.upper()}")

        # Organization score
        score = project_analysis.organization_score
        level = self._get_excellence_level(score)
        logging.info(f"Organization Score: {score:.1%} ({level})")

        # Protective structures found
        logging.info("🛡️ Protective Structures:")
        features = project_analysis.structural_features

        protective_indicators = [
            ("Core Package", features.get("has_core_package", False)),
            ("API Separation", features.get("has_api_package", False)),
            ("CLI Package", features.get("has_cli_package", False)),
            ("Test Suite", features.get("has_tests", False)),
            ("Settings Module", features.get("has_settings_file", False)),
            ("PyProject Config", features.get("has_pyproject", False)),
        ]

        for indicator, present in protective_indicators:
            status = "✅" if present else "❌"
            logging.info(f"  {status} {indicator}")

        # Violations prevented/found
        if project_analysis.violations_by_pattern:
            logging.info("⚠️ Areas for Improvement:")
            for pattern, count in project_analysis.violations_by_pattern.items():
                logging.info(f"  • {pattern}: {count} violations")
        else:
            logging.info("✨ No architectural violations detected!")

        # Recommendations
        if recommendations:
            logging.info("💡 Evidence-Based Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                logging.info(f"  {i}. {rec}")

        logging.info("Analysis based on organizational patterns that correlate with avoiding violations")

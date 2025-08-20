"""
Scan Registry - First-class scan management system for Codex.

This module defines all available scan types as first-class citizens with:
- Unique identifiers
- Descriptive names
- Specific detection logic
- Result tracking
"""

import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from .pattern_models import PatternMatch, ScanResult


class ScanSeverity(str, Enum):
    """Severity levels for scan findings."""

    CRITICAL = "CRITICAL"  # Must fix immediately
    HIGH = "HIGH"  # Should fix soon
    MEDIUM = "MEDIUM"  # Should fix
    LOW = "LOW"  # Nice to fix
    INFO = "INFO"  # Informational only


class ScanCategory(str, Enum):
    """Categories of scans."""

    SECURITY = "security"
    CONSISTENCY = "consistency"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    ARCHITECTURE = "architecture"


@dataclass
class ScanDefinition:
    """Definition of a scan type."""

    id: str  # Unique identifier (e.g., "hardcoded-paths")
    name: str  # Human-readable name
    description: str  # What this scan detects
    category: ScanCategory  # Scan category
    severity: ScanSeverity  # Default severity
    enabled: bool = True  # Is scan enabled by default
    tags: list[str] = None  # Tags for filtering

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BaseScan(ABC):
    """Base class for all scan implementations."""

    def __init__(self, definition: ScanDefinition):
        self.definition = definition
        self.scan_id = str(uuid.uuid4())
        self.start_time = None
        self.end_time = None

    @abstractmethod
    async def scan_file(self, file_path: Path, content: str) -> list[PatternMatch]:
        """Scan a single file for violations."""
        pass

    @abstractmethod
    async def scan_directory(self, directory: Path) -> ScanResult:
        """Scan entire directory for violations."""
        pass

    def create_match(
        self, file_path: Path, line_number: int, matched_code: str, message: str, fix_suggestion: str | None = None
    ) -> PatternMatch:
        """Create a pattern match for a violation."""
        return PatternMatch(
            pattern_id=self.definition.id,
            pattern_name=self.definition.name,
            category=self.definition.category.value,
            priority=self.definition.severity.value,
            file_path=str(file_path),
            line_number=line_number,
            matched_code=matched_code,
            confidence=1.0,
            suggestion=message,
            auto_fixable=fix_suggestion is not None,
            fix_code=fix_suggestion,
        )


class HardcodedPathScan(BaseScan):
    """Scan for hardcoded paths instead of using settings."""

    PATTERNS = [
        # Direct path construction
        (r'Path\(["\']/', "Hardcoded absolute path"),
        (r'["\']/.+/codex', "Hardcoded codex path"),
        (r'Path\(__file__\)\.parent\s*/\s*["\']data["\']', "Hardcoded data directory"),
        (r'db_path\s*=\s*["\'].+\.db["\']', "Hardcoded database path"),
        # Common hardcoded paths
        (r'["\']~/\.config/', "Hardcoded config path - use settings.config_dir"),
        (r'["\']~/\.local/share/', "Hardcoded data path - use settings.data_dir"),
        (r'["\']~/\.cache/', "Hardcoded cache path - use settings.cache_dir"),
        # Specific to our issues
        (r'patterns\.db["\']', "Hardcoded patterns.db - use settings.database_path"),
        (r'patterns_fts\.db["\']', "Hardcoded patterns_fts.db - use settings.database_path"),
        (r"data/patterns", "Hardcoded data/patterns path"),
    ]

    async def scan_file(self, file_path: Path, content: str) -> list[PatternMatch]:
        """Scan for hardcoded paths."""
        violations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.PATTERNS:
                if re.search(pattern, line):
                    # Skip if it's in a comment or string
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith('"""'):
                        continue

                    violations.append(
                        self.create_match(
                            file_path=file_path,
                            line_number=line_num,
                            matched_code=line.strip(),
                            message=message,
                            fix_suggestion="Use settings module instead",
                        )
                    )
                    break  # Only report first match per line

        return violations

    async def scan_directory(self, directory: Path) -> ScanResult:
        """Scan directory for hardcoded paths."""
        self.start_time = datetime.utcnow()
        all_violations = []
        files_scanned = 0

        for py_file in directory.rglob("*.py"):
            # Skip test files and migrations
            if "test" in py_file.name or "migration" in py_file.name:
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                violations = await self.scan_file(py_file, content)
                all_violations.extend(violations)
                files_scanned += 1
            except (OSError, UnicodeDecodeError):
                continue

        self.end_time = datetime.utcnow()
        duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

        return ScanResult(
            scan_id=self.scan_id,
            timestamp=self.start_time,
            repository_path=str(directory),
            files_scanned=files_scanned,
            patterns_checked=len(self.PATTERNS),
            violations=all_violations,
            duration_ms=duration_ms,
            confidence_avg=1.0 if all_violations else None,
        )


class MultipleImportsScan(BaseScan):
    """Scan for multiple database/settings imports in same file."""

    CONFLICTING_IMPORTS = [
        {
            "modules": ["database", "fts_database", "unified_database"],
            "message": "Multiple database imports - use only unified_database",
        },
        {
            "modules": ["Pattern", "FTSPattern"],
            "message": "Multiple pattern model imports - use only Pattern from pattern_models",
        },
    ]

    async def scan_file(self, file_path: Path, content: str) -> list[PatternMatch]:
        """Scan for conflicting imports."""
        violations = []
        lines = content.split("\n")

        for import_group in self.CONFLICTING_IMPORTS:
            found_imports = {}

            for line_num, line in enumerate(lines, 1):
                for module in import_group["modules"]:
                    if f"from .{module} import" in line or f"import {module}" in line:
                        found_imports[module] = (line_num, line.strip())

            if len(found_imports) > 1:
                # Found multiple conflicting imports
                for module, (line_num, line) in found_imports.items():
                    violations.append(
                        self.create_match(
                            file_path=file_path,
                            line_number=line_num,
                            matched_code=line,
                            message=import_group["message"],
                            fix_suggestion="Remove this import and use only unified_database",
                        )
                    )

        return violations

    async def scan_directory(self, directory: Path) -> ScanResult:
        """Scan directory for import conflicts."""
        self.start_time = datetime.utcnow()
        all_violations = []
        files_scanned = 0

        for py_file in directory.rglob("*.py"):
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                violations = await self.scan_file(py_file, content)
                all_violations.extend(violations)
                files_scanned += 1
            except (OSError, UnicodeDecodeError):
                continue

        self.end_time = datetime.utcnow()
        duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

        return ScanResult(
            scan_id=self.scan_id,
            timestamp=self.start_time,
            repository_path=str(directory),
            files_scanned=files_scanned,
            patterns_checked=len(self.CONFLICTING_IMPORTS),
            violations=all_violations,
            duration_ms=duration_ms,
            confidence_avg=1.0 if all_violations else None,
        )


class MissingSettingsUsageScan(BaseScan):
    """Scan for modules that should use settings but don't."""

    REQUIRED_SETTINGS = {
        "database": ["database_path", "data_dir"],
        "config": ["config_dir"],
        "cache": ["cache_dir"],
        "logging": ["log_level", "log_dir"],
    }

    async def scan_file(self, file_path: Path, content: str) -> list[PatternMatch]:
        """Scan for missing settings usage."""
        violations = []

        # Check if file imports settings
        has_settings_import = (
            "from .settings import settings" in content or "from codex.settings import settings" in content
        )

        # Check for patterns that suggest settings should be used
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            # Database paths
            if "db_path" in line and "settings." not in line and not has_settings_import:
                violations.append(
                    self.create_match(
                        file_path=file_path,
                        line_number=line_num,
                        matched_code=line.strip(),
                        message="Database path should come from settings.database_path",
                        fix_suggestion="from .settings import settings; use settings.database_path",
                    )
                )

            # Config directory
            if ".config" in line and "settings." not in line and not has_settings_import:
                violations.append(
                    self.create_match(
                        file_path=file_path,
                        line_number=line_num,
                        matched_code=line.strip(),
                        message="Config directory should come from settings.config_dir",
                        fix_suggestion="from .settings import settings; use settings.config_dir",
                    )
                )

        return violations

    async def scan_directory(self, directory: Path) -> ScanResult:
        """Scan directory for missing settings usage."""
        self.start_time = datetime.utcnow()
        all_violations = []
        files_scanned = 0

        for py_file in directory.rglob("*.py"):
            # Skip settings.py itself
            if py_file.name == "settings.py":
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                violations = await self.scan_file(py_file, content)
                all_violations.extend(violations)
                files_scanned += 1
            except (OSError, UnicodeDecodeError):
                continue

        self.end_time = datetime.utcnow()
        duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

        return ScanResult(
            scan_id=self.scan_id,
            timestamp=self.start_time,
            repository_path=str(directory),
            files_scanned=files_scanned,
            patterns_checked=1,
            violations=all_violations,
            duration_ms=duration_ms,
            confidence_avg=1.0 if all_violations else None,
        )


class ScanRegistry:
    """Registry of all available scans."""

    # Define all available scans
    SCAN_DEFINITIONS = [
        ScanDefinition(
            id="hardcoded-paths",
            name="Hardcoded Path Detection",
            description="Detects hardcoded paths that should use settings",
            category=ScanCategory.CONSISTENCY,
            severity=ScanSeverity.HIGH,
            tags=["settings", "paths", "configuration"],
        ),
        ScanDefinition(
            id="multiple-imports",
            name="Multiple Import Detection",
            description="Detects conflicting imports of similar modules",
            category=ScanCategory.CONSISTENCY,
            severity=ScanSeverity.MEDIUM,
            tags=["imports", "consistency"],
        ),
        ScanDefinition(
            id="missing-settings",
            name="Missing Settings Usage",
            description="Detects code that should use settings but doesn't",
            category=ScanCategory.CONSISTENCY,
            severity=ScanSeverity.MEDIUM,
            tags=["settings", "configuration"],
        ),
    ]

    # Map scan IDs to implementation classes
    SCAN_IMPLEMENTATIONS = {
        "hardcoded-paths": HardcodedPathScan,
        "multiple-imports": MultipleImportsScan,
        "missing-settings": MissingSettingsUsageScan,
    }

    @classmethod
    def get_scan(cls, scan_id: str) -> BaseScan | None:
        """Get a scan instance by ID."""
        definition = cls.get_definition(scan_id)
        if not definition:
            return None

        implementation = cls.SCAN_IMPLEMENTATIONS.get(scan_id)
        if not implementation:
            return None

        return implementation(definition)

    @classmethod
    def get_definition(cls, scan_id: str) -> ScanDefinition | None:
        """Get scan definition by ID."""
        for definition in cls.SCAN_DEFINITIONS:
            if definition.id == scan_id:
                return definition
        return None

    @classmethod
    def list_scans(cls, category: ScanCategory | None = None) -> list[ScanDefinition]:
        """List all available scans, optionally filtered by category."""
        if category:
            return [d for d in cls.SCAN_DEFINITIONS if d.category == category]
        return cls.SCAN_DEFINITIONS

    @classmethod
    def get_enabled_scans(cls) -> list[ScanDefinition]:
        """Get all enabled scans."""
        return [d for d in cls.SCAN_DEFINITIONS if d.enabled]

    @classmethod
    async def run_scan(cls, scan_id: str, directory: Path) -> ScanResult | None:
        """Run a specific scan on a directory."""
        scan = cls.get_scan(scan_id)
        if not scan:
            return None
        return await scan.scan_directory(directory)

    @classmethod
    async def run_all_scans(cls, directory: Path, category: ScanCategory | None = None) -> dict[str, ScanResult]:
        """Run all enabled scans on a directory."""
        results = {}
        scans = cls.list_scans(category)

        for definition in scans:
            if not definition.enabled:
                continue

            scan = cls.get_scan(definition.id)
            if scan:
                result = await scan.scan_directory(directory)
                results[definition.id] = result

        return results

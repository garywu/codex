"""
Pydantic models for Codex patterns - Single source of truth for pattern data.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatternCategory(str, Enum):
    """Categories of code patterns."""

    NAMING = "naming"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    VALIDATION = "validation"
    ORGANIZATION = "organization"
    IMPORTS = "imports"
    DEPENDENCIES = "dependencies"
    TESTING = "testing"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    DATABASE = "database"
    API_DESIGN = "api_design"
    CLI_DESIGN = "cli_design"
    FUNCTIONAL = "functional"
    GIT = "git"
    MONITORING = "monitoring"
    TYPING = "typing"
    CI_CD = "ci_cd"


class PatternPriority(str, Enum):
    """Priority levels for patterns."""

    MANDATORY = "MANDATORY"
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    OPTIONAL = "OPTIONAL"


class PatternDetection(BaseModel):
    """Pattern detection configuration."""

    model_config = ConfigDict(extra="allow")

    regex: str | None = Field(None, description="Regex pattern for detection")
    ast_pattern: str | None = Field(None, description="AST pattern for detection")
    keywords: list[str] = Field(default_factory=list, description="Keywords to search")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Detection confidence")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        return max(0.0, min(1.0, v))


class PatternFix(BaseModel):
    """Pattern fix configuration."""

    model_config = ConfigDict(extra="allow")

    template: str | None = Field(None, description="Fix template")
    complexity: str = Field(default="medium", pattern="^(simple|medium|complex)$")
    auto_fixable: bool = Field(default=False, description="Can be automatically fixed")
    suggestions: list[str] = Field(default_factory=list, description="Fix suggestions")
    prerequisites: list[str] = Field(default_factory=list, description="Prerequisites for fix")


class PatternExample(BaseModel):
    """Code examples for a pattern."""

    model_config = ConfigDict(extra="allow")

    good: str | None = Field(None, description="Good example code")
    bad: str | None = Field(None, description="Bad example code")
    context: str | None = Field(None, description="Context or explanation")


class Pattern(BaseModel):
    """Complete pattern definition using Pydantic."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    # Core fields
    id: int | None = Field(None, description="Database ID")
    name: str = Field(..., min_length=1, max_length=100, description="Unique pattern name")
    category: PatternCategory = Field(..., description="Pattern category")
    priority: PatternPriority = Field(PatternPriority.MEDIUM, description="Pattern priority")

    # Description fields
    description: str = Field(..., min_length=1, description="What this pattern does")
    rule: str = Field(..., description="The rule to follow")
    rationale: str = Field("", description="Why this pattern matters")

    # Detection and fixing
    detection: PatternDetection = Field(
        default_factory=lambda: PatternDetection(regex=None, ast_pattern=None, keywords=[], confidence=0.9)
    )
    fix: PatternFix = Field(
        default_factory=lambda: PatternFix(
            template=None, complexity="medium", auto_fixable=False, suggestions=[], prerequisites=[]
        )
    )

    # Examples
    examples: PatternExample = Field(default_factory=lambda: PatternExample(good=None, bad=None, context=None))

    # Metadata
    source: str = Field(default="project-init", description="Pattern source")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    enabled: bool = Field(default=True, description="Pattern is enabled")

    # AI-specific fields
    ai_explanation: str | None = Field(None, description="AI-friendly explanation")
    business_impact: str | None = Field(None, description="Business impact of violation")
    learning_value: str | None = Field(None, description="What can be learned")

    # Usage tracking
    usage_count: int = Field(default=0, ge=0, description="Times pattern was used")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Success rate")
    last_used: datetime | None = Field(None, description="Last usage timestamp")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name follows naming convention."""
        import re

        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Name must be lowercase with hyphens only")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are lowercase."""
        return [tag.lower().strip() for tag in v if tag.strip()]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage."""
        return self.model_dump(exclude_none=True)

    def to_fts_document(self) -> str:
        """Generate searchable document for FTS."""
        parts = [
            self.name,
            self.category.value,
            self.priority.value,
            self.description,
            self.rule,
            self.rationale,
            " ".join(self.tags),
        ]

        if self.ai_explanation:
            parts.append(self.ai_explanation)
        if self.business_impact:
            parts.append(self.business_impact)
        if self.examples.good:
            parts.append(self.examples.good)
        if self.examples.bad:
            parts.append(self.examples.bad)

        return " ".join(filter(None, parts))


class PatternMatch(BaseModel):
    """Result of pattern matching in code."""

    model_config = ConfigDict(extra="forbid")

    pattern: Pattern = Field(..., description="Matched pattern")
    file_path: str = Field(..., description="File where pattern was found")
    line_number: int | None = Field(None, ge=1, description="Line number")
    column: int | None = Field(None, ge=0, description="Column number")
    matched_code: str = Field(..., description="Code that matched")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence")

    # Context
    surrounding_code: str | None = Field(None, description="Code context")
    file_context: dict[str, Any] | None = Field(None, description="File metadata")

    # Fix information
    can_fix: bool = Field(default=False, description="Can be auto-fixed")
    fix_suggestion: str | None = Field(None, description="Suggested fix")
    fix_complexity: str | None = Field(None, pattern="^(simple|medium|complex)$")

    # AI enhancement
    ai_analysis: str | None = Field(None, description="AI analysis of violation")
    business_impact: str | None = Field(None, description="Business impact")
    learning_note: str | None = Field(None, description="Learning opportunity")


class ScanResult(BaseModel):
    """Result of scanning a file or repository."""

    model_config = ConfigDict(extra="forbid")

    # Scan metadata
    scan_id: str = Field(..., description="Unique scan ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    repository_path: str = Field(..., description="Repository scanned")

    # Results
    files_scanned: int = Field(default=0, ge=0)
    patterns_checked: int = Field(default=0, ge=0)
    violations: list[PatternMatch] = Field(default_factory=list)

    # Statistics
    duration_ms: int | None = Field(None, ge=0, description="Scan duration")
    confidence_avg: float | None = Field(None, ge=0.0, le=1.0)

    # AI context
    ai_context: str | None = Field(None, description="AI context for scan")
    repository_insights: dict[str, Any] | None = Field(None, description="Repository insights")

    def get_summary(self) -> dict[str, Any]:
        """Get scan summary."""
        violations_by_priority: dict[str, int] = {}
        violations_by_category: dict[str, int] = {}

        for violation in self.violations:
            # By priority
            priority = violation.pattern.priority.value
            violations_by_priority[priority] = violations_by_priority.get(priority, 0) + 1

            # By category
            category = violation.pattern.category.value
            violations_by_category[category] = violations_by_category.get(category, 0) + 1

        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp.isoformat(),
            "files_scanned": self.files_scanned,
            "total_violations": len(self.violations),
            "by_priority": violations_by_priority,
            "by_category": violations_by_category,
            "confidence_avg": self.confidence_avg,
            "duration_ms": self.duration_ms,
        }


class PatternImport(BaseModel):
    """Model for importing patterns from JSON."""

    model_config = ConfigDict(extra="allow")

    version: str = Field(default="2.0.0", description="Import format version")
    source: str = Field(..., description="Source of patterns")
    patterns: list[dict[str, Any]] = Field(..., description="Pattern data to import")

    def convert_to_patterns(self) -> list[Pattern]:
        """Convert imported data to Pattern models."""
        converted = []

        for pattern_data in self.patterns:
            try:
                # Map old format to new Pattern model
                pattern = Pattern(
                    name=pattern_data.get("name", ""),
                    category=self._map_category(pattern_data.get("category", "")),
                    priority=self._map_priority(pattern_data.get("priority", "MEDIUM")),
                    description=pattern_data.get("description", ""),
                    rule=pattern_data.get("rule", pattern_data.get("description", "")),
                    rationale=pattern_data.get("why", ""),
                    detection=PatternDetection(
                        regex=pattern_data.get("detect"),
                        ast_pattern=pattern_data.get("ast_pattern"),
                        confidence=pattern_data.get("confidence", 0.9),
                    ),
                    fix=PatternFix(
                        template=pattern_data.get("fix"),
                        auto_fixable=bool(pattern_data.get("auto_fixable", False)),
                        complexity=self._map_complexity(pattern_data.get("fix_complexity", "medium")),
                    ),
                    examples=PatternExample(
                        good=pattern_data.get("good_example"),
                        bad=pattern_data.get("bad_example"),
                        context=pattern_data.get("context"),
                    ),
                    source=pattern_data.get("source", self.source),
                    tags=self._extract_tags(pattern_data),
                    ai_explanation=pattern_data.get("ai_explanation"),
                    business_impact=pattern_data.get("business_impact"),
                )
                converted.append(pattern)
            except Exception as e:
                logging.info(f"Warning: Could not convert pattern {pattern_data.get('name', 'unknown')}: {e}")
                continue

        return converted

    @staticmethod
    def _map_category(category: str) -> PatternCategory:
        """Map string to PatternCategory."""
        category_map = {
            "naming": PatternCategory.NAMING,
            "error_handling": PatternCategory.ERROR_HANDLING,
            "logging": PatternCategory.LOGGING,
            "validation": PatternCategory.VALIDATION,
            "organization": PatternCategory.ORGANIZATION,
            "imports": PatternCategory.IMPORTS,
            "dependencies": PatternCategory.DEPENDENCIES,
            "testing": PatternCategory.TESTING,
            "security": PatternCategory.SECURITY,
            "documentation": PatternCategory.DOCUMENTATION,
            "git": PatternCategory.GIT,
        }
        return category_map.get(category.lower(), PatternCategory.ORGANIZATION)

    @staticmethod
    def _map_priority(priority: str) -> PatternPriority:
        """Map string to PatternPriority."""
        try:
            return PatternPriority(priority.upper())
        except ValueError:
            return PatternPriority.MEDIUM

    @staticmethod
    def _map_complexity(complexity: str) -> str:
        """Map complexity to valid values."""
        if complexity in ["simple", "medium", "complex"]:
            return complexity
        return "medium"

    @staticmethod
    def _extract_tags(pattern_data: dict[str, Any]) -> list[str]:
        """Extract tags from pattern data."""
        tags = []

        # From explicit tags field
        if "tags" in pattern_data:
            if isinstance(pattern_data["tags"], str):
                tags.extend(pattern_data["tags"].split())
            elif isinstance(pattern_data["tags"], list):
                tags.extend(pattern_data["tags"])

        # Add category and priority as tags
        if "category" in pattern_data:
            tags.append(pattern_data["category"])
        if "priority" in pattern_data:
            tags.append(pattern_data["priority"].lower())

        return list(set(tags))  # Remove duplicates

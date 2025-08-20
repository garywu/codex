"""
Data models for Codex pattern storage and analysis.

Using SQLModel for database persistence and Pydantic for validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlmodel import JSON, Column, SQLModel
from sqlmodel import Field as SQLField


class PatternCategory(str, Enum):
    """Categories of code patterns."""

    PACKAGE_MANAGEMENT = "package_management"
    CORE_LIBRARIES = "core_libraries"
    QUALITY_TOOLS = "quality_tools"
    PROJECT_STRUCTURE = "project_structure"
    ERROR_HANDLING = "error_handling"
    VALIDATION = "validation"
    RESOURCE_MANAGEMENT = "resource_management"
    TESTING = "testing"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    DECORATORS = "decorators"
    DATABASE = "database"
    API_DESIGN = "api_design"
    CLI_DESIGN = "cli_design"
    FUNCTIONAL = "functional"


class PatternPriority(str, Enum):
    """Priority levels for patterns."""

    MANDATORY = "mandatory"
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


class Pattern(SQLModel, table=True):
    """A code pattern or best practice stored in the database."""
    __tablename__ = "patterns"  # Explicitly set table name to match unified_database.py

    id: int | None = SQLField(default=None, primary_key=True)
    name: str = SQLField(index=True, description="Pattern name")
    category: PatternCategory = SQLField(description="Pattern category")
    priority: PatternPriority = SQLField(default=PatternPriority.MEDIUM)
    description: str = SQLField(description="What this pattern does")
    
    # Pattern details
    pattern_code: str | None = SQLField(default=None, description="Example code implementing the pattern")
    anti_pattern: str | None = SQLField(default=None, description="What to avoid")
    detection_rules: dict[str, Any] = SQLField(default={}, sa_column=Column(JSON))
    fix_template: str | None = SQLField(default=None, description="Template for fixing violations")
    
    # Metadata
    source: str = SQLField(default="project-init", description="Where this pattern came from")
    tags: list[str] = SQLField(default=[], sa_column=Column(JSON))
    when_to_use: list[str] = SQLField(default=[], sa_column=Column(JSON))
    best_practices: list[str] = SQLField(default=[], sa_column=Column(JSON))
    
    # Usage tracking
    usage_count: int = SQLField(default=0, description="Times this pattern was applied")
    success_rate: float = SQLField(default=1.0, description="Success rate when applied")
    last_used: datetime | None = SQLField(default=None)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class PatternMatch(BaseModel):
    """Result of pattern matching in code."""

    pattern_id: int
    pattern_name: str
    category: PatternCategory
    priority: PatternPriority
    file_path: str
    line_number: int | None = None
    column: int | None = None
    matched_code: str
    confidence: float = Field(ge=0.0, le=1.0)
    suggestion: str | None = None
    auto_fixable: bool = False
    fix_code: str | None = None


class CodeContext(BaseModel):
    """Context for code analysis."""

    project_root: str
    file_path: str
    content: str
    language: str | None = None
    framework: str | None = None
    dependencies: list[str] = []
    existing_patterns: list[str] = []


class AnalysisResult(BaseModel):
    """Result of analyzing code for patterns."""

    file_path: str
    matches: list[PatternMatch] = []
    applied_patterns: list[str] = []
    missing_patterns: list[str] = []
    violations: list[PatternMatch] = []
    score: float = Field(ge=0.0, le=1.0)
    suggestions: list[str] = []


class TrainingExample(BaseModel):
    """Training example for Farm SDK agents."""

    input: dict[str, Any]
    output: dict[str, Any]
    pattern_name: str
    category: PatternCategory
    description: str | None = None
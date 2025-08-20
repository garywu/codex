"""
Custom exceptions for Codex.

Following project-init best practices for actionable error messages.
"""


class CodexError(Exception):
    """Base exception for Codex errors."""

    def __init__(self, message: str, suggestion: str | None = None):
        """Initialize with message and optional suggestion."""
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.message)

    def __str__(self) -> str:
        """Format error message with suggestion."""
        if self.suggestion:
            return f"{self.message}\n💡 Suggestion: {self.suggestion}"
        return self.message


class PatternNotFoundError(CodexError):
    """Raised when a pattern is not found."""

    def __init__(self, pattern_name: str):
        """Initialize with pattern name."""
        super().__init__(
            f"Pattern '{pattern_name}' not found",
            "Use 'codex patterns list' to see available patterns",
        )


class AnalysisError(CodexError):
    """Raised when code analysis fails."""

    def __init__(self, file_path: str, reason: str):
        """Initialize with file path and reason."""
        super().__init__(
            f"Failed to analyze {file_path}: {reason}",
            "Check that the file exists and is readable",
        )


class PatternImportError(CodexError):
    """Raised when pattern import fails."""

    def __init__(self, source: str, reason: str):
        """Initialize with source and reason."""
        super().__init__(
            f"Failed to import patterns from {source}: {reason}",
            "Verify the source file format and content",
        )


class FarmAgentError(CodexError):
    """Raised when Farm SDK agent operations fail."""

    def __init__(self, agent_name: str, reason: str):
        """Initialize with agent name and reason."""
        super().__init__(
            f"Farm agent '{agent_name}' failed: {reason}",
            "Check Farm SDK connection and agent training status",
        )


class TemplateError(CodexError):
    """Raised when template operations fail."""

    def __init__(self, template_name: str, reason: str):
        """Initialize with template name and reason."""
        super().__init__(
            f"Template '{template_name}' failed: {reason}",
            "Verify CookieCutter template is properly configured",
        )

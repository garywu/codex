"""
Codex - Universal code generation platform with pattern-based best practices

Combines pattern recognition, Farm SDK agents, and CookieCutter templates
for intelligent code generation and quality assurance.
"""

__version__ = "0.1.0"

from .exceptions import AnalysisError, CodexError, PatternNotFoundError
from .models import CodeContext, Pattern, PatternCategory, PatternMatch

# Optional imports
try:
    from .client import CodexClient

    __all__ = [
        "CodexClient",
        "Pattern",
        "PatternCategory",
        "PatternMatch",
        "CodeContext",
        "CodexError",
        "PatternNotFoundError",
        "AnalysisError",
    ]
except ImportError:
    # Farm SDK not available
    __all__ = [
        "Pattern",
        "PatternCategory",
        "PatternMatch",
        "CodeContext",
        "CodexError",
        "PatternNotFoundError",
        "AnalysisError",
    ]

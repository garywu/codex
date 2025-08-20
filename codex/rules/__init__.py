"""
Codex Rules System - Inspired by Ruff's modular architecture.

This package organizes all Codex scanning rules following Astral's design principles:
- Each rule category has its own module
- Rules have unique codes with category prefixes
- Rich violation context and fix capabilities
- Semantic-aware analysis where possible
"""

from .categories import RulePrefix
from .registry import Rule, RuleRegistry, Violation

__all__ = [
    "Rule",
    "RulePrefix",
    "RuleRegistry",
    "Violation",
]

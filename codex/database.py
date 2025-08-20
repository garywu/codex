"""
Database module - REDIRECTS TO UNIFIED DATABASE.

This module now redirects to unified_database.py to ensure consistency.
"""

# Import everything from unified_database to maintain compatibility
# Add deprecation warning
import warnings

from .unified_database import UnifiedDatabase

warnings.warn(
    "database.py is deprecated. Please import from unified_database directly: "
    "from codex.unified_database import UnifiedDatabase",
    DeprecationWarning,
    stacklevel=2,
)

# Provide Database as alias for compatibility
Database = UnifiedDatabase

__all__ = ["Database", "UnifiedDatabase"]

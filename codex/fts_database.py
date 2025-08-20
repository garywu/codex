"""
FTS Database module - REDIRECTS TO UNIFIED DATABASE.

This module now redirects to unified_database.py to ensure consistency.
The UnifiedDatabase has FTS5 support built-in.
"""

# Import everything from unified_database to maintain compatibility
# Add deprecation warning
import warnings

from .unified_database import UnifiedDatabase

warnings.warn(
    "fts_database.py is deprecated. Please import from unified_database directly: "
    "from codex.unified_database import UnifiedDatabase",
    DeprecationWarning,
    stacklevel=2,
)

# Provide FTSDatabase as alias for compatibility
FTSDatabase = UnifiedDatabase

# For pattern extractor compatibility - redirect to proper model
from .pattern_models import Pattern as FTSPattern

__all__ = ["FTSDatabase", "UnifiedDatabase", "FTSPattern"]

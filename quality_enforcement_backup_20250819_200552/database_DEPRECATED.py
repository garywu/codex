"""
DEPRECATED - DO NOT USE!

This module is deprecated. Use unified_database.py instead.
This file is kept temporarily for reference during migration.

All new code MUST use:
    from .unified_database import UnifiedDatabase
    from .settings import settings

Database path MUST come from settings:
    settings.database_path
"""

raise ImportError(
    "database.py is deprecated! Use unified_database.py instead.\n"
    "Import with: from .unified_database import UnifiedDatabase"
)
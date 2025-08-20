"""
Modular Fixers Package

Small, focused, composable fixers following Unix philosophy.
Each fixer does one thing well and can be combined with others.
"""

from .external_tools_fixer import ExternalToolsFixer
from .fixer_orchestrator import FixerOrchestrator
from .hardcoded_paths_fixer import HardcodedPathsFixer
from .import_consolidation_fixer import ImportConsolidationFixer
from .print_to_logging_fixer import PrintToLoggingFixer

__all__ = [
    "ExternalToolsFixer",
    "PrintToLoggingFixer",
    "HardcodedPathsFixer",
    "ImportConsolidationFixer",
    "FixerOrchestrator",
]

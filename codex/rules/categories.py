"""
Rule category definitions with unique prefixes.

Following Ruff's pattern of using letter prefixes to categorize rules.
"""

from enum import Enum


class RulePrefix(str, Enum):
    """Rule prefixes for different categories."""
    
    # Codex-specific rules (CDX prefix)
    CDX = "CDX"  # Codex best practices
    
    # Settings and Configuration (SET prefix)  
    SET = "SET"  # Settings management (Pydantic, config)
    
    # Database (DB prefix)
    DB = "DB"    # Database patterns and practices
    
    # Dependencies (DEP prefix)
    DEP = "DEP"  # Package management, dependencies
    
    # Security (SEC prefix)
    SEC = "SEC"  # Security vulnerabilities
    
    # Architecture (ARC prefix)
    ARC = "ARC"  # Code structure, imports
    
    # Testing (TST prefix)
    TST = "TST"  # Testing patterns
    
    # Logging (LOG prefix)
    LOG = "LOG"  # Logging practices
    
    # API (API prefix)
    API = "API"  # API design patterns
    
    # Performance (PRF prefix)
    PRF = "PRF"  # Performance optimizations
    
    # External Tools (mirrors Ruff's approach)
    E = "E"      # pycodestyle errors
    W = "W"      # pycodestyle warnings
    F = "F"      # Pyflakes
    B = "B"      # flake8-bugbear
    T = "T"      # External tools (ruff, ty, typos)


CATEGORY_DESCRIPTIONS: dict[RulePrefix, str] = {
    RulePrefix.CDX: "Codex best practices and patterns",
    RulePrefix.SET: "Settings and configuration management",
    RulePrefix.DB: "Database patterns and practices",
    RulePrefix.DEP: "Dependency and package management",
    RulePrefix.SEC: "Security vulnerabilities and risks",
    RulePrefix.ARC: "Architecture and code structure",
    RulePrefix.TST: "Testing patterns and practices",
    RulePrefix.LOG: "Logging configuration and usage",
    RulePrefix.API: "API design and validation",
    RulePrefix.PRF: "Performance optimizations",
    RulePrefix.E: "pycodestyle errors",
    RulePrefix.W: "pycodestyle warnings", 
    RulePrefix.F: "Pyflakes",
    RulePrefix.B: "flake8-bugbear",
    RulePrefix.T: "External tools integration",
}


def get_prefix_from_code(code: str) -> RulePrefix:
    """Extract the prefix from a rule code."""
    # Handle multi-letter prefixes
    for prefix in RulePrefix:
        if code.startswith(prefix.value):
            return prefix
    
    # Default to first letter for single-letter prefixes
    return RulePrefix(code[0])


def is_codex_rule(code: str) -> bool:
    """Check if a rule code is a Codex-specific rule."""
    codex_prefixes = {
        RulePrefix.CDX, RulePrefix.SET, RulePrefix.DB,
        RulePrefix.DEP, RulePrefix.SEC, RulePrefix.ARC,
        RulePrefix.TST, RulePrefix.LOG, RulePrefix.API,
        RulePrefix.PRF
    }
    
    try:
        prefix = get_prefix_from_code(code)
        return prefix in codex_prefixes
    except (IndexError, ValueError):
        return False
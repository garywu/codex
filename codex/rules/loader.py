"""
Rule loader - Automatically discovers and registers all rules.

Following Ruff's pattern of modular rule loading.
"""


from .categories import RulePrefix
from .registry import Rule, registry


def load_all_rules():
    """Load all rule modules and register their rules."""
    # Import rule modules
    from .unified_database import UnifiedDatabase

    # Register rules from each module
    # settings_rules.register_settings_rules(registry)
    # database_rules.register_database_rules(registry)

    # Future modules will be added here:
    # security_rules.register_security_rules(registry)
    # api_rules.register_api_rules(registry)
    # testing_rules.register_testing_rules(registry)
    # etc.

    return registry


def get_rule_stats() -> dict[str, int]:
    """Get statistics about loaded rules."""
    stats = {
        "total_rules": len(registry._rules),
        "enabled_rules": len(registry.get_enabled_rules()),
        "categories": len(set(r.prefix for r in registry._rules.values())),
    }

    # Count by category
    for prefix in RulePrefix:
        rules = registry.get_rules_by_prefix(prefix)
        if rules:
            stats[f"{prefix.value}_rules"] = len(rules)

    return stats


def select_rules_from_config(config: dict) -> set[str]:
    """Select rules based on configuration."""
    selected = set()

    # Handle 'select' option (rules to enable)
    if 'select' in config:
        selectors = config['select']
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            rules = registry.select_rules([selector])
            selected.update(r.code for r in rules)

    # Handle 'ignore' option (rules to disable)
    if 'ignore' in config:
        ignores = config['ignore']
        if isinstance(ignores, str):
            ignores = [ignores]

        for ignore in ignores:
            rules = registry.select_rules([ignore])
            selected.difference_update(r.code for r in rules)

    # Handle 'extend-select' option (additional rules)
    if 'extend_select' in config:
        extends = config['extend_select']
        if isinstance(extends, str):
            extends = [extends]

        for extend in extends:
            rules = registry.select_rules([extend])
            selected.update(r.code for r in rules)

    return selected


def format_rule_help(rule: Rule) -> str:
    """Format help text for a rule."""
    lines = [
        f"{rule.code}: {rule.name}",
        f"  Severity: {rule.severity.value}",
        f"  {rule.description or 'No description'}",
    ]

    if rule.rationale:
        lines.append(f"  Rationale: {rule.rationale}")

    if rule.tags:
        lines.append(f"  Tags: {', '.join(rule.tags)}")

    if rule.examples:
        if 'good' in rule.examples:
            lines.append("  Good example:")
            for line in rule.examples['good'].split('\n'):
                lines.append(f"    {line}")
        if 'bad' in rule.examples:
            lines.append("  Bad example:")
            for line in rule.examples['bad'].split('\n'):
                lines.append(f"    {line}")

    return '\n'.join(lines)


def list_rules_by_category() -> dict[RulePrefix, list[Rule]]:
    """List all rules organized by category."""
    result = {}

    for prefix in RulePrefix:
        rules = registry.get_rules_by_prefix(prefix)
        if rules:
            result[prefix] = sorted(rules, key=lambda r: r.code)

    return result


# Initialize rules on module import
_initialized = False

def ensure_initialized():
    """Ensure rules are loaded."""
    global _initialized
    if not _initialized:
        load_all_rules()
        _initialized = True


# Auto-initialize when imported
ensure_initialized()

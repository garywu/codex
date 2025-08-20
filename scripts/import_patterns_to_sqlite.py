#!/usr/bin/env python3
"""
Import the extracted patterns from project-init v2 into Codex SQLite database.

This script takes the patterns we extracted and properly imports them into
the SQLModel-based SQLite database.
"""

import asyncio
import json

# Add parent directory to path for imports
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from codex.database import Database
from codex.fts_database import FTSDatabase
from codex.models import Pattern, PatternCategory, PatternPriority


def convert_category(category: str) -> PatternCategory:
    """Convert string category to PatternCategory enum."""
    category_map = {
        "naming": PatternCategory.PROJECT_STRUCTURE,
        "error_handling": PatternCategory.ERROR_HANDLING,
        "logging": PatternCategory.DOCUMENTATION,
        "validation": PatternCategory.VALIDATION,
        "organization": PatternCategory.PROJECT_STRUCTURE,
        "imports": PatternCategory.PROJECT_STRUCTURE,
        "dependencies": PatternCategory.PACKAGE_MANAGEMENT,
        "testing": PatternCategory.TESTING,
        "git": PatternCategory.DOCUMENTATION,
    }
    return category_map.get(category, PatternCategory.PROJECT_STRUCTURE)


def convert_priority(priority: str) -> PatternPriority:
    """Convert string priority to PatternPriority enum."""
    priority_map = {
        "MANDATORY": PatternPriority.MANDATORY,
        "CRITICAL": PatternPriority.CRITICAL,
        "HIGH": PatternPriority.HIGH,
        "MEDIUM": PatternPriority.MEDIUM,
        "LOW": PatternPriority.LOW,
        "OPTIONAL": PatternPriority.OPTIONAL,
    }
    return priority_map.get(priority.upper(), PatternPriority.MEDIUM)


async def import_patterns_to_sqlmodel(patterns_file: str):
    """Import patterns into SQLModel database."""

    print(f"📥 Loading patterns from {patterns_file}")
    with open(patterns_file) as f:
        data = json.load(f)

    patterns_data = data.get("patterns", [])
    print(f"Found {len(patterns_data)} patterns to import")

    # Initialize database
    db = Database()
    await db.init_db()

    imported_count = 0
    updated_count = 0

    async with db.get_session() as session:
        for pattern_data in patterns_data:
            # Check if pattern already exists
            existing = await db.get_pattern_by_name(pattern_data["name"])

            if existing:
                # Update existing pattern
                existing.description = pattern_data.get("description", existing.description)
                existing.category = convert_category(pattern_data.get("category", ""))
                existing.priority = convert_priority(pattern_data.get("priority", "MEDIUM"))
                existing.detection_rules = {
                    "detect": pattern_data.get("detect", ""),
                    "fix": pattern_data.get("fix", ""),
                    "why": pattern_data.get("why", ""),
                }
                existing.pattern_code = pattern_data.get("good_example", "")
                existing.anti_pattern = pattern_data.get("bad_example", "")
                existing.fix_template = pattern_data.get("fix", "")
                existing.tags = pattern_data.get("tags", "").split() if pattern_data.get("tags") else []
                existing.source = pattern_data.get("source", "project-init-v2")
                existing.updated_at = datetime.utcnow()

                session.add(existing)
                updated_count += 1
                print(f"  ✓ Updated: {pattern_data['name']}")
            else:
                # Create new pattern
                pattern = Pattern(
                    name=pattern_data["name"],
                    category=convert_category(pattern_data.get("category", "")),
                    priority=convert_priority(pattern_data.get("priority", "MEDIUM")),
                    description=pattern_data.get("description", ""),
                    pattern_code=pattern_data.get("good_example", ""),
                    anti_pattern=pattern_data.get("bad_example", ""),
                    detection_rules={
                        "detect": pattern_data.get("detect", ""),
                        "fix": pattern_data.get("fix", ""),
                        "why": pattern_data.get("why", ""),
                        "rule": pattern_data.get("rule", ""),
                    },
                    fix_template=pattern_data.get("fix", ""),
                    source=pattern_data.get("source", "project-init-v2"),
                    tags=pattern_data.get("tags", "").split() if pattern_data.get("tags") else [],
                    when_to_use=[pattern_data.get("rule", "")] if pattern_data.get("rule") else [],
                    best_practices=[pattern_data.get("why", "")] if pattern_data.get("why") else [],
                )

                session.add(pattern)
                imported_count += 1
                print(f"  ✓ Imported: {pattern_data['name']}")

        await session.commit()

    print(f"\n✅ Import complete!")
    print(f"  • Imported: {imported_count} new patterns")
    print(f"  • Updated: {updated_count} existing patterns")
    print(f"  • Total: {imported_count + updated_count} patterns processed")

    await db.close()


def import_patterns_to_fts(patterns_file: str):
    """Import patterns into FTS database for AI queries."""

    print(f"\n📥 Importing patterns to FTS database")
    with open(patterns_file) as f:
        data = json.load(f)

    patterns_data = data.get("patterns", [])

    # Initialize FTS database
    fts_db = FTSDatabase()

    imported_count = 0
    for pattern_data in patterns_data:
        # Convert to FTS format
        fts_pattern = {
            "name": pattern_data["name"],
            "category": pattern_data.get("category", ""),
            "priority": pattern_data.get("priority", "MEDIUM"),
            "description": pattern_data.get("description", ""),
            "rule": pattern_data.get("rule", ""),
            "detect": pattern_data.get("detect", ""),
            "fix": pattern_data.get("fix", ""),
            "why": pattern_data.get("why", ""),
            "good_example": pattern_data.get("good_example", ""),
            "bad_example": pattern_data.get("bad_example", ""),
        }

        fts_db.add_pattern(fts_pattern)
        imported_count += 1

    print(f"✅ Imported {imported_count} patterns to FTS database")

    # Test search
    print("\n🔍 Testing FTS search...")
    results = fts_db.search_patterns("naming")
    print(f"Found {len(results)} patterns related to 'naming'")

    results = fts_db.search_patterns("error handling")
    print(f"Found {len(results)} patterns related to 'error handling'")


async def verify_import():
    """Verify patterns were imported correctly."""

    print("\n🔍 Verifying import...")

    db = Database()

    # Get pattern counts by category
    async with db.get_session() as session:
        patterns = await db.get_all_patterns()

        categories = {}
        priorities = {}

        for pattern in patterns:
            cat = pattern.category.value
            categories[cat] = categories.get(cat, 0) + 1

            prio = pattern.priority.value
            priorities[prio] = priorities.get(prio, 0) + 1

        print(f"\n📊 Database Statistics:")
        print(f"Total patterns: {len(patterns)}")

        print("\nBy Category:")
        for cat, count in sorted(categories.items()):
            print(f"  • {cat}: {count}")

        print("\nBy Priority:")
        for prio in ["mandatory", "critical", "high", "medium", "low", "optional"]:
            if prio in priorities:
                print(f"  • {prio}: {priorities[prio]}")

        # Show some examples
        print("\n📝 Sample Patterns:")
        for pattern in patterns[:3]:
            print(f"\n[{pattern.priority.value.upper()}] {pattern.name}")
            print(f"  Category: {pattern.category.value}")
            print(f"  Description: {pattern.description[:80]}...")

    await db.close()


async def main():
    """Main import function."""

    print("🚀 Codex Pattern Import Tool")
    print("=" * 40)

    # Check for pattern files
    pattern_files = ["codex_patterns_v2_enhanced.json", "patterns_from_project_init_v2.json"]

    available_files = [f for f in pattern_files if Path(f).exists()]

    if not available_files:
        print("❌ No pattern files found!")
        print("Please run enhanced_pattern_extractor.py first")
        return

    # Use the most comprehensive file
    patterns_file = available_files[0]
    print(f"Using pattern file: {patterns_file}")

    # Import to SQLModel database
    await import_patterns_to_sqlmodel(patterns_file)

    # Import to FTS database
    import_patterns_to_fts(patterns_file)

    # Verify import
    await verify_import()

    print("\n✨ Pattern import complete!")
    print("\nYou can now use the patterns with:")
    print("  codex scan .                    # Scan current directory")
    print("  codex scan --fix                # Auto-fix violations")
    print("  codex query 'naming patterns'   # Search patterns")
    print("  codex explain no-bare-except    # Explain a pattern")


if __name__ == "__main__":
    asyncio.run(main())

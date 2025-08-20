#!/usr/bin/env python3
"""
Import patterns into the unified SQLite database using Pydantic models.
"""

import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from codex.unified_database import UnifiedDatabase
from codex.pattern_models import Pattern, PatternCategory, PatternPriority
from codex.settings import settings


def main():
    """Import patterns into unified database."""
    
    print("🚀 Unified Pattern Import")
    print("=" * 40)
    print(f"Database: {settings.database_path}")
    print(f"FTS Enabled: {settings.enable_fts}")
    print()
    
    # Initialize database
    db = UnifiedDatabase()
    
    # Find pattern files
    pattern_files = [
        "codex_patterns_v2_enhanced.json",
        "patterns_from_project_init_v2.json"
    ]
    
    available_files = [f for f in pattern_files if Path(f).exists()]
    
    if not available_files:
        print("❌ No pattern files found!")
        print("Run enhanced_pattern_extractor.py first")
        return
    
    # Import from the most comprehensive file
    import_file = Path(available_files[0])
    print(f"📥 Importing from: {import_file}")
    
    # Import patterns
    result = db.import_patterns(import_file)
    
    print(f"\n✅ Import Results:")
    print(f"  • New patterns: {result['imported']}")
    print(f"  • Updated patterns: {result['updated']}")
    print(f"  • Total processed: {result['total']}")
    
    # Show statistics
    stats = db.get_statistics()
    
    print(f"\n📊 Database Statistics:")
    print(f"  • Total patterns: {stats['total_patterns']}")
    print(f"  • Enabled patterns: {stats['enabled_patterns']}")
    
    print(f"\n📁 By Category:")
    for category, count in stats['by_category'].items():
        print(f"  • {category}: {count}")
    
    print(f"\n🎯 By Priority:")
    for priority, count in stats['by_priority'].items():
        print(f"  • {priority}: {count}")
    
    # Test search functionality
    print(f"\n🔍 Testing Search:")
    
    test_queries = ["naming", "error", "validation"]
    for query in test_queries:
        results = db.search_patterns(query, limit=3)
        print(f"  • '{query}': Found {len(results)} patterns")
        for pattern in results:
            print(f"    - {pattern.name} ({pattern.priority.value})")
    
    # Show MANDATORY patterns
    print(f"\n🔴 MANDATORY Patterns:")
    all_patterns = db.get_all_patterns()
    mandatory = [p for p in all_patterns if p.priority == PatternPriority.MANDATORY]
    
    for pattern in mandatory:
        print(f"  • {pattern.name}")
        print(f"    {pattern.description}")
    
    print(f"\n✨ Import complete!")
    print(f"\nDatabase ready at: {settings.database_path}")
    print("\nUse these commands:")
    print("  codex scan .           # Scan with new patterns")
    print("  codex scan --fix       # Auto-fix violations")
    print("  codex query 'naming'   # Search patterns")


if __name__ == "__main__":
    main()
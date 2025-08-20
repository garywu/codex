#!/usr/bin/env python3
"""
Test the new FTS implementation directly.
"""

import sys
import os
sys.path.insert(0, '/Users/admin/Work/codex')

from codex.fts_database import FTSDatabase, FTSPattern
from codex.pattern_extractor import PatternExtractor
from codex.ai_query import AIQueryInterface

def test_import_and_query():
    """Test importing patterns and running queries."""
    print("🧪 Testing Codex FTS Implementation\n")
    
    # Test pattern extraction
    print("1. Testing pattern extraction...")
    extractor = PatternExtractor()
    patterns = extractor.extract_from_project_init("/Users/admin/work/project-init.json")
    print(f"   ✅ Extracted {len(patterns)} patterns from project-init.json")
    
    # Test FTS database
    print("\n2. Testing FTS database...")
    db = FTSDatabase("test_patterns.db")
    
    imported_count = 0
    for pattern in patterns:
        db.add_pattern(pattern)
        imported_count += 1
    
    print(f"   ✅ Imported {imported_count} patterns to FTS database")
    
    # Test queries
    print("\n3. Testing natural language queries...")
    
    test_queries = [
        "HTTP client",
        "error handling",
        "dependency injection", 
        "ruff TRY401",
        "use uv not pip"
    ]
    
    for query in test_queries:
        results = db.query_patterns(query, limit=2)
        print(f"   Query: '{query}' → {len(results)} results")
        if results:
            print(f"     • {results[0]['name']} [{results[0]['priority']}]")
    
    # Test AI query interface
    print("\n4. Testing AI query interface...")
    ai_query = AIQueryInterface("test_patterns.db")
    
    # Test semantic search
    result = ai_query.semantic_search("I want to make HTTP requests")
    print(f"   Semantic search: '{result['intent']}'")
    print(f"   Summary: {result['summary']}")
    
    # Test file context
    context = ai_query.get_context_for_file("src/api.py")
    print(f"   File context for 'src/api.py': {len(context.split('##'))} sections")
    
    # Test code validation
    test_code = """
import requests
response = requests.get("https://api.example.com")
"""
    validation = ai_query.validate_code_snippet(test_code)
    print(f"   Code validation: {len(validation['violations'])} violations found")
    
    print("\n✅ All tests completed successfully!")
    
    # Show some example output
    print("\n" + "="*60)
    print("EXAMPLE AI QUERY OUTPUT")
    print("="*60)
    
    result = ai_query.query_patterns("HTTP client", limit=2, format="ai")
    print(f"Query: {result['query']}")
    print(f"Summary: {result['summary']}")
    for pattern in result['patterns']:
        print(f"\n• {pattern['name']} [{pattern['priority']}]")
        print(f"  Rule: {pattern['rule']}")
        if pattern['fix']:
            print(f"  Fix: {pattern['fix']}")

if __name__ == "__main__":
    test_import_and_query()
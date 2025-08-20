"""
Full-Text Search database for Codex patterns.
Extends the main database with FTS5 capabilities for AI queries.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

from .settings import settings


class FTSPattern:
    """Pattern data structure for FTS operations."""
    
    def __init__(
        self,
        name: str,
        category: str,
        priority: str,
        description: str,
        detection_pattern: str = "",
        fix_template: str = "",
        rationale: str = "",
        example_good: str = "",
        example_bad: str = "",
        replaces: str = "",
        source_file: str = "",
        full_context: str = "",
        **kwargs
    ):
        self.name = name
        self.category = category
        self.priority = priority
        self.description = description
        self.detection_pattern = detection_pattern
        self.fix_template = fix_template
        self.rationale = rationale
        self.example_good = example_good
        self.example_bad = example_bad
        self.replaces = replaces
        self.source_file = source_file
        self.full_context = full_context
        
    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'category': self.category,
            'priority': self.priority,
            'description': self.description,
            'detection_pattern': self.detection_pattern,
            'fix_template': self.fix_template,
            'rationale': self.rationale,
            'example_good': self.example_good,
            'example_bad': self.example_bad,
            'replaces': self.replaces,
            'source_file': self.source_file,
            'full_context': self.full_context
        }


class FTSDatabase:
    """SQLite database with Full-Text Search for pattern queries."""
    
    def __init__(self, db_path: str = settings.database_path):
        """Initialize FTS database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema with FTS5."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS patterns")
        cursor.execute("DROP TABLE IF EXISTS patterns_fts")
        cursor.execute("DROP TABLE IF EXISTS pattern_usage")
        
        # Create main patterns table
        cursor.execute("""
            CREATE TABLE patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                priority TEXT,
                description TEXT,
                detection_pattern TEXT,
                fix_template TEXT,
                rationale TEXT,
                example_good TEXT,
                example_bad TEXT,
                replaces TEXT,
                source_file TEXT,
                full_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create FTS5 virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE patterns_fts USING fts5(
                name,
                category,
                description,
                rationale,
                detection_pattern,
                fix_template,
                example_good,
                example_bad,
                full_context,
                content=patterns,
                content_rowid=id
            )
        """)
        
        # Create usage tracking table
        cursor.execute("""
            CREATE TABLE pattern_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                ai_assistant TEXT,
                project_path TEXT,
                FOREIGN KEY (pattern_id) REFERENCES patterns (id)
            )
        """)
        
        # Create triggers to keep FTS index in sync
        cursor.execute("""
            CREATE TRIGGER patterns_ai AFTER INSERT ON patterns BEGIN
                INSERT INTO patterns_fts(rowid, name, category, description, rationale, 
                                        detection_pattern, fix_template, example_good, 
                                        example_bad, full_context)
                VALUES (new.id, new.name, new.category, new.description, new.rationale,
                       new.detection_pattern, new.fix_template, new.example_good,
                       new.example_bad, new.full_context);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER patterns_au AFTER UPDATE ON patterns BEGIN
                INSERT INTO patterns_fts(patterns_fts, rowid, name, category, description, 
                                        rationale, detection_pattern, fix_template, 
                                        example_good, example_bad, full_context)
                VALUES('delete', old.id, old.name, old.category, old.description, 
                       old.rationale, old.detection_pattern, old.fix_template, 
                       old.example_good, old.example_bad, old.full_context);
                INSERT INTO patterns_fts(rowid, name, category, description, rationale, 
                                        detection_pattern, fix_template, example_good, 
                                        example_bad, full_context)
                VALUES (new.id, new.name, new.category, new.description, new.rationale,
                       new.detection_pattern, new.fix_template, new.example_good,
                       new.example_bad, new.full_context);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER patterns_ad AFTER DELETE ON patterns BEGIN
                INSERT INTO patterns_fts(patterns_fts, rowid, name, category, description,
                                        rationale, detection_pattern, fix_template,
                                        example_good, example_bad, full_context)
                VALUES('delete', old.id, old.name, old.category, old.description,
                       old.rationale, old.detection_pattern, old.fix_template,
                       old.example_good, old.example_bad, old.full_context);
            END
        """)
        
        conn.commit()
        conn.close()
    
    def add_pattern(self, pattern: FTSPattern) -> int:
        """Add a pattern to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO patterns (
                name, category, priority, description, detection_pattern,
                fix_template, rationale, example_good, example_bad,
                replaces, source_file, full_context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.name,
            pattern.category,
            pattern.priority,
            pattern.description,
            pattern.detection_pattern,
            pattern.fix_template,
            pattern.rationale,
            pattern.example_good,
            pattern.example_bad,
            pattern.replaces,
            pattern.source_file,
            pattern.full_context
        ))
        
        pattern_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pattern_id
    
    def query_patterns(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Query patterns using FTS5."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Clean query for FTS5
        fts_query = query.replace(".", " ").strip()
        if not fts_query:
            return []
        
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                p.category,
                p.priority,
                p.description,
                p.detection_pattern,
                p.fix_template,
                p.rationale,
                p.example_good,
                p.example_bad,
                p.replaces,
                snippet(patterns_fts, -1, '→', '←', '...', 20) as match_context,
                bm25(patterns_fts) as score
            FROM patterns p
            JOIN patterns_fts ON p.id = patterns_fts.rowid
            WHERE patterns_fts MATCH ?
            ORDER BY bm25(patterns_fts)
            LIMIT ?
        """, (fts_query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        return results
    
    def get_patterns_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get patterns by category."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM patterns 
            WHERE category = ?
            ORDER BY 
                CASE priority
                    WHEN 'MANDATORY' THEN 1
                    WHEN 'CRITICAL' THEN 2
                    WHEN 'HIGH' THEN 3
                    WHEN 'MEDIUM' THEN 4
                    WHEN 'LOW' THEN 5
                    ELSE 6
                END
        """, (category,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_pattern_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a specific pattern by name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM patterns WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def list_all_patterns(self) -> list[dict[str, Any]]:
        """List all patterns."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, category, priority, description
            FROM patterns
            ORDER BY category, priority, name
        """)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def track_usage(self, pattern_id: int, success: bool = True, 
                   ai_assistant: str = "unknown", project_path: str = ""):
        """Track pattern usage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pattern_usage (pattern_id, success, ai_assistant, project_path)
            VALUES (?, ?, ?, ?)
        """, (pattern_id, success, ai_assistant, project_path))
        
        conn.commit()
        conn.close()
    
    def get_usage_stats(self) -> dict[str, Any]:
        """Get usage statistics."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total patterns
        cursor.execute("SELECT COUNT(*) as total FROM patterns")
        total_patterns = cursor.fetchone()['total']
        
        # Most used patterns
        cursor.execute("""
            SELECT p.name, p.category, COUNT(u.id) as usage_count
            FROM patterns p
            LEFT JOIN pattern_usage u ON p.id = u.pattern_id
            GROUP BY p.id, p.name, p.category
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        most_used = [dict(row) for row in cursor.fetchall()]
        
        # Usage by AI assistant
        cursor.execute("""
            SELECT ai_assistant, COUNT(*) as count
            FROM pattern_usage
            GROUP BY ai_assistant
            ORDER BY count DESC
        """)
        by_assistant = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_patterns': total_patterns,
            'most_used': most_used,
            'by_assistant': by_assistant
        }
    
    def export_patterns(self, format: str = "markdown") -> str:
        """Export patterns in specified format."""
        patterns = self.list_all_patterns()
        
        if format == "markdown":
            output = "# Codex Patterns Database\n\n"
            
            current_category = None
            for pattern in patterns:
                if pattern['category'] != current_category:
                    current_category = pattern['category']
                    output += f"\n## {current_category.replace('_', ' ').title()}\n\n"
                
                output += f"### {pattern['name']} [{pattern['priority']}]\n"
                output += f"{pattern['description']}\n\n"
            
            return output
        
        elif format == "json":
            return json.dumps(patterns, indent=2)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
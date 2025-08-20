"""
Unified SQLite database manager for Codex.

Single database instance with all tables including FTS5 for AI queries.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from .pattern_models import Pattern, PatternImport, ScanResult
from .settings import settings


class UnifiedDatabase:
    """Single SQLite database for all Codex operations."""

    def __init__(self, db_path: Path | None = None):
        """Initialize database connection."""
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self.get_connection() as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Create main patterns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    description TEXT NOT NULL,
                    rule TEXT NOT NULL,
                    rationale TEXT,
                    detection JSON,
                    fix JSON,
                    examples JSON,
                    source TEXT DEFAULT 'project-init',
                    tags JSON,
                    enabled BOOLEAN DEFAULT 1,
                    ai_explanation TEXT,
                    business_impact TEXT,
                    learning_value TEXT,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 1.0,
                    last_used TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ensemble_rules JSON,
                    ensemble_min_votes INTEGER DEFAULT 1,
                    ensemble_confidence_threshold REAL DEFAULT 0.6
                )
            """)

            # Create ensemble rules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ensemble_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_name TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    rule_config JSON NOT NULL,
                    priority INTEGER DEFAULT 100,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_name) REFERENCES patterns (name)
                )
            """)

            # Create scan results table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT UNIQUE NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    repository_path TEXT NOT NULL,
                    files_scanned INTEGER DEFAULT 0,
                    patterns_checked INTEGER DEFAULT 0,
                    violations JSON,
                    duration_ms INTEGER,
                    confidence_avg REAL,
                    ai_context TEXT,
                    repository_insights JSON
                )
            """)

            # Create violations table for detailed tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT REFERENCES scan_results(scan_id),
                    pattern_id INTEGER REFERENCES patterns(id),
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    column_number INTEGER,
                    matched_code TEXT,
                    confidence REAL,
                    can_fix BOOLEAN DEFAULT 0,
                    fix_suggestion TEXT,
                    ai_analysis TEXT,
                    business_impact TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create AI query history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    intent TEXT,
                    results JSON,
                    response_time_ms INTEGER,
                    ai_assistant TEXT,
                    satisfaction_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create FTS5 tables if enabled
            if settings.enable_fts:
                self._init_fts_tables(conn)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_name ON patterns(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_category ON patterns(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_priority ON patterns(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_scan ON violations(scan_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_pattern ON violations(pattern_id)")

            conn.commit()

    def _init_fts_tables(self, conn: sqlite3.Connection) -> None:
        """Initialize FTS5 tables for full-text search."""
        try:
            # Check if FTS5 is available
            conn.execute("SELECT fts5(?)", (0,))

            # Create FTS table for patterns
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS patterns_fts USING fts5(
                    pattern_id,
                    name,
                    category,
                    priority,
                    description,
                    rule,
                    rationale,
                    tags,
                    ai_explanation,
                    searchable_content,
                    content='patterns',
                    content_rowid='id'
                )
            """)

            # Create FTS table for violations
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS violations_fts USING fts5(
                    violation_id,
                    pattern_name,
                    file_path,
                    matched_code,
                    ai_analysis,
                    content='violations',
                    content_rowid='id'
                )
            """)

            logging.info("✅ FTS5 tables initialized")

        except sqlite3.OperationalError:
            logging.info("⚠️  FTS5 not available - full-text search disabled")

    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ========== Pattern Operations ==========

    def add_pattern(self, pattern: Pattern) -> int:
        """Add or update a pattern in the database."""
        with self.get_connection() as conn:
            # Check if pattern exists
            existing = conn.execute("SELECT id FROM patterns WHERE name = ?", (pattern.name,)).fetchone()

            if existing:
                # Update existing pattern
                pattern_id = existing["id"]
                conn.execute(
                    """
                    UPDATE patterns SET
                        category = ?, priority = ?, description = ?,
                        rule = ?, rationale = ?, detection = ?, fix = ?,
                        examples = ?, tags = ?, ai_explanation = ?,
                        business_impact = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        pattern.category.value,
                        pattern.priority.value,
                        pattern.description,
                        pattern.rule,
                        pattern.rationale,
                        json.dumps(pattern.detection.model_dump()),
                        json.dumps(pattern.fix.model_dump()),
                        json.dumps(pattern.examples.model_dump()),
                        json.dumps(pattern.tags),
                        pattern.ai_explanation,
                        pattern.business_impact,
                        pattern_id,
                    ),
                )
            else:
                # Insert new pattern
                cursor = conn.execute(
                    """
                    INSERT INTO patterns (
                        name, category, priority, description, rule,
                        rationale, detection, fix, examples, source,
                        tags, ai_explanation, business_impact
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        pattern.name,
                        pattern.category.value,
                        pattern.priority.value,
                        pattern.description,
                        pattern.rule,
                        pattern.rationale,
                        json.dumps(pattern.detection.model_dump()),
                        json.dumps(pattern.fix.model_dump()),
                        json.dumps(pattern.examples.model_dump()),
                        pattern.source,
                        json.dumps(pattern.tags),
                        pattern.ai_explanation,
                        pattern.business_impact,
                    ),
                )
                pattern_id = cursor.lastrowid

            # Update FTS if available
            if settings.enable_fts:
                self._update_pattern_fts(conn, pattern_id, pattern)

            conn.commit()
            return pattern_id

    def _update_pattern_fts(self, conn: sqlite3.Connection, pattern_id: int, pattern: Pattern) -> None:
        """Update FTS index for a pattern."""
        try:
            # Delete existing FTS entry
            conn.execute("DELETE FROM patterns_fts WHERE pattern_id = ?", (str(pattern_id),))

            # Insert new FTS entry
            conn.execute(
                """
                INSERT INTO patterns_fts (
                    pattern_id, name, category, priority,
                    description, rule, rationale, tags,
                    ai_explanation, searchable_content
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(pattern_id),
                    pattern.name,
                    pattern.category.value,
                    pattern.priority.value,
                    pattern.description,
                    pattern.rule,
                    pattern.rationale,
                    " ".join(pattern.tags),
                    pattern.ai_explanation or "",
                    pattern.to_fts_document(),
                ),
            )
        except sqlite3.OperationalError:
            pass  # FTS not available

    def get_pattern(self, pattern_name: str) -> Pattern | None:
        """Get a pattern by name."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM patterns WHERE name = ?", (pattern_name,)).fetchone()

            if row:
                return self._row_to_pattern(dict(row))
            return None

    def get_patterns_by_category(self, category: str) -> list[Pattern]:
        """Get patterns by category."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM patterns WHERE category = ? AND enabled = 1", (category,)).fetchall()

            return [self._row_to_pattern(dict(row)) for row in rows]

    def get_all_patterns(self, enabled_only: bool = True) -> list[Pattern]:
        """Get all patterns from the database."""
        with self.get_connection() as conn:
            query = "SELECT * FROM patterns"
            if enabled_only:
                query += " WHERE enabled = 1"
            query += " ORDER BY priority, category, name"

            rows = conn.execute(query).fetchall()
            return [self._row_to_pattern(dict(row)) for row in rows]

    def search_patterns(self, query: str, limit: int = 20) -> list[Pattern]:
        """Search patterns using FTS or fallback to LIKE."""
        with self.get_connection() as conn:
            patterns = []

            # Try FTS first
            if settings.enable_fts:
                try:
                    rows = conn.execute(
                        """
                        SELECT p.*
                        FROM patterns p
                        JOIN patterns_fts f ON p.id = CAST(f.pattern_id AS INTEGER)
                        WHERE patterns_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """,
                        (query, limit),
                    ).fetchall()

                    patterns = [self._row_to_pattern(dict(row)) for row in rows]
                except sqlite3.OperationalError:
                    pass  # FTS not available, use fallback

            # Fallback to LIKE search
            if not patterns:
                search_term = f"%{query}%"
                rows = conn.execute(
                    """
                    SELECT * FROM patterns
                    WHERE name LIKE ? OR description LIKE ?
                    OR rule LIKE ? OR rationale LIKE ?
                    ORDER BY priority, name
                    LIMIT ?
                """,
                    (search_term, search_term, search_term, search_term, limit),
                ).fetchall()

                patterns = [self._row_to_pattern(dict(row)) for row in rows]

            return patterns

    def _row_to_pattern(self, row: dict[str, Any]) -> Pattern:
        """Convert database row to Pattern model."""
        from .pattern_models import PatternDetection, PatternExample, PatternFix

        # Parse JSON fields
        detection = json.loads(row.get("detection", "{}"))
        fix = json.loads(row.get("fix", "{}"))
        examples = json.loads(row.get("examples", "{}"))
        tags = json.loads(row.get("tags", "[]"))

        return Pattern(
            id=row.get("id"),
            name=row["name"],
            category=row["category"],
            priority=row["priority"],
            description=row["description"],
            rule=row["rule"],
            rationale=row.get("rationale", ""),
            detection=PatternDetection(**detection),
            fix=PatternFix(**fix),
            examples=PatternExample(**examples),
            source=row.get("source", ""),
            tags=tags,
            enabled=bool(row.get("enabled", True)),
            ai_explanation=row.get("ai_explanation"),
            business_impact=row.get("business_impact"),
            learning_value=row.get("learning_value"),
            usage_count=row.get("usage_count", 0),
            success_rate=row.get("success_rate", 1.0),
            last_used=row.get("last_used"),
            created_at=row.get("created_at") or datetime.utcnow(),
            updated_at=row.get("updated_at") or datetime.utcnow(),
        )

    # ========== Scan Operations ==========

    def save_scan_result(self, scan_result: ScanResult) -> None:
        """Save scan result to database."""
        with self.get_connection() as conn:
            # Save main scan result
            conn.execute(
                """
                INSERT INTO scan_results (
                    scan_id, repository_path, files_scanned,
                    patterns_checked, violations, duration_ms,
                    confidence_avg, ai_context, repository_insights
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan_result.scan_id,
                    scan_result.repository_path,
                    scan_result.files_scanned,
                    scan_result.patterns_checked,
                    json.dumps([v.model_dump() for v in scan_result.violations]),
                    scan_result.duration_ms,
                    scan_result.confidence_avg,
                    scan_result.ai_context,
                    json.dumps(scan_result.repository_insights) if scan_result.repository_insights else None,
                ),
            )

            # Save individual violations
            for violation in scan_result.violations:
                conn.execute(
                    """
                    INSERT INTO violations (
                        scan_id, pattern_id, file_path, line_number,
                        column_number, matched_code, confidence,
                        can_fix, fix_suggestion, ai_analysis, business_impact
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        scan_result.scan_id,
                        violation.pattern.id,
                        violation.file_path,
                        violation.line_number,
                        violation.column,
                        violation.matched_code,
                        violation.confidence,
                        violation.can_fix,
                        violation.fix_suggestion,
                        violation.ai_analysis,
                        violation.business_impact,
                    ),
                )

            conn.commit()

    # ========== Import Operations ==========

    def import_patterns(self, import_file: Path) -> dict[str, int]:
        """Import patterns from JSON file."""
        with open(import_file) as f:
            data = json.load(f)

        pattern_import = PatternImport(**data)
        patterns = pattern_import.convert_to_patterns()

        imported = 0
        updated = 0

        for pattern in patterns:
            existing = self.get_pattern(pattern.name)
            if existing:
                updated += 1
            else:
                imported += 1

            self.add_pattern(pattern)

        return {"imported": imported, "updated": updated, "total": imported + updated}

    # ========== Statistics Operations ==========

    def get_statistics(self) -> dict[str, Any]:
        """Get database statistics."""
        with self.get_connection() as conn:
            stats = {}

            # Pattern statistics
            stats["total_patterns"] = conn.execute("SELECT COUNT(*) as count FROM patterns").fetchone()["count"]

            stats["enabled_patterns"] = conn.execute(
                "SELECT COUNT(*) as count FROM patterns WHERE enabled = 1"
            ).fetchone()["count"]

            # Category breakdown
            categories = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM patterns
                GROUP BY category
                ORDER BY count DESC
            """).fetchall()
            stats["by_category"] = {row["category"]: row["count"] for row in categories}

            # Priority breakdown
            priorities = conn.execute("""
                SELECT priority, COUNT(*) as count
                FROM patterns
                GROUP BY priority
                ORDER BY
                    CASE priority
                        WHEN 'MANDATORY' THEN 1
                        WHEN 'CRITICAL' THEN 2
                        WHEN 'HIGH' THEN 3
                        WHEN 'MEDIUM' THEN 4
                        WHEN 'LOW' THEN 5
                        WHEN 'OPTIONAL' THEN 6
                    END
            """).fetchall()
            stats["by_priority"] = {row["priority"]: row["count"] for row in priorities}

            # Scan statistics
            stats["total_scans"] = conn.execute("SELECT COUNT(*) as count FROM scan_results").fetchone()["count"]

            stats["total_violations"] = conn.execute("SELECT COUNT(*) as count FROM violations").fetchone()["count"]

            return stats

    # ========== Async Wrappers for Pattern CLI ==========

    async def get_patterns(self, **filters) -> list[dict[str, Any]]:
        """Get patterns with optional filters (async wrapper)."""
        with self.get_connection() as conn:
            query = "SELECT * FROM patterns WHERE 1=1"
            params = []

            if "name" in filters:
                query += " AND name = ?"
                params.append(filters["name"])
            if "category" in filters:
                query += " AND category = ?"
                params.append(filters["category"])
            if "priority" in filters:
                query += " AND priority = ?"
                params.append(filters["priority"])

            query += " ORDER BY priority, category, name"

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    async def add_pattern_async(self, pattern_data: dict[str, Any]) -> dict[str, Any]:
        """Add pattern from dict (async wrapper)."""
        # Convert pattern_data to the format expected by the sync method
        pattern = Pattern(**pattern_data)
        pattern_id = self.add_pattern(pattern)
        return {"id": pattern_id, "name": pattern.name}

    async def update_pattern(self, pattern_id: int, updates: dict[str, Any]) -> bool:
        """Update pattern by ID (async wrapper)."""
        with self.get_connection() as conn:
            # Build update query dynamically
            set_parts = []
            values = []

            for key, value in updates.items():
                if key in ["name", "category", "priority", "description", "rule", "rationale"]:
                    set_parts.append(f"{key} = ?")
                    values.append(value)
                elif key in ["detection", "fix", "examples", "tags"]:
                    set_parts.append(f"{key} = ?")
                    values.append(json.dumps(value) if value else None)

            if set_parts:
                query = f"UPDATE patterns SET {', '.join(set_parts)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                values.append(pattern_id)

                conn.execute(query, values)
                return conn.total_changes > 0

        return False

    async def delete_pattern(self, pattern_id: int) -> bool:
        """Delete pattern by ID (async wrapper)."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
            return conn.total_changes > 0

    async def search_patterns_async(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search patterns and return as dicts (async wrapper)."""
        # Use direct SQL query to avoid Pydantic model complexity
        with self.get_connection() as conn:
            patterns = []

            # Try FTS first
            if settings.enable_fts:
                try:
                    rows = conn.execute(
                        """
                        SELECT p.*
                        FROM patterns p
                        JOIN patterns_fts f ON p.id = CAST(f.pattern_id AS INTEGER)
                        WHERE patterns_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """,
                        (query, limit),
                    ).fetchall()

                    patterns = [dict(row) for row in rows]
                except sqlite3.OperationalError:
                    pass  # FTS not available, use fallback

            # Fallback to LIKE search
            if not patterns:
                search_term = f"%{query}%"
                rows = conn.execute(
                    """
                    SELECT * FROM patterns
                    WHERE name LIKE ? OR description LIKE ?
                    OR rule LIKE ? OR rationale LIKE ?
                    ORDER BY priority, name
                    LIMIT ?
                """,
                    (search_term, search_term, search_term, search_term, limit),
                ).fetchall()

                patterns = [dict(row) for row in rows]

        return patterns

    # ========== Ensemble Rules Operations ==========

    def add_ensemble_rules(self, pattern_name: str, rules: list[dict]) -> None:
        """Add ensemble rules for a pattern."""
        with self.get_connection() as conn:
            # Clear existing rules for this pattern
            conn.execute("DELETE FROM ensemble_rules WHERE pattern_name = ?", (pattern_name,))

            # Add new rules
            for rule in rules:
                conn.execute(
                    """
                    INSERT INTO ensemble_rules (pattern_name, rule_type, rule_config, priority, enabled)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        pattern_name,
                        rule.get("type", "unknown"),
                        json.dumps(rule),
                        rule.get("priority", 100),
                        rule.get("enabled", True),
                    ),
                )

            conn.commit()

    def get_ensemble_rules(self, pattern_name: str) -> list[dict]:
        """Get ensemble rules for a pattern."""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT rule_type, rule_config, priority, enabled
                FROM ensemble_rules
                WHERE pattern_name = ? AND enabled = 1
                ORDER BY priority, id
            """,
                (pattern_name,),
            ).fetchall()

            return [
                {"type": row[0], "config": json.loads(row[1]), "priority": row[2], "enabled": bool(row[3])}
                for row in rows
            ]

    def update_pattern_ensemble_config(
        self, pattern_name: str, min_votes: int = 1, confidence_threshold: float = 0.6
    ) -> None:
        """Update ensemble configuration for a pattern."""
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE patterns
                SET ensemble_min_votes = ?, ensemble_confidence_threshold = ?
                WHERE name = ?
            """,
                (min_votes, confidence_threshold, pattern_name),
            )
            conn.commit()

    def close(self) -> None:
        """Close database connection (no-op for context manager pattern)."""
        # We use context managers for connections, so nothing to close
        pass


# Global database instance
db = UnifiedDatabase()

#!/usr/bin/env python3
"""
Fix Audit Trail System

Maintains a complete audit trail of all fixes applied, rejected, or rolled back.
This provides accountability and allows for learning from past decisions.
"""

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class FixStatus(str, Enum):
    """Status of a fix attempt."""
    PROPOSED = "proposed"
    VALIDATED = "validated"
    APPLIED = "applied"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class FixDecision(str, Enum):
    """Decision made about a fix."""
    AUTO_APPROVED = "auto_approved"
    USER_APPROVED = "user_approved"
    USER_REJECTED = "user_rejected"
    SYSTEM_REJECTED = "system_rejected"
    VALIDATION_FAILED = "validation_failed"


@dataclass
class FixAuditEntry:
    """Complete audit entry for a fix attempt."""
    
    # Identity
    audit_id: str
    timestamp: datetime
    session_id: str
    
    # File information
    file_path: str
    file_hash_before: str
    file_hash_after: Optional[str]
    
    # Violation information
    pattern_name: str
    line_number: int
    violation_text: str
    
    # Fix information
    fix_strategy: str
    fix_code: Optional[str]
    
    # Validation results
    syntax_valid: bool
    imports_valid: bool
    tests_passed: Optional[bool]
    validation_errors: List[str]
    
    # Decision and status
    decision: FixDecision
    status: FixStatus
    decision_reason: str
    
    # User information
    user_id: Optional[str]
    ai_assistant: Optional[str]
    
    # Performance metrics
    execution_time_ms: float
    lines_changed: int
    
    # Context
    context_data: Dict[str, Any]
    
    # Rollback information
    can_rollback: bool
    rollback_data: Optional[Dict[str, Any]]
    rolled_back_at: Optional[datetime]
    rollback_reason: Optional[str]


class FixAuditTrail:
    """Manages the audit trail for all fix operations."""
    
    def __init__(self, audit_db_path: Path = None):
        """Initialize audit trail database."""
        self.db_path = audit_db_path or Path.home() / ".codex" / "fix_audit.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.current_session_id = self._generate_session_id()
    
    def _init_database(self):
        """Initialize the audit database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fix_audits (
                audit_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                
                file_path TEXT NOT NULL,
                file_hash_before TEXT NOT NULL,
                file_hash_after TEXT,
                
                pattern_name TEXT NOT NULL,
                line_number INTEGER,
                violation_text TEXT,
                
                fix_strategy TEXT,
                fix_code TEXT,
                
                syntax_valid BOOLEAN,
                imports_valid BOOLEAN,
                tests_passed BOOLEAN,
                validation_errors TEXT,
                
                decision TEXT NOT NULL,
                status TEXT NOT NULL,
                decision_reason TEXT,
                
                user_id TEXT,
                ai_assistant TEXT,
                
                execution_time_ms REAL,
                lines_changed INTEGER,
                
                context_data TEXT,
                
                can_rollback BOOLEAN,
                rollback_data TEXT,
                rolled_back_at TEXT,
                rollback_reason TEXT
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON fix_audits(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path 
            ON fix_audits(file_path)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_name 
            ON fix_audits(pattern_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status 
            ON fix_audits(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON fix_audits(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def _generate_audit_id(self) -> str:
        """Generate unique audit ID."""
        timestamp = datetime.now().isoformat()
        random_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"FIX-{datetime.now().strftime('%Y%m%d')}-{random_part}"
    
    def record_fix_attempt(
        self,
        file_path: Path,
        pattern_name: str,
        line_number: int,
        violation_text: str,
        fix_strategy: str,
        fix_code: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record the start of a fix attempt.
        
        Returns:
            Audit ID for this fix attempt
        """
        audit_id = self._generate_audit_id()
        
        # Calculate file hash
        file_content = file_path.read_text() if file_path.exists() else ""
        file_hash = hashlib.md5(file_content.encode()).hexdigest()
        
        entry = FixAuditEntry(
            audit_id=audit_id,
            timestamp=datetime.now(),
            session_id=self.current_session_id,
            file_path=str(file_path),
            file_hash_before=file_hash,
            file_hash_after=None,
            pattern_name=pattern_name,
            line_number=line_number,
            violation_text=violation_text,
            fix_strategy=fix_strategy,
            fix_code=fix_code,
            syntax_valid=False,
            imports_valid=False,
            tests_passed=None,
            validation_errors=[],
            decision=FixDecision.AUTO_APPROVED,  # Default
            status=FixStatus.PROPOSED,
            decision_reason="",
            user_id=None,
            ai_assistant="codex",
            execution_time_ms=0,
            lines_changed=0,
            context_data=context_data or {},
            can_rollback=True,
            rollback_data=None,
            rolled_back_at=None,
            rollback_reason=None
        )
        
        self._save_entry(entry)
        return audit_id
    
    def update_validation_results(
        self,
        audit_id: str,
        syntax_valid: bool,
        imports_valid: bool,
        tests_passed: Optional[bool] = None,
        validation_errors: Optional[List[str]] = None
    ):
        """Update validation results for a fix attempt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE fix_audits
            SET syntax_valid = ?,
                imports_valid = ?,
                tests_passed = ?,
                validation_errors = ?,
                status = ?
            WHERE audit_id = ?
        """, (
            syntax_valid,
            imports_valid,
            tests_passed,
            json.dumps(validation_errors or []),
            FixStatus.VALIDATED if syntax_valid and imports_valid else FixStatus.FAILED,
            audit_id
        ))
        
        conn.commit()
        conn.close()
    
    def record_decision(
        self,
        audit_id: str,
        decision: FixDecision,
        reason: str,
        user_id: Optional[str] = None
    ):
        """Record the decision made about a fix."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE fix_audits
            SET decision = ?,
                decision_reason = ?,
                user_id = ?
            WHERE audit_id = ?
        """, (decision, reason, user_id, audit_id))
        
        conn.commit()
        conn.close()
    
    def record_application(
        self,
        audit_id: str,
        file_hash_after: str,
        execution_time_ms: float,
        lines_changed: int
    ):
        """Record successful application of a fix."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE fix_audits
            SET status = ?,
                file_hash_after = ?,
                execution_time_ms = ?,
                lines_changed = ?
            WHERE audit_id = ?
        """, (
            FixStatus.APPLIED,
            file_hash_after,
            execution_time_ms,
            lines_changed,
            audit_id
        ))
        
        conn.commit()
        conn.close()
    
    def record_rollback(
        self,
        audit_id: str,
        reason: str
    ):
        """Record rollback of a fix."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE fix_audits
            SET status = ?,
                rolled_back_at = ?,
                rollback_reason = ?
            WHERE audit_id = ?
        """, (
            FixStatus.ROLLED_BACK,
            datetime.now().isoformat(),
            reason,
            audit_id
        ))
        
        conn.commit()
        conn.close()
    
    def _save_entry(self, entry: FixAuditEntry):
        """Save an audit entry to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO fix_audits VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        """, (
            entry.audit_id,
            entry.timestamp.isoformat(),
            entry.session_id,
            entry.file_path,
            entry.file_hash_before,
            entry.file_hash_after,
            entry.pattern_name,
            entry.line_number,
            entry.violation_text,
            entry.fix_strategy,
            entry.fix_code,
            entry.syntax_valid,
            entry.imports_valid,
            entry.tests_passed,
            json.dumps(entry.validation_errors),
            entry.decision,
            entry.status,
            entry.decision_reason,
            entry.user_id,
            entry.ai_assistant,
            entry.execution_time_ms,
            entry.lines_changed,
            json.dumps(entry.context_data),
            entry.can_rollback,
            json.dumps(entry.rollback_data) if entry.rollback_data else None,
            entry.rolled_back_at.isoformat() if entry.rolled_back_at else None,
            entry.rollback_reason
        ))
        
        conn.commit()
        conn.close()
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of a fix session."""
        session_id = session_id or self.current_session_id
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get counts by status
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM fix_audits 
            WHERE session_id = ?
            GROUP BY status
        """, (session_id,))
        
        status_counts = dict(cursor.fetchall())
        
        # Get counts by pattern
        cursor.execute("""
            SELECT pattern_name, COUNT(*) 
            FROM fix_audits 
            WHERE session_id = ?
            GROUP BY pattern_name
        """, (session_id,))
        
        pattern_counts = dict(cursor.fetchall())
        
        # Get total execution time
        cursor.execute("""
            SELECT SUM(execution_time_ms) 
            FROM fix_audits 
            WHERE session_id = ?
        """, (session_id,))
        
        total_time = cursor.fetchone()[0] or 0
        
        # Get files modified
        cursor.execute("""
            SELECT COUNT(DISTINCT file_path) 
            FROM fix_audits 
            WHERE session_id = ? AND status = ?
        """, (session_id, FixStatus.APPLIED))
        
        files_modified = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'session_id': session_id,
            'status_counts': status_counts,
            'pattern_counts': pattern_counts,
            'total_execution_time_ms': total_time,
            'files_modified': files_modified,
            'success_rate': (
                status_counts.get(FixStatus.APPLIED, 0) / 
                sum(status_counts.values()) * 100
                if status_counts else 0
            )
        }
    
    def get_pattern_success_rate(self, pattern_name: str) -> float:
        """Get historical success rate for a pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = ? THEN 1 END) as applied,
                COUNT(*) as total
            FROM fix_audits
            WHERE pattern_name = ?
        """, (FixStatus.APPLIED, pattern_name))
        
        applied, total = cursor.fetchone()
        conn.close()
        
        return (applied / total * 100) if total > 0 else 0
    
    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get fix history for a specific file."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM fix_audits
            WHERE file_path = ?
            ORDER BY timestamp DESC
        """, (file_path,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def export_audit_report(
        self, 
        output_path: Path,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """Export audit report to JSON file."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM fix_audits WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        report = {
            'export_date': datetime.now().isoformat(),
            'total_fixes': len(rows),
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'fixes': [dict(row) for row in rows]
        }
        
        # Add summary statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT session_id) as sessions,
                COUNT(DISTINCT file_path) as files,
                COUNT(DISTINCT pattern_name) as patterns,
                AVG(execution_time_ms) as avg_time,
                SUM(lines_changed) as total_lines_changed
            FROM fix_audits
        """)
        
        stats = dict(cursor.fetchone())
        report['statistics'] = stats
        
        conn.close()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def learn_from_history(self) -> Dict[str, Any]:
        """Analyze historical data to learn patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Patterns most likely to fail
        cursor.execute("""
            SELECT pattern_name, 
                   COUNT(CASE WHEN status = ? THEN 1 END) as failures,
                   COUNT(*) as total
            FROM fix_audits
            GROUP BY pattern_name
            HAVING failures > 0
            ORDER BY (failures * 1.0 / total) DESC
            LIMIT 10
        """, (FixStatus.FAILED,))
        
        risky_patterns = [
            {'pattern': row[0], 'failure_rate': row[1] / row[2] * 100}
            for row in cursor.fetchall()
        ]
        
        # Most commonly rolled back
        cursor.execute("""
            SELECT pattern_name, COUNT(*) as rollback_count
            FROM fix_audits
            WHERE status = ?
            GROUP BY pattern_name
            ORDER BY rollback_count DESC
            LIMIT 10
        """, (FixStatus.ROLLED_BACK,))
        
        rollback_patterns = [
            {'pattern': row[0], 'rollback_count': row[1]}
            for row in cursor.fetchall()
        ]
        
        # Average execution time by pattern
        cursor.execute("""
            SELECT pattern_name, AVG(execution_time_ms) as avg_time
            FROM fix_audits
            WHERE execution_time_ms > 0
            GROUP BY pattern_name
            ORDER BY avg_time DESC
            LIMIT 10
        """)
        
        slow_patterns = [
            {'pattern': row[0], 'avg_time_ms': row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'risky_patterns': risky_patterns,
            'rollback_prone': rollback_patterns,
            'slow_patterns': slow_patterns,
            'recommendations': self._generate_recommendations(
                risky_patterns, rollback_patterns, slow_patterns
            )
        }
    
    def _generate_recommendations(
        self,
        risky_patterns: List[Dict],
        rollback_patterns: List[Dict],
        slow_patterns: List[Dict]
    ) -> List[str]:
        """Generate recommendations based on historical data."""
        recommendations = []
        
        if risky_patterns:
            top_risky = risky_patterns[0]
            if top_risky['failure_rate'] > 50:
                recommendations.append(
                    f"Pattern '{top_risky['pattern']}' fails {top_risky['failure_rate']:.1f}% "
                    f"of the time - consider manual review"
                )
        
        if rollback_patterns:
            top_rollback = rollback_patterns[0]
            if top_rollback['rollback_count'] > 5:
                recommendations.append(
                    f"Pattern '{top_rollback['pattern']}' has been rolled back "
                    f"{top_rollback['rollback_count']} times - needs improvement"
                )
        
        if slow_patterns:
            top_slow = slow_patterns[0]
            if top_slow['avg_time_ms'] > 1000:
                recommendations.append(
                    f"Pattern '{top_slow['pattern']}' takes {top_slow['avg_time_ms']:.0f}ms "
                    f"on average - consider optimization"
                )
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    audit_trail = FixAuditTrail()
    
    # Record a fix attempt
    audit_id = audit_trail.record_fix_attempt(
        file_path=Path("example.py"),
        pattern_name="mock-code-naming",
        line_number=42,
        violation_text="def fake_function():",
        fix_strategy="automatic",
        fix_code="def mock_function():",
        context_data={"function_name": "fake_function"}
    )
    
    print(f"Created audit entry: {audit_id}")
    
    # Update with validation results
    audit_trail.update_validation_results(
        audit_id=audit_id,
        syntax_valid=True,
        imports_valid=True,
        tests_passed=True,
        validation_errors=[]
    )
    
    # Record decision
    audit_trail.record_decision(
        audit_id=audit_id,
        decision=FixDecision.AUTO_APPROVED,
        reason="All validations passed"
    )
    
    # Record application
    import time
    start_time = time.time()
    # ... apply fix ...
    execution_time = (time.time() - start_time) * 1000
    
    audit_trail.record_application(
        audit_id=audit_id,
        file_hash_after="abc123def456",
        execution_time_ms=execution_time,
        lines_changed=1
    )
    
    # Get session summary
    summary = audit_trail.get_session_summary()
    print(f"\nSession Summary: {json.dumps(summary, indent=2)}")
    
    # Learn from history
    learnings = audit_trail.learn_from_history()
    print(f"\nLearnings: {json.dumps(learnings, indent=2)}")
    
    # Export report
    report_path = Path("fix_audit_report.json")
    audit_trail.export_audit_report(report_path)
    print(f"\nAudit report exported to {report_path}")
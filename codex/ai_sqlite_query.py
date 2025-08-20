"""
AI-Optimized SQLite Query Interface

Translates natural language queries into SQL and provides contextual explanations
optimized for Claude Code consumption.
"""

import re
import sqlite3
from typing import Any

from rich.console import Console


class NaturalLanguageQueryInterface:
    """Interface for querying scan results with natural language."""
    
    def __init__(self, db_path: str, quiet: bool = False):
        """Initialize query interface."""
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.console = Console(quiet=quiet)
        
        # Intent patterns for query translation
        self.intent_patterns = {
            # Violation queries
            r"(?:show|find|get).*violations?.*(?:in|for)\s+(.+)": self._query_violations_in_file,
            r"(?:show|find|get).*violations?.*(?:related to|about|containing)\s+(.+)": self._query_violations_by_content,
            r"(?:show|find|get).*(?:all|summary of).*violations?": self._query_all_violations,
            r"(?:show|find|get).*(?:critical|high|severe).*violations?": self._query_high_severity_violations,
            r"(?:count|how many).*violations?": self._count_violations,
            
            # File queries
            r"(?:what|which|show).*files?.*(?:most|highest).*violations?": self._query_files_most_violations,
            r"(?:show|list).*files?.*scanned": self._query_scanned_files,
            r"(?:show|get).*(?:file|files?).*(?:details|info|information).*for\s+(.+)": self._query_file_details,
            
            # Pattern queries
            r"(?:show|find|get).*patterns?.*(?:related to|about|containing)\s+(.+)": self._query_patterns_by_content,
            r"(?:explain|describe|what is).*pattern\s+(.+)": self._explain_pattern,
            r"(?:show|list).*(?:all|available).*patterns?": self._query_all_patterns,
            
            # Insight queries
            r"(?:show|get|what are).*(?:insights?|summary|overview)": self._query_repository_insights,
            r"(?:health|quality).*(?:score|summary|report)": self._query_repository_health,
            
            # Fix priority queries
            r"(?:what|which|show).*(?:should I|to).*fix.*first": self._query_fix_priority,
            r"(?:suggest|recommend).*fixes?": self._query_suggested_fixes,
            r"(?:easy|simple).*fixes?": self._query_simple_fixes,
            
            # Learning queries
            r"(?:what can I|help me).*learn.*(?:from|about)": self._query_learning_opportunities,
            r"(?:show|explain).*(?:best practices|recommendations)": self._query_best_practices,
        }
    
    def query(self, natural_query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process natural language query and return structured results."""
        
        # Normalize query
        query_lower = natural_query.lower().strip()
        
        # Try to match intent patterns
        for pattern, handler in self.intent_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                try:
                    result = handler(match, context or {})
                    return self._format_response(natural_query, result, pattern)
                except Exception as e:
                    return self._error_response(natural_query, str(e))
        
        # Fallback to FTS search
        return self._fallback_search(natural_query)
    
    def _query_violations_in_file(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query violations in specific file."""
        file_pattern = match.group(1).strip()
        
        sql = """
            SELECT 
                v.pattern_name,
                v.severity,
                v.line_number,
                v.code_snippet,
                v.ai_explanation,
                v.fix_complexity,
                f.file_path
            FROM violations v
            JOIN scanned_files f ON v.file_id = f.id
            WHERE f.file_path LIKE ?
            ORDER BY v.severity DESC, v.confidence DESC
        """
        
        cursor = self.db.execute(sql, (f"%{file_pattern}%",))
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Found {len(results)} violations in files matching '{file_pattern}'",
            "type": "violations_in_file"
        }
    
    def _query_violations_by_content(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query violations by content using FTS."""
        search_term = match.group(1).strip()
        
        sql = """
            SELECT 
                v.pattern_name,
                v.severity,
                v.confidence,
                v.ai_explanation,
                v.code_snippet,
                f.file_path,
                v.line_number
            FROM violations_fts vf
            JOIN violations v ON vf.violation_id = v.id
            JOIN scanned_files f ON v.file_id = f.id
            WHERE violations_fts MATCH ?
            ORDER BY v.severity DESC, v.confidence DESC
        """
        
        cursor = self.db.execute(sql, (search_term,))
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Found {len(results)} violations related to '{search_term}'",
            "type": "violations_by_content"
        }
    
    def _query_all_violations(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query all violations with summary."""
        sql = """
            SELECT 
                pattern_category,
                severity,
                COUNT(*) as count,
                ROUND(AVG(confidence), 2) as avg_confidence,
                GROUP_CONCAT(DISTINCT pattern_name) as patterns
            FROM violations v
            WHERE v.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            GROUP BY pattern_category, severity
            ORDER BY 
                CASE severity 
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    WHEN 'LOW' THEN 4 
                END,
                count DESC
        """
        
        cursor = self.db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        
        total_violations = sum(row["count"] for row in results)
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Found {total_violations} total violations across {len(results)} categories",
            "type": "all_violations_summary"
        }
    
    def _query_high_severity_violations(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query high severity violations."""
        sql = """
            SELECT 
                v.pattern_name,
                v.severity,
                v.confidence,
                v.ai_explanation,
                v.business_impact,
                f.file_path,
                v.line_number,
                v.fix_complexity
            FROM violations v
            JOIN scanned_files f ON v.file_id = f.id
            WHERE v.severity IN ('CRITICAL', 'HIGH')
            AND v.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            ORDER BY 
                CASE v.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 END,
                v.confidence DESC
        """
        
        cursor = self.db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Found {len(results)} high-severity violations requiring attention",
            "type": "high_severity_violations"
        }
    
    def _query_files_most_violations(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query files with most violations."""
        sql = """
            SELECT 
                f.file_path,
                COUNT(v.id) as violation_count,
                AVG(CASE v.severity 
                    WHEN 'CRITICAL' THEN 4
                    WHEN 'HIGH' THEN 3
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 1 
                END) as avg_severity_score,
                GROUP_CONCAT(DISTINCT v.pattern_category) as violation_categories,
                f.line_count,
                f.complexity_score
            FROM scanned_files f
            LEFT JOIN violations v ON f.id = v.file_id
            WHERE f.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            GROUP BY f.id, f.file_path
            HAVING violation_count > 0
            ORDER BY violation_count DESC, avg_severity_score DESC
            LIMIT 10
        """
        
        cursor = self.db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Top {len(results)} files by violation count",
            "type": "files_most_violations"
        }
    
    def _query_repository_insights(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query repository insights and summary."""
        sql = """
            SELECT 
                ri.insight_type,
                ri.title,
                ri.description,
                ri.impact_assessment,
                ri.recommendations,
                ri.confidence
            FROM repository_insights ri
            WHERE ri.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            ORDER BY ri.confidence DESC
        """
        
        cursor = self.db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Also get basic stats
        stats_sql = """
            SELECT 
                ss.files_scanned,
                ss.duration_ms,
                COUNT(v.id) as total_violations,
                COUNT(CASE WHEN v.severity = 'CRITICAL' THEN 1 END) as critical_violations,
                COUNT(CASE WHEN v.severity = 'HIGH' THEN 1 END) as high_violations
            FROM scan_sessions ss
            LEFT JOIN scanned_files f ON ss.id = f.scan_session_id
            LEFT JOIN violations v ON f.id = v.file_id
            WHERE ss.id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            GROUP BY ss.id
        """
        
        stats_cursor = self.db.execute(stats_sql)
        stats = dict(stats_cursor.fetchone() or {})
        
        return {
            "sql": sql,
            "results": results,
            "stats": stats,
            "summary": f"Repository analysis complete: {stats.get('files_scanned', 0)} files scanned, {stats.get('total_violations', 0)} violations found",
            "type": "repository_insights"
        }
    
    def _query_fix_priority(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query violations in fix priority order."""
        sql = """
            SELECT 
                v.id,
                v.pattern_name,
                f.file_path,
                v.line_number,
                v.severity,
                v.confidence,
                v.fix_complexity,
                v.ai_explanation,
                v.business_impact,
                (CASE v.severity 
                    WHEN 'CRITICAL' THEN 4
                    WHEN 'HIGH' THEN 3
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 1 
                END * v.confidence) as priority_score
            FROM violations v
            JOIN scanned_files f ON v.file_id = f.id
            WHERE v.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            AND v.confidence > 0.7
            ORDER BY 
                priority_score DESC,
                CASE v.fix_complexity 
                    WHEN 'simple' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'complex' THEN 3 
                END
            LIMIT 10
        """
        
        cursor = self.db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Top {len(results)} violations to fix first, prioritized by impact and ease",
            "type": "fix_priority"
        }
    
    def _query_simple_fixes(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Query simple/easy fixes."""
        sql = """
            SELECT 
                v.pattern_name,
                f.file_path,
                v.line_number,
                v.code_snippet,
                v.ai_explanation,
                v.fix_suggestions,
                v.confidence
            FROM violations v
            JOIN scanned_files f ON v.file_id = f.id
            WHERE v.fix_complexity = 'simple'
            AND v.confidence > 0.8
            AND v.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            ORDER BY v.confidence DESC
        """
        
        cursor = self.db.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Found {len(results)} simple fixes with high confidence",
            "type": "simple_fixes"
        }
    
    def _fallback_search(self, query: str) -> dict[str, Any]:
        """Fallback FTS search when no pattern matches."""
        sql = """
            SELECT 
                'violation' as result_type,
                v.pattern_name as title,
                v.ai_explanation as description,
                f.file_path as location,
                v.confidence
            FROM violations_fts vf
            JOIN violations v ON vf.violation_id = v.id
            JOIN scanned_files f ON v.file_id = f.id
            WHERE violations_fts MATCH ?
            
            UNION ALL
            
            SELECT 
                'insight' as result_type,
                ri.title,
                ri.description,
                ri.insight_type as location,
                ri.confidence
            FROM insights_fts inf
            JOIN repository_insights ri ON inf.insight_id = ri.id
            WHERE insights_fts MATCH ?
            
            ORDER BY confidence DESC
            LIMIT 20
        """
        
        cursor = self.db.execute(sql, (query, query))
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sql": sql,
            "results": results,
            "summary": f"Full-text search found {len(results)} results for '{query}'",
            "type": "fallback_search"
        }
    
    def _count_violations(self, match: re.Match, context: dict[str, Any]) -> dict[str, Any]:
        """Count violations by category."""
        sql = """
            SELECT 
                COUNT(*) as total_violations,
                COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical,
                COUNT(CASE WHEN severity = 'HIGH' THEN 1 END) as high,
                COUNT(CASE WHEN severity = 'MEDIUM' THEN 1 END) as medium,
                COUNT(CASE WHEN severity = 'LOW' THEN 1 END) as low,
                COUNT(CASE WHEN fix_complexity = 'simple' THEN 1 END) as simple_fixes
            FROM violations
            WHERE scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
        """
        
        cursor = self.db.execute(sql)
        result = dict(cursor.fetchone() or {})
        
        return {
            "sql": sql,
            "results": [result],
            "summary": f"Total: {result.get('total_violations', 0)} violations ({result.get('critical', 0)} critical, {result.get('high', 0)} high priority)",
            "type": "violation_count"
        }
    
    def _format_response(self, original_query: str, result: dict[str, Any], pattern: str) -> dict[str, Any]:
        """Format response for AI consumption."""
        return {
            "original_query": original_query,
            "intent_matched": pattern,
            "sql_executed": result["sql"],
            "results": result["results"],
            "summary": result["summary"],
            "result_type": result["type"],
            "result_count": len(result["results"]),
            "ai_insights": self._generate_ai_insights(result),
            "suggested_follow_ups": self._suggest_follow_ups(result)
        }
    
    def _generate_ai_insights(self, result: dict[str, Any]) -> list[str]:
        """Generate AI insights based on query results."""
        insights = []
        result_type = result["type"]
        results = result["results"]
        
        if result_type == "fix_priority" and results:
            insights.append(f"Recommend starting with {results[0]['pattern_name']} - high impact and {results[0]['fix_complexity']} to fix")
            
        elif result_type == "high_severity_violations" and results:
            critical_count = sum(1 for r in results if r["severity"] == "CRITICAL")
            if critical_count > 0:
                insights.append(f"{critical_count} critical violations need immediate attention")
                
        elif result_type == "files_most_violations" and results:
            top_file = results[0]
            insights.append(f"Focus on {top_file['file_path']} - it has {top_file['violation_count']} violations")
            
        elif result_type == "simple_fixes" and results:
            insights.append(f"{len(results)} quick wins available - these can be fixed easily")
        
        return insights
    
    def _suggest_follow_ups(self, result: dict[str, Any]) -> list[str]:
        """Suggest follow-up queries based on results."""
        suggestions = []
        result_type = result["type"]
        results = result["results"]
        
        if result_type == "violations_by_content" and results:
            suggestions.append(f"Show me simple fixes for {results[0]['pattern_name']}")
            suggestions.append("What files have the most violations?")
            
        elif result_type == "fix_priority" and results:
            suggestions.append(f"Show me all violations in {results[0]['file_path']}")
            suggestions.append("Show me simple fixes")
            
        elif result_type == "repository_insights":
            suggestions.append("What should I fix first?")
            suggestions.append("Show me high severity violations")
            
        # Always suggest these
        suggestions.extend([
            "Show me repository health summary",
            "Count violations by severity"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _error_response(self, query: str, error: str) -> dict[str, Any]:
        """Format error response."""
        return {
            "original_query": query,
            "error": True,
            "message": f"Error processing query: {error}",
            "suggested_queries": [
                "Show me all violations",
                "What files have the most violations?",
                "Show me repository insights",
                "What should I fix first?"
            ]
        }
    
    def get_available_commands(self) -> list[str]:
        """Get list of available query patterns for help."""
        return [
            "Show me violations in [filename]",
            "Show me violations related to [topic]",
            "Show me all violations",
            "Show me critical violations", 
            "Count violations",
            "What files have the most violations?",
            "Show me repository insights",
            "What should I fix first?",
            "Show me simple fixes",
            "Help me learn from this codebase"
        ]


def create_sample_queries() -> list[tuple[str, str]]:
    """Create sample queries for testing and documentation."""
    return [
        ("Show me all violations", "Get overview of all violations by category and severity"),
        ("What files have the most violations?", "Find files that need the most attention"),
        ("Show me violations related to http", "Find HTTP-related code issues"),
        ("What should I fix first?", "Get prioritized list of violations to address"),
        ("Show me simple fixes", "Find easy wins that can be fixed quickly"),
        ("Show me repository insights", "Get high-level analysis and recommendations"),
        ("Count violations", "Get violation statistics by severity"),
        ("Show me critical violations", "Find the most serious issues"),
        ("Show me violations in client.py", "Analyze specific file"),
        ("Help me learn from this codebase", "Find learning opportunities and best practices")
    ]
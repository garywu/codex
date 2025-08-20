# SQLite-First Reporting Architecture for AI Assistance

## 🎯 Core Concept: SQLite as AI Interface

**"Instead of generating reports, we generate queryable SQLite databases that Claude Code can explore interactively using natural language SQL queries."**

## 🧠 Why SQLite FTS for AI Reporting?

### **Traditional Approach Problems:**
```bash
codex scan src/ --format json > report.json
# Claude gets static snapshot, can't explore or drill down
# No ability to ask follow-up questions
# Limited to predefined report structure
```

### **SQLite FTS Approach Benefits:**
```bash
codex scan src/ --output-db scan_results.db
# Claude can query dynamically: "Show me all HTTP-related violations"
# Full-text search: "Find patterns related to error handling"
# Relational queries: "What files have the most violations?"
# Time-series analysis: "How has code quality changed?"
```

## 🗄️ Database Schema Design

### **Core Tables for AI Querying**

```sql
-- Scan metadata and session tracking
CREATE TABLE scan_sessions (
    id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    repository_path TEXT NOT NULL,
    duration_ms INTEGER,
    files_scanned INTEGER,
    patterns_checked INTEGER,
    codex_version TEXT,
    scan_config JSON,
    ai_context TEXT, -- Context from Claude Code session
    repository_hash TEXT -- Git commit hash if available
);

-- Files with metadata for AI understanding
CREATE TABLE scanned_files (
    id TEXT PRIMARY KEY,
    scan_session_id TEXT REFERENCES scan_sessions(id),
    file_path TEXT NOT NULL,
    file_type TEXT, -- python, javascript, etc.
    file_size INTEGER,
    line_count INTEGER,
    complexity_score REAL,
    last_modified DATETIME,
    git_blame_summary JSON, -- Recent authors, change frequency
    framework_indicators TEXT, -- fastapi, django, flask, etc.
    UNIQUE(scan_session_id, file_path)
);

-- Violations with full context for AI analysis
CREATE TABLE violations (
    id TEXT PRIMARY KEY,
    scan_session_id TEXT REFERENCES scan_sessions(id),
    file_id TEXT REFERENCES scanned_files(id),
    pattern_id TEXT NOT NULL,
    pattern_name TEXT NOT NULL,
    pattern_category TEXT, -- security, performance, style, etc.
    severity TEXT, -- CRITICAL, HIGH, MEDIUM, LOW
    confidence REAL, -- 0.0 to 1.0
    line_number INTEGER,
    column_number INTEGER,
    code_snippet TEXT,
    surrounding_context TEXT, -- 5 lines before/after
    violation_message TEXT,
    ai_explanation TEXT, -- Human-readable explanation for AI
    fix_complexity TEXT, -- simple, medium, complex
    fix_suggestions JSON,
    related_violation_ids JSON,
    business_impact TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Pattern library with searchable content
CREATE TABLE pattern_library (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    description TEXT,
    rationale TEXT, -- Why this pattern matters
    detection_rules JSON,
    fix_templates JSON,
    good_examples TEXT,
    bad_examples TEXT,
    related_patterns JSON,
    documentation_links JSON,
    tags TEXT, -- space-separated for FTS
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Repository insights for AI context
CREATE TABLE repository_insights (
    id TEXT PRIMARY KEY,
    scan_session_id TEXT REFERENCES scan_sessions(id),
    insight_type TEXT, -- architecture, frameworks, complexity, etc.
    insight_category TEXT, -- positive, negative, neutral
    confidence REAL,
    title TEXT,
    description TEXT,
    supporting_evidence JSON,
    impact_assessment TEXT,
    recommendations JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- AI interaction tracking
CREATE TABLE ai_interactions (
    id TEXT PRIMARY KEY,
    scan_session_id TEXT REFERENCES scan_sessions(id),
    interaction_type TEXT, -- query, explanation_request, fix_suggestion
    ai_query TEXT,
    sql_generated TEXT, -- SQL query generated from natural language
    results_returned JSON,
    ai_satisfaction_score REAL, -- If available from feedback
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### **Full-Text Search Tables**

```sql
-- FTS5 table for violations content
CREATE VIRTUAL TABLE violations_fts USING fts5(
    violation_id,
    pattern_name,
    pattern_category,
    code_snippet,
    violation_message,
    ai_explanation,
    file_path,
    tags,
    content='violations',
    content_rowid='rowid'
);

-- FTS5 table for pattern library
CREATE VIRTUAL TABLE patterns_fts USING fts5(
    pattern_id,
    name,
    category,
    description,
    rationale,
    good_examples,
    bad_examples,
    tags,
    content='pattern_library',
    content_rowid='rowid'
);

-- FTS5 table for repository insights
CREATE VIRTUAL TABLE insights_fts USING fts5(
    insight_id,
    insight_type,
    title,
    description,
    recommendations,
    content='repository_insights',
    content_rowid='rowid'
);
```

## 🔍 AI Query Interface

### **Natural Language to SQL Translation**

```python
class AIQueryInterface:
    """Translate natural language queries to SQL for Claude Code."""
    
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.db.enable_load_extension(True)
        
    def query_natural_language(self, query: str, context: dict = None) -> dict:
        """Convert natural language to SQL and execute."""
        sql_query = self._translate_to_sql(query, context)
        results = self._execute_query(sql_query)
        explanation = self._explain_results(results, query)
        
        return {
            "original_query": query,
            "sql_generated": sql_query,
            "results": results,
            "explanation": explanation,
            "suggested_follow_ups": self._suggest_follow_ups(results)
        }
    
    def _translate_to_sql(self, query: str, context: dict) -> str:
        """Translate natural language to SQL."""
        # Intent mapping
        intent_patterns = {
            "show me.*violations.*http": """
                SELECT v.*, f.file_path, p.description
                FROM violations v
                JOIN scanned_files f ON v.file_id = f.id
                JOIN pattern_library p ON v.pattern_id = p.id
                WHERE violations_fts MATCH 'http OR requests OR httpx'
                ORDER BY v.severity DESC, v.confidence DESC
            """,
            "what files.*most.*violations": """
                SELECT f.file_path, COUNT(v.id) as violation_count,
                       AVG(CASE v.severity 
                           WHEN 'CRITICAL' THEN 4
                           WHEN 'HIGH' THEN 3  
                           WHEN 'MEDIUM' THEN 2
                           WHEN 'LOW' THEN 1 END) as avg_severity
                FROM scanned_files f
                LEFT JOIN violations v ON f.id = v.file_id
                GROUP BY f.id, f.file_path
                ORDER BY violation_count DESC, avg_severity DESC
                LIMIT 10
            """,
            "patterns.*related.*error.*handling": """
                SELECT * FROM pattern_library
                WHERE patterns_fts MATCH 'error OR exception OR handling OR try OR catch'
                ORDER BY priority DESC
            """,
            "repository.*health.*summary": """
                SELECT 
                    ss.repository_path,
                    ss.files_scanned,
                    COUNT(v.id) as total_violations,
                    COUNT(CASE WHEN v.severity = 'CRITICAL' THEN 1 END) as critical_violations,
                    COUNT(CASE WHEN v.severity = 'HIGH' THEN 1 END) as high_violations,
                    AVG(f.complexity_score) as avg_complexity,
                    GROUP_CONCAT(DISTINCT ri.title) as key_insights
                FROM scan_sessions ss
                LEFT JOIN scanned_files f ON ss.id = f.scan_session_id
                LEFT JOIN violations v ON f.id = v.file_id
                LEFT JOIN repository_insights ri ON ss.id = ri.scan_session_id
                WHERE ss.id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
                GROUP BY ss.id
            """
        }
        
        # Pattern matching to find appropriate SQL
        for pattern, sql in intent_patterns.items():
            if re.search(pattern, query.lower()):
                return sql
                
        # Fallback to FTS search
        return f"""
            SELECT 'violation' as type, violation_message as content, file_path
            FROM violations_fts WHERE violations_fts MATCH '{query}'
            UNION ALL
            SELECT 'pattern' as type, description as content, name as file_path
            FROM patterns_fts WHERE patterns_fts MATCH '{query}'
            UNION ALL  
            SELECT 'insight' as type, description as content, insight_type as file_path
            FROM insights_fts WHERE insights_fts MATCH '{query}'
        """
```

### **Predefined Query Templates for Claude Code**

```python
class CommonAIQueries:
    """Predefined queries optimized for AI assistance workflows."""
    
    @staticmethod
    def get_violation_summary() -> str:
        """Get overview of all violations by severity and category."""
        return """
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
    
    @staticmethod
    def get_fix_priority_list() -> str:
        """Get violations ordered by fix priority for AI."""
        return """
            SELECT 
                v.id,
                v.pattern_name,
                v.file_path,
                v.line_number,
                v.severity,
                v.confidence,
                v.fix_complexity,
                v.ai_explanation,
                v.business_impact,
                COUNT(rv.related_id) as related_violations_count
            FROM violations v
            LEFT JOIN (
                SELECT 
                    violation_id,
                    json_each.value as related_id
                FROM violations,
                json_each(violations.related_violation_ids)
            ) rv ON v.id = rv.violation_id
            WHERE v.scan_session_id = (SELECT id FROM scan_sessions ORDER BY timestamp DESC LIMIT 1)
            AND v.confidence > 0.8
            GROUP BY v.id
            ORDER BY 
                CASE v.severity 
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3  
                    WHEN 'LOW' THEN 4
                END,
                CASE v.fix_complexity
                    WHEN 'simple' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'complex' THEN 3
                END,
                v.confidence DESC,
                related_violations_count DESC
        """
    
    @staticmethod
    def get_learning_opportunities() -> str:
        """Find patterns that represent learning opportunities."""
        return """
            SELECT 
                p.name,
                p.category,
                p.description,
                p.rationale,
                p.good_examples,
                COUNT(v.id) as violations_count,
                AVG(v.confidence) as avg_detection_confidence
            FROM pattern_library p
            LEFT JOIN violations v ON p.id = v.pattern_id
            WHERE p.priority IN ('HIGH', 'MEDIUM')
            GROUP BY p.id
            HAVING violations_count > 0
            ORDER BY violations_count DESC, avg_detection_confidence DESC
        """
    
    @staticmethod
    def get_codebase_evolution() -> str:
        """Track how codebase quality changes over time."""
        return """
            SELECT 
                DATE(ss.timestamp) as scan_date,
                ss.files_scanned,
                COUNT(v.id) as total_violations,
                COUNT(CASE WHEN v.severity = 'CRITICAL' THEN 1 END) as critical_count,
                COUNT(CASE WHEN v.severity = 'HIGH' THEN 1 END) as high_count,
                ROUND(AVG(v.confidence), 3) as avg_confidence,
                GROUP_CONCAT(DISTINCT v.pattern_category) as violation_categories
            FROM scan_sessions ss
            LEFT JOIN scanned_files f ON ss.id = f.scan_session_id  
            LEFT JOIN violations v ON f.id = v.file_id
            WHERE ss.timestamp > datetime('now', '-30 days')
            GROUP BY DATE(ss.timestamp)
            ORDER BY ss.timestamp DESC
        """
```

## 🔧 Implementation: Database-First Scanning

### **Enhanced Scanner with SQLite Output**

```python
class SQLiteReportingScanner:
    """Scanner that writes results directly to SQLite for AI querying."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.session_id = self._generate_session_id()
        
    async def scan_repository(self, repo_path: Path, ai_context: str = None) -> str:
        """Scan repository and write results to SQLite database."""
        
        # Initialize database and session
        self._initialize_database()
        self._create_scan_session(repo_path, ai_context)
        
        # Scan files and write to database
        async for file_result in self._scan_files_async(repo_path):
            self._write_file_result(file_result)
            
        # Generate insights and write to database
        insights = await self._generate_repository_insights()
        self._write_insights(insights)
        
        # Update session with final metrics
        self._finalize_scan_session()
        
        return self.db_path
    
    def _write_file_result(self, file_result: FileAnalysisResult):
        """Write file analysis to database."""
        # Insert file record
        file_id = self._insert_file_record(file_result)
        
        # Insert violations
        for violation in file_result.violations:
            self._insert_violation(violation, file_id)
    
    def _insert_violation(self, violation: PatternMatch, file_id: str):
        """Insert violation with AI-optimized data."""
        ai_explanation = self._generate_ai_explanation(violation)
        fix_suggestions = self._generate_fix_suggestions(violation)
        business_impact = self._assess_business_impact(violation)
        
        self.db.execute("""
            INSERT INTO violations (
                id, scan_session_id, file_id, pattern_id, pattern_name,
                pattern_category, severity, confidence, line_number,
                code_snippet, surrounding_context, violation_message,
                ai_explanation, fix_complexity, fix_suggestions,
                business_impact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            violation.id, self.session_id, file_id, violation.pattern_id,
            violation.pattern_name, violation.category, violation.severity,
            violation.confidence, violation.line_number, violation.code_snippet,
            violation.surrounding_context, violation.message, ai_explanation,
            violation.fix_complexity, json.dumps(fix_suggestions), business_impact
        ))
```

### **AI Query CLI Integration**

```python
@app.command(name="query-db")
def query_database(
    db_path: Annotated[Path, typer.Argument(help="Path to scan results database")],
    query: Annotated[str, typer.Argument(help="Natural language query")],
    ai_format: Annotated[bool, typer.Option("--ai", help="AI-optimized output")] = False,
    explain: Annotated[bool, typer.Option("--explain", help="Show SQL and explanation")] = False,
) -> None:
    """Query scan results database with natural language."""
    
    query_interface = AIQueryInterface(str(db_path))
    result = query_interface.query_natural_language(query)
    
    if explain:
        console.print(f"[bold]Generated SQL:[/bold]\n{result['sql_generated']}\n")
    
    if ai_format:
        # Output optimized for Claude Code consumption
        print(json.dumps({
            "query": result["original_query"],
            "results": result["results"],
            "explanation": result["explanation"],
            "follow_up_suggestions": result["suggested_follow_ups"]
        }, indent=2))
    else:
        # Human-readable output
        console.print(f"[bold green]Results for:[/bold green] {query}\n")
        for row in result["results"]:
            console.print(f"• {row}")
        
        if result["suggested_follow_ups"]:
            console.print(f"\n[bold blue]Suggested follow-up queries:[/bold blue]")
            for suggestion in result["suggested_follow_ups"]:
                console.print(f"  - {suggestion}")

@app.command(name="scan-to-db")
def scan_to_database(
    paths: Annotated[list[Path], typer.Argument(help="Paths to scan")],
    output_db: Annotated[Path, typer.Option("--output-db", "-o")] = Path("scan_results.db"),
    ai_context: Annotated[str, typer.Option("--ai-context")] = None,
    incremental: Annotated[bool, typer.Option("--incremental")] = False,
) -> None:
    """Scan files and output results to SQLite database for AI querying."""
    
    async def _scan():
        scanner = SQLiteReportingScanner(str(output_db))
        
        for path in paths:
            if path.is_file():
                await scanner.scan_file(path)
            else:
                await scanner.scan_repository(path, ai_context)
        
        console.print(f"[green]✅ Scan results written to: {output_db}[/green]")
        console.print(f"[blue]🔍 Query with: codex query-db {output_db} 'your question'[/blue]")
    
    asyncio.run(_scan())
```

## 🎯 MCP Tools for SQLite Querying

### **Database-Aware MCP Tools**

```python
@mcp_tool
def query_scan_database(
    db_path: str,
    natural_query: str,
    context: str = None
) -> dict:
    """Query scan results database using natural language."""
    
    query_interface = AIQueryInterface(db_path)
    result = query_interface.query_natural_language(natural_query, {"context": context})
    
    return {
        "query": natural_query,
        "sql": result["sql_generated"],
        "results": result["results"],
        "explanation": result["explanation"],
        "confidence": result.get("confidence", 0.9),
        "suggested_actions": result["suggested_follow_ups"]
    }

@mcp_tool
def get_violation_details(
    db_path: str,
    violation_id: str = None,
    pattern_name: str = None,
    file_path: str = None
) -> dict:
    """Get detailed information about specific violations."""
    
    db = sqlite3.connect(db_path)
    
    where_clause = []
    params = []
    
    if violation_id:
        where_clause.append("v.id = ?")
        params.append(violation_id)
    elif pattern_name:
        where_clause.append("v.pattern_name = ?")
        params.append(pattern_name)
    elif file_path:
        where_clause.append("f.file_path = ?")
        params.append(file_path)
    
    sql = f"""
        SELECT 
            v.*,
            f.file_path,
            f.file_type,
            p.description as pattern_description,
            p.rationale,
            p.good_examples,
            p.bad_examples
        FROM violations v
        JOIN scanned_files f ON v.file_id = f.id
        JOIN pattern_library p ON v.pattern_id = p.id
        WHERE {' AND '.join(where_clause)}
    """
    
    cursor = db.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    return {
        "violations": results,
        "count": len(results),
        "ai_summary": f"Found {len(results)} violation(s) matching your criteria"
    }

@mcp_tool
def suggest_fix_priority(
    db_path: str,
    max_suggestions: int = 10,
    complexity_preference: str = "simple"
) -> dict:
    """Suggest violations to fix first based on impact and complexity."""
    
    query_interface = AIQueryInterface(db_path)
    
    complexity_filter = {
        "simple": "WHERE v.fix_complexity = 'simple'",
        "medium": "WHERE v.fix_complexity IN ('simple', 'medium')",
        "all": ""
    }
    
    sql = f"""
        SELECT 
            v.id,
            v.pattern_name,
            v.file_path,
            v.ai_explanation,
            v.fix_complexity,
            v.business_impact,
            v.confidence,
            CASE v.severity 
                WHEN 'CRITICAL' THEN 4
                WHEN 'HIGH' THEN 3
                WHEN 'MEDIUM' THEN 2  
                WHEN 'LOW' THEN 1
            END as severity_score
        FROM violations v
        {complexity_filter.get(complexity_preference, "")}
        AND v.confidence > 0.8
        ORDER BY severity_score DESC, v.confidence DESC
        LIMIT {max_suggestions}
    """
    
    db = sqlite3.connect(db_path)
    cursor = db.execute(sql)
    results = [dict(row) for row in cursor.fetchall()]
    
    return {
        "suggested_fixes": results,
        "fix_strategy": f"Prioritized by severity and confidence, filtered for {complexity_preference} fixes",
        "total_suggestions": len(results)
    }
```

This SQLite-first approach transforms Codex from a static report generator into an interactive, queryable knowledge base that Claude Code can explore dynamically, making AI-assisted code improvement dramatically more effective and contextual.
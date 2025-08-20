# Codex Revised Architecture (v2)

## Pre-Commit Focused Architecture

Based on clarifications and analysis of related projects (ALLM and open-lovable), Codex will implement a **pre-commit hook architecture** with multi-factor analysis.

### Core Architecture Principles

1. **On-Demand Analysis**: No real-time file monitoring initially - analysis triggered by git hooks
2. **Multi-Factor Voting**: Layered analysis from simple patterns to sophisticated AI
3. **Local-First**: All processing happens on the local machine
4. **Claude Code CLI Integration**: Primary integration target for AI assistant communication
5. **Optional Auto-Fix**: Automatic correction of detected issues when possible

## System Components

### 1. Pre-Commit Hook Engine
```bash
# Installed in each project
.git/hooks/pre-commit -> codex-pre-commit-hook

# Hook workflow:
git commit -> codex analyze -> [optional fix] -> commit or abort
```

**Responsibilities:**
- Intercept git commits
- Trigger analysis of staged changes
- Present results to developer
- Optionally apply automatic fixes
- Allow/block commit based on analysis

### 2. Multi-Factor Analysis Engine

Inspired by pattern analysis in open-lovable and the provider abstraction in ALLM:

#### Layer 1: Pattern Matching (Fast)
- **Regex-based detection** of common anti-patterns
- **AST analysis** for structural issues
- **Import/API validation** against known libraries
- **Basic syntax and formatting checks**

#### Layer 2: Contextual Analysis (Medium)
- **Project-aware analysis** using local context
- **Framework-specific patterns** (React, FastAPI, etc.)
- **Code style consistency** with existing codebase
- **Dependency compatibility** checks

#### Layer 3: AI-Powered Analysis (Sophisticated)
- **LLM-based code review** for complex logic issues
- **Goal alignment assessment** against project requirements
- **Hallucination detection** for non-existent APIs
- **Architecture compliance** verification

### 3. Voting and Decision Engine

```python
class AnalysisResult:
    pattern_score: float      # 0-1 from regex/AST analysis
    context_score: float      # 0-1 from contextual analysis
    ai_score: float          # 0-1 from LLM analysis
    confidence: float        # Overall confidence in assessment
    issues: List[Issue]      # Specific problems found
    fixes: List[AutoFix]     # Automatic fixes available

def calculate_commit_decision(results: List[AnalysisResult]) -> CommitDecision:
    # Weighted voting algorithm
    # Higher weights for higher-confidence results
    # Can be tuned per project
```

### 4. Claude Code CLI Integration

Based on ALLM's provider abstraction pattern:

```python
class CodexMCPProvider:
    """MCP interface for Claude Code CLI integration"""

    async def analyze_code_intent(self, code: str, context: str) -> Intent
    async def suggest_improvements(self, analysis: AnalysisResult) -> List[Suggestion]
    async def validate_against_requirements(self, code: str, requirements: str) -> ValidationResult
```

**Integration Points:**
- **Pre-generation**: Codex provides project context to Claude Code CLI
- **Post-generation**: Codex analyzes generated code before commit
- **Iterative refinement**: Codex guides Claude Code CLI toward better solutions

### 5. Auto-Fix Engine

Inspired by error fixing patterns in open-lovable:

```python
class AutoFixEngine:
    """Automatic code fixing capabilities"""

    def fix_imports(self, code: str) -> str
    def fix_formatting(self, code: str) -> str
    def fix_simple_patterns(self, code: str, issues: List[Issue]) -> str
    def suggest_complex_fixes(self, code: str, context: str) -> List[FixSuggestion]
```

## Workflow Integration

### Development Workflow
```
1. Developer requests feature from Claude Code CLI
2. Claude Code CLI generates code (with optional Codex context)
3. Developer reviews and stages changes
4. git commit triggers Codex pre-commit hook
5. Codex runs multi-factor analysis
6. Results presented with optional auto-fixes
7. Developer accepts/modifies/rejects changes
8. Commit proceeds or is aborted
```

### Analysis Workflow
```
Pre-commit trigger
    ↓
Staged file analysis
    ↓
Layer 1: Pattern matching (< 100ms)
    ↓
Layer 2: Context analysis (< 500ms)
    ↓
Layer 3: AI analysis (< 2s, only if needed)
    ↓
Vote aggregation and decision
    ↓
Present results + optional fixes
    ↓
Developer decision (commit/fix/abort)
```

## Technical Stack (Inspired by ALLM)

### Core Technologies
- **Python 3.11+**: Main implementation language
- **Pydantic**: Data validation and settings
- **httpx**: Async HTTP for any external calls
- **Rich**: Beautiful CLI output and progress indicators
- **Typer**: CLI interface with type hints
- **Tree-sitter**: Multi-language AST parsing

### Analysis Components
- **AST Parsers**: Language-specific parsing (tree-sitter)
- **Pattern Engine**: Regex + rule-based detection
- **Context Engine**: Project-aware analysis
- **AI Integration**: LLM providers for sophisticated analysis
- **Fix Engine**: Automatic code correction

### Integration Layer
- **Git Hooks**: Pre-commit hook installation and management
- **MCP Protocol**: Claude Code CLI communication
- **File System**: Local project analysis
- **Configuration**: Project-specific settings and rules

## Performance Targets

- **Pattern Analysis**: < 100ms for typical changes
- **Context Analysis**: < 500ms for complex changes
- **AI Analysis**: < 2s when needed
- **Total Analysis**: < 1s for 90% of commits
- **Auto-fix Application**: < 200ms for common fixes

## Configuration and Customization

```yaml
# .codex.yml per project
analysis:
  layers:
    pattern: true        # Always enabled
    context: true        # Enable project context
    ai: "on_complex"     # only | always | on_complex | off

  thresholds:
    pattern_confidence: 0.8
    context_confidence: 0.7
    ai_confidence: 0.6

  auto_fix:
    formatting: true
    imports: true
    simple_patterns: true

integrations:
  claude_code_cli: true
  custom_rules: "./rules/"
```

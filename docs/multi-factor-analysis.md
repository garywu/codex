# Multi-Factor Analysis & Voting System

## Overview

Codex implements a **multi-factor voting mechanism** that balances analysis speed with depth, using multiple analysis layers that vote on code quality and issues. This approach provides fast feedback for simple issues while leveraging sophisticated AI analysis only when needed.

## Analysis Layers

### Layer 1: Pattern Matching (Fast & Deterministic)

**Purpose**: Catch obvious issues quickly with high confidence
**Performance**: < 100ms for typical changes
**Coverage**: ~60% of common issues

#### Components:

**Regex-Based Pattern Detection**
```python
# Examples inspired by open-lovable's intent patterns
HALLUCINATION_PATTERNS = [
    r'import\s+(\w+)\s+from\s+["\'](\w+)["\']',  # Import validation
    r'\.(\w+)\(',                                 # Method call validation  
    r'await\s+fetch\(["\']([^"\']+)["\']',       # API endpoint validation
    r'process\.env\.(\w+)',                       # Environment variable check
]

ANTI_PATTERNS = [
    r'console\.log\(',                            # Debug statements
    r'TODO|FIXME|XXX',                           # TODO comments
    r'\.innerHTML\s*=',                          # XSS risk
    r'eval\(',                                   # Code injection risk
]
```

**AST-Based Structural Analysis**  
```python
class ASTAnalyzer:
    def check_imports(self, tree) -> List[Issue]:
        """Validate that imported modules/functions exist"""
        
    def check_function_calls(self, tree) -> List[Issue]:
        """Verify called functions are defined or imported"""
        
    def check_complexity(self, tree) -> List[Issue]:
        """Measure cyclomatic complexity, nesting depth"""
        
    def check_naming_conventions(self, tree) -> List[Issue]:
        """Verify consistent naming patterns"""
```

**Language-Specific Validators**
- **Python**: Import validation against installed packages, PEP 8 compliance
- **JavaScript/TypeScript**: Package.json dependency validation, ESLint-style checks
- **Go**: Module and interface validation
- **Rust**: Crate and trait validation

### Layer 2: Contextual Analysis (Project-Aware)

**Purpose**: Understand project context and enforce consistency
**Performance**: < 500ms for complex changes  
**Coverage**: ~25% of contextual issues

#### Components:

**Project Context Engine**
```python
class ProjectContext:
    def __init__(self, project_root: str):
        self.dependencies = self.load_dependencies()      # package.json, pyproject.toml, etc.
        self.frameworks = self.detect_frameworks()        # React, FastAPI, Django, etc.
        self.patterns = self.learn_patterns()             # Existing code patterns
        self.architecture = self.analyze_architecture()   # Project structure
        
    def validate_dependency(self, import_name: str) -> bool:
        """Check if imported module is actually available"""
        
    def check_framework_compliance(self, code: str) -> List[Issue]:
        """Verify code follows framework best practices"""
        
    def assess_consistency(self, code: str) -> List[Issue]:
        """Compare against existing patterns in the project"""
```

**Framework-Specific Analysis**
- **React**: Component patterns, hook usage, prop validation
- **FastAPI**: Route patterns, dependency injection, response models
- **Django**: Model/view/template patterns, security practices
- **Express**: Middleware patterns, error handling

**Consistency Checks**
- **Code Style**: Indentation, naming conventions, import organization
- **Architecture**: File organization, module boundaries, dependency direction
- **Patterns**: Function signatures, error handling, logging patterns

### Layer 3: AI-Powered Analysis (Deep Understanding)

**Purpose**: Complex semantic analysis and goal alignment
**Performance**: < 2s when triggered
**Coverage**: ~15% of sophisticated issues
**Trigger**: Only when lower layers indicate complexity or uncertainty

#### Components:

**Semantic Code Analysis**
```python
class AIAnalyzer:
    async def analyze_logic_correctness(self, code: str, context: str) -> AnalysisResult:
        """Deep analysis of code logic and potential bugs"""
        
    async def check_goal_alignment(self, code: str, requirements: str) -> AnalysisResult:  
        """Verify code serves intended purpose"""
        
    async def detect_hallucinations(self, code: str, available_apis: List[str]) -> AnalysisResult:
        """Identify references to non-existent APIs/functions"""
        
    async def assess_architecture_fit(self, code: str, project_arch: str) -> AnalysisResult:
        """Check if code fits project architecture"""
```

**AI Provider Integration** (Similar to ALLM pattern)
```python
class AIProviderManager:
    def __init__(self):
        self.providers = [
            ClaudeProvider(priority=100),
            GPT4Provider(priority=90),  
            LocalModelProvider(priority=50)
        ]
    
    async def analyze_with_fallback(self, prompt: str, code: str) -> AnalysisResult:
        """Try providers in priority order with fallback"""
```

## Voting Algorithm

### Vote Aggregation
```python
class VotingEngine:
    def aggregate_votes(self, results: List[LayerResult]) -> CommitDecision:
        weighted_score = 0
        total_confidence = 0
        
        for result in results:
            weight = self.calculate_weight(result)
            weighted_score += result.score * weight
            total_confidence += result.confidence * weight
            
        return CommitDecision(
            should_commit=weighted_score > self.threshold,
            confidence=total_confidence / len(results),
            issues=self.merge_issues(results),
            fixes=self.merge_fixes(results)
        )
    
    def calculate_weight(self, result: LayerResult) -> float:
        """Weight based on layer type and confidence"""
        base_weights = {
            LayerType.PATTERN: 0.8,    # High confidence in pattern matching
            LayerType.CONTEXT: 0.6,    # Medium confidence in context  
            LayerType.AI: 0.4          # Lower weight, but high value
        }
        return base_weights[result.layer] * result.confidence
```

### Decision Thresholds

**Configurable per project:**
```yaml
voting:
  commit_threshold: 0.7      # Overall score needed to auto-commit
  block_threshold: 0.3       # Score below which commit is blocked
  ai_trigger_threshold: 0.5  # When to engage AI analysis
  
layer_weights:
  pattern: 0.8               # Trust pattern matching highly  
  context: 0.6               # Medium trust in context analysis
  ai: 0.4                    # Conservative weight for AI (but high value)
```

### Example Voting Scenarios

**Scenario 1: Clean Code**
```python
# Layer 1: No issues found (score: 1.0, confidence: 0.9)
# Layer 2: Consistent with project (score: 0.95, confidence: 0.8)  
# Layer 3: Not triggered
# Decision: Auto-commit (weighted score: 0.98)
```

**Scenario 2: Suspicious Import**
```python
# Layer 1: Unknown import detected (score: 0.2, confidence: 0.9)
# Layer 2: Import not in dependencies (score: 0.1, confidence: 0.8)
# Layer 3: AI confirms hallucination (score: 0.05, confidence: 0.7)
# Decision: Block commit (weighted score: 0.12)
```

**Scenario 3: Complex Logic**
```python
# Layer 1: No obvious patterns (score: 0.8, confidence: 0.3) 
# Layer 2: Unusual for project (score: 0.6, confidence: 0.4)
# Layer 3: AI analysis needed -> Logic looks correct (score: 0.85, confidence: 0.8)
# Decision: Allow with review (weighted score: 0.71)
```

## Performance Optimization

### Caching Strategy
```python
class AnalysisCache:
    def cache_pattern_results(self, file_hash: str, results: PatternResult):
        """Cache regex and AST analysis results"""
        
    def cache_context_analysis(self, project_hash: str, results: ContextResult):
        """Cache project-level analysis"""
        
    def invalidate_on_dependency_change(self):
        """Clear cache when dependencies change"""
```

### Incremental Analysis
```python
class IncrementalAnalyzer:
    def analyze_only_changes(self, diff: GitDiff) -> List[AnalysisTarget]:
        """Focus analysis on changed lines and their context"""
        
    def propagate_impact(self, changes: List[Change]) -> List[FileToAnalyze]:
        """Identify files affected by changes"""
```

### Early Termination
```python
class EarlyTermination:
    def should_continue_to_next_layer(self, current_results: LayerResult) -> bool:
        """Skip expensive analysis if early layers are conclusive"""
        
    # Examples:
    # - Skip AI if pattern analysis finds critical security issue
    # - Skip context if pattern analysis shows perfect code
    # - Always run AI if pattern/context results are contradictory
```

## Configuration and Tuning

### Per-Project Customization
```yaml
# .codex.yml
analysis:
  layers:
    pattern:
      enabled: true
      custom_patterns: "./patterns/"
    context:  
      enabled: true
      learn_from_history: true
    ai:
      enabled: "smart"  # always | smart | never
      model: "claude-3.5-sonnet"
      
  voting:
    weights:
      pattern: 0.8
      context: 0.6  
      ai: 0.4
    thresholds:
      commit: 0.7
      block: 0.3
```

### Learning and Adaptation
```python
class AdaptiveTuning:
    def learn_from_feedback(self, commit_hash: str, developer_override: bool):
        """Adjust weights based on developer decisions"""
        
    def update_project_patterns(self, successful_commits: List[Commit]):
        """Learn project-specific good patterns"""
        
    def calibrate_thresholds(self, commit_history: CommitHistory):
        """Optimize thresholds based on historical data"""
```

This multi-factor approach ensures that Codex can provide fast, accurate analysis while scaling the computational cost appropriately based on code complexity and confidence levels.
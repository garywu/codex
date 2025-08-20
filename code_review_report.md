# 🔍 Code Review Report
**Total Issues Found:** 458
## Summary by Severity
- 🔴 **CRITICAL**: 18 issues
- 🟠 **HIGH**: 208 issues
- 🟡 **MEDIUM**: 232 issues

## Detailed Findings

### CRITICAL Issues

#### Security: eval() usage
- **File:** `codex/fix_validation_rules.py:103`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: exec() usage
- **File:** `codex/fix_validation_rules.py:104`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: eval() usage
- **File:** `codex/scan_rules.py:175`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: eval() usage
- **File:** `codex/scan_rules.py:178`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: eval() usage
- **File:** `codex/scan_rules.py:181`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: exec() usage
- **File:** `codex/scan_rules.py:175`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: exec() usage
- **File:** `codex/scan_rules.py:179`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: exec() usage
- **File:** `codex/tools.py:368`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: shell=True
- **File:** `codex/pattern_cli.py:1027`
- **Category:** Security
- **Description:** Command injection risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: exec() usage
- **File:** `codex/portable_tools.py:701`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: eval() usage
- **File:** `codex/code_review_agent.py:192`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: exec() usage
- **File:** `codex/code_review_agent.py:193`
- **Category:** Security
- **Description:** Arbitrary code execution risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: pickle.loads()
- **File:** `codex/code_review_agent.py:194`
- **Category:** Security
- **Description:** Deserialization vulnerability
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: shell=True
- **File:** `codex/code_review_agent.py:195`
- **Category:** Security
- **Description:** Command injection risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: os.system()
- **File:** `codex/code_review_agent.py:196`
- **Category:** Security
- **Description:** Command injection risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: SQL string formatting
- **File:** `codex/code_review_agent.py:197`
- **Category:** Security
- **Description:** SQL injection risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: os.system()
- **File:** `codex/batch_fixer.py:121`
- **Category:** Security
- **Description:** Command injection risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

#### Security: os.system()
- **File:** `codex/batch_fixer.py:122`
- **Category:** Security
- **Description:** Command injection risk
- **Suggestion:** Use safe alternatives or add input validation
- **Impact:** Potential security vulnerability

### HIGH Issues

#### God object anti-pattern
- **File:** `codex/pattern_models.py:86`
- **Category:** Architecture
- **Description:** Class 'Pattern' has too many attributes (21)
- **Suggestion:** Apply Single Responsibility Principle
- **Impact:** Violates SOLID principles

#### Missing test coverage
- **File:** `codex/pattern_models.py:1`
- **Category:** Testing
- **Description:** File has 7 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/safe_fixer.py:1`
- **Category:** Testing
- **Description:** File has 16 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/fix_audit_trail.py:102`
- **Category:** Type Safety
- **Description:** Function '_init_database' lacks return type annotation
- **Suggestion:** Add return type hint: def _init_database(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _init_database(self):`

#### Missing return type annotation
- **File:** `codex/fix_audit_trail.py:243`
- **Category:** Type Safety
- **Description:** Function 'update_validation_results' lacks return type annotation
- **Suggestion:** Add return type hint: def update_validation_results(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def update_validation_results(`

#### Missing return type annotation
- **File:** `codex/fix_audit_trail.py:278`
- **Category:** Type Safety
- **Description:** Function 'record_decision' lacks return type annotation
- **Suggestion:** Add return type hint: def record_decision(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def record_decision(self, audit_id: str, decision: FixDecision, reason: str, user_id: str | None = None):`

#### Missing return type annotation
- **File:** `codex/fix_audit_trail.py:297`
- **Category:** Type Safety
- **Description:** Function 'record_application' lacks return type annotation
- **Suggestion:** Add return type hint: def record_application(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def record_application(self, audit_id: str, file_hash_after: str, execution_time_ms: float, lines_changed: int):`

#### Missing return type annotation
- **File:** `codex/fix_audit_trail.py:317`
- **Category:** Type Safety
- **Description:** Function 'record_rollback' lacks return type annotation
- **Suggestion:** Add return type hint: def record_rollback(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def record_rollback(self, audit_id: str, reason: str):`

#### Missing return type annotation
- **File:** `codex/fix_audit_trail.py:336`
- **Category:** Type Safety
- **Description:** Function '_save_entry' lacks return type annotation
- **Suggestion:** Add return type hint: def _save_entry(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _save_entry(self, entry: FixAuditEntry):`

#### Missing return type annotation
- **File:** `codex/fix_audit_trail.py:494`
- **Category:** Type Safety
- **Description:** Function 'export_audit_report' lacks return type annotation
- **Suggestion:** Add return type hint: def export_audit_report(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def export_audit_report(`

#### God object anti-pattern
- **File:** `codex/fix_audit_trail.py:41`
- **Category:** Architecture
- **Description:** Class 'FixAuditEntry' has too many attributes (27)
- **Suggestion:** Apply Single Responsibility Principle
- **Impact:** Violates SOLID principles

#### Missing test coverage
- **File:** `codex/fix_audit_trail.py:1`
- **Category:** Testing
- **Description:** File has 10 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### High cyclomatic complexity
- **File:** `codex/scanner.py:270`
- **Category:** Complexity
- **Description:** Function '_check_pattern_simple' has complexity of 24
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/scanner.py:1`
- **Category:** Testing
- **Description:** File has 2 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:393`
- **Category:** Type Safety
- **Description:** Function 'main' lacks return type annotation
- **Suggestion:** Add return type hint: def main(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def main():`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:114`
- **Category:** Type Safety
- **Description:** Function '_check_backup_dirs' lacks return type annotation
- **Suggestion:** Add return type hint: def _check_backup_dirs(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _check_backup_dirs(self, results: dict):`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:134`
- **Category:** Type Safety
- **Description:** Function '_check_root_organization' lacks return type annotation
- **Suggestion:** Add return type hint: def _check_root_organization(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _check_root_organization(self, results: dict):`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:187`
- **Category:** Type Safety
- **Description:** Function '_check_duplicates' lacks return type annotation
- **Suggestion:** Add return type hint: def _check_duplicates(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _check_duplicates(self, results: dict):`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:210`
- **Category:** Type Safety
- **Description:** Function '_check_missing_dirs' lacks return type annotation
- **Suggestion:** Add return type hint: def _check_missing_dirs(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _check_missing_dirs(self, results: dict):`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:230`
- **Category:** Type Safety
- **Description:** Function '_check_old_files' lacks return type annotation
- **Suggestion:** Add return type hint: def _check_old_files(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _check_old_files(self, results: dict):`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:248`
- **Category:** Type Safety
- **Description:** Function '_check_test_organization' lacks return type annotation
- **Suggestion:** Add return type hint: def _check_test_organization(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _check_test_organization(self, results: dict):`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:268`
- **Category:** Type Safety
- **Description:** Function '_generate_recommendations' lacks return type annotation
- **Suggestion:** Add return type hint: def _generate_recommendations(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _generate_recommendations(self, results: dict):`

#### Missing return type annotation
- **File:** `codex/organization_scanner.py:320`
- **Category:** Type Safety
- **Description:** Function 'print_report' lacks return type annotation
- **Suggestion:** Add return type hint: def print_report(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_report(self, results: dict):`

#### High cyclomatic complexity
- **File:** `codex/organization_scanner.py:320`
- **Category:** Complexity
- **Description:** Function 'print_report' has complexity of 20
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/organization_scanner.py:1`
- **Category:** Testing
- **Description:** File has 3 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/config.py:1`
- **Category:** Testing
- **Description:** File has 5 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### God object anti-pattern
- **File:** `codex/models.py:57`
- **Category:** Architecture
- **Description:** Class 'Pattern' has too many attributes (18)
- **Suggestion:** Apply Single Responsibility Principle
- **Impact:** Violates SOLID principles

#### Missing return type annotation
- **File:** `codex/fix_validation_rules.py:171`
- **Category:** Type Safety
- **Description:** Function 'validate_fix_safety_rules' lacks return type annotation
- **Suggestion:** Add return type hint: def validate_fix_safety_rules(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def validate_fix_safety_rules():`

#### Missing test coverage
- **File:** `codex/fix_validation_rules.py:1`
- **Category:** Testing
- **Description:** File has 4 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/negative_space_patterns.py:465`
- **Category:** Type Safety
- **Description:** Function 'integrate_negative_space_with_scanner' lacks return type annotation
- **Suggestion:** Add return type hint: def integrate_negative_space_with_scanner(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def integrate_negative_space_with_scanner():`

#### Missing test coverage
- **File:** `codex/negative_space_patterns.py:1`
- **Category:** Testing
- **Description:** File has 5 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/unified_database.py:184`
- **Category:** Type Safety
- **Description:** Function 'get_connection' lacks return type annotation
- **Suggestion:** Add return type hint: def get_connection(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def get_connection(self):`

#### Missing test coverage
- **File:** `codex/unified_database.py:1`
- **Category:** Testing
- **Description:** File has 13 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/scan_rules.py:1`
- **Category:** Testing
- **Description:** File has 5 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/scan_discovery.py:1`
- **Category:** Testing
- **Description:** File has 6 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### High cyclomatic complexity
- **File:** `codex/recommendation_engine.py:85`
- **Category:** Complexity
- **Description:** Function '_analyze_file_context' has complexity of 18
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/recommendation_engine.py:1`
- **Category:** Testing
- **Description:** File has 2 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/tools.py:1`
- **Category:** Testing
- **Description:** File has 1 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/ai_sqlite_query.py:1`
- **Category:** Testing
- **Description:** File has 3 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:38`
- **Category:** Type Safety
- **Description:** Function 'add' lacks return type annotation
- **Suggestion:** Add return type hint: def add(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def add(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:138`
- **Category:** Type Safety
- **Description:** Function 'list' lacks return type annotation
- **Suggestion:** Add return type hint: def list(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def list(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:244`
- **Category:** Type Safety
- **Description:** Function 'show' lacks return type annotation
- **Suggestion:** Add return type hint: def show(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def show(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:303`
- **Category:** Type Safety
- **Description:** Function 'update' lacks return type annotation
- **Suggestion:** Add return type hint: def update(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def update(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:377`
- **Category:** Type Safety
- **Description:** Function 'delete' lacks return type annotation
- **Suggestion:** Add return type hint: def delete(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def delete(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:419`
- **Category:** Type Safety
- **Description:** Function 'import_file' lacks return type annotation
- **Suggestion:** Add return type hint: def import_file(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def import_file(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:514`
- **Category:** Type Safety
- **Description:** Function 'search' lacks return type annotation
- **Suggestion:** Add return type hint: def search(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def search(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:559`
- **Category:** Type Safety
- **Description:** Function 'bulk' lacks return type annotation
- **Suggestion:** Add return type hint: def bulk(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def bulk(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:863`
- **Category:** Type Safety
- **Description:** Function 'ai_assist' lacks return type annotation
- **Suggestion:** Add return type hint: def ai_assist(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def ai_assist(`

#### Missing return type annotation
- **File:** `codex/pattern_cli.py:1035`
- **Category:** Type Safety
- **Description:** Function 'stats' lacks return type annotation
- **Suggestion:** Add return type hint: def stats(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def stats(`

#### High cyclomatic complexity
- **File:** `codex/pattern_cli.py:419`
- **Category:** Complexity
- **Description:** Function 'import_file' has complexity of 17
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/pattern_cli.py:559`
- **Category:** Complexity
- **Description:** Function 'bulk' has complexity of 53
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/pattern_cli.py:863`
- **Category:** Complexity
- **Description:** Function 'ai_assist' has complexity of 22
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/pattern_cli.py:1`
- **Category:** Testing
- **Description:** File has 10 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:41`
- **Category:** Type Safety
- **Description:** Function '_initialize_database' lacks return type annotation
- **Suggestion:** Add return type hint: def _initialize_database(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _initialize_database(self):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:55`
- **Category:** Type Safety
- **Description:** Function '_create_tables' lacks return type annotation
- **Suggestion:** Add return type hint: def _create_tables(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _create_tables(self):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:159`
- **Category:** Type Safety
- **Description:** Function '_create_fts_tables' lacks return type annotation
- **Suggestion:** Add return type hint: def _create_fts_tables(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _create_fts_tables(self):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:191`
- **Category:** Type Safety
- **Description:** Function '_create_indexes' lacks return type annotation
- **Suggestion:** Add return type hint: def _create_indexes(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _create_indexes(self):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:242`
- **Category:** Type Safety
- **Description:** Function '_create_scan_session' lacks return type annotation
- **Suggestion:** Add return type hint: def _create_scan_session(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _create_scan_session(self, repo_path: Path):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:360`
- **Category:** Type Safety
- **Description:** Function '_write_violation' lacks return type annotation
- **Suggestion:** Add return type hint: def _write_violation(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _write_violation(self, violation: PatternMatch, file_id: str):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:569`
- **Category:** Type Safety
- **Description:** Function '_write_insights' lacks return type annotation
- **Suggestion:** Add return type hint: def _write_insights(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _write_insights(self, insights: list[dict[str, Any]]):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:614`
- **Category:** Type Safety
- **Description:** Function '_finalize_scan_session' lacks return type annotation
- **Suggestion:** Add return type hint: def _finalize_scan_session(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _finalize_scan_session(self, files_scanned: int, total_violations: int):`

#### Missing return type annotation
- **File:** `codex/sqlite_scanner.py:632`
- **Category:** Type Safety
- **Description:** Function 'close' lacks return type annotation
- **Suggestion:** Add return type hint: def close(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def close(self):`

#### Missing test coverage
- **File:** `codex/sqlite_scanner.py:1`
- **Category:** Testing
- **Description:** File has 1 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/project_config.py:54`
- **Category:** Type Safety
- **Description:** Function '__post_init__' lacks return type annotation
- **Suggestion:** Add return type hint: def __post_init__(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def __post_init__(self):`

#### Missing return type annotation
- **File:** `codex/project_config.py:74`
- **Category:** Type Safety
- **Description:** Function 'ensure_config_dir' lacks return type annotation
- **Suggestion:** Add return type hint: def ensure_config_dir(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def ensure_config_dir(self):`

#### Missing return type annotation
- **File:** `codex/project_config.py:143`
- **Category:** Type Safety
- **Description:** Function 'save_config' lacks return type annotation
- **Suggestion:** Add return type hint: def save_config(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def save_config(self, config: ProjectConfig | None = None):`

#### Missing return type annotation
- **File:** `codex/project_config.py:262`
- **Category:** Type Safety
- **Description:** Function 'clean_cache' lacks return type annotation
- **Suggestion:** Add return type hint: def clean_cache(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def clean_cache(self, older_than_hours: int | None = None):`

#### Missing return type annotation
- **File:** `codex/project_config.py:300`
- **Category:** Type Safety
- **Description:** Function 'update_setting' lacks return type annotation
- **Suggestion:** Add return type hint: def update_setting(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def update_setting(self, key: str, value: Any):`

#### God object anti-pattern
- **File:** `codex/project_config.py:21`
- **Category:** Architecture
- **Description:** Class 'ProjectConfig' has too many attributes (16)
- **Suggestion:** Apply Single Responsibility Principle
- **Impact:** Violates SOLID principles

#### Missing test coverage
- **File:** `codex/project_config.py:1`
- **Category:** Testing
- **Description:** File has 11 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/scan_cli.py:41`
- **Category:** Type Safety
- **Description:** Function 'run' lacks return type annotation
- **Suggestion:** Add return type hint: def run(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def run(`

#### Missing return type annotation
- **File:** `codex/scan_cli.py:144`
- **Category:** Type Safety
- **Description:** Function 'list' lacks return type annotation
- **Suggestion:** Add return type hint: def list(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def list(`

#### Missing return type annotation
- **File:** `codex/scan_cli.py:203`
- **Category:** Type Safety
- **Description:** Function 'history' lacks return type annotation
- **Suggestion:** Add return type hint: def history(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def history(`

#### Missing return type annotation
- **File:** `codex/scan_cli.py:255`
- **Category:** Type Safety
- **Description:** Function 'trends' lacks return type annotation
- **Suggestion:** Add return type hint: def trends(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def trends(`

#### Missing return type annotation
- **File:** `codex/scan_cli.py:287`
- **Category:** Type Safety
- **Description:** Function 'explain' lacks return type annotation
- **Suggestion:** Add return type hint: def explain(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def explain(`

#### Missing return type annotation
- **File:** `codex/scan_cli.py:364`
- **Category:** Type Safety
- **Description:** Function '_output_results' lacks return type annotation
- **Suggestion:** Add return type hint: def _output_results(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _output_results(session, format: OutputFormat, quiet: bool, verbose: bool):`

#### High cyclomatic complexity
- **File:** `codex/scan_cli.py:41`
- **Category:** Complexity
- **Description:** Function 'run' has complexity of 17
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/scan_cli.py:1`
- **Category:** Testing
- **Description:** File has 5 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/fix_context_analyzer.py:1`
- **Category:** Testing
- **Description:** File has 5 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:549`
- **Category:** Type Safety
- **Description:** Function 'main' lacks return type annotation
- **Suggestion:** Add return type hint: def main(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def main():`

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:85`
- **Category:** Type Safety
- **Description:** Function '_init_database' lacks return type annotation
- **Suggestion:** Add return type hint: def _init_database(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _init_database(self):`

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:243`
- **Category:** Type Safety
- **Description:** Function 'record_violation' lacks return type annotation
- **Suggestion:** Add return type hint: def record_violation(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def record_violation(self, scan_id: str, violation: dict):`

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:403`
- **Category:** Type Safety
- **Description:** Function 'mark_violations_fixed' lacks return type annotation
- **Suggestion:** Add return type hint: def mark_violations_fixed(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def mark_violations_fixed(self, scan_id: str, file_path: str, pattern_names: list[str]):`

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:417`
- **Category:** Type Safety
- **Description:** Function 'print_summary' lacks return type annotation
- **Suggestion:** Add return type hint: def print_summary(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_summary(self):`

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:452`
- **Category:** Type Safety
- **Description:** Function 'print_history' lacks return type annotation
- **Suggestion:** Add return type hint: def print_history(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_history(self, limit: int = 10):`

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:480`
- **Category:** Type Safety
- **Description:** Function 'print_progress' lacks return type annotation
- **Suggestion:** Add return type hint: def print_progress(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_progress(self):`

#### Missing return type annotation
- **File:** `codex/scan_tracker.py:544`
- **Category:** Type Safety
- **Description:** Function 'close' lacks return type annotation
- **Suggestion:** Add return type hint: def close(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def close(self):`

#### Bare except clause
- **File:** `codex/scan_tracker.py:185`
- **Category:** Error Handling
- **Description:** Catches all exceptions including SystemExit and KeyboardInterrupt
- **Suggestion:** Use 'except Exception:' or specific exception types
- **Impact:** Can hide critical errors and make debugging difficult

#### Bare except clause
- **File:** `codex/scan_tracker.py:516`
- **Category:** Error Handling
- **Description:** Catches all exceptions including SystemExit and KeyboardInterrupt
- **Suggestion:** Use 'except Exception:' or specific exception types
- **Impact:** Can hide critical errors and make debugging difficult

#### Bare except clause
- **File:** `codex/scan_tracker.py:526`
- **Category:** Error Handling
- **Description:** Catches all exceptions including SystemExit and KeyboardInterrupt
- **Suggestion:** Use 'except Exception:' or specific exception types
- **Impact:** Can hide critical errors and make debugging difficult

#### Missing test coverage
- **File:** `codex/scan_tracker.py:1`
- **Category:** Testing
- **Description:** File has 14 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/improved_scanner.py:270`
- **Category:** Type Safety
- **Description:** Function 'compare_scanners' lacks return type annotation
- **Suggestion:** Add return type hint: def compare_scanners(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def compare_scanners(file_path: str, content: str):`

#### Missing return type annotation
- **File:** `codex/improved_scanner.py:288`
- **Category:** Type Safety
- **Description:** Function 'test_improved_scanner' lacks return type annotation
- **Suggestion:** Add return type hint: def test_improved_scanner(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def test_improved_scanner():`

#### Missing return type annotation
- **File:** `codex/improved_scanner.py:29`
- **Category:** Type Safety
- **Description:** Function '__post_init__' lacks return type annotation
- **Suggestion:** Add return type hint: def __post_init__(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def __post_init__(self):`

#### Bare except clause
- **File:** `codex/improved_scanner.py:42`
- **Category:** Error Handling
- **Description:** Catches all exceptions including SystemExit and KeyboardInterrupt
- **Suggestion:** Use 'except Exception:' or specific exception types
- **Impact:** Can hide critical errors and make debugging difficult

#### High cyclomatic complexity
- **File:** `codex/improved_scanner.py:86`
- **Category:** Complexity
- **Description:** Function 'check_cors_pattern' has complexity of 16
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/improved_scanner.py:202`
- **Category:** Complexity
- **Description:** Function 'check_structured_logging' has complexity of 16
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/improved_scanner.py:1`
- **Category:** Testing
- **Description:** File has 8 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/console_types.py:1`
- **Category:** Testing
- **Description:** File has 4 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/ai_query.py:1`
- **Category:** Testing
- **Description:** File has 6 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/ensemble_scanner.py:630`
- **Category:** Type Safety
- **Description:** Function 'test_ensemble_scanner' lacks return type annotation
- **Suggestion:** Add return type hint: def test_ensemble_scanner(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def test_ensemble_scanner():`

#### Missing return type annotation
- **File:** `codex/ensemble_scanner.py:119`
- **Category:** Type Safety
- **Description:** Function 'update_statistics' lacks return type annotation
- **Suggestion:** Add return type hint: def update_statistics(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def update_statistics(self, violations_found: int, execution_time_ms: float):`

#### Missing return type annotation
- **File:** `codex/ensemble_scanner.py:329`
- **Category:** Type Safety
- **Description:** Function '_init_statistics_db' lacks return type annotation
- **Suggestion:** Add return type hint: def _init_statistics_db(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _init_statistics_db(self):`

#### Missing return type annotation
- **File:** `codex/ensemble_scanner.py:364`
- **Category:** Type Safety
- **Description:** Function 'register_pattern' lacks return type annotation
- **Suggestion:** Add return type hint: def register_pattern(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def register_pattern(self, pattern_name: str, rules: list[Rule]):`

#### Missing return type annotation
- **File:** `codex/ensemble_scanner.py:447`
- **Category:** Type Safety
- **Description:** Function '_save_statistics' lacks return type annotation
- **Suggestion:** Add return type hint: def _save_statistics(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _save_statistics(self):`

#### Missing return type annotation
- **File:** `codex/ensemble_scanner.py:475`
- **Category:** Type Safety
- **Description:** Function 'record_feedback' lacks return type annotation
- **Suggestion:** Add return type hint: def record_feedback(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def record_feedback(`

#### Bare except clause
- **File:** `codex/ensemble_scanner.py:59`
- **Category:** Error Handling
- **Description:** Catches all exceptions including SystemExit and KeyboardInterrupt
- **Suggestion:** Use 'except Exception:' or specific exception types
- **Impact:** Can hide critical errors and make debugging difficult

#### Missing test coverage
- **File:** `codex/ensemble_scanner.py:1`
- **Category:** Testing
- **Description:** File has 17 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/violation_analysis.py:424`
- **Category:** Type Safety
- **Description:** Function 'main' lacks return type annotation
- **Suggestion:** Add return type hint: def main(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def main():`

#### Missing return type annotation
- **File:** `codex/violation_analysis.py:38`
- **Category:** Type Safety
- **Description:** Function '__post_init__' lacks return type annotation
- **Suggestion:** Add return type hint: def __post_init__(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def __post_init__(self):`

#### Missing return type annotation
- **File:** `codex/violation_analysis.py:198`
- **Category:** Type Safety
- **Description:** Function 'print_location_analysis' lacks return type annotation
- **Suggestion:** Add return type hint: def print_location_analysis(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_location_analysis(self):`

#### Missing return type annotation
- **File:** `codex/violation_analysis.py:264`
- **Category:** Type Safety
- **Description:** Function 'print_category_analysis' lacks return type annotation
- **Suggestion:** Add return type hint: def print_category_analysis(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_category_analysis(self):`

#### Missing return type annotation
- **File:** `codex/violation_analysis.py:309`
- **Category:** Type Safety
- **Description:** Function 'print_cross_analysis' lacks return type annotation
- **Suggestion:** Add return type hint: def print_cross_analysis(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_cross_analysis(self):`

#### Missing return type annotation
- **File:** `codex/violation_analysis.py:371`
- **Category:** Type Safety
- **Description:** Function 'print_summary' lacks return type annotation
- **Suggestion:** Add return type hint: def print_summary(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_summary(self):`

#### Missing return type annotation
- **File:** `codex/violation_analysis.py:392`
- **Category:** Type Safety
- **Description:** Function 'export_json' lacks return type annotation
- **Suggestion:** Add return type hint: def export_json(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def export_json(self, output_path: Path):`

#### Bare except clause
- **File:** `codex/violation_analysis.py:137`
- **Category:** Error Handling
- **Description:** Catches all exceptions including SystemExit and KeyboardInterrupt
- **Suggestion:** Use 'except Exception:' or specific exception types
- **Impact:** Can hide critical errors and make debugging difficult

#### Missing test coverage
- **File:** `codex/violation_analysis.py:1`
- **Category:** Testing
- **Description:** File has 8 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/scan_registry.py:55`
- **Category:** Type Safety
- **Description:** Function '__post_init__' lacks return type annotation
- **Suggestion:** Add return type hint: def __post_init__(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def __post_init__(self):`

#### Missing test coverage
- **File:** `codex/scan_registry.py:1`
- **Category:** Testing
- **Description:** File has 5 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/ensemble_integration.py:34`
- **Category:** Type Safety
- **Description:** Function '_register_all_patterns' lacks return type annotation
- **Suggestion:** Add return type hint: def _register_all_patterns(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _register_all_patterns(self):`

#### Missing return type annotation
- **File:** `codex/ensemble_integration.py:130`
- **Category:** Type Safety
- **Description:** Function '_get_ast_condition_function' lacks return type annotation
- **Suggestion:** Add return type hint: def _get_ast_condition_function(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _get_ast_condition_function(self, condition_name: str):`

#### Missing return type annotation
- **File:** `codex/ensemble_integration.py:145`
- **Category:** Type Safety
- **Description:** Function '_get_context_check_function' lacks return type annotation
- **Suggestion:** Add return type hint: def _get_context_check_function(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _get_context_check_function(self, rule_id: str):`

#### Missing return type annotation
- **File:** `codex/ensemble_integration.py:161`
- **Category:** Type Safety
- **Description:** Function '_register_fallback_patterns' lacks return type annotation
- **Suggestion:** Add return type hint: def _register_fallback_patterns(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _register_fallback_patterns(self):`

#### Class too complex
- **File:** `codex/ensemble_integration.py:24`
- **Category:** Architecture
- **Description:** Class 'IntegratedEnsembleScanner' has 22 methods
- **Suggestion:** Consider splitting into smaller, focused classes
- **Impact:** Difficult to maintain and test

#### Missing test coverage
- **File:** `codex/ensemble_integration.py:1`
- **Category:** Testing
- **Description:** File has 2 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/linting_8020_patterns.py:1`
- **Category:** Testing
- **Description:** File has 3 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/cli.py:2056`
- **Category:** Type Safety
- **Description:** Function 'install_mcp' lacks return type annotation
- **Suggestion:** Add return type hint: def install_mcp(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def install_mcp(`

#### Missing return type annotation
- **File:** `codex/cli.py:2202`
- **Category:** Type Safety
- **Description:** Function 'uninstall_mcp' lacks return type annotation
- **Suggestion:** Add return type hint: def uninstall_mcp(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def uninstall_mcp(`

#### Missing return type annotation
- **File:** `codex/cli.py:2243`
- **Category:** Type Safety
- **Description:** Function 'mcp_status' lacks return type annotation
- **Suggestion:** Add return type hint: def mcp_status(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def mcp_status():`

#### Missing return type annotation
- **File:** `codex/cli.py:2308`
- **Category:** Type Safety
- **Description:** Function 'learn_pattern' lacks return type annotation
- **Suggestion:** Add return type hint: def learn_pattern(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def learn_pattern(`

#### Missing return type annotation
- **File:** `codex/cli.py:2400`
- **Category:** Type Safety
- **Description:** Function '_interactive_pattern_creation' lacks return type annotation
- **Suggestion:** Add return type hint: def _interactive_pattern_creation(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _interactive_pattern_creation():`

#### Missing return type annotation
- **File:** `codex/cli.py:2493`
- **Category:** Type Safety
- **Description:** Function 'pattern_feedback' lacks return type annotation
- **Suggestion:** Add return type hint: def pattern_feedback(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def pattern_feedback(`

#### Missing return type annotation
- **File:** `codex/cli.py:2549`
- **Category:** Type Safety
- **Description:** Function 'scan_history' lacks return type annotation
- **Suggestion:** Add return type hint: def scan_history(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def scan_history(`

#### Missing return type annotation
- **File:** `codex/cli.py:2582`
- **Category:** Type Safety
- **Description:** Function 'scan_report' lacks return type annotation
- **Suggestion:** Add return type hint: def scan_report(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def scan_report(`

#### Missing return type annotation
- **File:** `codex/cli.py:2614`
- **Category:** Type Safety
- **Description:** Function 'scan_progress' lacks return type annotation
- **Suggestion:** Add return type hint: def scan_progress(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def scan_progress():`

#### Missing return type annotation
- **File:** `codex/cli.py:2635`
- **Category:** Type Safety
- **Description:** Function 'analyze_violations' lacks return type annotation
- **Suggestion:** Add return type hint: def analyze_violations(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def analyze_violations(`

#### High cyclomatic complexity
- **File:** `codex/cli.py:120`
- **Category:** Complexity
- **Description:** Function 'scan' has complexity of 57
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:1383`
- **Category:** Complexity
- **Description:** Function 'startup_status' has complexity of 18
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:1642`
- **Category:** Complexity
- **Description:** Function 'any_repo' has complexity of 17
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:2056`
- **Category:** Complexity
- **Description:** Function 'install_mcp' has complexity of 21
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/cli.py:1`
- **Category:** Testing
- **Description:** File has 44 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/config_cli.py:26`
- **Category:** Type Safety
- **Description:** Function 'show' lacks return type annotation
- **Suggestion:** Add return type hint: def show(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def show(`

#### Missing return type annotation
- **File:** `codex/config_cli.py:67`
- **Category:** Type Safety
- **Description:** Function 'sources' lacks return type annotation
- **Suggestion:** Add return type hint: def sources(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def sources():`

#### Missing return type annotation
- **File:** `codex/config_cli.py:117`
- **Category:** Type Safety
- **Description:** Function 'init' lacks return type annotation
- **Suggestion:** Add return type hint: def init(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def init():`

#### Missing return type annotation
- **File:** `codex/config_cli.py:186`
- **Category:** Type Safety
- **Description:** Function 'validate' lacks return type annotation
- **Suggestion:** Add return type hint: def validate(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def validate():`

#### Missing return type annotation
- **File:** `codex/config_cli.py:257`
- **Category:** Type Safety
- **Description:** Function 'list_settings' lacks return type annotation
- **Suggestion:** Add return type hint: def list_settings(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def list_settings():`

#### Missing return type annotation
- **File:** `codex/config_cli.py:288`
- **Category:** Type Safety
- **Description:** Function 'add_exclude' lacks return type annotation
- **Suggestion:** Add return type hint: def add_exclude(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def add_exclude(pattern: str):`

#### Missing return type annotation
- **File:** `codex/config_cli.py:372`
- **Category:** Type Safety
- **Description:** Function '_save_codex_toml' lacks return type annotation
- **Suggestion:** Add return type hint: def _save_codex_toml(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _save_codex_toml(config: dict[str, Any]):`

#### Missing return type annotation
- **File:** `codex/config_cli.py:396`
- **Category:** Type Safety
- **Description:** Function '_save_pyproject_toml' lacks return type annotation
- **Suggestion:** Add return type hint: def _save_pyproject_toml(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _save_pyproject_toml(config: dict[str, Any]):`

#### Missing return type annotation
- **File:** `codex/config_cli.py:422`
- **Category:** Type Safety
- **Description:** Function '_save_user_config' lacks return type annotation
- **Suggestion:** Add return type hint: def _save_user_config(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _save_user_config(config: dict[str, Any]):`

#### Missing test coverage
- **File:** `codex/config_cli.py:1`
- **Category:** Testing
- **Description:** File has 6 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### High cyclomatic complexity
- **File:** `codex/scan_context.py:139`
- **Category:** Complexity
- **Description:** Function 'record_decision' has complexity of 18
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/scan_context.py:1`
- **Category:** Testing
- **Description:** File has 18 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/scan_report_generator.py:427`
- **Category:** Type Safety
- **Description:** Function 'main' lacks return type annotation
- **Suggestion:** Add return type hint: def main(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def main():`

#### Missing return type annotation
- **File:** `codex/scan_report_generator.py:34`
- **Category:** Type Safety
- **Description:** Function '_setup_reporting_infrastructure' lacks return type annotation
- **Suggestion:** Add return type hint: def _setup_reporting_infrastructure(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _setup_reporting_infrastructure(self):`

#### Missing return type annotation
- **File:** `codex/scan_report_generator.py:352`
- **Category:** Type Safety
- **Description:** Function 'print_automatic_report' lacks return type annotation
- **Suggestion:** Add return type hint: def print_automatic_report(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def print_automatic_report(self):`

#### Missing return type annotation
- **File:** `codex/scan_report_generator.py:413`
- **Category:** Type Safety
- **Description:** Function 'export_markdown_report' lacks return type annotation
- **Suggestion:** Add return type hint: def export_markdown_report(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def export_markdown_report(self, output_path: Path):`

#### Missing return type annotation
- **File:** `codex/scan_report_generator.py:422`
- **Category:** Type Safety
- **Description:** Function 'close' lacks return type annotation
- **Suggestion:** Add return type hint: def close(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def close(self):`

#### Missing test coverage
- **File:** `codex/scan_report_generator.py:1`
- **Category:** Testing
- **Description:** File has 7 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/portable_tools.py:1`
- **Category:** Testing
- **Description:** File has 1 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### God object anti-pattern
- **File:** `codex/settings.py:19`
- **Category:** Architecture
- **Description:** Class 'CodexSettings' has too many attributes (21)
- **Suggestion:** Apply Single Responsibility Principle
- **Impact:** Violates SOLID principles

#### Missing test coverage
- **File:** `codex/settings.py:1`
- **Category:** Testing
- **Description:** File has 8 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/code_review_agent.py:1`
- **Category:** Testing
- **Description:** File has 4 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/gitignore_handler.py:117`
- **Category:** Type Safety
- **Description:** Function '_load_gitignore_patterns' lacks return type annotation
- **Suggestion:** Add return type hint: def _load_gitignore_patterns(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _load_gitignore_patterns(self):`

#### Missing return type annotation
- **File:** `codex/gitignore_handler.py:139`
- **Category:** Type Safety
- **Description:** Function '_parse_gitignore_file' lacks return type annotation
- **Suggestion:** Add return type hint: def _parse_gitignore_file(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _parse_gitignore_file(self, gitignore_file: Path):`

#### Missing return type annotation
- **File:** `codex/gitignore_handler.py:161`
- **Category:** Type Safety
- **Description:** Function '_compile_patterns' lacks return type annotation
- **Suggestion:** Add return type hint: def _compile_patterns(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _compile_patterns(self):`

#### Missing test coverage
- **File:** `codex/gitignore_handler.py:1`
- **Category:** Testing
- **Description:** File has 4 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/pattern_extractor.py:1`
- **Category:** Testing
- **Description:** File has 1 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/scan_manager.py:137`
- **Category:** Type Safety
- **Description:** Function '_init_scan_tables' lacks return type annotation
- **Suggestion:** Add return type hint: def _init_scan_tables(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _init_scan_tables(self):`

#### Missing test coverage
- **File:** `codex/scan_manager.py:1`
- **Category:** Testing
- **Description:** File has 3 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/rules_cli.py:30`
- **Category:** Type Safety
- **Description:** Function 'check' lacks return type annotation
- **Suggestion:** Add return type hint: def check(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def check(`

#### Missing return type annotation
- **File:** `codex/rules_cli.py:175`
- **Category:** Type Safety
- **Description:** Function 'list' lacks return type annotation
- **Suggestion:** Add return type hint: def list(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def list(`

#### Missing return type annotation
- **File:** `codex/rules_cli.py:259`
- **Category:** Type Safety
- **Description:** Function 'explain' lacks return type annotation
- **Suggestion:** Add return type hint: def explain(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def explain(`

#### Missing return type annotation
- **File:** `codex/rules_cli.py:289`
- **Category:** Type Safety
- **Description:** Function 'stats' lacks return type annotation
- **Suggestion:** Add return type hint: def stats(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def stats():`

#### High cyclomatic complexity
- **File:** `codex/rules_cli.py:30`
- **Category:** Complexity
- **Description:** Function 'check' has complexity of 30
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/rules_cli.py:1`
- **Category:** Testing
- **Description:** File has 4 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/violation_reporter.py:1`
- **Category:** Testing
- **Description:** File has 7 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/uv_check.py:269`
- **Category:** Type Safety
- **Description:** Function 'check' lacks return type annotation
- **Suggestion:** Add return type hint: def check(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def check(quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output")):`

#### Missing test coverage
- **File:** `codex/uv_check.py:1`
- **Category:** Testing
- **Description:** File has 10 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/mcp_server.py:32`
- **Category:** Type Safety
- **Description:** Function 'setup_logging' lacks return type annotation
- **Suggestion:** Add return type hint: def setup_logging(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def setup_logging():`

#### Missing return type annotation
- **File:** `codex/mcp_server.py:526`
- **Category:** Type Safety
- **Description:** Function 'run_mcp_server' lacks return type annotation
- **Suggestion:** Add return type hint: def run_mcp_server(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def run_mcp_server():`

#### Missing test coverage
- **File:** `codex/mcp_server.py:1`
- **Category:** Testing
- **Description:** File has 2 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### High cyclomatic complexity
- **File:** `codex/batch_fixer.py:134`
- **Category:** Complexity
- **Description:** Function '_fix_print_statements_batch' has complexity of 16
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/batch_fixer.py:183`
- **Category:** Complexity
- **Description:** Function '_fix_import_order_batch' has complexity of 28
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing test coverage
- **File:** `codex/batch_fixer.py:1`
- **Category:** Testing
- **Description:** File has 3 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/python_env_enforcer.py:178`
- **Category:** Type Safety
- **Description:** Function 'ensure_proper_environment' lacks return type annotation
- **Suggestion:** Add return type hint: def ensure_proper_environment(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def ensure_proper_environment():`

#### Missing test coverage
- **File:** `codex/python_env_enforcer.py:1`
- **Category:** Testing
- **Description:** File has 8 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/rules/settings_rules.py:186`
- **Category:** Type Safety
- **Description:** Function 'register_settings_rules' lacks return type annotation
- **Suggestion:** Add return type hint: def register_settings_rules(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def register_settings_rules(registry):`

#### Missing return type annotation
- **File:** `codex/rules/settings_rules.py:109`
- **Category:** Type Safety
- **Description:** Function 'visit_Call' lacks return type annotation
- **Suggestion:** Add return type hint: def visit_Call(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def visit_Call(self, node):`

#### Missing test coverage
- **File:** `codex/rules/settings_rules.py:1`
- **Category:** Testing
- **Description:** File has 4 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/rules/registry.py:1`
- **Category:** Testing
- **Description:** File has 17 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing test coverage
- **File:** `codex/rules/categories.py:1`
- **Category:** Testing
- **Description:** File has 2 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:264`
- **Category:** Type Safety
- **Description:** Function 'register_database_rules' lacks return type annotation
- **Suggestion:** Add return type hint: def register_database_rules(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def register_database_rules(registry):`

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:95`
- **Category:** Type Safety
- **Description:** Function 'visit_With' lacks return type annotation
- **Suggestion:** Add return type hint: def visit_With(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def visit_With(self, node):`

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:101`
- **Category:** Type Safety
- **Description:** Function 'visit_Assign' lacks return type annotation
- **Suggestion:** Add return type hint: def visit_Assign(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def visit_Assign(self, node):`

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:123`
- **Category:** Type Safety
- **Description:** Function '_get_call_name' lacks return type annotation
- **Suggestion:** Add return type hint: def _get_call_name(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _get_call_name(self, call):`

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:219`
- **Category:** Type Safety
- **Description:** Function 'visit_With' lacks return type annotation
- **Suggestion:** Add return type hint: def visit_With(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def visit_With(self, node):`

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:230`
- **Category:** Type Safety
- **Description:** Function 'visit_Call' lacks return type annotation
- **Suggestion:** Add return type hint: def visit_Call(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def visit_Call(self, node):`

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:245`
- **Category:** Type Safety
- **Description:** Function '_is_transaction_context' lacks return type annotation
- **Suggestion:** Add return type hint: def _is_transaction_context(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _is_transaction_context(self, expr):`

#### Missing return type annotation
- **File:** `codex/rules/database_rules.py:252`
- **Category:** Type Safety
- **Description:** Function '_is_session_call' lacks return type annotation
- **Suggestion:** Add return type hint: def _is_session_call(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def _is_session_call(self, value):`

#### Missing test coverage
- **File:** `codex/rules/database_rules.py:1`
- **Category:** Testing
- **Description:** File has 9 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/rules/loader.py:11`
- **Category:** Type Safety
- **Description:** Function 'load_all_rules' lacks return type annotation
- **Suggestion:** Add return type hint: def load_all_rules(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def load_all_rules():`

#### Missing return type annotation
- **File:** `codex/rules/loader.py:125`
- **Category:** Type Safety
- **Description:** Function 'ensure_initialized' lacks return type annotation
- **Suggestion:** Add return type hint: def ensure_initialized(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def ensure_initialized():`

#### Missing test coverage
- **File:** `codex/rules/loader.py:1`
- **Category:** Testing
- **Description:** File has 6 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

#### Missing return type annotation
- **File:** `codex/data/default_patterns.py:165`
- **Category:** Type Safety
- **Description:** Function 'get_default_patterns' lacks return type annotation
- **Suggestion:** Add return type hint: def get_default_patterns(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def get_default_patterns():`

#### Missing return type annotation
- **File:** `codex/data/default_patterns.py:172`
- **Category:** Type Safety
- **Description:** Function 'get_patterns_by_priority' lacks return type annotation
- **Suggestion:** Add return type hint: def get_patterns_by_priority(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def get_patterns_by_priority(priority: str):`

#### Missing return type annotation
- **File:** `codex/data/default_patterns.py:177`
- **Category:** Type Safety
- **Description:** Function 'get_patterns_by_category' lacks return type annotation
- **Suggestion:** Add return type hint: def get_patterns_by_category(...) -> ReturnType:
- **Impact:** Type checking tools cannot verify return type correctness
- **Code:** `def get_patterns_by_category(category: str):`

#### Missing test coverage
- **File:** `codex/data/default_patterns.py:1`
- **Category:** Testing
- **Description:** File has 3 public functions but no tests found
- **Suggestion:** Add unit tests for public functions
- **Impact:** Unverified functionality, potential bugs

### MEDIUM Issues

#### Usage of Any type
- **File:** `codex/pattern_models.py:150`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/pattern_models.py:228`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/pattern_models.py:192`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/pattern_models.py:226`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/pattern_models.py:261`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/pattern_models.py:338`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/safe_fixer.py:206`
- **Category:** Complexity
- **Description:** Function 'apply_fix_safely' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/fix_audit_trail.py:83`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_audit_trail.py:383`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_audit_trail.py:549`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_audit_trail.py:87`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_audit_trail.py:474`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_audit_trail.py:196`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Missing parameter type annotation
- **File:** `codex/scanner.py:595`
- **Category:** Type Safety
- **Description:** Parameter 'project_analysis' in '_generate_negative_space_recommendations' lacks type annotation
- **Suggestion:** Add type hint: project_analysis: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/scanner.py:658`
- **Category:** Type Safety
- **Description:** Parameter 'project_analysis' in '_print_negative_space_analysis' lacks type annotation
- **Suggestion:** Add type hint: project_analysis: TypeName
- **Impact:** Reduces type safety and IDE support

#### Usage of Any type
- **File:** `codex/scanner.py:368`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/scanner.py:270`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/scanner.py:355`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/scanner.py:533`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/scanner.py:30`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config.py:50`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config.py:62`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config.py:12`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config.py:57`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/models.py:71`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/models.py:132`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/models.py:133`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/fix_validation_rules.py:67`
- **Category:** Complexity
- **Description:** Function 'is_fix_safe' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/negative_space_patterns.py:51`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/negative_space_patterns.py:164`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/negative_space_patterns.py:135`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/negative_space_patterns.py:237`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/negative_space_patterns.py:237`
- **Category:** Complexity
- **Description:** Function '_calculate_organization_score' has complexity of 12
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/unified_database.py:477`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/unified_database.py:545`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/unified_database.py:524`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/unified_database.py:582`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/unified_database.py:363`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/unified_database.py:545`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/unified_database.py:552`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/client.py:109`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/client.py:260`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/recommendation_engine.py:59`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/recommendation_engine.py:85`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/recommendation_engine.py:85`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/recommendation_engine.py:142`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/recommendation_engine.py:174`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/recommendation_engine.py:220`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/tools.py:51`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/tools.py:383`
- **Category:** Complexity
- **Description:** Function 'print_results' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:53`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:72`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:101`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:131`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:165`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:196`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:230`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:274`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:317`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:346`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:386`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:410`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:472`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:72`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:101`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:131`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:165`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:196`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:230`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:274`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:317`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:386`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:410`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:424`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:449`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_sqlite_query.py:53`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:128`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:131`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:134`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:373`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:507`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:510`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:859`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/pattern_cli.py:1031`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### List comprehension in loop
- **File:** `codex/pattern_cli.py:634`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### High cyclomatic complexity
- **File:** `codex/pattern_cli.py:138`
- **Category:** Complexity
- **Description:** Function 'list' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/pattern_cli.py:303`
- **Category:** Complexity
- **Description:** Function 'update' has complexity of 12
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/sqlite_scanner.py:439`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/sqlite_scanner.py:498`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/sqlite_scanner.py:569`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/project_config.py:284`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/project_config.py:300`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/project_config.py:310`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/project_config.py:36`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Missing exception chaining
- **File:** `codex/project_config.py:176`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing parameter type annotation
- **File:** `codex/scan_cli.py:364`
- **Category:** Type Safety
- **Description:** Parameter 'session' in '_output_results' lacks type annotation
- **Suggestion:** Add type hint: session: TypeName
- **Impact:** Reduces type safety and IDE support

#### High cyclomatic complexity
- **File:** `codex/scan_cli.py:364`
- **Category:** Complexity
- **Description:** Function '_output_results' has complexity of 15
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:49`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:119`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:267`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:323`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:366`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:547`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:568`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:115`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:164`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:202`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:231`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:108`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:110`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:111`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:285`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:373`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:446`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:118`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:164`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:202`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:231`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:267`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:322`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:366`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:476`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:527`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:547`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_orchestrator.py:589`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/fix_orchestrator.py:231`
- **Category:** Complexity
- **Description:** Function '_validate_safety' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/fix_context_analyzer.py:419`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_context_analyzer.py:370`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/fix_context_analyzer.py:418`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/fix_context_analyzer.py:264`
- **Category:** Complexity
- **Description:** Function 'is_fix_safe_in_context' has complexity of 14
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/fix_context_analyzer.py:390`
- **Category:** Complexity
- **Description:** Function '_check_conflict' has complexity of 13
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/improved_scanner.py:52`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/improved_scanner.py:86`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/improved_scanner.py:134`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/improved_scanner.py:166`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/improved_scanner.py:202`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/improved_scanner.py:249`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/improved_scanner.py:52`
- **Category:** Complexity
- **Description:** Function 'check_mock_pattern' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/ai_query.py:23`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_query.py:63`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_query.py:104`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_query.py:163`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_query.py:167`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_query.py:197`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_query.py:274`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/ai_query.py:84`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Missing parameter type annotation
- **File:** `codex/ensemble_scanner.py:247`
- **Category:** Type Safety
- **Description:** Parameter 'condition_fn' in '__init__' lacks type annotation
- **Suggestion:** Add type hint: condition_fn: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/ensemble_scanner.py:285`
- **Category:** Type Safety
- **Description:** Parameter 'check_fn' in '__init__' lacks type annotation
- **Suggestion:** Add type hint: check_fn: TypeName
- **Impact:** Reduces type safety and IDE support

#### Usage of Any type
- **File:** `codex/ensemble_scanner.py:84`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### List comprehension in loop
- **File:** `codex/ensemble_scanner.py:373`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### List comprehension in loop
- **File:** `codex/ensemble_scanner.py:401`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### High cyclomatic complexity
- **File:** `codex/violation_analysis.py:198`
- **Category:** Complexity
- **Description:** Function 'print_location_analysis' has complexity of 12
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing parameter type annotation
- **File:** `codex/ensemble_integration.py:293`
- **Category:** Type Safety
- **Description:** Parameter 'node' in '_check_cors_assignment' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/ensemble_integration.py:353`
- **Category:** Type Safety
- **Description:** Parameter 'node' in '_check_subprocess_pip' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/ensemble_integration.py:377`
- **Category:** Type Safety
- **Description:** Parameter 'node' in '_check_print_statement' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/ensemble_integration.py:384`
- **Category:** Type Safety
- **Description:** Parameter 'node' in '_check_basic_logging' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Usage of Any type
- **File:** `codex/ensemble_integration.py:545`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/ensemble_integration.py:55`
- **Category:** Complexity
- **Description:** Function '_convert_db_rules_to_ensemble' has complexity of 12
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/ensemble_integration.py:353`
- **Category:** Complexity
- **Description:** Function '_check_subprocess_pip' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/linting_8020_patterns.py:22`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Missing exception chaining
- **File:** `codex/cli.py:1873`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2050`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2239`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2397`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2545`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:1201`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:1266`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:1347`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2136`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2139`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2198`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2665`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:1303`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:1379`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:2090`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### Missing exception chaining
- **File:** `codex/cli.py:1956`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### List comprehension in loop
- **File:** `codex/cli.py:640`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### List comprehension in loop
- **File:** `codex/cli.py:640`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### List comprehension in loop
- **File:** `codex/cli.py:660`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### High cyclomatic complexity
- **File:** `codex/cli.py:432`
- **Category:** Complexity
- **Description:** Function 'ci' has complexity of 15
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:572`
- **Category:** Complexity
- **Description:** Function 'fix_safe' has complexity of 13
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:1011`
- **Category:** Complexity
- **Description:** Function 'explain' has complexity of 13
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:1208`
- **Category:** Complexity
- **Description:** Function 'install_startup' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:1312`
- **Category:** Complexity
- **Description:** Function 'uninstall_startup' has complexity of 12
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:1804`
- **Category:** Complexity
- **Description:** Function 'query_database' has complexity of 12
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/cli.py:1912`
- **Category:** Complexity
- **Description:** Function 'config_cmd' has complexity of 13
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/config_cli.py:356`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config_cli.py:321`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config_cli.py:372`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config_cli.py:396`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/config_cli.py:422`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/config_cli.py:186`
- **Category:** Complexity
- **Description:** Function 'validate' has complexity of 15
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing parameter type annotation
- **File:** `codex/scan_context.py:445`
- **Category:** Type Safety
- **Description:** Parameter 'console' in 'print_decision_summary' lacks type annotation
- **Suggestion:** Add type hint: console: TypeName
- **Impact:** Reduces type safety and IDE support

#### Usage of Any type
- **File:** `codex/scan_context.py:40`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/scan_context.py:361`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/scan_context.py:94`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/scan_context.py:323`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/portable_tools.py:412`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/portable_tools.py:717`
- **Category:** Complexity
- **Description:** Function 'print_results' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### List comprehension in loop
- **File:** `codex/code_review_agent.py:252`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### List comprehension in loop
- **File:** `codex/code_review_agent.py:252`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### High cyclomatic complexity
- **File:** `codex/code_review_agent.py:107`
- **Category:** Complexity
- **Description:** Function '_check_type_safety' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/pattern_importer.py:19`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/pattern_importer.py:165`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### List comprehension in loop
- **File:** `codex/gitignore_handler.py:309`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### Usage of Any type
- **File:** `codex/pattern_extractor.py:31`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/pattern_extractor.py:185`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### High cyclomatic complexity
- **File:** `codex/pattern_extractor.py:31`
- **Category:** Complexity
- **Description:** Function '_extract_from_main_format' has complexity of 13
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Missing exception chaining
- **File:** `codex/rules_cli.py:204`
- **Category:** Error Handling
- **Description:** Re-raising without 'from' loses original traceback
- **Suggestion:** Use 'raise NewException(...) from e'
- **Impact:** Loss of debugging information

#### High cyclomatic complexity
- **File:** `codex/rules_cli.py:175`
- **Category:** Complexity
- **Description:** Function 'list' has complexity of 13
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/violation_reporter.py:153`
- **Category:** Complexity
- **Description:** Function 'print_summary' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### High cyclomatic complexity
- **File:** `codex/uv_check.py:185`
- **Category:** Complexity
- **Description:** Function 'run_all_checks' has complexity of 13
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

#### Usage of Any type
- **File:** `codex/mcp_server.py:185`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### List comprehension in loop
- **File:** `codex/batch_fixer.py:301`
- **Category:** Performance
- **Description:** Creating lists in loops can be inefficient
- **Suggestion:** Consider using generator or accumulating results
- **Impact:** Memory and performance overhead

#### Usage of Any type
- **File:** `codex/interactive_fixer.py:420`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/interactive_fixer.py:48`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/interactive_fixer.py:441`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/interactive_fixer.py:455`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/interactive_fixer.py:493`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Usage of Any type
- **File:** `codex/interactive_fixer.py:499`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Missing parameter type annotation
- **File:** `codex/rules/settings_rules.py:186`
- **Category:** Type Safety
- **Description:** Parameter 'registry' in 'register_settings_rules' lacks type annotation
- **Suggestion:** Add type hint: registry: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/settings_rules.py:109`
- **Category:** Type Safety
- **Description:** Parameter 'node' in 'visit_Call' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Usage of Any type
- **File:** `codex/rules/registry.py:68`
- **Category:** Type Safety
- **Description:** Any type defeats purpose of type checking
- **Suggestion:** Replace with specific type union or generic
- **Impact:** Loss of type safety guarantees

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:264`
- **Category:** Type Safety
- **Description:** Parameter 'registry' in 'register_database_rules' lacks type annotation
- **Suggestion:** Add type hint: registry: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:95`
- **Category:** Type Safety
- **Description:** Parameter 'node' in 'visit_With' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:101`
- **Category:** Type Safety
- **Description:** Parameter 'node' in 'visit_Assign' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:123`
- **Category:** Type Safety
- **Description:** Parameter 'call' in '_get_call_name' lacks type annotation
- **Suggestion:** Add type hint: call: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:219`
- **Category:** Type Safety
- **Description:** Parameter 'node' in 'visit_With' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:230`
- **Category:** Type Safety
- **Description:** Parameter 'node' in 'visit_Call' lacks type annotation
- **Suggestion:** Add type hint: node: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:245`
- **Category:** Type Safety
- **Description:** Parameter 'expr' in '_is_transaction_context' lacks type annotation
- **Suggestion:** Add type hint: expr: TypeName
- **Impact:** Reduces type safety and IDE support

#### Missing parameter type annotation
- **File:** `codex/rules/database_rules.py:252`
- **Category:** Type Safety
- **Description:** Parameter 'value' in '_is_session_call' lacks type annotation
- **Suggestion:** Add type hint: value: TypeName
- **Impact:** Reduces type safety and IDE support

#### High cyclomatic complexity
- **File:** `codex/rules/database_rules.py:202`
- **Category:** Complexity
- **Description:** Function 'check_ast' has complexity of 11
- **Suggestion:** Refactor into smaller functions or use strategy pattern
- **Impact:** Difficult to test and maintain

"""
Code Review Agent - Critical analysis of implementation details.

This agent performs deep code review focusing on:
1. Architectural issues
2. Security vulnerabilities
3. Performance bottlenecks
4. Type safety violations
5. Best practice violations
6. Technical debt
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# from rich.console import Console
# from rich.table import Table


class Severity(str, Enum):
    """Severity levels for code issues."""
    
    CRITICAL = "CRITICAL"  # Security vulnerabilities, data loss risks
    HIGH = "HIGH"         # Bugs, type safety issues
    MEDIUM = "MEDIUM"     # Performance, maintainability
    LOW = "LOW"          # Style, minor improvements
    INFO = "INFO"        # Suggestions, alternatives


class IssueCategory(str, Enum):
    """Categories of code issues."""
    
    SECURITY = "Security"
    TYPE_SAFETY = "Type Safety"
    PERFORMANCE = "Performance"
    ARCHITECTURE = "Architecture"
    ERROR_HANDLING = "Error Handling"
    TESTING = "Testing"
    DOCUMENTATION = "Documentation"
    COMPLEXITY = "Complexity"
    DEPENDENCIES = "Dependencies"
    CONSISTENCY = "Consistency"


@dataclass
class CodeIssue:
    """Represents a code review issue."""
    
    file: str
    line: int
    severity: Severity
    category: IssueCategory
    title: str
    description: str
    suggestion: str
    code_snippet: str = ""
    impact: str = ""
    references: list[str] = field(default_factory=list)


class CodeReviewAgent:
    """Performs critical code review and analysis."""
    
    def __init__(self, verbose: bool = True):
        """Initialize the code review agent."""
        self.verbose = verbose
        self.console = None  # Console() if verbose else None
        self.issues: list[CodeIssue] = []
        
    def review_file(self, file_path: Path) -> list[CodeIssue]:
        """Review a single Python file."""
        if not file_path.exists():
            return []
            
        content = file_path.read_text()
        
        # Parse AST for deep analysis
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            self.issues.append(CodeIssue(
                file=str(file_path),
                line=0,
                severity=Severity.CRITICAL,
                category=IssueCategory.ARCHITECTURE,
                title="Syntax Error",
                description="File contains syntax errors and cannot be parsed",
                suggestion="Fix syntax errors before proceeding with review"
            ))
            return self.issues
        
        # Run all review checks
        self._check_type_safety(tree, file_path, content)
        self._check_error_handling(tree, file_path, content)
        self._check_security_issues(tree, file_path, content)
        self._check_performance_issues(tree, file_path, content)
        self._check_architectural_issues(tree, file_path, content)
        self._check_complexity(tree, file_path, content)
        self._check_testing_coverage(tree, file_path, content)
        
        return self.issues
    
    def _check_type_safety(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for type safety issues."""
        lines = content.splitlines()
        
        for node in ast.walk(tree):
            # Check for missing type hints in function definitions
            if isinstance(node, ast.FunctionDef):
                if not node.returns and node.name != "__init__":
                    self.issues.append(CodeIssue(
                        file=str(file_path),
                        line=node.lineno,
                        severity=Severity.HIGH,
                        category=IssueCategory.TYPE_SAFETY,
                        title="Missing return type annotation",
                        description=f"Function '{node.name}' lacks return type annotation",
                        suggestion=f"Add return type hint: def {node.name}(...) -> ReturnType:",
                        code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else "",
                        impact="Type checking tools cannot verify return type correctness"
                    ))
                
                # Check for untyped parameters
                for arg in node.args.args:
                    if not arg.annotation and arg.arg != "self" and arg.arg != "cls":
                        self.issues.append(CodeIssue(
                            file=str(file_path),
                            line=node.lineno,
                            severity=Severity.MEDIUM,
                            category=IssueCategory.TYPE_SAFETY,
                            title="Missing parameter type annotation",
                            description=f"Parameter '{arg.arg}' in '{node.name}' lacks type annotation",
                            suggestion=f"Add type hint: {arg.arg}: TypeName",
                            impact="Reduces type safety and IDE support"
                        ))
            
            # Check for Any type usage
            if isinstance(node, ast.Name) and node.id == "Any":
                self.issues.append(CodeIssue(
                    file=str(file_path),
                    line=node.lineno,
                    severity=Severity.MEDIUM,
                    category=IssueCategory.TYPE_SAFETY,
                    title="Usage of Any type",
                    description="Any type defeats purpose of type checking",
                    suggestion="Replace with specific type union or generic",
                    impact="Loss of type safety guarantees"
                ))
    
    def _check_error_handling(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for error handling issues."""
        for node in ast.walk(tree):
            # Check for bare except clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append(CodeIssue(
                        file=str(file_path),
                        line=node.lineno,
                        severity=Severity.HIGH,
                        category=IssueCategory.ERROR_HANDLING,
                        title="Bare except clause",
                        description="Catches all exceptions including SystemExit and KeyboardInterrupt",
                        suggestion="Use 'except Exception:' or specific exception types",
                        impact="Can hide critical errors and make debugging difficult"
                    ))
            
            # Check for missing error context
            if isinstance(node, ast.Raise):
                if node.cause is None and isinstance(node.exc, ast.Call):
                    # Check if we're in an except block
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ExceptHandler):
                            if node in ast.walk(parent):
                                self.issues.append(CodeIssue(
                                    file=str(file_path),
                                    line=node.lineno,
                                    severity=Severity.MEDIUM,
                                    category=IssueCategory.ERROR_HANDLING,
                                    title="Missing exception chaining",
                                    description="Re-raising without 'from' loses original traceback",
                                    suggestion="Use 'raise NewException(...) from e'",
                                    impact="Loss of debugging information"
                                ))
    
    def _check_security_issues(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for security vulnerabilities."""
        # Skip pattern definition files to avoid false positives
        pattern_files = {
            'scan_rules.py', 'fix_validation_rules.py', 'code_review_agent.py',
            'pattern_models.py', 'security_patterns.py', 'validation_rules.py'
        }
        
        if file_path.name in pattern_files:
            return
            
        dangerous_patterns = [
            (r'eval\s*\(', "eval() usage", "Arbitrary code execution risk"),
            (r'exec\s*\(', "exec() usage", "Arbitrary code execution risk"),
            (r'pickle\.loads', "pickle.loads()", "Deserialization vulnerability"),
            (r'subprocess.*shell\s*=\s*True', "shell=True", "Command injection risk"),
            (r'os\.system\s*\(', "os.system()", "Command injection risk"),
            (r'SQL.*%s|SQL.*format\(', "SQL string formatting", "SQL injection risk"),
            (r'verify\s*=\s*False', "SSL verification disabled", "MITM vulnerability"),
        ]
        
        for pattern, title, risk in dangerous_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append(CodeIssue(
                    file=str(file_path),
                    line=line_num,
                    severity=Severity.CRITICAL,
                    category=IssueCategory.SECURITY,
                    title=f"Security: {title}",
                    description=risk,
                    suggestion="Use safe alternatives or add input validation",
                    impact="Potential security vulnerability"
                ))
    
    def _check_performance_issues(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for performance issues."""
        for node in ast.walk(tree):
            # Check for inefficient list comprehensions in loops
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.ListComp):
                        self.issues.append(CodeIssue(
                            file=str(file_path),
                            line=node.lineno,
                            severity=Severity.MEDIUM,
                            category=IssueCategory.PERFORMANCE,
                            title="List comprehension in loop",
                            description="Creating lists in loops can be inefficient",
                            suggestion="Consider using generator or accumulating results",
                            impact="Memory and performance overhead"
                        ))
            
            # Check for repeated attribute access
            if isinstance(node, ast.Attribute):
                # Simple heuristic: if same attribute accessed multiple times
                attr_name = f"{node.value}.{node.attr}" if isinstance(node.value, ast.Name) else None
                if attr_name and content.count(attr_name) > 5:
                    self.issues.append(CodeIssue(
                        file=str(file_path),
                        line=node.lineno,
                        severity=Severity.LOW,
                        category=IssueCategory.PERFORMANCE,
                        title="Repeated attribute access",
                        description=f"'{attr_name}' accessed multiple times",
                        suggestion="Cache in local variable for better performance",
                        impact="Minor performance overhead"
                    ))
    
    def _check_architectural_issues(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for architectural issues."""
        # Check class complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    self.issues.append(CodeIssue(
                        file=str(file_path),
                        line=node.lineno,
                        severity=Severity.HIGH,
                        category=IssueCategory.ARCHITECTURE,
                        title="Class too complex",
                        description=f"Class '{node.name}' has {len(methods)} methods",
                        suggestion="Consider splitting into smaller, focused classes",
                        impact="Difficult to maintain and test"
                    ))
                
                # Check for god object pattern
                attributes = [n for n in node.body if isinstance(n, ast.AnnAssign)]
                if len(attributes) > 15:
                    self.issues.append(CodeIssue(
                        file=str(file_path),
                        line=node.lineno,
                        severity=Severity.HIGH,
                        category=IssueCategory.ARCHITECTURE,
                        title="God object anti-pattern",
                        description=f"Class '{node.name}' has too many attributes ({len(attributes)})",
                        suggestion="Apply Single Responsibility Principle",
                        impact="Violates SOLID principles"
                    ))
    
    def _check_complexity(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for cyclomatic complexity issues."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    self.issues.append(CodeIssue(
                        file=str(file_path),
                        line=node.lineno,
                        severity=Severity.HIGH if complexity > 15 else Severity.MEDIUM,
                        category=IssueCategory.COMPLEXITY,
                        title="High cyclomatic complexity",
                        description=f"Function '{node.name}' has complexity of {complexity}",
                        suggestion="Refactor into smaller functions or use strategy pattern",
                        impact="Difficult to test and maintain"
                    ))
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.Assert):
                complexity += 1
                
        return complexity
    
    def _check_testing_coverage(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for testing issues."""
        # Check if this is a test file
        if "test_" in str(file_path) or "_test" in str(file_path):
            return
            
        # Count functions and check for corresponding tests
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        public_functions = [f for f in functions if not f.name.startswith("_")]
        
        if public_functions and not self._has_tests(file_path):
            self.issues.append(CodeIssue(
                file=str(file_path),
                line=1,
                severity=Severity.HIGH,
                category=IssueCategory.TESTING,
                title="Missing test coverage",
                description=f"File has {len(public_functions)} public functions but no tests found",
                suggestion="Add unit tests for public functions",
                impact="Unverified functionality, potential bugs"
            ))
    
    def _has_tests(self, file_path: Path) -> bool:
        """Check if tests exist for this file."""
        test_patterns = [
            file_path.parent / f"test_{file_path.name}",
            file_path.parent / f"{file_path.stem}_test.py",
            file_path.parent.parent / "tests" / f"test_{file_path.name}",
        ]
        
        return any(test_path.exists() for test_path in test_patterns)
    
    def generate_report(self) -> str:
        """Generate a comprehensive review report."""
        if not self.issues:
            return "✅ No critical issues found!"
        
        # Group issues by severity
        by_severity = {}
        for issue in self.issues:
            by_severity.setdefault(issue.severity, []).append(issue)
        
        report = []
        report.append("# 🔍 Code Review Report\n")
        report.append(f"**Total Issues Found:** {len(self.issues)}\n")
        
        # Summary table
        report.append("## Summary by Severity\n")
        for severity in Severity:
            count = len(by_severity.get(severity, []))
            if count > 0:
                emoji = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠", 
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "🔵",
                    Severity.INFO: "⚪"
                }[severity]
                report.append(f"- {emoji} **{severity.value}**: {count} issues\n")
        
        # Detailed issues
        report.append("\n## Detailed Findings\n")
        
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            issues = by_severity.get(severity, [])
            if not issues:
                continue
                
            report.append(f"\n### {severity.value} Issues\n")
            
            for issue in issues:
                report.append(f"\n#### {issue.title}\n")
                report.append(f"- **File:** `{issue.file}:{issue.line}`\n")
                report.append(f"- **Category:** {issue.category.value}\n")
                report.append(f"- **Description:** {issue.description}\n")
                report.append(f"- **Suggestion:** {issue.suggestion}\n")
                if issue.impact:
                    report.append(f"- **Impact:** {issue.impact}\n")
                if issue.code_snippet:
                    report.append(f"- **Code:** `{issue.code_snippet.strip()}`\n")
        
        return "".join(report)
    
    def review_codebase(self, root_path: Path, patterns: list[str] = None) -> str:
        """Review entire codebase."""
        patterns = patterns or ["**/*.py"]
        
        for pattern in patterns:
            for file_path in root_path.glob(pattern):
                if file_path.is_file():
                    self.review_file(file_path)
        
        return self.generate_report()


def perform_critical_review(target_path: str = "codex/") -> None:
    """Perform a critical code review of the target path."""
    agent = CodeReviewAgent(verbose=True)
    
    # Review the codebase
    report = agent.review_codebase(Path(target_path))
    
    # Print report
    print(report)
    
    # Save report to file
    report_path = Path("code_review_report.md")
    report_path.write_text(report)
    print(f"\n📄 Report saved to: {report_path}")


if __name__ == "__main__":
    perform_critical_review()
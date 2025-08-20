"""
Database rules (DB prefix).

Patterns for database usage, connection management, and consistency.
"""

import ast
import re
from pathlib import Path

from .registry import (
    ASTChecker,
    Fix,
    FixApplicability,
    Location,
    PatternChecker,
    Rule,
    RuleChecker,
    Severity,
    Violation,
)

# Rule definitions
USE_CONTEXT_MANAGERS = Rule(
    code="DB001",
    name="use-context-managers",
    message_template="Database {resource} not using context manager",
    severity=Severity.ERROR,
    description="Always use context managers for database resources",
    rationale="Context managers ensure proper cleanup and prevent resource leaks",
    tags=["database", "resource-management"],
    examples={
        "good": """
with get_db_session() as session:
    result = session.query(User).all()
""",
        "bad": """
session = SessionLocal()
result = session.query(User).all()
session.close()  # May not be called if exception occurs
""",
    },
)


USE_UNIFIED_DATABASE = Rule(
    code="DB002",
    name="use-unified-database",
    message_template="Using deprecated {module} module - use unified_database",
    severity=Severity.ERROR,
    description="Use unified_database module for all database operations",
    rationale="Multiple database modules lead to inconsistent state and configuration",
    tags=["database", "consistency"],
)


NO_RAW_SQL = Rule(
    code="DB003",
    name="no-raw-sql",
    message_template="Raw SQL query detected - use ORM or parameterized queries",
    severity=Severity.WARNING,
    description="Avoid raw SQL strings to prevent injection",
    rationale="Raw SQL is vulnerable to injection attacks and harder to maintain",
    tags=["database", "security", "sql-injection"],
)


EXPLICIT_TRANSACTIONS = Rule(
    code="DB004",
    name="explicit-transactions",
    message_template="Database modification without explicit transaction",
    severity=Severity.WARNING,
    description="Use explicit transactions for data modifications",
    rationale="Explicit transactions ensure atomicity and proper error handling",
    tags=["database", "transactions"],
)


# Checker implementations
class ContextManagerChecker(ASTChecker):
    """Check for database resources without context managers."""

    def __init__(self):
        super().__init__(USE_CONTEXT_MANAGERS)

    def check_ast(self, tree: ast.AST, file_path: Path) -> list[Violation]:
        """Find database operations without context managers."""
        violations = []

        class DatabaseVisitor(ast.NodeVisitor):
            def __init__(self):
                self.in_with = False
                self.session_vars = set()

            def visit_With(self, node):
                old_in_with = self.in_with
                self.in_with = True
                self.generic_visit(node)
                self.in_with = old_in_with

            def visit_Assign(self, node):
                # Check for session/connection assignments
                if isinstance(node.value, ast.Call):
                    call_name = self._get_call_name(node.value)
                    if call_name and any(
                        db_term in call_name.lower() for db_term in ["session", "connection", "conn", "cursor"]
                    ):
                        if not self.in_with:
                            # Track variable name for later checks
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    self.session_vars.add(target.id)

                                    location = Location(file_path, node.lineno, node.col_offset)
                                    violation = USE_CONTEXT_MANAGERS.create_violation(
                                        location=location,
                                        resource=call_name,
                                        context=ast.unparse(node) if hasattr(ast, "unparse") else str(node),
                                    )
                                    violations.append(violation)
                self.generic_visit(node)

            def _get_call_name(self, call):
                """Extract the function/class name from a call."""
                if isinstance(call.func, ast.Name):
                    return call.func.id
                elif isinstance(call.func, ast.Attribute):
                    return call.func.attr
                return None

        visitor = DatabaseVisitor()
        visitor.visit(tree)
        return violations


class UnifiedDatabaseChecker(PatternChecker):
    """Check for usage of deprecated database modules."""

    def __init__(self):
        patterns = [
            (r"from\s+\.database\s+import", "database"),
            (r"from\s+\.fts_database\s+import", "fts_database"),
            (r"import\s+database(?:\s|$)", "database"),
            (r"import\s+fts_database", "fts_database"),
        ]
        super().__init__(USE_UNIFIED_DATABASE, patterns)

    def check_file(self, file_path: Path, content: str) -> list[Violation]:
        """Check for deprecated imports with fix suggestions."""
        violations = super().check_file(file_path, content)

        # Add fix suggestions
        for violation in violations:
            old_import = violation.context
            new_import = old_import.replace("database", "unified_database")
            new_import = new_import.replace("fts_unified_database", "unified_database")

            violation.fix = Fix(
                description="Use unified_database module",
                replacements=[(violation.location, new_import)],
                applicability=FixApplicability.ALWAYS,
            )

        return violations


class RawSQLChecker(RuleChecker):
    """Check for raw SQL queries."""

    SQL_KEYWORDS = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "EXEC", "EXECUTE"]

    def __init__(self):
        super().__init__(NO_RAW_SQL)

    def check_file(self, file_path: Path, content: str) -> list[Violation]:
        """Check for SQL in strings."""
        violations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue

            # Look for SQL keywords in strings
            if any(f'"{keyword} ' in line.upper() or f"'{keyword} " in line.upper() for keyword in self.SQL_KEYWORDS):
                # Check if it's actually SQL (not just a word)
                if re.search(r'["\'].*\b(FROM|WHERE|JOIN|INTO|VALUES)\b', line, re.IGNORECASE):
                    location = Location(file_path, line_num, 0)
                    violation = self.rule.create_violation(location=location, context=line.strip())
                    violations.append(violation)

        return violations


class TransactionChecker(ASTChecker):
    """Check for database modifications without transactions."""

    def __init__(self):
        super().__init__(EXPLICIT_TRANSACTIONS)

    def check_ast(self, tree: ast.AST, file_path: Path) -> list[Violation]:
        """Find DB modifications without transaction context."""
        violations = []

        class TransactionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.in_transaction = False
                self.modification_methods = {
                    "add",
                    "delete",
                    "merge",
                    "bulk_insert_mappings",
                    "bulk_update_mappings",
                    "execute",
                    "commit",
                }

            def visit_With(self, node):
                # Check if this is a transaction context
                for item in node.items:
                    if self._is_transaction_context(item.context_expr):
                        old_in_transaction = self.in_transaction
                        self.in_transaction = True
                        self.generic_visit(node)
                        self.in_transaction = old_in_transaction
                        return
                self.generic_visit(node)

            def visit_Call(self, node):
                # Check for modification methods
                if isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr
                    if method_name in self.modification_methods:
                        # Check if we're calling it on a session
                        if self._is_session_call(node.func.value):
                            if not self.in_transaction:
                                location = Location(file_path, node.lineno, node.col_offset)
                                violation = EXPLICIT_TRANSACTIONS.create_violation(
                                    location=location, method=method_name
                                )
                                violations.append(violation)
                self.generic_visit(node)

            def _is_transaction_context(self, expr):
                """Check if expression is a transaction context."""
                if isinstance(expr, ast.Call):
                    if isinstance(expr.func, ast.Attribute):
                        return expr.func.attr in ("begin", "transaction", "atomic")
                return False

            def _is_session_call(self, value):
                """Check if value looks like a database session."""
                if isinstance(value, ast.Name):
                    return "session" in value.id.lower() or "db" in value.id.lower()
                return False

        visitor = TransactionVisitor()
        visitor.visit(tree)
        return violations


# Register all rules
def register_database_rules(registry):
    """Register all database rules with the registry."""
    registry.register(USE_CONTEXT_MANAGERS, ContextManagerChecker())
    registry.register(USE_UNIFIED_DATABASE, UnifiedDatabaseChecker())
    registry.register(NO_RAW_SQL, RawSQLChecker())
    registry.register(EXPLICIT_TRANSACTIONS, TransactionChecker())

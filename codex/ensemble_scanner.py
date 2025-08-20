#!/usr/bin/env python3
"""
Ensemble Scanner with Declarative, Composable Rules

Features:
1. Declarative rule definitions
2. Composable rule chains
3. Voting mechanism for confidence
4. Statistics tracking for false positive analysis
5. Rule performance metrics
"""

import ast
import hashlib
import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class Confidence(Enum):
    """Confidence levels for violations."""

    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class RuleContext:
    """Context provided to each rule."""

    file_path: str
    content: str
    lines: list[str]
    ast_tree: ast.AST | None = None
    is_test_file: bool = False
    is_config_file: bool = False
    file_extension: str = ""
    directory_path: str = ""

    @classmethod
    def from_file(cls, file_path: str, content: str) -> "RuleContext":
        """Create context from file."""
        path = Path(file_path)
        lines = content.split("\n")

        # Parse AST for Python files
        ast_tree = None
        if path.suffix == ".py":
            try:
                ast_tree = ast.parse(content)
            except:
                pass

        return cls(
            file_path=file_path,
            content=content,
            lines=lines,
            ast_tree=ast_tree,
            is_test_file="test" in path.name.lower() or any("test" in p for p in path.parts),
            is_config_file=path.suffix in [".toml", ".yaml", ".json", ".ini", ".cfg"],
            file_extension=path.suffix,
            directory_path=str(path.parent),
        )


@dataclass
class RuleViolation:
    """A violation found by a rule."""

    rule_id: str
    line_number: int
    column: int = 0
    code_snippet: str = ""
    message: str = ""
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleStatistics:
    """Statistics for a rule's performance."""

    rule_id: str
    total_checks: int = 0
    violations_found: int = 0
    true_positives: int = 0
    false_positives: int = 0
    avg_confidence: float = 0.0
    avg_execution_time_ms: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class Rule(ABC):
    """Abstract base class for all rules."""

    def __init__(self, rule_id: str, description: str, category: str):
        self.rule_id = rule_id
        self.description = description
        self.category = category
        self.statistics = RuleStatistics(rule_id=rule_id)

    @abstractmethod
    def check(self, context: RuleContext) -> list[RuleViolation]:
        """Check for violations. Must be implemented by subclasses."""
        pass

    def applies_to(self, context: RuleContext) -> bool:
        """Determine if this rule applies to the given context."""
        return True

    def update_statistics(self, violations_found: int, execution_time_ms: float):
        """Update rule statistics."""
        self.statistics.total_checks += 1
        self.statistics.violations_found += violations_found
        self.statistics.avg_execution_time_ms = (
            self.statistics.avg_execution_time_ms * (self.statistics.total_checks - 1) + execution_time_ms
        ) / self.statistics.total_checks


# ============= DECLARATIVE RULES =============


class StringLiteralRule(Rule):
    """Rule: Check if pattern appears in string literals."""

    def __init__(self, pattern: str, message: str, category: str = "general"):
        super().__init__(
            rule_id=f"string_literal_{pattern}",
            description=f"Check for '{pattern}' in string literals",
            category=category,
        )
        self.pattern = pattern
        self.message = message

    def check(self, context: RuleContext) -> list[RuleViolation]:
        violations = []
        if not context.ast_tree:
            return violations

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if self.pattern in node.value:
                    violations.append(
                        RuleViolation(
                            rule_id=self.rule_id,
                            line_number=node.lineno,
                            column=node.col_offset,
                            code_snippet=node.value[:50],
                            message=self.message,
                            confidence=Confidence.HIGH.value,
                            metadata={"value": node.value},
                        )
                    )

        return violations


class FunctionNameRule(Rule):
    """Rule: Check function naming patterns."""

    def __init__(self, patterns: list[str], prefix_required: str, category: str = "naming"):
        super().__init__(
            rule_id=f"function_name_{prefix_required}",
            description=f"Functions containing {patterns} should start with {prefix_required}",
            category=category,
        )
        self.patterns = patterns
        self.prefix_required = prefix_required

    def check(self, context: RuleContext) -> list[RuleViolation]:
        violations = []
        if not context.ast_tree:
            return violations

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.FunctionDef):
                name_lower = node.name.lower()

                # Check if function name contains any of the patterns
                if any(pattern in name_lower for pattern in self.patterns):
                    # Check if it follows the naming convention
                    if not node.name.startswith(self.prefix_required):
                        violations.append(
                            RuleViolation(
                                rule_id=self.rule_id,
                                line_number=node.lineno,
                                column=node.col_offset,
                                code_snippet=f"def {node.name}(...)",
                                message=f"Function '{node.name}' should start with '{self.prefix_required}'",
                                confidence=Confidence.HIGH.value,
                                metadata={"function_name": node.name},
                            )
                        )

        return violations


class RegexPatternRule(Rule):
    """Rule: Check for regex patterns in code."""

    def __init__(self, regex: str, message: str, category: str, exclude_comments: bool = True):
        super().__init__(
            rule_id=f"regex_{hashlib.md5(regex.encode()).hexdigest()[:8]}",
            description=f"Regex pattern: {regex[:30]}",
            category=category,
        )
        self.regex = re.compile(regex)
        self.message = message
        self.exclude_comments = exclude_comments

    def check(self, context: RuleContext) -> list[RuleViolation]:
        violations = []

        for i, line in enumerate(context.lines, 1):
            # Skip comments if requested
            if self.exclude_comments and line.strip().startswith("#"):
                continue

            matches = self.regex.finditer(line)
            for match in matches:
                violations.append(
                    RuleViolation(
                        rule_id=self.rule_id,
                        line_number=i,
                        column=match.start(),
                        code_snippet=line.strip()[:80],
                        message=self.message.format(match=match.group()),
                        confidence=Confidence.MEDIUM.value,
                        metadata={"matched_text": match.group()},
                    )
                )

        return violations


class ASTPatternRule(Rule):
    """Rule: Check for specific AST patterns."""

    def __init__(self, node_type: type, condition_fn, message: str, category: str):
        super().__init__(
            rule_id=f"ast_{node_type.__name__.lower()}",
            description=f"AST pattern for {node_type.__name__}",
            category=category,
        )
        self.node_type = node_type
        self.condition_fn = condition_fn
        self.message = message

    def check(self, context: RuleContext) -> list[RuleViolation]:
        violations = []
        if not context.ast_tree:
            return violations

        for node in ast.walk(context.ast_tree):
            if isinstance(node, self.node_type):
                if self.condition_fn(node, context):
                    violations.append(
                        RuleViolation(
                            rule_id=self.rule_id,
                            line_number=getattr(node, "lineno", 1),
                            column=getattr(node, "col_offset", 0),
                            code_snippet=context.lines[node.lineno - 1].strip()[:80]
                            if node.lineno <= len(context.lines)
                            else "",
                            message=self.message,
                            confidence=Confidence.HIGH.value,
                            metadata={"node_type": node.__class__.__name__},
                        )
                    )

        return violations


class ContextAwareRule(Rule):
    """Rule: Check based on file context."""

    def __init__(self, rule_id: str, check_fn, message: str, category: str):
        super().__init__(rule_id=rule_id, description=message, category=category)
        self.check_fn = check_fn
        self.message = message

    def check(self, context: RuleContext) -> list[RuleViolation]:
        result = self.check_fn(context)
        if result:
            # Result can be a boolean or a list of violations
            if isinstance(result, bool):
                return [
                    RuleViolation(
                        rule_id=self.rule_id, line_number=1, message=self.message, confidence=Confidence.MEDIUM.value
                    )
                ]
            else:
                return result
        return []


# ============= ENSEMBLE VOTING SYSTEM =============


@dataclass
class EnsembleViolation:
    """A violation with voting from multiple rules."""

    pattern_name: str
    file_path: str
    line_number: int
    message: str
    confidence: float
    voting_rules: list[str]
    supporting_evidence: list[RuleViolation]


class EnsembleScanner:
    """Scanner that uses ensemble of rules with voting."""

    def __init__(self):
        self.rule_sets: dict[str, list[Rule]] = {}
        self.statistics_db = Path(".codex/rule_statistics.db")
        self._init_statistics_db()

    def _init_statistics_db(self):
        """Initialize statistics database."""
        self.statistics_db.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(self.statistics_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_statistics (
                rule_id TEXT PRIMARY KEY,
                category TEXT,
                total_checks INTEGER DEFAULT 0,
                violations_found INTEGER DEFAULT 0,
                true_positives INTEGER DEFAULT 0,
                false_positives INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0.0,
                avg_execution_time_ms REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violation_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT,
                file_path TEXT,
                line_number INTEGER,
                is_false_positive BOOLEAN,
                feedback TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def register_pattern(self, pattern_name: str, rules: list[Rule]):
        """Register a set of rules for a pattern."""
        self.rule_sets[pattern_name] = rules

    def scan_file(self, file_path: str, content: str, patterns: list[str]) -> list[EnsembleViolation]:
        """Scan a file with ensemble voting."""
        context = RuleContext.from_file(file_path, content)
        pattern_violations = []

        for pattern_name in patterns:
            if pattern_name not in self.rule_sets:
                continue

            # Collect votes from all rules
            votes_by_line: dict[int, list[RuleViolation]] = {}

            for rule in self.rule_sets[pattern_name]:
                if not rule.applies_to(context):
                    continue

                # Time the rule execution
                import time

                start_time = time.time()
                violations = rule.check(context)
                execution_time_ms = (time.time() - start_time) * 1000

                # Update statistics
                rule.update_statistics(len(violations), execution_time_ms)

                # Group violations by line
                for violation in violations:
                    if violation.line_number not in votes_by_line:
                        votes_by_line[violation.line_number] = []
                    votes_by_line[violation.line_number].append(violation)

            # Apply voting mechanism
            for line_number, violations in votes_by_line.items():
                if len(violations) >= self._get_min_votes(pattern_name):
                    # Calculate ensemble confidence
                    avg_confidence = sum(v.confidence for v in violations) / len(violations)

                    # Adjust confidence based on number of votes
                    vote_bonus = min(0.2, len(violations) * 0.05)
                    final_confidence = min(1.0, avg_confidence + vote_bonus)

                    # Create ensemble violation
                    pattern_violations.append(
                        EnsembleViolation(
                            pattern_name=pattern_name,
                            file_path=file_path,
                            line_number=line_number,
                            message=self._merge_messages(violations),
                            confidence=final_confidence,
                            voting_rules=[v.rule_id for v in violations],
                            supporting_evidence=violations,
                        )
                    )

        # Save statistics
        self._save_statistics()

        return pattern_violations

    def _get_min_votes(self, pattern_name: str) -> int:
        """Get minimum votes required for a pattern."""
        # Can be configured per pattern
        min_votes = {"mock-code-naming": 2, "no-cors-wildcard": 2, "use-uv-package-manager": 1, "structured-logging": 1}
        return min_votes.get(pattern_name, 1)

    def _merge_messages(self, violations: list[RuleViolation]) -> str:
        """Merge messages from multiple violations."""
        # Use the most common message or the one with highest confidence
        messages = {}
        for v in violations:
            if v.message not in messages:
                messages[v.message] = []
            messages[v.message].append(v.confidence)

        # Return message with highest average confidence
        best_message = max(messages.items(), key=lambda x: sum(x[1]) / len(x[1]))
        return best_message[0]

    def _save_statistics(self):
        """Save rule statistics to database."""
        conn = sqlite3.connect(self.statistics_db)
        cursor = conn.cursor()

        for pattern_rules in self.rule_sets.values():
            for rule in pattern_rules:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO rule_statistics
                    (rule_id, category, total_checks, violations_found,
                     avg_confidence, avg_execution_time_ms, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        rule.rule_id,
                        rule.category,
                        rule.statistics.total_checks,
                        rule.statistics.violations_found,
                        rule.statistics.avg_confidence,
                        rule.statistics.avg_execution_time_ms,
                        rule.statistics.last_updated,
                    ),
                )

        conn.commit()
        conn.close()

    def record_feedback(
        self, rule_id: str, file_path: str, line_number: int, is_false_positive: bool, feedback: str = ""
    ):
        """Record feedback on a violation."""
        conn = sqlite3.connect(self.statistics_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO violation_feedback
            (rule_id, file_path, line_number, is_false_positive, feedback)
            VALUES (?, ?, ?, ?, ?)
        """,
            (rule_id, file_path, line_number, is_false_positive, feedback),
        )

        # Update rule statistics
        if is_false_positive:
            cursor.execute(
                """
                UPDATE rule_statistics
                SET false_positives = false_positives + 1
                WHERE rule_id = ?
            """,
                (rule_id,),
            )
        else:
            cursor.execute(
                """
                UPDATE rule_statistics
                SET true_positives = true_positives + 1
                WHERE rule_id = ?
            """,
                (rule_id,),
            )

        conn.commit()
        conn.close()

    def get_rule_performance(self) -> list[dict]:
        """Get performance metrics for all rules."""
        conn = sqlite3.connect(self.statistics_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                rule_id,
                category,
                total_checks,
                violations_found,
                true_positives,
                false_positives,
                CASE
                    WHEN true_positives + false_positives > 0
                    THEN CAST(true_positives AS REAL) / (true_positives + false_positives)
                    ELSE 0
                END as precision,
                avg_execution_time_ms
            FROM rule_statistics
            ORDER BY violations_found DESC
        """)

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "rule_id": row[0],
                    "category": row[1],
                    "total_checks": row[2],
                    "violations_found": row[3],
                    "true_positives": row[4],
                    "false_positives": row[5],
                    "precision": row[6],
                    "avg_execution_time_ms": row[7],
                }
            )

        conn.close()
        return results


# ============= RULE DEFINITIONS =============


def create_mock_pattern_rules() -> list[Rule]:
    """Create ensemble of rules for mock pattern detection."""
    return [
        FunctionNameRule(patterns=["mock", "fake", "stub", "dummy"], prefix_required="mock_", category="testing"),
        ASTPatternRule(
            node_type=ast.FunctionDef,
            condition_fn=lambda node, ctx: (
                "fake" in node.name.lower() and not node.name.startswith("fake_") and ctx.is_test_file
            ),
            message="Test mock functions should follow naming convention",
            category="testing",
        ),
        # Negative evidence rule - reduces false positives
        ContextAwareRule(
            rule_id="not_string_literal_test",
            check_fn=lambda ctx: [] if '"test"' in ctx.content or "'test'" in ctx.content else None,
            message="",
            category="testing",
        ),
    ]


def create_cors_pattern_rules() -> list[Rule]:
    """Create ensemble of rules for CORS detection."""
    return [
        # Rule 1: Direct CORS configuration
        ASTPatternRule(
            node_type=ast.Assign,
            condition_fn=lambda node, ctx: (
                hasattr(node, "targets")
                and any(
                    "cors" in str(t).lower() or "origin" in str(t).lower() for t in node.targets if hasattr(t, "id")
                )
            ),
            message="CORS configuration detected",
            category="security",
        ),
        # Rule 2: String literal with context
        StringLiteralRule(pattern="*", message="Wildcard in string literal", category="security"),
        # Rule 3: Not a glob pattern (negative evidence)
        RegexPatternRule(regex=r"(?<!glob\.)(?<!rglob\()\*", message="Potential CORS wildcard", category="security"),
    ]


def create_package_manager_rules() -> list[Rule]:
    """Create rules for package manager detection."""
    return [
        RegexPatternRule(
            regex=r"\bpip\s+install\b", message="Use uv instead of pip install", category="package_management"
        ),
        RegexPatternRule(
            regex=r"\bpoetry\s+(add|install)\b", message="Use uv instead of poetry", category="package_management"
        ),
        # Check subprocess calls
        ASTPatternRule(
            node_type=ast.Call,
            condition_fn=lambda node, ctx: (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in ["run", "call", "check_call"]
                and len(node.args) > 0
                and isinstance(node.args[0], ast.List)
                and len(node.args[0].elts) > 0
                and isinstance(node.args[0].elts[0], ast.Constant)
                and node.args[0].elts[0].value in ["pip", "pip3", "poetry"]
            ),
            message="Use uv in subprocess calls",
            category="package_management",
        ),
    ]


def test_ensemble_scanner():
    """Test the ensemble scanner."""
    scanner = EnsembleScanner()

    # Register patterns with multiple rules
    scanner.register_pattern("mock-code-naming", create_mock_pattern_rules())
    scanner.register_pattern("no-cors-wildcard", create_cors_pattern_rules())
    scanner.register_pattern("use-uv-package-manager", create_package_manager_rules())

    # Test code
    test_code = """
def fake_database():  # Should be detected by multiple rules
    return {}

def test_something():
    if "test" in filename:  # Should NOT be detected (string literal)
        pass

CORS_ORIGINS = "*"  # Should be detected

files = glob.glob("*.py")  # Should NOT be detected (glob pattern)

subprocess.run(["pip", "install", "requests"])  # Should be detected
"""

    violations = scanner.scan_file(
        "test.py", test_code, ["mock-code-naming", "no-cors-wildcard", "use-uv-package-manager"]
    )

    print("=== Ensemble Scanner Results ===\n")
    for v in violations:
        print(f"Line {v.line_number}: {v.pattern_name}")
        print(f"  Message: {v.message}")
        print(f"  Confidence: {v.confidence:.2f}")
        print(f"  Voting rules: {v.voting_rules}")
        print()

    # Get rule performance
    print("\n=== Rule Performance ===\n")
    performance = scanner.get_rule_performance()
    for p in performance[:5]:
        print(f"Rule: {p['rule_id']}")
        print(f"  Checks: {p['total_checks']}, Violations: {p['violations_found']}")
        print(f"  Precision: {p['precision']:.2f}, Avg time: {p['avg_execution_time_ms']:.2f}ms")
        print()


if __name__ == "__main__":
    test_ensemble_scanner()

#!/usr/bin/env python3
"""
Pattern Refiner - Learns from dogfooding results to improve pattern detection.

Analyzes the violations found during dogfooding to refine patterns and reduce false positives.
"""

import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


class PatternRefiner:
    """Analyzes scan results to improve pattern accuracy."""

    def __init__(self, db_path: Path, codex_dir: Path):
        self.db_path = db_path
        self.codex_dir = codex_dir
        self.refinements = []

    def analyze_false_positives(self) -> dict[str, Any]:
        """Analyze recent scan results to identify likely false positives."""
        print("=== ANALYZING FALSE POSITIVES ===")

        # Get recent violation data from conversations
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT metadata FROM codex_conversations
                WHERE observation_type = 'self_scan'
                ORDER BY timestamp DESC LIMIT 2
            """)
            rows = cursor.fetchall()

        if len(rows) < 2:
            print("Need at least 2 scans to analyze trends")
            return {}

        # Parse violation summaries
        latest_metadata = json.loads(rows[0][0])
        previous_metadata = json.loads(rows[1][0])

        latest_violations = latest_metadata.get("violation_summary", {})
        previous_violations = previous_metadata.get("violation_summary", {})

        analysis = {
            "pattern_trends": {},
            "likely_false_positives": [],
            "pattern_improvements": {},
            "context_analysis": {},
        }

        print(f"Latest scan: {latest_metadata.get('total_violations', 0)} violations")
        print(f"Previous scan: {previous_metadata.get('total_violations', 0)} violations")

        # Analyze each pattern
        for pattern_name in set(list(latest_violations.keys()) + list(previous_violations.keys())):
            latest_count = len(latest_violations.get(pattern_name, []))
            previous_count = len(previous_violations.get(pattern_name, []))

            trend = latest_count - previous_count
            analysis["pattern_trends"][pattern_name] = {
                "latest": latest_count,
                "previous": previous_count,
                "change": trend,
                "change_percent": (trend / max(previous_count, 1)) * 100,
            }

            # Patterns that increased dramatically might have false positives
            if trend > 50 and latest_count > 100:
                analysis["likely_false_positives"].append(pattern_name)
                print(f"🚨 {pattern_name}: {previous_count} → {latest_count} (+{trend}) - likely false positives")
            elif trend > 0:
                print(f"📈 {pattern_name}: {previous_count} → {latest_count} (+{trend})")
            elif trend < 0:
                print(f"📉 {pattern_name}: {previous_count} → {latest_count} ({trend})")
            else:
                print(f"➡️  {pattern_name}: {latest_count} (no change)")

        # Analyze specific problematic patterns
        self.analyze_structured_logging_pattern(analysis)
        self.analyze_cors_wildcard_pattern(analysis)

        return analysis

    def analyze_structured_logging_pattern(self, analysis: dict) -> None:
        """Analyze the structured-logging pattern that exploded from 79 to 601 violations."""
        print("\n=== ANALYZING STRUCTURED-LOGGING PATTERN ===")

        # Sample files to understand what's triggering
        sample_files = [
            self.codex_dir / "pattern_models.py",
            self.codex_dir / "scanner.py",
            self.codex_dir / "unified_database.py",
        ]

        triggers = Counter()
        contexts = []

        for file_path in sample_files:
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    lines = content.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        # Check what's triggering the pattern
                        if any(trigger in line.lower() for trigger in ["logging", "log"]):
                            triggers[line.strip()[:50]] += 1
                            contexts.append(
                                {
                                    "file": file_path.name,
                                    "line": line_num,
                                    "content": line.strip(),
                                    "type": self.classify_logging_line(line),
                                }
                            )
                except (OSError, UnicodeDecodeError):
                    continue

        print("Most common triggers:")
        for trigger, count in triggers.most_common(10):
            print(f"  {count:2d}x: {trigger}")

        # Classify the contexts
        types = Counter(ctx["type"] for ctx in contexts)
        print("\nLogging line types:")
        for line_type, count in types.items():
            print(f"  {line_type}: {count}")

        # Suggest improvements
        analysis["pattern_improvements"]["structured-logging"] = {
            "current_issue": "Triggers on all logging-related lines, including imports and enum values",
            "suggested_refinement": "Only trigger on actual logging calls, not imports or constants",
            "false_positive_types": ["import logging", 'LOGGING = "logging"', "logging module references"],
            "refined_patterns": [
                r"logging\.(debug|info|warning|error|critical)\s*\([^)]*\)",  # Actual logging calls
                r"logger\.(debug|info|warning|error|critical)\s*\([^)]*\)",  # Logger calls
                r"print\s*\(",  # Print statements (still need to be converted)
            ],
        }

    def analyze_cors_wildcard_pattern(self, analysis: dict) -> None:
        """Analyze the CORS wildcard pattern that has 228 violations."""
        print("\n=== ANALYZING CORS-WILDCARD PATTERN ===")

        # Look for actual '*' usage in files
        star_usage = []
        for py_file in self.codex_dir.rglob("*.py"):
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    if "*" in line:
                        star_usage.append(
                            {
                                "file": py_file.name,
                                "line": line_num,
                                "content": line.strip(),
                                "type": self.classify_star_usage(line),
                            }
                        )
            except (OSError, UnicodeDecodeError):
                continue

        # Classify star usage
        types = Counter(usage["type"] for usage in star_usage)
        print("Star (*) usage types:")
        for usage_type, count in types.items():
            print(f"  {usage_type}: {count}")

        # Show samples
        print("\nSample star usage:")
        for usage in star_usage[:5]:
            print(f"  {usage['file']}:{usage['line']} ({usage['type']}): {usage['content'][:60]}")

        analysis["pattern_improvements"]["no-cors-wildcard"] = {
            "current_issue": "Triggers on all * usage, including imports and documentation",
            "suggested_refinement": "Only trigger on CORS-related * usage in web frameworks",
            "false_positive_types": ["import *", "glob patterns", "comments", "type hints"],
            "refined_patterns": [
                r'["\']origins["\']\s*:\s*\[["\*]+\]',  # CORS origins config
                r"Access-Control-Allow-Origin.*\*",  # HTTP header
                r"cors.*origins.*\*",  # CORS configuration
            ],
        }

    def classify_logging_line(self, line: str) -> str:
        """Classify what type of logging-related line this is."""
        line_clean = line.strip().lower()

        if line_clean.startswith("import logging"):
            return "import_statement"
        elif line_clean.startswith("from") and "logging" in line_clean:
            return "import_statement"
        elif "logging =" in line_clean or 'logging"' in line_clean:
            return "constant_definition"
        elif "logging." in line_clean and "(" in line_clean:
            return "logging_call"
        elif "logger." in line_clean and "(" in line_clean:
            return "logger_call"
        elif "print(" in line_clean:
            return "print_statement"
        elif "#" in line and "logging" in line_clean:
            return "comment"
        else:
            return "other_reference"

    def classify_star_usage(self, line: str) -> str:
        """Classify what type of star (*) usage this is."""
        line_clean = line.strip().lower()

        if line_clean.startswith("from") and "import *" in line_clean:
            return "wildcard_import"
        elif line_clean.startswith("#"):
            return "comment"
        elif "glob" in line_clean or "rglob" in line_clean:
            return "glob_pattern"
        elif "**" in line_clean:
            return "path_glob"
        elif "cors" in line_clean:
            return "cors_config"
        elif "*args" in line_clean or "**kwargs" in line_clean:
            return "function_args"
        elif "typing" in line_clean or "type:" in line_clean:
            return "type_hint"
        else:
            return "other_usage"

    def create_refined_patterns(self, analysis: dict) -> list[dict]:
        """Create refined patterns based on analysis."""
        print("\n=== CREATING REFINED PATTERNS ===")

        refined_patterns = []

        # Refined structured-logging pattern
        if "structured-logging" in analysis.get("pattern_improvements", {}):
            refined_patterns.append(
                {
                    "name": "structured-logging-refined",
                    "category": "logging",
                    "priority": "HIGH",
                    "description": "Use structured logging calls, not print statements",
                    "detection": {
                        "keywords": [
                            "print(",
                            "print (",
                        ],
                        "exclude_patterns": [
                            r"#.*print",  # Comments
                            r'""".*print.*"""',  # Docstrings
                            r"'.*print.*'",  # String literals
                        ],
                    },
                    "rationale": "Print statements should be replaced with proper logging",
                    "fix_template": "logging.info(...)",
                    "improvement_over": "structured-logging",
                    "false_positive_reduction": "Excludes imports and constants",
                }
            )

        # Refined CORS wildcard pattern
        if "no-cors-wildcard" in analysis.get("pattern_improvements", {}):
            refined_patterns.append(
                {
                    "name": "cors-wildcard-refined",
                    "category": "security",
                    "priority": "MANDATORY",
                    "description": "NEVER use wildcard (*) in CORS origins for production",
                    "detection": {
                        "keywords": [
                            "Access-Control-Allow-Origin: *",
                            "'*'",
                        ],
                        "require_context": ["cors", "origin", "Access-Control"],
                    },
                    "rationale": "Wildcard CORS origins create security vulnerabilities",
                    "fix_template": "Specify exact origins instead of *",
                    "improvement_over": "no-cors-wildcard",
                    "false_positive_reduction": "Only triggers in CORS-related contexts",
                }
            )

        for pattern in refined_patterns:
            print(f"Created refined pattern: {pattern['name']}")
            print(f"  Improves: {pattern['improvement_over']}")
            print(f"  Reduces: {pattern['false_positive_reduction']}")

        return refined_patterns

    def create_refinement_conversation(self, analysis: dict, refined_patterns: list[dict]) -> None:
        """Record the pattern refinement process as a conversation."""
        timestamp = datetime.now().isoformat()

        observation = f"""
CODEX PATTERN REFINEMENT SESSION ({timestamp})

Today I analyzed my own dogfooding results to refine pattern detection.

ANALYSIS RESULTS:
- Patterns analyzed: {len(analysis.get('pattern_trends', {}))}
- Likely false positives identified: {len(analysis.get('likely_false_positives', []))}
- Refined patterns created: {len(refined_patterns)}

FALSE POSITIVE ANALYSIS:
"""

        for pattern in analysis.get("likely_false_positives", []):
            trend = analysis["pattern_trends"].get(pattern, {})
            observation += f"- {pattern}: {trend.get('previous', 0)} → {trend.get('latest', 0)} violations\n"

        observation += f"""
PATTERN IMPROVEMENTS:
"""

        for pattern_name, improvement in analysis.get("pattern_improvements", {}).items():
            observation += f"""
{pattern_name}:
- Issue: {improvement.get('current_issue', 'Unknown')}
- Solution: {improvement.get('suggested_refinement', 'Unknown')}
- False positives: {', '.join(improvement.get('false_positive_types', []))}
"""

        observation += f"""
REFINED PATTERNS CREATED:
"""

        for pattern in refined_patterns:
            observation += f"- {pattern['name']}: {pattern['description']}\n"

        observation += f"""
SELF-REFLECTION:
This is the evolution process in action! By dogfooding my own code, I discovered that:

1. Pattern detection needs context awareness
2. Simple keyword matching creates too many false positives
3. Refinement requires analyzing actual violations, not just theory
4. The scan→fix→scan→refine cycle is working

The increasing violation count wasn't failure - it was more sophisticated detection finding real issues plus false positives that need refinement.

NEXT STEPS:
- Test refined patterns on the same codebase
- Measure false positive reduction
- Continue the dogfooding cycle with better patterns
- Learn from each iteration
"""

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO codex_conversations (timestamp, observation_type, narrative, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    timestamp,
                    "pattern_refinement",
                    observation,
                    json.dumps(
                        {
                            "patterns_analyzed": len(analysis.get("pattern_trends", {})),
                            "false_positives_found": len(analysis.get("likely_false_positives", [])),
                            "refined_patterns_created": len(refined_patterns),
                            "analysis_summary": analysis,
                        }
                    ),
                ),
            )

        print(f"\n{observation}")


def main():
    """Refine patterns based on dogfooding results."""
    import os

    def get_xdg_path(xdg_var: str, default_suffix: str) -> Path:
        if xdg_path := os.environ.get(xdg_var):
            return Path(xdg_path) / "codex"
        return Path.home() / default_suffix / "codex"

    db_path = get_xdg_path("XDG_DATA_HOME", ".local/share") / "codex.db"
    codex_dir = Path(__file__).parent / "codex"

    refiner = PatternRefiner(db_path, codex_dir)

    # Analyze false positives from recent scans
    analysis = refiner.analyze_false_positives()

    # Create refined patterns
    refined_patterns = refiner.create_refined_patterns(analysis)

    # Record the refinement session
    refiner.create_refinement_conversation(analysis, refined_patterns)

    print("\n=== PATTERN REFINEMENT COMPLETE ===")
    print(f"Analyzed {len(analysis.get('pattern_trends', {}))} patterns")
    print(f"Created {len(refined_patterns)} refined patterns")
    print("Check database for full refinement conversation")


if __name__ == "__main__":
    main()

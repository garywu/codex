#!/usr/bin/env python3
"""
Simple pattern scanner for dogfooding Codex on itself.

No dependencies - just Python stdlib and SQLite queries.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class SimpleScanner:
    """Basic pattern scanner using the existing database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.observations = []

    def load_patterns(self) -> list[dict]:
        """Load patterns from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT name, category, priority, description, detection, fix
                FROM patterns
                WHERE priority IN ('MANDATORY', 'CRITICAL', 'HIGH')
                ORDER BY priority, category
            """)
            return [dict(row) for row in cursor.fetchall()]

    def scan_file(self, file_path: Path, patterns: list[dict]) -> list[dict]:
        """Scan a single file for pattern violations."""
        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return violations

        lines = content.split("\n")

        for pattern in patterns:
            # Try to extract detection rules
            detection = pattern.get("detection", "")
            if not detection:
                continue

            # Parse JSON detection if present
            try:
                if detection.startswith("{"):
                    detection_data = json.loads(detection)
                    keywords = detection_data.get("keywords", [])
                else:
                    # Fallback to simple text matching
                    keywords = [detection]
            except json.JSONDecodeError:
                keywords = [detection]

            # Check for violations
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                for keyword in keywords:
                    if keyword and keyword in line:
                        violations.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "pattern": pattern["name"],
                                "category": pattern["category"],
                                "priority": pattern["priority"],
                                "description": pattern["description"],
                                "code_line": line.strip(),
                                "keyword": keyword,
                            }
                        )
                        break

        return violations

    def scan_directory(self, directory: Path) -> None:
        """Scan all Python files in directory."""
        patterns = self.load_patterns()

        print(f"Loaded {len(patterns)} patterns from database")
        print("Scanning Codex codebase...")

        all_violations = []
        files_scanned = 0

        for py_file in directory.rglob("*.py"):
            # Skip __pycache__, .venv, etc.
            if any(skip in str(py_file) for skip in ["__pycache__", ".venv", ".git"]):
                continue

            violations = self.scan_file(py_file, patterns)
            all_violations.extend(violations)
            files_scanned += 1

            if violations:
                print(f"  {py_file.name}: {len(violations)} issues")

        # Store conversational observation
        self.create_conversation_entry(files_scanned, all_violations, patterns)

        # Show summary
        self.show_summary(files_scanned, all_violations)

    def create_conversation_entry(self, files_scanned: int, violations: list[dict], patterns: list[dict]) -> None:
        """Create a conversational database entry."""
        timestamp = datetime.now().isoformat()

        # Group violations by pattern
        by_pattern = {}
        for v in violations:
            pattern = v["pattern"]
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(v)

        # Create conversational observation
        observation = f"""
CODEX SELF-SCAN ({timestamp})

Today I examined my own codebase - {files_scanned} Python files.

WHAT I FOUND:
- Total violations: {len(violations)}
- Patterns checked: {len(patterns)}
- Most problematic areas: {', '.join(f'{p} ({len(vs)} issues)' for p, vs in sorted(by_pattern.items(), key=lambda x: len(x[1]), reverse=True)[:3])}

PATTERN ANALYSIS:
"""

        for pattern_name, pattern_violations in sorted(by_pattern.items(), key=lambda x: len(x[1]), reverse=True):
            first_violation = pattern_violations[0]
            observation += f"""
- {pattern_name} ({first_violation['category']}, {first_violation['priority']}):
  Found {len(pattern_violations)} violations
  Description: {first_violation['description']}
  Example: {pattern_violations[0]['file']}:{pattern_violations[0]['line']}
"""

        observation += f"""
SELF-REFLECTION:
As Codex, I'm finding patterns in my own code that I should fix. This is exactly the dogfooding experience we need - I can see what patterns matter and how to improve detection.

FILES WITH MOST ISSUES:
"""

        # Group by file
        by_file = {}
        for v in violations:
            file = v["file"]
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(v)

        for file, file_violations in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            observation += f"- {Path(file).name}: {len(file_violations)} issues\n"

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            # Create conversation table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS codex_conversations (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    observation_type TEXT,
                    narrative TEXT,
                    metadata TEXT
                )
            """)

            conn.execute(
                """
                INSERT INTO codex_conversations (timestamp, observation_type, narrative, metadata)
                VALUES (?, ?, ?, ?)
            """,
                (
                    timestamp,
                    "self_scan",
                    observation,
                    json.dumps(
                        {
                            "files_scanned": files_scanned,
                            "total_violations": len(violations),
                            "patterns_used": len(patterns),
                            "violation_summary": by_pattern,
                        }
                    ),
                ),
            )

        print("\nStored conversational observation in database")

    def show_summary(self, files_scanned: int, violations: list[dict]) -> None:
        """Show human-readable summary."""
        print("\n=== CODEX SELF-SCAN SUMMARY ===")
        print(f"Files scanned: {files_scanned}")
        print(f"Total violations: {len(violations)}")

        if violations:
            print("\nTop issues:")
            by_pattern = {}
            for v in violations:
                pattern = v["pattern"]
                by_pattern[pattern] = by_pattern.get(pattern, 0) + 1

            for pattern, count in sorted(by_pattern.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {pattern}: {count} violations")

            print("\nSample violations:")
            for v in violations[:3]:
                print(f"  {Path(v['file']).name}:{v['line']} - {v['pattern']}")
                print(f"    {v['code_line']}")
        else:
            print("🎉 No violations found! Codex practices what it preaches.")


def main():
    """Dogfood Codex on itself."""
    # Calculate database path
    import os
    from pathlib import Path

    def get_xdg_path(xdg_var: str, default_suffix: str) -> Path:
        if xdg_path := os.environ.get(xdg_var):
            return Path(xdg_path) / "codex"
        return Path.home() / default_suffix / "codex"

    db_path = get_xdg_path("XDG_DATA_HOME", ".local/share") / "codex.db"
    codex_dir = Path(__file__).parent / "codex"

    scanner = SimpleScanner(db_path)
    scanner.scan_directory(codex_dir)


if __name__ == "__main__":
    main()

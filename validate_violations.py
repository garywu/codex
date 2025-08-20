#!/usr/bin/env python3
"""
Validate scan violations to check for false positives.
"""

import sqlite3
from pathlib import Path


def analyze_violations():
    """Analyze violations from the scan database."""

    db_path = Path(".codex/scans.db")
    if not db_path.exists():
        print("No scan database found. Run 'codex analyze-violations' first.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get latest scan
    cursor.execute("SELECT scan_id FROM scans ORDER BY timestamp DESC LIMIT 1")
    latest_scan = cursor.fetchone()
    if not latest_scan:
        print("No scans found.")
        return

    scan_id = latest_scan["scan_id"]

    # Analyze violations by pattern
    print(f"\n=== Analyzing Scan {scan_id} ===\n")

    # Get violations grouped by pattern
    cursor.execute(
        """
        SELECT
            pattern_name,
            COUNT(*) as count,
            GROUP_CONCAT(DISTINCT file_path) as files
        FROM violations
        WHERE scan_id = ?
        GROUP BY pattern_name
        ORDER BY count DESC
    """,
        (scan_id,),
    )

    patterns = cursor.fetchall()

    # Categories of suspicious patterns
    suspicious_patterns = {"mock-code-naming": [], "minimum-test": [], "no-cors": [], "secure-jwt": []}

    # Sample some violations for each pattern
    for pattern in patterns:
        pattern_name = pattern["pattern_name"]

        # Get sample violations
        cursor.execute(
            """
            SELECT file_path, line_number, message
            FROM violations
            WHERE scan_id = ? AND pattern_name = ?
            LIMIT 3
        """,
            (scan_id, pattern_name),
        )

        samples = cursor.fetchall()

        print(f"\n### {pattern_name} ({pattern['count']} violations)")

        # Check specific patterns for false positives
        if "mock" in pattern_name:
            # Check if these are really mock-related
            for sample in samples:
                file_path = sample["file_path"]
                line = sample["line_number"]

                # Read the actual line
                try:
                    with open(file_path) as f:
                        lines = f.readlines()
                        if line > 0 and line <= len(lines):
                            actual_line = lines[line - 1].strip()
                            print(f"  {file_path}:{line}")
                            print(f"    Code: {actual_line[:80]}")

                            # Check if it's actually mock-related
                            if "def " in actual_line and ("fake" in actual_line or "mock" in actual_line):
                                print(f"    ✓ Valid: Function with 'fake' or 'mock'")
                            elif "test" in actual_line and '"test"' in actual_line:
                                print(f"    ✗ FALSE POSITIVE: String literal 'test'")
                                suspicious_patterns["mock-code-naming"].append(f"{file_path}:{line}")
                            else:
                                print(f"    ? Unclear: {sample['message'][:60]}")
                except:
                    print(f"    ! Could not read file")

        elif "cors" in pattern_name.lower():
            for sample in samples:
                file_path = sample["file_path"]
                line = sample["line_number"]

                try:
                    with open(file_path) as f:
                        lines = f.readlines()
                        if line > 0 and line <= len(lines):
                            actual_line = lines[line - 1].strip()
                            print(f"  {file_path}:{line}")
                            print(f"    Code: {actual_line[:80]}")

                            # Check if it's actually CORS-related
                            if "cors" in actual_line.lower() or "origin" in actual_line.lower():
                                print(f"    ✓ Valid: CORS-related code")
                            elif "*" in actual_line and ("glob" in actual_line or "pattern" in actual_line):
                                print(f"    ✗ FALSE POSITIVE: Glob pattern, not CORS")
                                suspicious_patterns["no-cors"].append(f"{file_path}:{line}")
                            else:
                                print(f"    ? Check: {sample['message'][:60]}")
                except:
                    print(f"    ! Could not read file")

        elif "minimum-test" in pattern_name:
            for sample in samples:
                print(f"  {sample['file_path']}:{sample['line_number']}")
                print(f"    Message: {sample['message'][:80]}")

        else:
            # Just show samples for other patterns
            for sample in samples:
                print(f"  {sample['file_path']}:{sample['line_number']}: {sample['message'][:60]}")

    # Summary of suspicious patterns
    print("\n\n=== VALIDATION SUMMARY ===\n")

    false_positive_count = 0
    for pattern, locations in suspicious_patterns.items():
        if locations:
            print(f"\n{pattern}: {len(locations)} likely false positives")
            for loc in locations[:3]:
                print(f"  - {loc}")
            false_positive_count += len(locations)

    if false_positive_count > 0:
        print(f"\n⚠️  Found {false_positive_count} likely false positives")
        print("The pattern matching may be too broad.")
    else:
        print("\n✅ No obvious false positives detected in samples")

    # Get category summary
    cursor.execute(
        """
        SELECT
            category,
            COUNT(*) as count
        FROM violations
        WHERE scan_id = ?
        GROUP BY category
        ORDER BY count DESC
    """,
        (scan_id,),
    )

    print("\n\n=== VIOLATIONS BY CATEGORY ===\n")
    for row in cursor.fetchall():
        print(f"{row['category']}: {row['count']} violations")

    conn.close()


if __name__ == "__main__":
    analyze_violations()

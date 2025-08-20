#!/usr/bin/env python3
"""
Detailed Violation Scanner - Show specific violations found
"""

from pathlib import Path

from enhanced_intelligent_scanner import EnhancedIntelligentScanner


def show_detailed_violations():
    """Show detailed breakdown of violations found."""
    print("=== DETAILED VIOLATION ANALYSIS ===")

    codex_dir = Path(__file__).parent / "codex"
    scanner = EnhancedIntelligentScanner(codex_dir)
    results = scanner.comprehensive_scan()

    print("\n=== PATTERN DETECTION SUMMARY ===")
    print(f"Total patterns loaded: {len(scanner.enhanced_patterns)}")
    for pattern in scanner.enhanced_patterns:
        print(f"  - {pattern['name']} ({pattern['priority']}): {pattern['description'][:60]}...")

    print("\n=== VIOLATION BREAKDOWN ===")

    # Group violations by pattern
    violations_by_pattern = {}
    for fix_plan in results.get("fix_plans", []):
        violation = fix_plan.get("violation", {})
        pattern = violation.get("pattern", "unknown")
        if pattern not in violations_by_pattern:
            violations_by_pattern[pattern] = []
        violations_by_pattern[pattern].append(violation)

    # Show violations by pattern
    for pattern, violations in violations_by_pattern.items():
        print(f"\n🔍 PATTERN: {pattern}")
        print(f"   Violations: {len(violations)}")
        for i, violation in enumerate(violations[:3]):  # Show first 3
            file_path = violation.get("file", "unknown")
            line_num = violation.get("line", 0)
            code = violation.get("code", violation.get("matched_text", ""))
            print(f"   {i+1}. {Path(file_path).name}:{line_num}")
            if code:
                print(f"      Code: {code[:80]}...")
            print(f"      Priority: {violation.get('priority', 'unknown')}")
            intelligent_verdict = violation.get("intelligent_verdict", "not_assessed")
            confidence = violation.get("confidence", 0)
            print(f"      Intelligence: {intelligent_verdict} ({confidence:.1%} confidence)")

    print("\n=== INTELLIGENCE ASSESSMENT DETAILS ===")

    # Show samples of filtered out violations
    print("\nSample violations filtered out as false positives:")

    # Get some raw violations from file analysis
    raw_violations = []
    for file_path, analysis in scanner.file_analysis_cache.items():
        if not analysis.get("error"):
            raw_violations.extend(analysis.get("violations", []))

    filtered_out = [
        v
        for v in raw_violations
        if not any(
            fp["violation"].get("file") == v.get("file") and fp["violation"].get("line") == v.get("line")
            for fp in results.get("fix_plans", [])
        )
    ]

    for i, violation in enumerate(filtered_out[:5]):  # Show first 5 filtered
        file_path = violation.get("file", "unknown")
        line_num = violation.get("line", 0)
        pattern = violation.get("pattern", "unknown")
        code = violation.get("code", violation.get("matched_text", ""))
        print(f"   {i+1}. {Path(file_path).name}:{line_num} - {pattern}")
        if code:
            print(f"      Code: {code[:80]}...")
        print("      Reason: Filtered by intelligence")

    print("\n=== RECOMMENDATIONS ===")

    critical_count = sum(
        1 for fp in results.get("fix_plans", []) if fp.get("violation", {}).get("priority") == "CRITICAL"
    )
    mandatory_count = sum(
        1 for fp in results.get("fix_plans", []) if fp.get("violation", {}).get("priority") == "MANDATORY"
    )

    if critical_count > 0:
        print(f"🔴 IMMEDIATE ACTION REQUIRED: {critical_count} critical security issues")
        print("   - Review hardcoded secrets and security vulnerabilities")
        print("   - Move sensitive data to environment variables")

    if mandatory_count > 0:
        print(f"🟠 POLICY COMPLIANCE: {mandatory_count} mandatory violations")
        print("   - Fix CORS wildcard configurations")
        print("   - Ensure mock code naming compliance")

    high_count = sum(1 for fp in results.get("fix_plans", []) if fp.get("violation", {}).get("priority") == "HIGH")
    if high_count > 0:
        print(f"🟡 ARCHITECTURAL IMPROVEMENTS: {high_count} high priority issues")
        print("   - Move business logic to core packages")
        print("   - Implement unified data source interfaces")


if __name__ == "__main__":
    show_detailed_violations()

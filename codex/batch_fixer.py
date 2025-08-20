#!/usr/bin/env python3
"""
Batch Fixer - Apply common fixes across the entire codebase.

This module provides batch fixing capabilities for common patterns
that can be safely fixed automatically.
"""

import ast
import logging
import re
from pathlib import Path

from .models import PatternMatch


class BatchFixer:
    """Batch fixer for common violations."""

    # Patterns that are safe to fix in batch mode
    SAFE_BATCH_PATTERNS = {
        "mock-code-naming",
        "use-uv-package-manager",
        "no-print-production",
        "standard-import-order",
    }

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fixes_applied = 0
        self.files_modified = set()

    def fix_file(self, file_path: Path, violations: list[PatternMatch]) -> int:
        """Fix violations in a single file."""
        if not file_path.exists():
            return 0

        content = file_path.read_text()
        original_content = content
        fixes = 0

        # Group violations by pattern for efficient fixing
        by_pattern = {}
        for v in violations:
            if v.pattern_name not in by_pattern:
                by_pattern[v.pattern_name] = []
            by_pattern[v.pattern_name].append(v)

        # Apply fixes for each pattern
        for pattern_name, pattern_violations in by_pattern.items():
            if pattern_name in self.SAFE_BATCH_PATTERNS:
                content, count = self._apply_pattern_fixes(content, pattern_name, pattern_violations)
                fixes += count

        # Write back if changed
        if content != original_content and not self.dry_run:
            file_path.write_text(content)
            self.files_modified.add(file_path)
            self.fixes_applied += fixes

        return fixes

    def _apply_pattern_fixes(self, content: str, pattern_name: str, violations: list[PatternMatch]) -> tuple[str, int]:
        """Apply fixes for a specific pattern."""
        if pattern_name == "mock-code-naming":
            return self._fix_mock_naming_batch(content)
        elif pattern_name == "use-uv-package-manager":
            return self._fix_uv_package_manager_batch(content)
        elif pattern_name == "no-print-production":
            return self._fix_print_statements_batch(content)
        elif pattern_name == "standard-import-order":
            return self._fix_import_order_batch(content)

        return content, 0

    def _fix_mock_naming_batch(self, content: str) -> tuple[str, int]:
        """Fix all mock function naming in content."""
        fixes = 0
        lines = content.split("\n")

        for i, line in enumerate(lines):
            # Find function definitions that should have mock_ prefix
            match = re.search(r"def\s+(fake|stub|dummy|test)_(\w+)\s*\(", line)
            if match:
                old_name = f"{match.group(1)}_{match.group(2)}"
                new_name = f"mock_{match.group(2)}"

                # Replace in current line
                lines[i] = line.replace(f"def {old_name}", f"def {new_name}")

                # Add logging import if needed
                if i == 0 or not any("import logging" in line for line in lines[:i]):
                    lines.insert(0, "import logging")

                # Add warning after function definition
                indent = len(line) - len(line.lstrip())
                warning = " " * (indent + 4) + 'logging.warning(f"Using mock function {__name__}")'
                if i + 1 < len(lines) and '"""' in lines[i + 1]:
                    # Find end of docstring
                    for j in range(i + 2, min(i + 20, len(lines))):
                        if '"""' in lines[j]:
                            lines.insert(j + 1, warning)
                            break
                else:
                    lines.insert(i + 1, warning)

                fixes += 1

        return "\n".join(lines), fixes

    def _fix_uv_package_manager_batch(self, content: str) -> tuple[str, int]:
        """Replace all pip commands with uv."""
        replacements = [
            (r"\bpip install\b", "uv pip install"),
            (r"\bpip freeze\b", "uv pip freeze"),
            (r"\bpip list\b", "uv pip list"),
            (r"\bpip show\b", "uv pip show"),
            (r"\bpython -m pip\b", "uv pip"),
            (r'subprocess\.run\(\["pip"', 'subprocess.run(["uv", "pip"'),
            (r'subprocess\.call\(\["pip"', 'subprocess.call(["uv", "pip"'),
            (r'os\.system\("pip ', 'os.system("uv pip '),
            (r"os\.system\(\'pip ", "os.system('uv pip "),
        ]

        fixes = 0
        for pattern, replacement in replacements:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                fixes += count

        return content, fixes

    def _fix_print_statements_batch(self, content: str) -> tuple[str, int]:
        """Replace print statements with logging."""
        fixes = 0
        lines = content.split("\n")

        # Check if logging is imported
        has_logging = any("import logging" in line for line in lines)

        for i, line in enumerate(lines):
            # Skip comments and strings
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue

            # Find print statements
            match = re.search(r"(\s*)print\((.*?)\)", line)
            if match:
                indent = match.group(1)
                print_args = match.group(2)

                # Convert to logging
                if 'f"' in print_args or "f'" in print_args:
                    # f-string
                    new_line = f"{indent}logging.info({print_args})"
                else:
                    # Regular string
                    new_line = f"{indent}logging.info({print_args})"

                lines[i] = new_line
                fixes += 1

        # Add logging import if needed and we made fixes
        if fixes > 0 and not has_logging:
            # Find the right place to add import (after other imports)
            import_line = -1
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    import_line = i
                elif import_line >= 0 and line and not line.startswith(" "):
                    # Found first non-import line
                    break

            if import_line >= 0:
                lines.insert(import_line + 1, "import logging")
            else:
                lines.insert(0, "import logging")

        return "\n".join(lines), fixes

    def _fix_import_order_batch(self, content: str) -> tuple[str, int]:
        """Fix import order to follow PEP 8."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content, 0

        # Extract imports
        imports = {"stdlib": [], "third_party": [], "local": []}

        stdlib_modules = {
            "os",
            "sys",
            "json",
            "asyncio",
            "typing",
            "pathlib",
            "re",
            "datetime",
            "collections",
            "itertools",
            "functools",
            "logging",
            "unittest",
            "math",
            "random",
            "string",
            "io",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    if module.split(".")[0] in stdlib_modules:
                        imports["stdlib"].append(ast.unparse(node))
                    elif module.startswith("."):
                        imports["local"].append(ast.unparse(node))
                    else:
                        imports["third_party"].append(ast.unparse(node))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(".") or module == "":
                    imports["local"].append(ast.unparse(node))
                elif module.split(".")[0] in stdlib_modules:
                    imports["stdlib"].append(ast.unparse(node))
                else:
                    imports["third_party"].append(ast.unparse(node))

        # Sort each group
        for group in imports.values():
            group.sort()

        # Build new import section
        new_imports = []
        if imports["stdlib"]:
            new_imports.extend(imports["stdlib"])
        if imports["third_party"]:
            if new_imports:
                new_imports.append("")  # Blank line
            new_imports.extend(imports["third_party"])
        if imports["local"]:
            if new_imports:
                new_imports.append("")  # Blank line
            new_imports.extend(imports["local"])

        # Replace in content
        lines = content.split("\n")

        # Find import section
        import_start = -1
        import_end = -1
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                if import_start == -1:
                    import_start = i
                import_end = i
            elif import_start >= 0 and import_end >= 0 and line and not line.startswith(" "):
                break

        if import_start >= 0 and import_end >= 0:
            # Replace import section
            new_lines = lines[:import_start] + new_imports + lines[import_end + 1 :]
            return "\n".join(new_lines), 1

        return content, 0

    def get_summary(self) -> dict[str, any]:
        """Get summary of fixes applied."""
        return {
            "fixes_applied": self.fixes_applied,
            "files_modified": len(self.files_modified),
            "modified_files": list(self.files_modified),
        }


def batch_fix_directory(directory: Path, patterns: list[str] | None = None, dry_run: bool = False) -> dict[str, any]:
    """
    Apply batch fixes to an entire directory.

    Args:
        directory: Directory to fix
        patterns: Specific patterns to fix (None = all safe patterns)
        dry_run: If True, don't actually modify files

    Returns:
        Summary of fixes applied
    """
    from .scanner import Scanner

    fixer = BatchFixer(dry_run=dry_run)
    scanner = Scanner(quiet=True)

    # Scan directory
    logging.info(f"Scanning {directory} for violations...")
    results = asyncio.run(scanner.scan_directory(directory))

    # Process each file
    for result in results:
        if result.violations:
            # Filter violations if patterns specified
            violations = result.violations
            if patterns:
                violations = [v for v in violations if v.pattern_name in patterns]

            if violations:
                fixes = fixer.fix_file(Path(result.file_path), violations)
                if fixes > 0:
                    logging.info(f"Fixed {fixes} violations in {result.file_path}")

    return fixer.get_summary()


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 2:
        print("Usage: batch_fixer.py <directory> [--dry-run]")
        sys.exit(1)

    directory = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    summary = batch_fix_directory(directory, dry_run=dry_run)

    print("\nBatch Fix Summary:")
    print(f"  Files modified: {summary['files_modified']}")
    print(f"  Total fixes: {summary['fixes_applied']}")

    if dry_run:
        print("\n(Dry run - no files were actually modified)")

#!/usr/bin/env python3
"""
Hardcoded Paths Fixer - Replaces hardcoded paths with settings references.

Small, focused fixer that handles hardcoded path replacement only.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class HardcodedPathsFixer:
    """Replaces hardcoded paths with settings references."""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.fixes_applied = []

        # Define path replacement patterns
        self.path_replacements = {
            r'["\']patterns\.db["\']': "settings.database_path",
            r'["\']patterns_fts\.db["\']': "settings.database_path",
            r'["\']~/.config/codex["\']': "settings.config_dir",
            r'["\']~/.local/share/codex["\']': "settings.data_dir",
            r'["\']~/.cache/codex["\']': "settings.cache_dir",
        }

    def needs_settings_import(self, content: str) -> bool:
        """Check if file needs settings import."""
        uses_settings = any(replacement.startswith("settings.") for replacement in self.path_replacements.values())
        has_settings = any(
            line in content for line in ["from .settings import settings", "from codex.settings import settings"]
        )
        return uses_settings and not has_settings

    def add_settings_import(self, lines: list[str]) -> list[str]:
        """Add settings import to file."""
        # Find good spot for import (after other imports)
        import_line = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")):
                import_line = i

        lines.insert(import_line + 1, "from .settings import settings")
        return lines

    def apply_path_replacements(self, line: str) -> str:
        """Apply path replacements to a line."""
        original_line = line

        for pattern, replacement in self.path_replacements.items():
            if re.search(pattern, line):
                line = re.sub(pattern, replacement, line)

        return line

    def fix_file(self, file_path: Path) -> dict[str, Any]:
        """Fix hardcoded paths in a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            modified = False
            file_fixes = []
            needs_settings = False

            # Apply path replacements
            for i, line in enumerate(lines):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                original_line = line
                new_line = self.apply_path_replacements(line)

                if new_line != original_line:
                    lines[i] = new_line
                    modified = True
                    needs_settings = True
                    file_fixes.append(
                        {
                            "type": "path_replaced",
                            "line_num": i + 1,
                            "old": original_line.strip(),
                            "new": new_line.strip(),
                        }
                    )

            # Add settings import if needed
            if needs_settings and self.needs_settings_import(content):
                lines = self.add_settings_import(lines)
                modified = True
                file_fixes.append({"type": "import_added", "description": "Added settings import"})

            # Write back if modified
            if modified:
                content = "\n".join(lines)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return {"success": True, "fixes_applied": len(file_fixes), "details": file_fixes}
            else:
                return {"success": True, "fixes_applied": 0, "details": []}

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error processing {file_path}: {e}")
            return {"success": False, "error": str(e), "fixes_applied": 0}

    def fix_directory(self) -> dict[str, Any]:
        """Fix hardcoded paths in all Python files."""
        logger.info("Replacing hardcoded paths with settings...")

        files_processed = 0
        total_fixes = 0
        file_results = {}

        for py_file in self.target_dir.rglob("*.py"):
            # Skip unwanted directories
            if any(skip in str(py_file) for skip in ["__pycache__", ".venv", ".git", "backup_"]):
                continue

            result = self.fix_file(py_file)
            file_results[str(py_file)] = result

            if result["success"]:
                files_processed += 1
                total_fixes += result["fixes_applied"]

                if result["fixes_applied"] > 0:
                    logger.info(f"Fixed {py_file.name}: {result['fixes_applied']} paths")

        self.fixes_applied = [
            fix for result in file_results.values() if result.get("details") for fix in result["details"]
        ]

        return {"files_processed": files_processed, "total_fixes": total_fixes, "file_results": file_results}

    def get_summary(self) -> dict[str, Any]:
        """Get summary of fixes applied."""
        path_fixes = sum(1 for fix in self.fixes_applied if fix["type"] == "path_replaced")
        import_additions = sum(1 for fix in self.fixes_applied if fix["type"] == "import_added")

        return {
            "total_fixes": len(self.fixes_applied),
            "path_replacements": path_fixes,
            "import_additions": import_additions,
        }


def main():
    """Test hardcoded paths fixer."""
    codex_dir = Path(__file__).parent.parent / "codex"

    fixer = HardcodedPathsFixer(codex_dir)
    results = fixer.fix_directory()

    print("=== HARDCODED PATHS FIXER RESULTS ===")
    print(f"Files processed: {results['files_processed']}")
    print(f"Total fixes applied: {results['total_fixes']}")

    summary = fixer.get_summary()
    print(f"Path replacements: {summary['path_replacements']}")
    print(f"Import additions: {summary['import_additions']}")


if __name__ == "__main__":
    main()

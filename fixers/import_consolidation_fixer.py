#!/usr/bin/env python3
"""
Import Consolidation Fixer - Consolidates and cleans up imports.

Small, focused fixer that handles import consolidation only.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ImportConsolidationFixer:
    """Consolidates deprecated imports to unified modules."""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.fixes_applied = []

        # Define deprecated import replacements
        self.deprecated_imports = {
            "from .database import": "from .unified_database import UnifiedDatabase",
            "from .fts_database import": "from .unified_database import UnifiedDatabase",
            "import database": "from .unified_database import UnifiedDatabase",
            "import fts_database": "from .unified_database import UnifiedDatabase",
        }

    def replace_deprecated_imports(self, line: str) -> str:
        """Replace deprecated imports in a line."""
        original_line = line

        for old_import, new_import in self.deprecated_imports.items():
            if old_import in line:
                # Replace the entire line for import statements
                return new_import

        return line

    def fix_file(self, file_path: Path) -> dict[str, Any]:
        """Fix imports in a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            modified = False
            file_fixes = []

            # Replace deprecated imports
            for i, line in enumerate(lines):
                original_line = line
                new_line = self.replace_deprecated_imports(line)

                if new_line != original_line:
                    lines[i] = new_line
                    modified = True
                    file_fixes.append(
                        {
                            "type": "import_replaced",
                            "line_num": i + 1,
                            "old": original_line.strip(),
                            "new": new_line.strip(),
                        }
                    )

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
        """Fix imports in all Python files."""
        logger.info("Consolidating deprecated imports...")

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
                    logger.info(f"Fixed {py_file.name}: {result['fixes_applied']} imports")

        self.fixes_applied = [
            fix for result in file_results.values() if result.get("details") for fix in result["details"]
        ]

        return {"files_processed": files_processed, "total_fixes": total_fixes, "file_results": file_results}

    def get_summary(self) -> dict[str, Any]:
        """Get summary of fixes applied."""
        import_fixes = sum(1 for fix in self.fixes_applied if fix["type"] == "import_replaced")

        return {"total_fixes": len(self.fixes_applied), "import_replacements": import_fixes}


def main():
    """Test import consolidation fixer."""
    codex_dir = Path(__file__).parent.parent / "codex"

    fixer = ImportConsolidationFixer(codex_dir)
    results = fixer.fix_directory()

    print("=== IMPORT CONSOLIDATION FIXER RESULTS ===")
    print(f"Files processed: {results['files_processed']}")
    print(f"Total fixes applied: {results['total_fixes']}")

    summary = fixer.get_summary()
    print(f"Import replacements: {summary['import_replacements']}")


if __name__ == "__main__":
    main()

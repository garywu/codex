#!/usr/bin/env python3
"""
Print to Logging Fixer - Converts print statements to proper logging calls.

Small, focused fixer that handles print statement conversion only.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PrintToLoggingFixer:
    """Converts print statements to logging calls."""
    
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.fixes_applied = []
    
    def needs_logging_import(self, content: str) -> bool:
        """Check if file needs logging import."""
        has_print = 'print(' in content
        has_logging = any(line in content for line in [
            'import logging',
            'from logging import'
        ])
        return has_print and not has_logging
    
    def add_logging_import(self, lines: List[str]) -> List[str]:
        """Add logging import to file."""
        # Find good spot for import (after other imports)
        import_line = 0
        for i, line in enumerate(lines):
            if line.startswith(('import ', 'from ')) and 'logging' not in line:
                import_line = i
        
        lines.insert(import_line + 1, 'import logging')
        return lines
    
    def should_skip_line(self, line: str) -> bool:
        """Check if line should be skipped."""
        stripped = line.strip()
        return (
            stripped.startswith('#') or           # Comments
            '"""' in line or                      # Docstrings
            "'''" in line or                      # Docstrings
            line.count('"') >= 2 or              # String literals
            line.count("'") >= 2                 # String literals
        )
    
    def convert_print_to_logging(self, line: str) -> str:
        """Convert a single print statement to logging."""
        original_line = line
        
        # Convert print( to logging.info(
        if 'print(' in line:
            line = re.sub(r'print\s*\(', 'logging.info(', line)
        
        # Convert print with space to logging.info
        elif 'print ' in line and not line.strip().startswith('#'):
            line = re.sub(r'print\s+', 'logging.info(', line)
            if not line.rstrip().endswith(')'):
                line = line.rstrip() + ')'
        
        # Convert console.print to logging.info
        if 'console.print(' in line:
            line = re.sub(r'console\.print\s*\(', 'logging.info(', line)
        
        return line
    
    def fix_file(self, file_path: Path) -> Dict[str, Any]:
        """Fix print statements in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            modified = False
            file_fixes = []
            
            # Add logging import if needed
            if self.needs_logging_import(content):
                lines = self.add_logging_import(lines)
                modified = True
                file_fixes.append({
                    'type': 'import_added',
                    'description': 'Added logging import'
                })
            
            # Convert print statements
            for i, line in enumerate(lines):
                if self.should_skip_line(line):
                    continue
                
                if 'print(' in line or 'print ' in line or 'console.print(' in line:
                    original_line = line
                    new_line = self.convert_print_to_logging(line)
                    
                    if new_line != original_line:
                        lines[i] = new_line
                        modified = True
                        file_fixes.append({
                            'type': 'print_converted',
                            'line_num': i + 1,
                            'old': original_line.strip(),
                            'new': new_line.strip()
                        })
            
            # Write back if modified
            if modified:
                content = '\n'.join(lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    'success': True,
                    'fixes_applied': len(file_fixes),
                    'details': file_fixes
                }
            else:
                return {
                    'success': True,
                    'fixes_applied': 0,
                    'details': []
                }
                
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error processing {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'fixes_applied': 0
            }
    
    def fix_directory(self) -> Dict[str, Any]:
        """Fix print statements in all Python files."""
        logger.info("Converting print statements to logging...")
        
        files_processed = 0
        total_fixes = 0
        file_results = {}
        
        for py_file in self.target_dir.rglob("*.py"):
            # Skip unwanted directories
            if any(skip in str(py_file) for skip in [
                '__pycache__', '.venv', '.git', 'backup_'
            ]):
                continue
            
            result = self.fix_file(py_file)
            file_results[str(py_file)] = result
            
            if result['success']:
                files_processed += 1
                total_fixes += result['fixes_applied']
                
                if result['fixes_applied'] > 0:
                    logger.info(f"Fixed {py_file.name}: {result['fixes_applied']} changes")
        
        self.fixes_applied = [
            fix for result in file_results.values() 
            if result.get('details') 
            for fix in result['details']
        ]
        
        return {
            'files_processed': files_processed,
            'total_fixes': total_fixes,
            'file_results': file_results
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of fixes applied."""
        print_fixes = sum(1 for fix in self.fixes_applied if fix['type'] == 'print_converted')
        import_additions = sum(1 for fix in self.fixes_applied if fix['type'] == 'import_added')
        
        return {
            'total_fixes': len(self.fixes_applied),
            'print_conversions': print_fixes,
            'import_additions': import_additions
        }


def main():
    """Test print to logging fixer."""
    codex_dir = Path(__file__).parent.parent / 'codex'
    
    fixer = PrintToLoggingFixer(codex_dir)
    results = fixer.fix_directory()
    
    print("=== PRINT TO LOGGING FIXER RESULTS ===")
    print(f"Files processed: {results['files_processed']}")
    print(f"Total fixes applied: {results['total_fixes']}")
    
    summary = fixer.get_summary()
    print(f"Print conversions: {summary['print_conversions']}")
    print(f"Import additions: {summary['import_additions']}")


if __name__ == "__main__":
    main()
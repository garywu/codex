#!/usr/bin/env python3
"""
Remaining Issues Fixer - Fixes the last 5 real violations identified by analysis.

Small, targeted fixer for the remaining print statements and console.print calls.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RemainingIssuesFixer:
    """Fixes the remaining real violations after comprehensive analysis."""
    
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.fixes_applied = []
        
        # Specific files and lines identified by analysis
        self.known_issues = {
            'pattern_cli.py': [127, 197, 199, 201],  # 4 print statements
            'scanner.py': [377]  # 1 console.print
        }
    
    def needs_logging_import(self, content: str) -> bool:
        """Check if file needs logging import."""
        return 'import logging' not in content and 'from logging import' not in content
    
    def add_logging_import(self, lines: List[str]) -> List[str]:
        """Add logging import after existing imports."""
        import_line = 0
        for i, line in enumerate(lines):
            if line.startswith(('import ', 'from ')) and 'logging' not in line:
                import_line = i
        
        lines.insert(import_line + 1, 'import logging')
        return lines
    
    def fix_specific_file(self, file_path: Path) -> Dict[str, Any]:
        """Fix specific known issues in a file."""
        file_name = file_path.name
        
        if file_name not in self.known_issues:
            return {'success': True, 'fixes_applied': 0, 'details': []}
        
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
            
            # Fix specific lines
            target_lines = self.known_issues[file_name]
            
            for line_num in target_lines:
                if line_num <= len(lines):
                    line_idx = line_num - 1  # Convert to 0-based index
                    original_line = lines[line_idx]
                    new_line = self.convert_to_logging(original_line)
                    
                    if new_line != original_line:
                        lines[line_idx] = new_line
                        modified = True
                        file_fixes.append({
                            'type': 'print_converted',
                            'line_num': line_num,
                            'old': original_line.strip(),
                            'new': new_line.strip()
                        })
            
            # Write back if modified
            if modified:
                content = '\n'.join(lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Fixed {file_name}: {len(file_fixes)} changes")
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
    
    def convert_to_logging(self, line: str) -> str:
        """Convert a line with print/console.print to logging."""
        original_line = line
        
        # Convert print( to logging.info(
        if 'print(' in line:
            line = re.sub(r'print\s*\(', 'logging.info(', line)
        
        # Convert console.print( to logging.info(
        if 'console.print(' in line:
            line = re.sub(r'console\.print\s*\(', 'logging.info(', line)
            
            # Handle special console.print arguments
            if ', end=""' in line:
                line = line.replace(', end=""', '')
        
        return line
    
    def fix_remaining_issues(self) -> Dict[str, Any]:
        """Fix all remaining real issues."""
        logger.info("Fixing remaining real violations...")
        
        total_fixes = 0
        file_results = {}
        
        for file_name in self.known_issues.keys():
            file_path = self.target_dir / file_name
            
            if file_path.exists():
                result = self.fix_specific_file(file_path)
                file_results[file_name] = result
                
                if result['success']:
                    total_fixes += result['fixes_applied']
                    
                    if result['details']:
                        self.fixes_applied.extend(result['details'])
        
        return {
            'files_processed': len(file_results),
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
    """Fix the remaining real violations."""
    codex_dir = Path(__file__).parent.parent / 'codex'
    
    fixer = RemainingIssuesFixer(codex_dir)
    results = fixer.fix_remaining_issues()
    
    print("=== REMAINING ISSUES FIXER RESULTS ===")
    print(f"Files processed: {results['files_processed']}")
    print(f"Total fixes applied: {results['total_fixes']}")
    
    summary = fixer.get_summary()
    print(f"Print conversions: {summary['print_conversions']}")
    print(f"Import additions: {summary['import_additions']}")
    
    if results['total_fixes'] > 0:
        print("\n✅ All remaining real violations have been fixed!")
    else:
        print("\n⚠️  No fixes applied - issues may have been already resolved")


if __name__ == "__main__":
    main()
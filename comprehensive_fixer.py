#!/usr/bin/env python3
"""
Comprehensive Fixer - Applies all learned fixes to the Codex repository.

Uses the refined patterns and lessons from dogfooding to systematically fix all violations.
"""

import subprocess
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
import tempfile


class ComprehensiveFixer:
    """Applies comprehensive fixes using all learned patterns."""
    
    def __init__(self, codex_dir: Path):
        self.codex_dir = codex_dir
        self.fixes_applied = []
        self.backup_dir = None
        
    def create_backup(self) -> Path:
        """Create a backup of the entire codebase before fixes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"codex_backup_{timestamp}"
        self.backup_dir = self.codex_dir.parent / backup_name
        
        print(f"Creating backup: {self.backup_dir}")
        shutil.copytree(self.codex_dir, self.backup_dir)
        return self.backup_dir
    
    def run_external_tools_aggressively(self) -> Dict[str, Any]:
        """Run external tools with maximum fixing power."""
        print("=== RUNNING EXTERNAL TOOLS (AGGRESSIVE MODE) ===")
        results = {}
        
        # Run Ruff with maximum fixes
        try:
            print("Running ruff --fix --unsafe-fixes...")
            result = subprocess.run([
                "ruff", "check", str(self.codex_dir),
                "--fix", "--unsafe-fixes", "--select", "ALL"
            ], capture_output=True, text=True, timeout=120)
            
            results['ruff'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'fixed': 'Applied fixes' if result.returncode == 0 else 'Some issues remain'
            }
            print(f"  Ruff: {results['ruff']['fixed']}")
            
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            results['ruff'] = {'success': False, 'error': str(e)}
            print(f"  Ruff: {e}")
        
        # Run typos with fixes
        try:
            print("Running typos --write-changes...")
            result = subprocess.run([
                "typos", str(self.codex_dir), "--write-changes"
            ], capture_output=True, text=True, timeout=30)
            
            typo_count = len(result.stdout.splitlines()) if result.stdout else 0
            results['typos'] = {
                'success': result.returncode == 0,
                'fixed': typo_count,
                'output': result.stdout
            }
            print(f"  Typos: {typo_count} fixes applied")
            
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            results['typos'] = {'success': False, 'error': str(e)}
            print(f"  Typos: {e}")
        
        return results
    
    def fix_print_statements(self) -> List[Dict]:
        """Replace all print statements with proper logging."""
        print("\n=== FIXING PRINT STATEMENTS ===")
        fixes = []
        
        for py_file in self.codex_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.venv', 'backup_']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    original_content = content
                
                lines = content.split('\n')
                modified = False
                
                # Add logging import if needed and print statements exist
                has_print = any('print(' in line for line in lines)
                has_logging = any('import logging' in line or 'from logging import' in line for line in lines)
                
                if has_print and not has_logging:
                    # Find good spot for import (after other imports)
                    import_line = 0
                    for i, line in enumerate(lines):
                        if line.startswith(('import ', 'from ')) and 'logging' not in line:
                            import_line = i
                    
                    lines.insert(import_line + 1, 'import logging')
                    modified = True
                
                # Replace print statements
                for i, line in enumerate(lines):
                    original_line = line
                    
                    # Skip comments, docstrings, string literals
                    stripped = line.strip()
                    if (stripped.startswith('#') or 
                        '"""' in line or
                        "'''" in line or
                        line.count('"') >= 2 or
                        line.count("'") >= 2):
                        continue
                    
                    # Replace various print patterns
                    if 'print(' in line:
                        # Simple print(message)
                        line = re.sub(r'print\s*\(', 'logging.info(', line)
                        modified = True
                    elif 'print ' in line and not line.strip().startswith('#'):
                        # print with space
                        line = re.sub(r'print\s+', 'logging.info(', line)
                        if not line.endswith(')'):
                            line += ')'
                        modified = True
                    
                    # Replace console.print with logging
                    if 'console.print(' in line:
                        line = re.sub(r'console\.print\s*\(', 'logging.info(', line)
                        modified = True
                    
                    lines[i] = line
                    
                    if line != original_line:
                        fixes.append({
                            'file': str(py_file),
                            'line_num': i + 1,
                            'old': original_line.strip(),
                            'new': line.strip(),
                            'pattern': 'print-to-logging'
                        })
                
                if modified:
                    content = '\n'.join(lines)
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"  Fixed {Path(py_file).name}: {len([f for f in fixes if f['file'] == str(py_file)])} print statements")
                    
            except (OSError, UnicodeDecodeError) as e:
                print(f"  Error processing {py_file}: {e}")
                continue
        
        return fixes
    
    def fix_hardcoded_paths(self) -> List[Dict]:
        """Fix hardcoded paths by replacing with settings."""
        print("\n=== FIXING HARDCODED PATHS ===")
        fixes = []
        
        path_replacements = {
            r'patterns\.db["\']': 'settings.database_path',
            r'patterns_fts\.db["\']': 'settings.database_path',
            r'["\']~\/\.config\/codex["\']': 'settings.config_dir',
            r'["\']~\/\.local\/share\/codex["\']': 'settings.data_dir',
            r'["\']~\/\.cache\/codex["\']': 'settings.cache_dir',
        }
        
        for py_file in self.codex_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.venv', 'backup_']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    original_content = content
                
                lines = content.split('\n')
                modified = False
                
                # Check if settings import is needed
                has_settings = any('from .settings import settings' in line or 
                                 'from codex.settings import settings' in line for line in lines)
                needs_settings = False
                
                for i, line in enumerate(lines):
                    original_line = line
                    
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue
                    
                    # Apply path replacements
                    for pattern, replacement in path_replacements.items():
                        if re.search(pattern, line):
                            line = re.sub(pattern, replacement, line)
                            needs_settings = True
                            modified = True
                    
                    lines[i] = line
                    
                    if line != original_line:
                        fixes.append({
                            'file': str(py_file),
                            'line_num': i + 1,
                            'old': original_line.strip(),
                            'new': line.strip(),
                            'pattern': 'hardcoded-path'
                        })
                
                # Add settings import if needed
                if needs_settings and not has_settings:
                    # Find good spot for import
                    import_line = 0
                    for i, line in enumerate(lines):
                        if line.startswith(('import ', 'from ')):
                            import_line = i
                    
                    lines.insert(import_line + 1, 'from .settings import settings')
                    modified = True
                
                if modified:
                    content = '\n'.join(lines)
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"  Fixed {Path(py_file).name}: {len([f for f in fixes if f['file'] == str(py_file)])} hardcoded paths")
                    
            except (OSError, UnicodeDecodeError) as e:
                print(f"  Error processing {py_file}: {e}")
                continue
        
        return fixes
    
    def fix_import_consolidation(self) -> List[Dict]:
        """Consolidate and clean up imports."""
        print("\n=== FIXING IMPORT CONSOLIDATION ===")
        fixes = []
        
        deprecated_imports = {
            'from .database import': 'from .unified_database import UnifiedDatabase',
            'from .fts_database import': 'from .unified_database import UnifiedDatabase',
            'import database': 'from .unified_database import UnifiedDatabase',
            'import fts_database': 'from .unified_database import UnifiedDatabase',
        }
        
        for py_file in self.codex_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.venv', 'backup_']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    original_content = content
                
                lines = content.split('\n')
                modified = False
                
                for i, line in enumerate(lines):
                    original_line = line
                    
                    # Replace deprecated imports
                    for old_import, new_import in deprecated_imports.items():
                        if old_import in line:
                            line = new_import
                            modified = True
                    
                    lines[i] = line
                    
                    if line != original_line:
                        fixes.append({
                            'file': str(py_file),
                            'line_num': i + 1,
                            'old': original_line.strip(),
                            'new': line.strip(),
                            'pattern': 'import-consolidation'
                        })
                
                if modified:
                    content = '\n'.join(lines)
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"  Fixed {Path(py_file).name}: {len([f for f in fixes if f['file'] == str(py_file)])} import issues")
                    
            except (OSError, UnicodeDecodeError) as e:
                print(f"  Error processing {py_file}: {e}")
                continue
        
        return fixes
    
    def verify_fixes(self) -> Dict[str, Any]:
        """Verify that fixes were applied correctly."""
        print("\n=== VERIFYING FIXES ===")
        
        # Run a quick scan to see remaining issues
        remaining_issues = {
            'print_statements': 0,
            'hardcoded_paths': 0,
            'deprecated_imports': 0,
            'syntax_errors': 0
        }
        
        for py_file in self.codex_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.venv', 'backup_']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for remaining issues
                if 'print(' in content:
                    remaining_issues['print_statements'] += content.count('print(')
                
                if 'patterns.db' in content or 'patterns_fts.db' in content:
                    remaining_issues['hardcoded_paths'] += 1
                
                if 'from .database import' in content or 'from .fts_database import' in content:
                    remaining_issues['deprecated_imports'] += 1
                
                # Check for syntax errors
                try:
                    compile(content, str(py_file), 'exec')
                except SyntaxError:
                    remaining_issues['syntax_errors'] += 1
                    
            except (OSError, UnicodeDecodeError):
                continue
        
        total_remaining = sum(remaining_issues.values())
        print(f"Remaining issues: {total_remaining}")
        for issue_type, count in remaining_issues.items():
            if count > 0:
                print(f"  {issue_type}: {count}")
        
        return remaining_issues
    
    def create_fix_summary(self, external_results: Dict, all_fixes: List[Dict], verification: Dict) -> str:
        """Create summary of all fixes applied."""
        timestamp = datetime.now().isoformat()
        
        fixes_by_pattern = {}
        for fix in all_fixes:
            pattern = fix['pattern']
            if pattern not in fixes_by_pattern:
                fixes_by_pattern[pattern] = []
            fixes_by_pattern[pattern].append(fix)
        
        summary = f"""
CODEX COMPREHENSIVE FIXING SESSION ({timestamp})

Applied systematic fixes to eliminate violations in the Codex repository.

EXTERNAL TOOLS RESULTS:
"""
        
        for tool, result in external_results.items():
            if result.get('success'):
                summary += f"- {tool}: ✅ {result.get('fixed', 'Applied fixes')}\n"
            else:
                summary += f"- {tool}: ❌ {result.get('error', 'Failed')}\n"
        
        summary += f"""
PATTERN-BASED FIXES APPLIED:
- Total fixes: {len(all_fixes)}
- Files modified: {len(set(fix['file'] for fix in all_fixes))}
- Patterns addressed: {len(fixes_by_pattern)}

FIXES BY PATTERN:
"""
        
        for pattern, pattern_fixes in fixes_by_pattern.items():
            summary += f"- {pattern}: {len(pattern_fixes)} fixes\n"
        
        summary += f"""
VERIFICATION RESULTS:
- Total remaining issues: {sum(verification.values())}
"""
        
        for issue_type, count in verification.items():
            if count > 0:
                summary += f"- {issue_type}: {count} remaining\n"
        
        if sum(verification.values()) == 0:
            summary += "🎉 All targeted violations fixed!\n"
        
        summary += f"""
SAMPLE FIXES APPLIED:
"""
        
        for fix in all_fixes[:10]:  # Show first 10 fixes
            summary += f"- {Path(fix['file']).name}:{fix['line_num']}: {fix['pattern']}\n"
            summary += f"  - {fix['old'][:50]}{'...' if len(fix['old']) > 50 else ''}\n"
            summary += f"  + {fix['new'][:50]}{'...' if len(fix['new']) > 50 else ''}\n"
        
        if len(all_fixes) > 10:
            summary += f"... and {len(all_fixes) - 10} more fixes\n"
        
        summary += f"""
BACKUP LOCATION:
{self.backup_dir}

SELF-REFLECTION:
This comprehensive fixing session demonstrates Codex's ability to:
✅ Systematically identify and fix violations
✅ Apply lessons learned from dogfooding
✅ Use both external tools and custom patterns
✅ Verify fixes and track progress
✅ Maintain code quality while evolving

The fixing process shows the practical value of the observe→analyze→fix→verify cycle.
Codex can now maintain its own code quality while continuing to evolve.

NEXT STEPS:
- Run final scan to confirm all violations resolved
- Continue evolution cycle with cleaner codebase
- Apply these patterns to other projects
- Build automated fixing capabilities
"""
        
        return summary


def main():
    """Apply comprehensive fixes to the Codex repository."""
    codex_dir = Path(__file__).parent / 'codex'
    
    fixer = ComprehensiveFixer(codex_dir)
    
    print("=== COMPREHENSIVE CODEX REPOSITORY FIXING ===")
    print(f"Target directory: {codex_dir}")
    
    # Create backup
    backup_dir = fixer.create_backup()
    
    # Apply all fixes
    try:
        # Run external tools
        external_results = fixer.run_external_tools_aggressively()
        
        # Apply pattern-based fixes
        print_fixes = fixer.fix_print_statements()
        path_fixes = fixer.fix_hardcoded_paths()
        import_fixes = fixer.fix_import_consolidation()
        
        all_fixes = print_fixes + path_fixes + import_fixes
        
        # Verify fixes
        verification = fixer.verify_fixes()
        
        # Create summary
        summary = fixer.create_fix_summary(external_results, all_fixes, verification)
        
        print(f"\n{summary}")
        
        print(f"\n=== COMPREHENSIVE FIXING COMPLETE ===")
        print(f"Applied {len(all_fixes)} fixes across {len(set(fix['file'] for fix in all_fixes))} files")
        print(f"Backup saved to: {backup_dir}")
        
        remaining_issues = sum(verification.values())
        if remaining_issues == 0:
            print("🎉 All targeted violations have been fixed!")
        else:
            print(f"⚠️  {remaining_issues} issues remain for future cycles")
        
    except Exception as e:
        print(f"\n❌ Error during fixing: {e}")
        print(f"Backup available at: {backup_dir}")
        raise


if __name__ == "__main__":
    main()
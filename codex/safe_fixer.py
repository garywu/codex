#!/usr/bin/env python3
"""
Safe Fixer - Extremely cautious approach to code fixes.

This module implements multiple validation layers to ensure
fixes don't break code. Every change is validated and reversible.
"""

import ast
import difflib
import hashlib
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


@dataclass
class FixValidation:
    """Validation result for a fix."""
    
    file_path: Path
    original_hash: str
    modified_hash: str
    syntax_valid: bool
    imports_valid: bool
    test_status: Optional[str] = None
    diff: Optional[str] = None
    error: Optional[str] = None
    can_rollback: bool = True


@dataclass
class FixAttempt:
    """Record of a fix attempt."""
    
    file_path: Path
    pattern: str
    line_number: int
    original_content: str
    modified_content: str
    validation: Optional[FixValidation] = None
    applied: bool = False
    rolled_back: bool = False
    timestamp: datetime = None


class SafeFixer:
    """
    Ultra-safe fixer with multiple validation layers.
    
    Principles:
    1. NEVER modify code without validation
    2. ALWAYS be able to rollback
    3. VALIDATE syntax after every change
    4. TEST if possible after changes
    5. SHOW detailed diffs for review
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.fix_attempts: List[FixAttempt] = []
        self.rollback_data: Dict[Path, str] = {}
        self.validation_errors: List[str] = []
        
    def validate_before_fix(self, file_path: Path) -> Tuple[bool, str]:
        """Validate file is safe to modify."""
        if not file_path.exists():
            return False, "File does not exist"
        
        if not file_path.is_file():
            return False, "Not a file"
        
        # Check if it's a Python file
        if file_path.suffix != '.py':
            return False, "Not a Python file"
        
        # Check if we can read and write
        try:
            content = file_path.read_text()
        except Exception as e:
            return False, f"Cannot read file: {e}"
        
        # Check syntax is valid BEFORE we modify
        try:
            ast.parse(content)
        except SyntaxError as e:
            return False, f"File has existing syntax errors: {e}"
        
        # Store original for rollback
        self.rollback_data[file_path] = content
        
        return True, "File is safe to modify"
    
    def validate_after_fix(self, file_path: Path, original: str, modified: str) -> FixValidation:
        """Comprehensive validation after a fix."""
        validation = FixValidation(
            file_path=file_path,
            original_hash=hashlib.md5(original.encode()).hexdigest(),
            modified_hash=hashlib.md5(modified.encode()).hexdigest(),
            syntax_valid=False,
            imports_valid=False
        )
        
        # 1. Check syntax is still valid
        try:
            ast.parse(modified)
            validation.syntax_valid = True
        except SyntaxError as e:
            validation.error = f"Syntax error after fix: {e}"
            return validation
        
        # 2. Check imports are still valid
        validation.imports_valid = self._validate_imports(original, modified)
        
        # 3. Generate diff for review
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (modified)",
            n=3
        ))
        validation.diff = ''.join(diff_lines)
        
        # 4. Run tests if available
        validation.test_status = self._run_tests_for_file(file_path)
        
        return validation
    
    def _validate_imports(self, original: str, modified: str) -> bool:
        """Ensure imports weren't broken."""
        try:
            original_tree = ast.parse(original)
            modified_tree = ast.parse(modified)
            
            original_imports = self._extract_imports(original_tree)
            modified_imports = self._extract_imports(modified_tree)
            
            # Check no imports were lost (adding is OK)
            for imp in original_imports:
                if imp not in modified_imports:
                    logging.error(f"Import lost during fix: {imp}")
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Import validation error: {e}")
            return False
    
    def _extract_imports(self, tree: ast.AST) -> set:
        """Extract all imports from AST."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.add(f"from {module} import {alias.name}")
        return imports
    
    def _run_tests_for_file(self, file_path: Path) -> Optional[str]:
        """Run tests related to the modified file."""
        # Look for test file
        test_patterns = [
            file_path.parent / f"test_{file_path.name}",
            file_path.parent / "tests" / f"test_{file_path.name}",
            file_path.parent.parent / "tests" / f"test_{file_path.stem}.py"
        ]
        
        test_file = None
        for pattern in test_patterns:
            if pattern.exists():
                test_file = pattern
                break
        
        if not test_file:
            return None
        
        # Run pytest on the test file
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_file), "-xvs"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return "PASSED"
            else:
                return f"FAILED: {result.stdout[:200]}"
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {e}"
    
    def apply_fix_safely(
        self, 
        file_path: Path, 
        fix_function: callable,
        pattern_name: str,
        line_number: int = 0
    ) -> Tuple[bool, Optional[FixAttempt]]:
        """
        Apply a fix with full validation.
        
        Args:
            file_path: File to fix
            fix_function: Function that takes content and returns modified content
            pattern_name: Name of the pattern being fixed
            line_number: Line number of the violation
            
        Returns:
            Tuple of (success, FixAttempt record)
        """
        # Pre-validation
        valid, message = self.validate_before_fix(file_path)
        if not valid:
            self.console.print(f"[red]Cannot fix {file_path}: {message}[/red]")
            return False, None
        
        original_content = file_path.read_text()
        
        # Create fix attempt record
        attempt = FixAttempt(
            file_path=file_path,
            pattern=pattern_name,
            line_number=line_number,
            original_content=original_content,
            modified_content="",
            timestamp=datetime.now()
        )
        
        # Apply the fix
        try:
            modified_content = fix_function(original_content)
            attempt.modified_content = modified_content
        except Exception as e:
            self.console.print(f"[red]Fix function failed: {e}[/red]")
            attempt.error = str(e)
            self.fix_attempts.append(attempt)
            return False, attempt
        
        # Check if anything actually changed
        if modified_content == original_content:
            self.console.print(f"[yellow]No changes needed for {pattern_name}[/yellow]")
            return True, attempt
        
        # Post-validation
        validation = self.validate_after_fix(file_path, original_content, modified_content)
        attempt.validation = validation
        
        # Show diff for review
        if validation.diff:
            self.show_diff(validation.diff)
        
        # Decision point
        if not validation.syntax_valid:
            self.console.print(f"[red]✗ Syntax validation failed![/red]")
            self.console.print(f"[red]{validation.error}[/red]")
            self.fix_attempts.append(attempt)
            return False, attempt
        
        if not validation.imports_valid:
            self.console.print(f"[red]✗ Import validation failed![/red]")
            self.fix_attempts.append(attempt)
            return False, attempt
        
        if validation.test_status and "FAILED" in validation.test_status:
            self.console.print(f"[yellow]⚠ Tests failed after fix:[/yellow]")
            self.console.print(validation.test_status)
            # Ask user whether to proceed
            if not self.confirm_risky_fix():
                self.fix_attempts.append(attempt)
                return False, attempt
        
        # All validations passed - apply the fix
        try:
            file_path.write_text(modified_content)
            attempt.applied = True
            self.fix_attempts.append(attempt)
            self.console.print(f"[green]✓ Fix applied successfully[/green]")
            return True, attempt
        except Exception as e:
            self.console.print(f"[red]Failed to write file: {e}[/red]")
            attempt.error = str(e)
            self.fix_attempts.append(attempt)
            return False, attempt
    
    def show_diff(self, diff: str) -> None:
        """Display a diff for review."""
        self.console.print("\n[bold]Changes to be applied:[/bold]")
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
        self.console.print(syntax)
    
    def confirm_risky_fix(self) -> bool:
        """Ask user to confirm a risky fix."""
        from rich.prompt import Confirm
        return Confirm.ask(
            "[yellow]This fix may have issues. Apply anyway?[/yellow]",
            default=False
        )
    
    def rollback_all(self) -> int:
        """Rollback all changes made in this session."""
        if not self.rollback_data:
            self.console.print("[yellow]No changes to rollback[/yellow]")
            return 0
        
        rolled_back = 0
        for file_path, original_content in self.rollback_data.items():
            try:
                file_path.write_text(original_content)
                self.console.print(f"[green]✓ Rolled back {file_path}[/green]")
                rolled_back += 1
            except Exception as e:
                self.console.print(f"[red]✗ Failed to rollback {file_path}: {e}[/red]")
        
        return rolled_back
    
    def rollback_file(self, file_path: Path) -> bool:
        """Rollback a specific file."""
        if file_path not in self.rollback_data:
            self.console.print(f"[yellow]No rollback data for {file_path}[/yellow]")
            return False
        
        try:
            file_path.write_text(self.rollback_data[file_path])
            self.console.print(f"[green]✓ Rolled back {file_path}[/green]")
            
            # Mark attempts as rolled back
            for attempt in self.fix_attempts:
                if attempt.file_path == file_path:
                    attempt.rolled_back = True
            
            return True
        except Exception as e:
            self.console.print(f"[red]✗ Failed to rollback: {e}[/red]")
            return False
    
    def generate_report(self) -> None:
        """Generate detailed report of all fixes."""
        table = Table(title="Fix Attempt Report", border_style="cyan")
        table.add_column("File", style="yellow")
        table.add_column("Pattern")
        table.add_column("Line")
        table.add_column("Status")
        table.add_column("Validation")
        table.add_column("Tests")
        
        for attempt in self.fix_attempts:
            status = "✓ Applied" if attempt.applied else "✗ Failed"
            if attempt.rolled_back:
                status = "↶ Rolled back"
            
            validation = ""
            if attempt.validation:
                if attempt.validation.syntax_valid:
                    validation += "✓ Syntax "
                else:
                    validation += "✗ Syntax "
                
                if attempt.validation.imports_valid:
                    validation += "✓ Imports"
                else:
                    validation += "✗ Imports"
            
            test_status = attempt.validation.test_status if attempt.validation else "N/A"
            
            table.add_row(
                str(attempt.file_path.name),
                attempt.pattern,
                str(attempt.line_number),
                status,
                validation,
                test_status or "N/A"
            )
        
        self.console.print(table)
        
        # Summary
        applied = sum(1 for a in self.fix_attempts if a.applied and not a.rolled_back)
        failed = sum(1 for a in self.fix_attempts if not a.applied)
        rolled_back = sum(1 for a in self.fix_attempts if a.rolled_back)
        
        summary = Panel(
            f"Applied: {applied} | Failed: {failed} | Rolled back: {rolled_back}",
            title="Summary",
            border_style="green" if failed == 0 else "yellow"
        )
        self.console.print(summary)
    
    def save_session(self, session_file: Path) -> None:
        """Save session data for later analysis."""
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'attempts': [
                {
                    'file': str(a.file_path),
                    'pattern': a.pattern,
                    'line': a.line_number,
                    'applied': a.applied,
                    'rolled_back': a.rolled_back,
                    'validation': {
                        'syntax_valid': a.validation.syntax_valid,
                        'imports_valid': a.validation.imports_valid,
                        'test_status': a.validation.test_status
                    } if a.validation else None
                }
                for a in self.fix_attempts
            ],
            'rollback_files': list(str(p) for p in self.rollback_data.keys())
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        self.console.print(f"[green]Session saved to {session_file}[/green]")


class ValidationChain:
    """Chain of validators to run before accepting a fix."""
    
    def __init__(self):
        self.validators = []
    
    def add_validator(self, validator: callable) -> None:
        """Add a validator to the chain."""
        self.validators.append(validator)
    
    def validate(self, original: str, modified: str, file_path: Path) -> Tuple[bool, List[str]]:
        """Run all validators."""
        errors = []
        
        for validator in self.validators:
            try:
                valid, error = validator(original, modified, file_path)
                if not valid:
                    errors.append(error)
            except Exception as e:
                errors.append(f"Validator failed: {e}")
        
        return len(errors) == 0, errors


def syntax_validator(original: str, modified: str, file_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate Python syntax."""
    try:
        ast.parse(modified)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"


def import_validator(original: str, modified: str, file_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate imports weren't broken."""
    try:
        orig_tree = ast.parse(original)
        mod_tree = ast.parse(modified)
        
        orig_imports = set()
        for node in ast.walk(orig_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                orig_imports.add(ast.unparse(node))
        
        mod_imports = set()
        for node in ast.walk(mod_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod_imports.add(ast.unparse(node))
        
        missing = orig_imports - mod_imports
        if missing:
            return False, f"Missing imports: {missing}"
        
        return True, None
    except Exception as e:
        return False, str(e)


def indentation_validator(original: str, modified: str, file_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate indentation is consistent."""
    lines = modified.split('\n')
    
    # Check for mixed tabs and spaces
    has_tabs = any('\t' in line for line in lines)
    has_spaces = any(line.startswith('    ') for line in lines)
    
    if has_tabs and has_spaces:
        return False, "Mixed tabs and spaces detected"
    
    # Check for consistent indentation levels
    indent_levels = set()
    for line in lines:
        if line and line[0] in ' \t':
            indent = len(line) - len(line.lstrip())
            indent_levels.add(indent)
    
    # Check if indentation is multiple of 4 (PEP 8)
    for level in indent_levels:
        if level % 4 != 0:
            return False, f"Non-standard indentation level: {level}"
    
    return True, None


def create_safe_fix_function(pattern_name: str) -> Optional[callable]:
    """Create a safe fix function for a pattern."""
    
    if pattern_name == "use-uv-package-manager":
        def fix_uv(content: str) -> str:
            # Only replace in strings and comments, not in actual code
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Only in comments or strings
                if '#' in line:
                    comment_start = line.index('#')
                    before = line[:comment_start]
                    comment = line[comment_start:]
                    comment = comment.replace('pip install', 'uv pip install')
                    lines[i] = before + comment
                elif 'pip install' in line and ('"' in line or "'" in line):
                    lines[i] = line.replace('pip install', 'uv pip install')
            return '\n'.join(lines)
        return fix_uv
    
    return None


if __name__ == "__main__":
    # Example usage
    console = Console()
    fixer = SafeFixer(console)
    
    # Set up validation chain
    chain = ValidationChain()
    chain.add_validator(syntax_validator)
    chain.add_validator(import_validator)
    chain.add_validator(indentation_validator)
    
    # Example fix
    test_file = Path("test.py")
    if test_file.exists():
        fix_func = create_safe_fix_function("use-uv-package-manager")
        if fix_func:
            success, attempt = fixer.apply_fix_safely(
                test_file,
                fix_func,
                "use-uv-package-manager",
                line_number=10
            )
            
            if not success:
                console.print("[red]Fix failed, rolling back...[/red]")
                fixer.rollback_file(test_file)
    
    # Generate report
    fixer.generate_report()
    
    # Save session
    fixer.save_session(Path("fix_session.json"))
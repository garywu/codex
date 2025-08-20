#!/usr/bin/env python3
"""
Interactive Fixer for Codex

Provides an interactive command-line interface for fixing code violations
with Claude's intelligence for complex decisions.
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .models import PatternMatch
from .scanner import Scanner
from .unified_database import UnifiedDatabase


class FixStrategy(str, Enum):
    """Fix strategies for different violation types."""
    
    AUTOMATIC = "automatic"  # Can be fixed automatically
    GUIDED = "guided"  # Needs user input for parameters
    INTELLIGENT = "intelligent"  # Needs Claude's analysis
    MANUAL = "manual"  # Requires manual intervention
    SKIP = "skip"  # Cannot be auto-fixed


@dataclass
class FixPlan:
    """Plan for fixing a violation."""
    
    violation: PatternMatch
    strategy: FixStrategy
    fix_code: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.0
    requires_context: bool = False
    estimated_impact: str = "low"  # low, medium, high
    rollback_info: Optional[Dict[str, Any]] = None


class InteractiveFixer:
    """Interactive fixer with Claude intelligence integration."""
    
    def __init__(self, quiet: bool = False, auto_approve: bool = False):
        self.console = Console() if not quiet else None
        self.auto_approve = auto_approve
        self.db = UnifiedDatabase()
        self.scanner = Scanner(quiet=quiet)
        self.fix_strategies = self._load_fix_strategies()
        self.fixed_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.rollback_stack = []
        
    def _load_fix_strategies(self) -> Dict[str, FixStrategy]:
        """Load fix strategies for each pattern."""
        strategies = {
            # Security patterns - need intelligent review
            "no-cors-wildcard": FixStrategy.INTELLIGENT,
            "secure-jwt-storage": FixStrategy.INTELLIGENT,
            "sanitize-production-errors": FixStrategy.GUIDED,
            
            # Code quality - mostly automatic
            "mock-code-naming": FixStrategy.AUTOMATIC,
            "structured-logging": FixStrategy.GUIDED,
            "use-pydantic-validation": FixStrategy.INTELLIGENT,
            
            # Testing - needs context
            "minimum-test-coverage": FixStrategy.MANUAL,
            
            # Package management - automatic
            "use-uv-package-manager": FixStrategy.AUTOMATIC,
            "use-db-context-managers": FixStrategy.GUIDED,
        }
        return strategies
    
    async def run_interactive_fix(self, target_path: Path, pattern_filter: Optional[str] = None) -> int:
        """Run interactive fixing session."""
        if self.console:
            self.console.print(Panel.fit(
                "[bold cyan]🔧 Codex Interactive Fixer[/bold cyan]\n"
                "Intelligent code improvement with Claude assistance",
                border_style="cyan"
            ))
        
        # Scan for violations
        violations = await self._scan_for_violations(target_path, pattern_filter)
        
        if not violations:
            if self.console:
                self.console.print("[green]✅ No violations found![/green]")
            return 0
        
        # Group violations by pattern
        grouped_violations = self._group_violations(violations)
        
        # Show summary
        if self.console:
            self._show_violation_summary(grouped_violations)
        
        # Process each group
        for pattern_name, pattern_violations in grouped_violations.items():
            await self._process_pattern_group(pattern_name, pattern_violations)
        
        # Show final summary
        if self.console:
            self._show_final_summary()
        
        return 0 if self.failed_count == 0 else 1
    
    async def _scan_for_violations(self, target_path: Path, pattern_filter: Optional[str] = None) -> List[PatternMatch]:
        """Scan for violations to fix."""
        if self.console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Scanning for violations...", total=None)
                
                if target_path.is_file():
                    result = await self.scanner.scan_file(target_path)
                    violations = result.violations
                else:
                    results = await self.scanner.scan_directory(target_path)
                    violations = []
                    for result in results:
                        violations.extend(result.violations)
                
                progress.update(task, completed=True)
        else:
            if target_path.is_file():
                result = await self.scanner.scan_file(target_path)
                violations = result.violations
            else:
                results = await self.scanner.scan_directory(target_path)
                violations = []
                for result in results:
                    violations.extend(result.violations)
        
        # Filter by pattern if specified
        if pattern_filter:
            violations = [v for v in violations if pattern_filter in v.pattern_name]
        
        return violations
    
    def _group_violations(self, violations: List[PatternMatch]) -> Dict[str, List[PatternMatch]]:
        """Group violations by pattern name."""
        grouped = {}
        for violation in violations:
            if violation.pattern_name not in grouped:
                grouped[violation.pattern_name] = []
            grouped[violation.pattern_name].append(violation)
        return grouped
    
    def _show_violation_summary(self, grouped_violations: Dict[str, List[PatternMatch]]) -> None:
        """Show summary of violations found."""
        table = Table(title="Violations Summary", border_style="cyan")
        table.add_column("Pattern", style="yellow")
        table.add_column("Count", justify="right")
        table.add_column("Strategy", style="magenta")
        table.add_column("Auto-fixable", justify="center")
        
        total_violations = 0
        for pattern_name, violations in grouped_violations.items():
            count = len(violations)
            total_violations += count
            strategy = self.fix_strategies.get(pattern_name, FixStrategy.MANUAL)
            auto_fixable = "✅" if strategy in [FixStrategy.AUTOMATIC, FixStrategy.GUIDED] else "❌"
            table.add_row(pattern_name, str(count), strategy.value, auto_fixable)
        
        self.console.print(table)
        self.console.print(f"\n[bold]Total violations: {total_violations}[/bold]")
    
    async def _process_pattern_group(self, pattern_name: str, violations: List[PatternMatch]) -> None:
        """Process a group of violations for the same pattern."""
        strategy = self.fix_strategies.get(pattern_name, FixStrategy.MANUAL)
        
        if self.console:
            self.console.print(f"\n[bold yellow]Processing: {pattern_name}[/bold yellow]")
            self.console.print(f"Strategy: {strategy.value}")
            self.console.print(f"Violations: {len(violations)}")
        
        if strategy == FixStrategy.AUTOMATIC:
            await self._process_automatic_fixes(pattern_name, violations)
        elif strategy == FixStrategy.GUIDED:
            await self._process_guided_fixes(pattern_name, violations)
        elif strategy == FixStrategy.INTELLIGENT:
            await self._process_intelligent_fixes(pattern_name, violations)
        elif strategy == FixStrategy.MANUAL:
            self._process_manual_fixes(pattern_name, violations)
        else:  # SKIP
            self.skipped_count += len(violations)
            if self.console:
                self.console.print(f"[yellow]Skipped {len(violations)} violations (not auto-fixable)[/yellow]")
    
    async def _process_automatic_fixes(self, pattern_name: str, violations: List[PatternMatch]) -> None:
        """Process violations that can be fixed automatically."""
        fix_functions = {
            "mock-code-naming": self._fix_mock_naming,
            "use-uv-package-manager": self._fix_uv_package_manager,
        }
        
        fix_func = fix_functions.get(pattern_name)
        if not fix_func:
            if self.console:
                self.console.print(f"[red]No automatic fix available for {pattern_name}[/red]")
            self.failed_count += len(violations)
            return
        
        for violation in violations:
            if self.console:
                self.console.print(f"  Fixing: {violation.file_path}:{violation.line_number}")
            
            try:
                success = await fix_func(violation)
                if success:
                    self.fixed_count += 1
                    if self.console:
                        self.console.print(f"    [green]✅ Fixed[/green]")
                else:
                    self.failed_count += 1
                    if self.console:
                        self.console.print(f"    [red]❌ Failed[/red]")
            except Exception as e:
                self.failed_count += 1
                if self.console:
                    self.console.print(f"    [red]❌ Error: {e}[/red]")
    
    async def _process_guided_fixes(self, pattern_name: str, violations: List[PatternMatch]) -> None:
        """Process violations that need user guidance."""
        if self.console:
            self.console.print("[cyan]This pattern requires your input for proper fixing.[/cyan]")
        
        # Get user preferences once for the pattern
        preferences = await self._get_fix_preferences(pattern_name)
        
        for violation in violations:
            if self.console:
                self.console.print(f"\n[yellow]Violation:[/yellow] {violation.file_path}:{violation.line_number}")
                self.console.print(f"[dim]{violation.matched_code}[/dim]")
                
                if not self.auto_approve:
                    fix_it = Confirm.ask("Fix this violation?", default=True)
                    if not fix_it:
                        self.skipped_count += 1
                        continue
            
            try:
                success = await self._apply_guided_fix(pattern_name, violation, preferences)
                if success:
                    self.fixed_count += 1
                    if self.console:
                        self.console.print("[green]✅ Fixed[/green]")
                else:
                    self.failed_count += 1
                    if self.console:
                        self.console.print("[red]❌ Failed[/red]")
            except Exception as e:
                self.failed_count += 1
                if self.console:
                    self.console.print(f"[red]❌ Error: {e}[/red]")
    
    async def _process_intelligent_fixes(self, pattern_name: str, violations: List[PatternMatch]) -> None:
        """Process violations that need Claude's intelligence."""
        if self.console:
            self.console.print("[bold magenta]🤖 This requires intelligent analysis[/bold magenta]")
            self.console.print("Claude will analyze each violation and suggest appropriate fixes.\n")
        
        for violation in violations:
            if self.console:
                self.console.print(f"\n[yellow]Analyzing:[/yellow] {violation.file_path}:{violation.line_number}")
            
            # Create fix plan with Claude's help
            fix_plan = await self._create_intelligent_fix_plan(pattern_name, violation)
            
            if fix_plan.strategy == FixStrategy.SKIP:
                self.skipped_count += 1
                if self.console:
                    self.console.print(f"[yellow]Skipped: {fix_plan.explanation}[/yellow]")
                continue
            
            if self.console:
                self._show_fix_plan(fix_plan)
                
                if not self.auto_approve:
                    approve = Confirm.ask("Apply this fix?", default=True)
                    if not approve:
                        self.skipped_count += 1
                        continue
            
            # Apply the fix
            try:
                success = await self._apply_intelligent_fix(fix_plan)
                if success:
                    self.fixed_count += 1
                    if self.console:
                        self.console.print("[green]✅ Fixed successfully[/green]")
                else:
                    self.failed_count += 1
                    if self.console:
                        self.console.print("[red]❌ Fix failed[/red]")
            except Exception as e:
                self.failed_count += 1
                if self.console:
                    self.console.print(f"[red]❌ Error: {e}[/red]")
    
    def _process_manual_fixes(self, pattern_name: str, violations: List[PatternMatch]) -> None:
        """Process violations that require manual intervention."""
        self.skipped_count += len(violations)
        if self.console:
            self.console.print(f"[yellow]⚠️  {pattern_name} requires manual fixing[/yellow]")
            self.console.print(f"   {len(violations)} violations need manual attention")
            
            # Show locations for manual fixing
            for v in violations[:5]:  # Show first 5
                self.console.print(f"   - {v.file_path}:{v.line_number}")
            if len(violations) > 5:
                self.console.print(f"   ... and {len(violations) - 5} more")
    
    async def _fix_mock_naming(self, violation: PatternMatch) -> bool:
        """Fix mock function naming violations."""
        file_path = Path(violation.file_path)
        if not file_path.exists():
            return False
        
        content = file_path.read_text()
        
        # CRITICAL: Validate syntax before modification
        try:
            import ast
            ast.parse(content)
        except SyntaxError:
            if self.console:
                self.console.print(f"[red]⚠️  File has existing syntax errors, skipping[/red]")
            return False
        
        lines = content.split('\n')
        
        if violation.line_number and 0 < violation.line_number <= len(lines):
            line = lines[violation.line_number - 1]
            
            # Fix mock function naming
            import re
            # Pattern to find function definitions
            match = re.search(r'def\s+(\w+)\s*\(', line)
            if match:
                old_name = match.group(1)
                if not old_name.startswith('mock_'):
                    new_name = f'mock_{old_name}'
                    new_line = line.replace(f'def {old_name}', f'def {new_name}')
                    
                    # Store rollback info
                    self.rollback_stack.append({
                        'file': str(file_path),
                        'line': violation.line_number - 1,
                        'old': line,
                        'new': new_line
                    })
                    
                    lines[violation.line_number - 1] = new_line
                    
                    # Add warning log after function definition
                    indent = len(line) - len(line.lstrip())
                    warning_line = ' ' * (indent + 4) + 'logging.warning("Using mock function %s", __name__)'
                    lines.insert(violation.line_number, warning_line)
                    
                    # CRITICAL: Validate the fix before writing
                    new_content = '\n'.join(lines)
                    try:
                        ast.parse(new_content)
                    except SyntaxError as e:
                        if self.console:
                            self.console.print(f"[red]⚠️  Fix would create syntax error: {e}[/red]")
                        return False
                    
                    file_path.write_text(new_content)
                    return True
        
        return False
    
    async def _fix_uv_package_manager(self, violation: PatternMatch) -> bool:
        """Fix package manager to use uv."""
        file_path = Path(violation.file_path)
        if not file_path.exists():
            return False
        
        content = file_path.read_text()
        
        # Replace pip with uv
        replacements = [
            ('pip install', 'uv pip install'),
            ('pip freeze', 'uv pip freeze'),
            ('python -m pip', 'uv pip'),
        ]
        
        modified = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                modified = True
        
        if modified:
            # Store rollback info
            self.rollback_stack.append({
                'file': str(file_path),
                'content': file_path.read_text()
            })
            
            file_path.write_text(content)
            return True
        
        return False
    
    async def _get_fix_preferences(self, pattern_name: str) -> Dict[str, Any]:
        """Get user preferences for guided fixes."""
        preferences = {}
        
        if pattern_name == "structured-logging":
            if self.console and not self.auto_approve:
                log_format = Prompt.ask(
                    "Preferred log format",
                    choices=["json", "structured", "console"],
                    default="json"
                )
                preferences['format'] = log_format
            else:
                preferences['format'] = 'json'
        
        elif pattern_name == "use-db-context-managers":
            preferences['style'] = 'with'  # Use 'with' statements
        
        elif pattern_name == "sanitize-production-errors":
            preferences['mode'] = 'generic'  # Return generic messages
        
        return preferences
    
    async def _apply_guided_fix(self, pattern_name: str, violation: PatternMatch, preferences: Dict[str, Any]) -> bool:
        """Apply a guided fix with user preferences."""
        fix_functions = {
            "structured-logging": self._fix_structured_logging,
            "use-db-context-managers": self._fix_db_context_managers,
            "sanitize-production-errors": self._fix_error_sanitization,
        }
        
        fix_func = fix_functions.get(pattern_name)
        if fix_func:
            return await fix_func(violation, preferences)
        
        return False
    
    async def _fix_structured_logging(self, violation: PatternMatch, preferences: Dict[str, Any]) -> bool:
        """Fix logging to use structured format."""
        file_path = Path(violation.file_path)
        if not file_path.exists():
            return False
        
        content = file_path.read_text()
        lines = content.split('\n')
        
        if violation.line_number and 0 < violation.line_number <= len(lines):
            line = lines[violation.line_number - 1]
            
            # Convert print to structured logging
            import re
            if 'print(' in line:
                # Extract the print content
                match = re.search(r'print\((.*?)\)', line)
                if match:
                    print_content = match.group(1)
                    indent = len(line) - len(line.lstrip())
                    
                    if preferences['format'] == 'json':
                        new_line = f"{' ' * indent}logging.info({{'message': {print_content}}})"
                    else:
                        new_line = f"{' ' * indent}logging.info({print_content})"
                    
                    lines[violation.line_number - 1] = new_line
                    
                    # Ensure logging is imported
                    if 'import logging' not in content:
                        lines.insert(0, 'import logging')
                    
                    file_path.write_text('\n'.join(lines))
                    return True
        
        return False
    
    async def _fix_db_context_managers(self, violation: PatternMatch, preferences: Dict[str, Any]) -> bool:
        """Fix database access to use context managers."""
        # This would require more complex AST manipulation
        # For now, return False to indicate manual fix needed
        return False
    
    async def _fix_error_sanitization(self, violation: PatternMatch, preferences: Dict[str, Any]) -> bool:
        """Fix error messages to be sanitized for production."""
        file_path = Path(violation.file_path)
        if not file_path.exists():
            return False
        
        content = file_path.read_text()
        lines = content.split('\n')
        
        if violation.line_number and 0 < violation.line_number <= len(lines):
            line = lines[violation.line_number - 1]
            
            # Look for error returns
            import re
            if 'return' in line and ('error' in line.lower() or 'exception' in line.lower()):
                # Replace with generic message
                indent = len(line) - len(line.lstrip())
                new_line = f"{' ' * indent}return {{'error': 'An error occurred. Please try again.'}}"
                
                # Add comment about original error
                comment_line = f"{' ' * indent}# Original: {line.strip()}"
                
                lines[violation.line_number - 1] = comment_line
                lines.insert(violation.line_number, new_line)
                
                file_path.write_text('\n'.join(lines))
                return True
        
        return False
    
    async def _create_intelligent_fix_plan(self, pattern_name: str, violation: PatternMatch) -> FixPlan:
        """Create an intelligent fix plan using Claude's analysis."""
        # Read the file context
        file_path = Path(violation.file_path)
        if not file_path.exists():
            return FixPlan(
                violation=violation,
                strategy=FixStrategy.SKIP,
                explanation="File not found"
            )
        
        content = file_path.read_text()
        lines = content.split('\n')
        
        # Get context around the violation
        context_start = max(0, violation.line_number - 10) if violation.line_number else 0
        context_end = min(len(lines), violation.line_number + 10) if violation.line_number else len(lines)
        context_lines = lines[context_start:context_end]
        
        # Analyze based on pattern
        if pattern_name == "no-cors-wildcard":
            return self._analyze_cors_wildcard(violation, context_lines)
        elif pattern_name == "secure-jwt-storage":
            return self._analyze_jwt_storage(violation, context_lines)
        elif pattern_name == "use-pydantic-validation":
            return self._analyze_pydantic_validation(violation, context_lines)
        
        return FixPlan(
            violation=violation,
            strategy=FixStrategy.MANUAL,
            explanation="Pattern requires manual analysis"
        )
    
    def _analyze_cors_wildcard(self, violation: PatternMatch, context: List[str]) -> FixPlan:
        """Analyze CORS wildcard usage."""
        # Check if it's in test/dev code
        if 'test' in violation.file_path.lower() or 'dev' in violation.file_path.lower():
            return FixPlan(
                violation=violation,
                strategy=FixStrategy.SKIP,
                explanation="CORS wildcard acceptable in test/dev code"
            )
        
        # Suggest specific origins
        return FixPlan(
            violation=violation,
            strategy=FixStrategy.INTELLIGENT,
            fix_code="origins = ['https://app.example.com', 'https://api.example.com']",
            explanation="Replace wildcard with specific allowed origins",
            confidence=0.8,
            requires_context=True,
            estimated_impact="high"
        )
    
    def _analyze_jwt_storage(self, violation: PatternMatch, context: List[str]) -> FixPlan:
        """Analyze JWT secret storage."""
        return FixPlan(
            violation=violation,
            strategy=FixStrategy.INTELLIGENT,
            fix_code="jwt_secret = os.environ.get('JWT_SECRET')",
            explanation="Move JWT secret to environment variable",
            confidence=0.9,
            requires_context=False,
            estimated_impact="high"
        )
    
    def _analyze_pydantic_validation(self, violation: PatternMatch, context: List[str]) -> FixPlan:
        """Analyze where Pydantic validation is needed."""
        # This would need more complex analysis
        return FixPlan(
            violation=violation,
            strategy=FixStrategy.MANUAL,
            explanation="Pydantic model creation requires understanding data structure",
            requires_context=True
        )
    
    def _show_fix_plan(self, plan: FixPlan) -> None:
        """Display a fix plan to the user."""
        panel_content = f"""
[bold]Fix Plan[/bold]
Strategy: {plan.strategy.value}
Confidence: {plan.confidence:.0%}
Impact: {plan.estimated_impact}

[yellow]Explanation:[/yellow]
{plan.explanation}

[cyan]Suggested Fix:[/cyan]
{plan.fix_code if plan.fix_code else 'Manual intervention required'}
"""
        self.console.print(Panel(panel_content, border_style="magenta"))
    
    async def _apply_intelligent_fix(self, plan: FixPlan) -> bool:
        """Apply an intelligent fix plan."""
        if not plan.fix_code:
            return False
        
        file_path = Path(plan.violation.file_path)
        if not file_path.exists():
            return False
        
        content = file_path.read_text()
        lines = content.split('\n')
        
        if plan.violation.line_number and 0 < plan.violation.line_number <= len(lines):
            # Store rollback info
            self.rollback_stack.append({
                'file': str(file_path),
                'line': plan.violation.line_number - 1,
                'old': lines[plan.violation.line_number - 1],
                'plan': plan
            })
            
            # Apply the fix
            lines[plan.violation.line_number - 1] = plan.fix_code
            file_path.write_text('\n'.join(lines))
            return True
        
        return False
    
    def _show_final_summary(self) -> None:
        """Show final summary of the fixing session."""
        total = self.fixed_count + self.skipped_count + self.failed_count
        
        panel_content = f"""
[bold green]✅ Fixed: {self.fixed_count}[/bold green]
[bold yellow]⏭️  Skipped: {self.skipped_count}[/bold yellow]
[bold red]❌ Failed: {self.failed_count}[/bold red]

[bold]Total processed: {total}[/bold]
Success rate: {(self.fixed_count / total * 100) if total > 0 else 0:.1f}%
"""
        
        self.console.print(Panel.fit(
            panel_content,
            title="[bold]Fixing Summary[/bold]",
            border_style="green" if self.failed_count == 0 else "yellow"
        ))
        
        if self.rollback_stack:
            self.console.print(f"\n[dim]Rollback information saved ({len(self.rollback_stack)} changes)[/dim]")
    
    async def rollback_changes(self) -> int:
        """Rollback all changes made in this session."""
        if not self.rollback_stack:
            if self.console:
                self.console.print("[yellow]No changes to rollback[/yellow]")
            return 0
        
        if self.console:
            self.console.print(f"[bold]Rolling back {len(self.rollback_stack)} changes...[/bold]")
        
        for change in reversed(self.rollback_stack):
            try:
                file_path = Path(change['file'])
                if 'content' in change:
                    # Full content rollback
                    file_path.write_text(change['content'])
                elif 'old' in change:
                    # Line-by-line rollback
                    content = file_path.read_text()
                    lines = content.split('\n')
                    lines[change['line']] = change['old']
                    file_path.write_text('\n'.join(lines))
                
                if self.console:
                    self.console.print(f"  ✅ Rolled back: {file_path}")
            except Exception as e:
                if self.console:
                    self.console.print(f"  ❌ Failed to rollback {change['file']}: {e}")
        
        self.rollback_stack.clear()
        return 0


async def main():
    """Main entry point for interactive fixer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive code fixer with Claude intelligence")
    parser.add_argument("path", type=Path, help="Path to scan and fix")
    parser.add_argument("--pattern", help="Fix only specific pattern")
    parser.add_argument("--auto", action="store_true", help="Auto-approve all fixes")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("--rollback", action="store_true", help="Rollback previous changes")
    
    args = parser.parse_args()
    
    fixer = InteractiveFixer(quiet=args.quiet, auto_approve=args.auto)
    
    if args.rollback:
        return await fixer.rollback_changes()
    else:
        return await fixer.run_interactive_fix(args.path, args.pattern)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
#!/usr/bin/env python3
"""
Fix Context Analyzer

Analyzes the context around violations to make intelligent fix decisions.
This helps prevent fixes that would break code due to dependencies.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class CodeContext:
    """Context information about code around a violation."""
    
    file_path: Path
    line_number: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    imports: List[str] = None
    local_variables: Set[str] = None
    called_functions: Set[str] = None
    is_test_code: bool = False
    is_async: bool = False
    has_decorators: bool = False
    indentation_level: int = 0
    surrounding_try_except: bool = False
    in_conditional: bool = False
    dependencies: Set[str] = None


class FixContextAnalyzer:
    """Analyzes context to make intelligent fix decisions."""
    
    def analyze_violation_context(
        self, 
        file_path: Path, 
        line_number: int,
        window_size: int = 10
    ) -> CodeContext:
        """
        Analyze the context around a violation.
        
        Args:
            file_path: Path to the file
            line_number: Line number of violation
            window_size: Lines before/after to analyze
            
        Returns:
            CodeContext with detailed information
        """
        if not file_path.exists():
            return CodeContext(file_path=file_path, line_number=line_number)
        
        content = file_path.read_text()
        lines = content.split('\n')
        
        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Can't parse, return minimal context
            return CodeContext(
                file_path=file_path,
                line_number=line_number,
                is_test_code=self._is_test_file(file_path)
            )
        
        context = CodeContext(
            file_path=file_path,
            line_number=line_number,
            imports=[],
            local_variables=set(),
            called_functions=set(),
            dependencies=set(),
            is_test_code=self._is_test_file(file_path)
        )
        
        # Find the node at the specified line
        target_node = self._find_node_at_line(tree, line_number)
        
        if target_node:
            # Get function/class context
            context.function_name = self._get_enclosing_function(target_node, tree)
            context.class_name = self._get_enclosing_class(target_node, tree)
            
            # Check if async
            context.is_async = self._is_async_context(target_node, tree)
            
            # Check decorators
            context.has_decorators = self._has_decorators(target_node, tree)
            
            # Get local variables
            context.local_variables = self._extract_local_variables(target_node, tree)
            
            # Get called functions
            context.called_functions = self._extract_called_functions(target_node)
            
            # Check if in try/except
            context.surrounding_try_except = self._in_try_except(target_node, tree)
            
            # Check if in conditional
            context.in_conditional = self._in_conditional(target_node, tree)
        
        # Extract imports
        context.imports = self._extract_imports(tree)
        
        # Calculate indentation
        if 0 <= line_number - 1 < len(lines):
            line = lines[line_number - 1]
            context.indentation_level = len(line) - len(line.lstrip())
        
        # Analyze dependencies
        context.dependencies = self._analyze_dependencies(content, line_number, window_size)
        
        return context
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file."""
        path_str = str(file_path).lower()
        return any(pattern in path_str for pattern in ['test', 'spec', 'tests'])
    
    def _find_node_at_line(self, tree: ast.AST, line_number: int) -> Optional[ast.AST]:
        """Find the AST node at the specified line."""
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno == line_number:
                return node
        
        # Try to find closest node
        closest_node = None
        min_distance = float('inf')
        
        for node in ast.walk(tree):
            if hasattr(node, 'lineno'):
                distance = abs(node.lineno - line_number)
                if distance < min_distance:
                    min_distance = distance
                    closest_node = node
        
        return closest_node
    
    def _get_enclosing_function(self, node: ast.AST, tree: ast.AST) -> Optional[str]:
        """Get the name of the enclosing function."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.FunctionDef):
                for child in ast.walk(parent):
                    if child == node:
                        return parent.name
        return None
    
    def _get_enclosing_class(self, node: ast.AST, tree: ast.AST) -> Optional[str]:
        """Get the name of the enclosing class."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.walk(parent):
                    if child == node:
                        return parent.name
        return None
    
    def _is_async_context(self, node: ast.AST, tree: ast.AST) -> bool:
        """Check if node is in async context."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.AsyncFunctionDef):
                for child in ast.walk(parent):
                    if child == node:
                        return True
        return False
    
    def _has_decorators(self, node: ast.AST, tree: ast.AST) -> bool:
        """Check if the enclosing function/class has decorators."""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for child in ast.walk(parent):
                    if child == node and parent.decorator_list:
                        return True
        return False
    
    def _extract_local_variables(self, node: ast.AST, tree: ast.AST) -> Set[str]:
        """Extract local variables in scope."""
        variables = set()
        
        # Find the enclosing function
        enclosing_func = None
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(parent):
                    if child == node:
                        enclosing_func = parent
                        break
        
        if enclosing_func:
            for node in ast.walk(enclosing_func):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    variables.add(node.id)
        
        return variables
    
    def _extract_called_functions(self, node: ast.AST) -> Set[str]:
        """Extract functions called in the node."""
        functions = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    functions.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    functions.add(child.func.attr)
        
        return functions
    
    def _in_try_except(self, node: ast.AST, tree: ast.AST) -> bool:
        """Check if node is within a try/except block."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.Try):
                for child in ast.walk(parent):
                    if child == node:
                        return True
        return False
    
    def _in_conditional(self, node: ast.AST, tree: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.If, ast.While, ast.For)):
                for child in ast.walk(parent):
                    if child == node:
                        return True
        return False
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all imports from the file."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
        
        return imports
    
    def _analyze_dependencies(
        self, 
        content: str, 
        line_number: int, 
        window_size: int
    ) -> Set[str]:
        """Analyze what the code at this line depends on."""
        lines = content.split('\n')
        dependencies = set()
        
        # Get window of lines
        start = max(0, line_number - window_size)
        end = min(len(lines), line_number + window_size)
        
        for i in range(start, end):
            if i < len(lines):
                line = lines[i]
                
                # Look for variable usage
                var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*='
                matches = re.findall(var_pattern, line)
                dependencies.update(matches)
                
                # Look for function calls
                func_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                matches = re.findall(func_pattern, line)
                dependencies.update(matches)
        
        return dependencies
    
    def is_fix_safe_in_context(
        self, 
        context: CodeContext, 
        fix_type: str
    ) -> Tuple[bool, str]:
        """
        Determine if a fix is safe given the context.
        
        Args:
            context: The code context
            fix_type: Type of fix to apply
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check async context
        if context.is_async and fix_type in ["blocking-io", "synchronous-call"]:
            return False, "Cannot add blocking operations in async context"
        
        # Check test context
        if context.is_test_code:
            # More lenient in test code
            if fix_type in ["mock-code-naming", "test-assertions"]:
                return True, "Safe fix in test code"
        
        # Check decorator context
        if context.has_decorators:
            if fix_type in ["function-signature-change"]:
                return False, "Function with decorators may have specific signature requirements"
        
        # Check try/except context
        if context.surrounding_try_except:
            if fix_type in ["error-handling-change"]:
                return False, "Already within error handling context"
        
        # Check conditional context
        if context.in_conditional:
            if fix_type in ["early-return", "control-flow-change"]:
                return False, "Within conditional - control flow changes risky"
        
        # Check dependencies
        if fix_type == "import-change":
            # Check if imports are used
            for imp in context.imports:
                module_name = imp.split()[-1]
                if module_name in context.dependencies:
                    return False, f"Import {module_name} is actively used"
        
        return True, "Context appears safe for fix"
    
    def suggest_fix_adjustments(
        self, 
        context: CodeContext, 
        original_fix: str
    ) -> str:
        """
        Suggest adjustments to a fix based on context.
        
        Args:
            context: The code context
            original_fix: The original fix code
            
        Returns:
            Adjusted fix code
        """
        adjusted_fix = original_fix
        
        # Adjust indentation
        if context.indentation_level > 0:
            indent = ' ' * context.indentation_level
            lines = adjusted_fix.split('\n')
            adjusted_lines = [indent + line if line.strip() else line for line in lines]
            adjusted_fix = '\n'.join(adjusted_lines)
        
        # Add async if needed
        if context.is_async and 'def ' in adjusted_fix:
            adjusted_fix = adjusted_fix.replace('def ', 'async def ')
        
        # Add imports if missing
        required_imports = self._detect_required_imports(adjusted_fix)
        existing_imports = set(context.imports)
        
        for req_import in required_imports:
            if req_import not in existing_imports:
                adjusted_fix = f"{req_import}\n{adjusted_fix}"
        
        return adjusted_fix
    
    def _detect_required_imports(self, code: str) -> Set[str]:
        """Detect imports required by code."""
        required = set()
        
        # Common patterns
        if 'logging.' in code or 'logger.' in code:
            required.add('import logging')
        
        if 'os.environ' in code:
            required.add('import os')
        
        if 'Path(' in code:
            required.add('from pathlib import Path')
        
        if 'typing.' in code:
            required.add('import typing')
        
        if 'asyncio.' in code:
            required.add('import asyncio')
        
        return required


class FixConflictDetector:
    """Detects potential conflicts between fixes."""
    
    def detect_conflicts(
        self, 
        fixes: List[Dict[str, Any]]
    ) -> List[Tuple[int, int, str]]:
        """
        Detect conflicts between multiple fixes.
        
        Args:
            fixes: List of fix dictionaries with 'file', 'line', 'pattern' keys
            
        Returns:
            List of (fix1_index, fix2_index, conflict_reason) tuples
        """
        conflicts = []
        
        for i, fix1 in enumerate(fixes):
            for j, fix2 in enumerate(fixes[i+1:], i+1):
                conflict = self._check_conflict(fix1, fix2)
                if conflict:
                    conflicts.append((i, j, conflict))
        
        return conflicts
    
    def _check_conflict(self, fix1: Dict, fix2: Dict) -> Optional[str]:
        """Check if two fixes conflict."""
        # Same file and overlapping lines
        file1 = fix1.get('file_path') or fix1.get('file')
        file2 = fix2.get('file_path') or fix2.get('file')
        
        if file1 == file2:
            line1 = fix1.get('line_number') or fix1.get('line', 0)
            line2 = fix2.get('line_number') or fix2.get('line', 0)
            
            # Adjacent or same lines
            if abs(line1 - line2) <= 1:
                return f"Fixes on adjacent lines {line1} and {line2}"
            
            # Both modify imports
            pattern1 = fix1.get('pattern_name') or fix1.get('pattern', '')
            pattern2 = fix2.get('pattern_name') or fix2.get('pattern', '')
            
            if pattern1 in ['import-order', 'unused-import'] and \
               pattern2 in ['import-order', 'unused-import']:
                return "Both fixes modify imports"
            
            # Both modify function signature
            if pattern1 in ['function-signature', 'type-hints'] and \
               pattern2 in ['function-signature', 'type-hints']:
                return "Both fixes modify function signature"
        
        return None
    
    def resolve_conflicts(
        self, 
        fixes: List[Dict[str, Any]], 
        conflicts: List[Tuple[int, int, str]]
    ) -> List[Dict[str, Any]]:
        """
        Resolve conflicts by prioritizing fixes.
        
        Args:
            fixes: List of fixes
            conflicts: List of detected conflicts
            
        Returns:
            List of non-conflicting fixes
        """
        # Mark conflicting fixes
        conflicting_indices = set()
        for i, j, _ in conflicts:
            # Keep the higher priority fix
            pattern1 = fixes[i].get('pattern_name') or fixes[i].get('pattern', '')
            pattern2 = fixes[j].get('pattern_name') or fixes[j].get('pattern', '')
            fix1_priority = self._get_fix_priority(pattern1)
            fix2_priority = self._get_fix_priority(pattern2)
            
            if fix1_priority < fix2_priority:
                conflicting_indices.add(i)
            else:
                conflicting_indices.add(j)
        
        # Return non-conflicting fixes
        return [fix for i, fix in enumerate(fixes) if i not in conflicting_indices]
    
    def _get_fix_priority(self, pattern: str) -> int:
        """Get priority of a fix pattern (lower = higher priority)."""
        priorities = {
            'security': 0,
            'syntax-error': 1,
            'import-error': 2,
            'type-error': 3,
            'logic-error': 4,
            'style': 5,
            'formatting': 6
        }
        
        # Map patterns to categories
        if 'security' in pattern or 'jwt' in pattern or 'cors' in pattern:
            return priorities['security']
        elif 'syntax' in pattern:
            return priorities['syntax-error']
        elif 'import' in pattern:
            return priorities['import-error']
        elif 'type' in pattern:
            return priorities['type-error']
        elif 'mock' in pattern or 'test' in pattern:
            return priorities['logic-error']
        else:
            return priorities['style']


if __name__ == "__main__":
    # Example usage
    analyzer = FixContextAnalyzer()
    
    # Analyze context around a violation
    test_file = Path("test.py")
    if test_file.exists():
        context = analyzer.analyze_violation_context(test_file, line_number=10)
        
        print(f"Context for {test_file}:10")
        print(f"  Function: {context.function_name}")
        print(f"  Class: {context.class_name}")
        print(f"  Is async: {context.is_async}")
        print(f"  Is test: {context.is_test_code}")
        print(f"  Local vars: {context.local_variables}")
        print(f"  Dependencies: {context.dependencies}")
        
        # Check if fix is safe
        is_safe, reason = analyzer.is_fix_safe_in_context(context, "mock-code-naming")
        print(f"\nFix safety: {is_safe}")
        print(f"Reason: {reason}")
    
    # Test conflict detection
    detector = FixConflictDetector()
    
    fixes = [
        {'file': 'app.py', 'line': 10, 'pattern': 'import-order'},
        {'file': 'app.py', 'line': 11, 'pattern': 'unused-import'},
        {'file': 'app.py', 'line': 50, 'pattern': 'mock-naming'},
    ]
    
    conflicts = detector.detect_conflicts(fixes)
    if conflicts:
        print("\nConflicts detected:")
        for i, j, reason in conflicts:
            print(f"  Fix {i} conflicts with Fix {j}: {reason}")
        
        resolved = detector.resolve_conflicts(fixes, conflicts)
        print(f"\nResolved to {len(resolved)} non-conflicting fixes")
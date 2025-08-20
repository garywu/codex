#!/usr/bin/env python3
"""
Test Suite for Safe Fixing System

Tests various edge cases and ensures fixes don't break code.
"""

import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from codex.safe_fixer import SafeFixer, syntax_validator, import_validator, indentation_validator
from codex.fix_validation_rules import FixSafetyAnalyzer


class TestSafeFixer(unittest.TestCase):
    """Test the SafeFixer class."""
    
    def setUp(self):
        self.fixer = SafeFixer(console=MagicMock())
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def test_validate_before_fix_valid_file(self):
        """Test validation of a valid Python file."""
        test_file = self.temp_path / "valid.py"
        test_file.write_text("def hello():\n    return 'world'\n")
        
        valid, message = self.fixer.validate_before_fix(test_file)
        self.assertTrue(valid)
        self.assertEqual(message, "File is safe to modify")
    
    def test_validate_before_fix_syntax_error(self):
        """Test validation rejects file with syntax errors."""
        test_file = self.temp_path / "invalid.py"
        test_file.write_text("def hello(\n    return 'world'\n")
        
        valid, message = self.fixer.validate_before_fix(test_file)
        self.assertFalse(valid)
        self.assertIn("syntax errors", message)
    
    def test_validate_before_fix_non_python(self):
        """Test validation rejects non-Python files."""
        test_file = self.temp_path / "data.json"
        test_file.write_text('{"key": "value"}')
        
        valid, message = self.fixer.validate_before_fix(test_file)
        self.assertFalse(valid)
        self.assertEqual(message, "Not a Python file")
    
    def test_rollback_functionality(self):
        """Test rollback restores original content."""
        test_file = self.temp_path / "test.py"
        original = "print('hello')\n"
        test_file.write_text(original)
        
        # Store for rollback
        self.fixer.rollback_data[test_file] = original
        
        # Modify file
        test_file.write_text("print('modified')\n")
        
        # Rollback
        success = self.fixer.rollback_file(test_file)
        self.assertTrue(success)
        self.assertEqual(test_file.read_text(), original)
    
    def test_fix_breaks_syntax(self):
        """Test that fixes breaking syntax are rejected."""
        test_file = self.temp_path / "syntax_test.py"
        original = "def test():\n    pass\n"
        test_file.write_text(original)
        
        # Fix function that breaks syntax
        def bad_fix(content):
            return "def test(\n    pass\n"
        
        success, attempt = self.fixer.apply_fix_safely(
            test_file,
            bad_fix,
            "test-pattern",
            line_number=1
        )
        
        self.assertFalse(success)
        self.assertIsNotNone(attempt)
        self.assertFalse(attempt.validation.syntax_valid)
        # File should remain unchanged
        self.assertEqual(test_file.read_text(), original)
    
    def test_fix_removes_imports(self):
        """Test that fixes removing imports are rejected."""
        test_file = self.temp_path / "import_test.py"
        original = "import os\nimport sys\n\ndef test():\n    pass\n"
        test_file.write_text(original)
        
        # Fix function that removes an import
        def bad_fix(content):
            return "import os\n\ndef test():\n    pass\n"
        
        success, attempt = self.fixer.apply_fix_safely(
            test_file,
            bad_fix,
            "test-pattern",
            line_number=1
        )
        
        self.assertFalse(success)
        self.assertFalse(attempt.validation.imports_valid)


class TestValidators(unittest.TestCase):
    """Test individual validators."""
    
    def test_syntax_validator_valid(self):
        """Test syntax validator with valid code."""
        original = "print('hello')"
        modified = "print('world')"
        
        valid, error = syntax_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_syntax_validator_invalid(self):
        """Test syntax validator with invalid code."""
        original = "print('hello')"
        modified = "print('world'"  # Missing closing parenthesis
        
        valid, error = syntax_validator(original, modified, Path("test.py"))
        self.assertFalse(valid)
        self.assertIn("Syntax error", error)
    
    def test_import_validator_preserved(self):
        """Test import validator when imports are preserved."""
        original = "import os\nimport sys\nprint('test')"
        modified = "import os\nimport sys\nimport json\nprint('test')"
        
        valid, error = import_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)  # Adding imports is OK
    
    def test_import_validator_removed(self):
        """Test import validator when imports are removed."""
        original = "import os\nimport sys\nprint('test')"
        modified = "import os\nprint('test')"  # sys import removed
        
        valid, error = import_validator(original, modified, Path("test.py"))
        self.assertFalse(valid)
        self.assertIn("Missing imports", error)
    
    def test_indentation_validator_consistent(self):
        """Test indentation validator with consistent indentation."""
        original = "def test():\n    pass"
        modified = "def test():\n    print('hello')\n    pass"
        
        valid, error = indentation_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)
    
    def test_indentation_validator_mixed(self):
        """Test indentation validator with mixed tabs/spaces."""
        original = "def test():\n    pass"
        modified = "def test():\n    print('hello')\n\tpass"  # Mixed spaces and tab
        
        valid, error = indentation_validator(original, modified, Path("test.py"))
        self.assertFalse(valid)
        self.assertIn("Mixed tabs and spaces", error)


class TestFixSafetyAnalyzer(unittest.TestCase):
    """Test the FixSafetyAnalyzer."""
    
    def test_never_auto_fix_patterns(self):
        """Test that security-critical patterns are never auto-fixed."""
        analyzer = FixSafetyAnalyzer()
        
        is_safe, reason = analyzer.is_fix_safe(
            "secure-jwt-storage",
            "auth/handler.py",
            "JWT_SECRET = 'hardcoded'"
        )
        
        self.assertFalse(is_safe)
        self.assertIn("security-critical", reason)
    
    def test_protected_files(self):
        """Test that protected files are not modified."""
        analyzer = FixSafetyAnalyzer()
        
        is_safe, reason = analyzer.is_fix_safe(
            "mock-code-naming",
            "project/__init__.py",
            "def test():"
        )
        
        self.assertFalse(is_safe)
        self.assertIn("protected", reason)
    
    def test_critical_path_detection(self):
        """Test detection of critical code paths."""
        analyzer = FixSafetyAnalyzer()
        
        is_safe, reason = analyzer.is_fix_safe(
            "use-uv-package-manager",
            "security/auth_module.py",
            "pip install requests"
        )
        
        self.assertFalse(is_safe)
        self.assertIn("critical pattern", reason)
    
    def test_safe_pattern_in_test_file(self):
        """Test that safe patterns in test files are allowed."""
        analyzer = FixSafetyAnalyzer()
        
        is_safe, reason = analyzer.is_fix_safe(
            "mock-code-naming",
            "tests/test_example.py",
            "def fake_function():"
        )
        
        self.assertTrue(is_safe)
        self.assertIn("Test file", reason)
    
    def test_dangerous_keywords_detection(self):
        """Test detection of dangerous keywords in code."""
        analyzer = FixSafetyAnalyzer()
        
        is_safe, reason = analyzer.is_fix_safe(
            "use-uv-package-manager",
            "script.py",
            "eval(user_input)"
        )
        
        self.assertFalse(is_safe)
        self.assertIn("dangerous keyword", reason)
    
    def test_risk_level_estimation(self):
        """Test risk level estimation."""
        analyzer = FixSafetyAnalyzer()
        
        # Critical risk
        risk = analyzer.estimate_risk_level("secure-jwt-storage", "auth.py")
        self.assertEqual(risk, "critical")
        
        # Low risk in test
        risk = analyzer.estimate_risk_level("mock-code-naming", "test_file.py")
        self.assertEqual(risk, "low")
        
        # High risk in critical path
        risk = analyzer.estimate_risk_level("use-uv-package-manager", "payment/processor.py")
        self.assertEqual(risk, "high")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and complex scenarios."""
    
    def test_unicode_in_file(self):
        """Test handling of Unicode characters."""
        content = "# -*- coding: utf-8 -*-\n# Comment with émoji 🎉\nprint('hello')\n"
        
        valid, error = syntax_validator(content, content, Path("test.py"))
        self.assertTrue(valid)
    
    def test_multiline_strings(self):
        """Test preservation of multiline strings."""
        original = '"""\nMultiline\nstring\n"""\nprint("test")'
        modified = '"""\nMultiline\nstring\n"""\nprint("modified")'
        
        valid, error = syntax_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)
    
    def test_complex_imports(self):
        """Test complex import statements."""
        original = "from typing import List, Dict, Optional\nfrom ..parent import module"
        modified = "from typing import List, Dict, Optional, Set\nfrom ..parent import module"
        
        valid, error = import_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)  # Adding to imports is OK
    
    def test_async_syntax(self):
        """Test async/await syntax preservation."""
        content = "async def test():\n    await something()\n    return 42\n"
        
        valid, error = syntax_validator(content, content, Path("test.py"))
        self.assertTrue(valid)
    
    def test_type_annotations(self):
        """Test preservation of type annotations."""
        content = "def test(x: int, y: str) -> bool:\n    return True\n"
        
        valid, error = syntax_validator(content, content, Path("test.py"))
        self.assertTrue(valid)


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world fixing scenarios."""
    
    def test_mock_naming_fix(self):
        """Test actual mock naming fix."""
        original = """def fake_database():
    return {"connected": True}
"""
        
        expected = """def mock_database():
    logging.warning("Using mock function %s", __name__)
    return {"connected": True}
"""
        
        # Simulate the fix
        lines = original.split('\n')
        lines[0] = lines[0].replace('fake_database', 'mock_database')
        lines.insert(1, '    logging.warning("Using mock function %s", __name__)')
        modified = '\n'.join(lines)
        
        # Validate
        valid, error = syntax_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)
    
    def test_package_manager_fix(self):
        """Test package manager replacement."""
        original = 'subprocess.run(["pip", "install", "requests"])'
        modified = 'subprocess.run(["uv", "pip", "install", "requests"])'
        
        valid, error = syntax_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)
    
    def test_error_sanitization_fix(self):
        """Test error message sanitization."""
        original = 'return {"error": str(e), "traceback": e.__traceback__}'
        modified = 'return {"error": "An error occurred. Please try again."}'
        
        valid, error = syntax_validator(original, modified, Path("test.py"))
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
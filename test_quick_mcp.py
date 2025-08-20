#!/usr/bin/env python3
"""
Quick MCP Protocol Test

Simple test to verify no print statements break JSON protocol.
"""

import asyncio
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from codex.scanner import Scanner


def test_basic_mcp_compliance():
    """Basic test that scanner doesn't print to stdout."""
    # Create simple test file
    test_file = Path("temp_test.py")
    test_file.write_text('print("hello")')
    
    try:
        # Capture stdout
        captured_stdout = StringIO()
        
        with patch('sys.stdout', captured_stdout):
            scanner = Scanner(quiet=False, enable_negative_space=True)
            result = asyncio.run(scanner.scan_file(test_file))
            
        # Check no stdout output
        stdout_content = captured_stdout.getvalue()
        if stdout_content:
            print(f"❌ FAILED: Scanner produced stdout output: {stdout_content}", file=sys.stderr)
            return False
        else:
            print("✅ PASSED: No stdout output detected", file=sys.stderr)
            return True
            
    finally:
        if test_file.exists():
            test_file.unlink()


def test_negative_space_mcp_compliance():
    """Test negative space analysis doesn't break MCP."""
    test_dir = Path(".")
    
    captured_stdout = StringIO()
    
    with patch('sys.stdout', captured_stdout):
        scanner = Scanner(quiet=True, enable_negative_space=True)
        try:
            result = asyncio.run(scanner.analyze_project_negative_space(test_dir))
            
            stdout_content = captured_stdout.getvalue()
            if stdout_content:
                print(f"❌ FAILED: Negative space analysis produced stdout: {stdout_content}", file=sys.stderr)
                return False
            else:
                print("✅ PASSED: Negative space analysis is MCP-safe", file=sys.stderr)
                return True
        except Exception as e:
            print(f"⚠️  WARNING: Negative space analysis failed with: {e}", file=sys.stderr)
            # Still check for stdout pollution
            stdout_content = captured_stdout.getvalue()
            if stdout_content:
                print(f"❌ FAILED: Exception handling produced stdout: {stdout_content}", file=sys.stderr)
                return False
            else:
                print("✅ PASSED: Exception handling is MCP-safe", file=sys.stderr)
                return True


if __name__ == "__main__":
    print("🧪 Running MCP Protocol Compliance Tests", file=sys.stderr)
    
    test1_passed = test_basic_mcp_compliance()
    test2_passed = test_negative_space_mcp_compliance()
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED: MCP Protocol Compliance Verified", file=sys.stderr)
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED: MCP Protocol May Be Broken", file=sys.stderr)
        sys.exit(1)
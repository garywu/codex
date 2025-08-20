"""
MCP Protocol Regression Tests

Tests to ensure that all scanner operations maintain JSON protocol compatibility
and do not break MCP server communications through unauthorized print statements.
"""

import asyncio
import json
import logging
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from codex.negative_space_patterns import NegativeSpaceDetector
from codex.scanner import Scanner


class TestMCPProtocolCompliance:
    """Test suite to ensure MCP JSON protocol compliance."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = Path(__file__).parent.parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)

        # Create a simple test file
        self.test_file = self.test_dir / "test_code.py"
        self.test_file.write_text("""
import os
# Test file for scanning
def example_function():
    password = "hardcoded-secret"  # Should trigger violation
    return password
""")

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_file.exists():
            self.test_file.unlink()

    def test_scanner_no_print_output(self):
        """Test that Scanner produces no print output that would break MCP JSON."""
        # Capture all stdout to detect any print statements
        captured_stdout = StringIO()
        captured_stderr = StringIO()

        with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
            scanner = Scanner(quiet=False, enable_negative_space=True)

            # Run synchronous operations first
            result = asyncio.run(scanner.scan_file(self.test_file))

            # Check that no output went to stdout (which would break JSON)
            stdout_content = captured_stdout.getvalue()
            stderr_content = captured_stderr.getvalue()

            # MCP protocol requires clean stdout
            assert stdout_content == "", f"Scanner produced stdout output: {stdout_content}"

            # Stderr is allowed for logging but should not contain raw print statements
            if stderr_content:
                # Ensure stderr content is structured (logging) not raw prints
                lines = stderr_content.strip().split("\n")
                for line in lines:
                    # Should be properly formatted log messages, not raw prints
                    assert not line.startswith("=== "), f"Raw print detected in stderr: {line}"
                    assert not line.startswith("🔍 "), f"Raw print detected in stderr: {line}"

    def test_negative_space_analysis_json_safe(self):
        """Test that negative space analysis doesn't break JSON protocol."""
        captured_stdout = StringIO()
        captured_stderr = StringIO()

        with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
            scanner = Scanner(quiet=False, enable_negative_space=True)

            # Run negative space analysis
            result = asyncio.run(scanner.analyze_project_negative_space(self.test_dir))

            # Verify JSON protocol compliance
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", f"Negative space analysis broke JSON protocol: {stdout_content}"

            # Verify result is JSON serializable
            try:
                json.dumps(result)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Negative space result not JSON serializable: {e}")

    def test_logging_configuration_mcp_compatible(self):
        """Test that logging is configured to not interfere with MCP."""
        # Test with various logging levels
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]:
            captured_stdout = StringIO()

            with patch("sys.stdout", captured_stdout):
                # Configure logging to not use stdout
                logger = logging.getLogger("codex")
                logger.setLevel(level)

                # Test logging doesn't go to stdout
                logger.info("Test message")
                logger.warning("Test warning")

                stdout_content = captured_stdout.getvalue()
                assert stdout_content == "", f"Logging level {level} produced stdout output"

    def test_scanner_directory_mcp_compliance(self):
        """Test directory scanning maintains MCP protocol compliance."""
        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            scanner = Scanner(quiet=False, enable_negative_space=True)

            # Run directory scan
            results = asyncio.run(scanner.scan_directory(self.test_dir))

            # Verify no stdout pollution
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", f"Directory scan broke JSON protocol: {stdout_content}"

            # Verify results are JSON serializable
            try:
                serialized = json.dumps(
                    [{"file_path": r.file_path, "violations": len(r.violations), "score": r.score} for r in results]
                )
                # Verify it's valid JSON
                json.loads(serialized)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Directory scan results not JSON serializable: {e}")

    def test_quiet_mode_absolute_silence(self):
        """Test that quiet mode produces absolutely no output."""
        captured_stdout = StringIO()
        captured_stderr = StringIO()

        with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
            scanner = Scanner(quiet=True, enable_negative_space=True)

            # Run all scanner operations in quiet mode
            file_result = asyncio.run(scanner.scan_file(self.test_file))
            dir_results = asyncio.run(scanner.scan_directory(self.test_dir))
            negative_space_result = asyncio.run(scanner.analyze_project_negative_space(self.test_dir))

            # Verify absolute silence
            stdout_content = captured_stdout.getvalue()
            stderr_content = captured_stderr.getvalue()

            assert stdout_content == "", f"Quiet mode produced stdout: {stdout_content}"
            assert stderr_content == "", f"Quiet mode produced stderr: {stderr_content}"

    def test_negative_space_detector_json_compliance(self):
        """Test NegativeSpaceDetector directly for JSON compliance."""
        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            detector = NegativeSpaceDetector()

            # Test pattern loading doesn't print
            patterns = detector._load_known_negative_space_patterns()

            # Test project analysis doesn't print
            violation_data = {"fix_plans": [], "total_violations": 0}
            analysis = detector.analyze_project_negative_space(self.test_dir, violation_data)

            # Verify no stdout output
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", f"NegativeSpaceDetector broke JSON protocol: {stdout_content}"

            # Verify analysis result is JSON serializable
            try:
                json.dumps(
                    {
                        "name": analysis.name,
                        "violations_by_pattern": analysis.violations_by_pattern,
                        "organization_score": analysis.organization_score,
                        "has_core_package": analysis.has_core_package,
                    }
                )
            except (TypeError, ValueError) as e:
                pytest.fail(f"NegativeSpaceDetector result not JSON serializable: {e}")

    def test_cli_integration_mcp_safe(self):
        """Test CLI integration maintains MCP safety."""
        from codex.cli import scan

        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            with patch("typer.Exit"):  # Prevent actual exit
                try:
                    # Simulate CLI call with best practices
                    scan(paths=[self.test_dir], fix=False, quiet=True, best_practices=True)
                except SystemExit:
                    pass  # Expected from typer.Exit
                except Exception:
                    pass  # Ignore other exceptions for this test

            # Verify no stdout pollution
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", f"CLI integration broke JSON protocol: {stdout_content}"

    def test_error_handling_json_safe(self):
        """Test that error conditions don't break JSON protocol."""
        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            scanner = Scanner(quiet=False, enable_negative_space=True)

            # Test with non-existent file
            result = asyncio.run(scanner.scan_file(Path("nonexistent.py")))

            # Test with non-existent directory
            result = asyncio.run(scanner.analyze_project_negative_space(Path("nonexistent_dir")))

            # Verify no stdout output even during errors
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", f"Error handling broke JSON protocol: {stdout_content}"

    def test_json_serialization_comprehensive(self):
        """Comprehensive test of JSON serialization for all result types."""
        scanner = Scanner(quiet=True, enable_negative_space=True)

        # Test all result types are JSON serializable
        file_result = asyncio.run(scanner.scan_file(self.test_file))
        dir_results = asyncio.run(scanner.scan_directory(self.test_dir))
        negative_space_result = asyncio.run(scanner.analyze_project_negative_space(self.test_dir))

        # Test file result serialization
        try:
            file_json = json.dumps(
                {
                    "file_path": file_result.file_path,
                    "violations": [
                        {
                            "pattern_id": v.pattern_id,
                            "pattern_name": v.pattern_name,
                            "category": v.category.value if hasattr(v.category, "value") else str(v.category),
                            "priority": v.priority.value if hasattr(v.priority, "value") else str(v.priority),
                            "file_path": v.file_path,
                            "line_number": v.line_number,
                            "suggestion": v.suggestion,
                            "confidence": v.confidence,
                            "auto_fixable": v.auto_fixable,
                        }
                        for v in file_result.violations
                    ],
                    "score": file_result.score,
                }
            )
            json.loads(file_json)  # Verify valid JSON
        except (TypeError, ValueError) as e:
            pytest.fail(f"File result not JSON serializable: {e}")

        # Test negative space result serialization
        if "error" not in negative_space_result:
            try:
                ns_json = json.dumps(negative_space_result)
                json.loads(ns_json)  # Verify valid JSON
            except (TypeError, ValueError) as e:
                pytest.fail(f"Negative space result not JSON serializable: {e}")

    def test_mcp_protocol_simulation(self):
        """Simulate actual MCP protocol communication."""
        # Simulate MCP request/response cycle
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "scan_with_best_practices",
                "arguments": {"path": str(self.test_dir), "include_negative_space": True},
            },
        }

        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            # Simulate tool execution
            scanner = Scanner(quiet=True, enable_negative_space=True)
            scan_result = asyncio.run(scanner.analyze_project_negative_space(self.test_dir))

            # Create MCP response
            mcp_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analysis complete. Organization score: {scan_result.get('organization_score', 0):.1%}",
                        }
                    ],
                    "isError": False,
                },
            }

            # Verify response is valid JSON
            response_json = json.dumps(mcp_response)
            parsed_response = json.loads(response_json)

            # Verify no stdout pollution during MCP simulation
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", f"MCP simulation broke protocol: {stdout_content}"

            # Verify response structure
            assert parsed_response["jsonrpc"] == "2.0"
            assert parsed_response["id"] == 1
            assert "result" in parsed_response


def test_no_print_imports():
    """Test that no modules use print statements."""
    # This is a static analysis test
    modules_to_check = ["codex.scanner", "codex.negative_space_patterns", "codex.cli"]

    for module_name in modules_to_check:
        try:
            module = __import__(module_name, fromlist=[""])

            # Check module source for print statements (basic check)
            if hasattr(module, "__file__") and module.__file__:
                with open(module.__file__) as f:
                    content = f.read()

                # Look for print( statements that aren't in comments or strings
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "print(" in line and not line.strip().startswith("#"):
                        # Allow print in specific contexts (like error handling with sys.stderr)
                        if "sys.stderr" not in line and "logging.info" not in line:
                            pytest.fail(f"Found print statement in {module_name} line {i}: {line}")

        except ImportError:
            # Module might not exist, skip
            continue


if __name__ == "__main__":
    pytest.main([__file__])

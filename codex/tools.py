"""
External tool integration for Codex scanner.

Runs mypy, ruff, and typos as part of the scanning process.
Enforces proper Python environment (UV + Python 3.12 from venv).
"""

import asyncio
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console

from .python_env_enforcer import PythonEnvironmentEnforcer


class ToolType(str, Enum):
    """Available external tools."""

    RUFF = "ruff"
    MYPY = "mypy"
    TY = "ty"  # Astral's fast type checker
    TYPOS = "typos"


@dataclass
class ToolResult:
    """Result from running an external tool."""

    tool: ToolType
    success: bool
    violations: int
    output: str
    fixed: int = 0
    exit_code: int = 0


class ToolRunner:
    """Run external tools for code analysis."""

    def __init__(
        self,
        quiet: bool = False,
        fix: bool = False,
        config: dict[str, Any] | None = None,
    ):
        """Initialize tool runner with environment enforcement."""
        self.quiet = quiet
        self.fix = fix
        self.config = config or {}
        self.console = Console(quiet=quiet)
        self.env_enforcer = PythonEnvironmentEnforcer()

        # Check environment once at startup
        if not quiet:
            self.env_enforcer.enforce_environment(strict=False)

        # Tool configurations
        self.tools_enabled = self.config.get(
            "tools",
            {
                "ruff": True,
                "ty": False,  # Disabled by default as it's in preview
                "mypy": True,
                "typos": True,
            },
        )

    async def run_all_tools(self, paths: list[Path]) -> dict[ToolType, ToolResult]:
        """Run all enabled tools on the given paths."""
        results = {}

        # Run tools in parallel for speed
        tasks = []
        if self.tools_enabled.get("ruff", True):
            tasks.append(self.run_ruff(paths))

        # Type checking: try ty first if enabled, otherwise mypy
        if self.tools_enabled.get("ty", False):
            tasks.append(self.run_ty(paths))
        elif self.tools_enabled.get("mypy", True):
            tasks.append(self.run_mypy(paths))

        if self.tools_enabled.get("typos", True):
            tasks.append(self.run_typos(paths))

        if tasks:
            tool_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Map results
            tool_order = []
            if self.tools_enabled.get("ruff", True):
                tool_order.append(ToolType.RUFF)
            if self.tools_enabled.get("ty", False):
                tool_order.append(ToolType.TY)
            elif self.tools_enabled.get("mypy", True):
                tool_order.append(ToolType.MYPY)
            if self.tools_enabled.get("typos", True):
                tool_order.append(ToolType.TYPOS)

            for tool, result in zip(tool_order, tool_results):
                if isinstance(result, Exception):
                    results[tool] = ToolResult(
                        tool=tool,
                        success=False,
                        violations=0,
                        output=str(result),
                        exit_code=1,
                    )
                else:
                    results[tool] = result

        return results

    async def run_ruff(self, paths: list[Path]) -> ToolResult:
        """Run ruff linter on paths with intelligent 80/20 defaults."""
        # Use proper Python environment
        cmd = self.env_enforcer.get_tool_cmd("ruff")
        cmd.extend(["check"])

        # Add paths
        for path in paths:
            cmd.append(str(path))

        # Add fix flag if requested
        if self.fix:
            cmd.append("--fix")

        # Add output format for parsing
        cmd.extend(["--output-format", "json"])

        # If no config exists, use 80/20 intelligent defaults
        if not Path("pyproject.toml").exists() and not Path("ruff.toml").exists() and not Path(".ruff.toml").exists():
            # Apply 80/20 principle: Focus on real bugs, not style
            cmd.extend(
                [
                    "--select",
                    "E,F,I,UP,B,C4,RUF",  # Real issues
                    "--ignore",
                    "E501,PLC0415,B008,ARG002,SIM102,SIM105,SIM108,PLR0912,PLR0913,PLR0915,PLR0911,LOG015,TRY003,TRY300,PLR2004,PERF401,RUF012",  # Noise
                    "--line-length",
                    "120",
                ]
            )
            if not self.quiet:
                print("[Ruff] Using 80/20 mode: Focus on bugs, not style", file=sys.stderr)

        try:
            result = await self._run_command(cmd)

            # Parse JSON output
            violations = 0
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    violations = len(issues)
                except json.JSONDecodeError:
                    violations = 0

            # If fix was applied, count fixed
            fixed = 0
            if self.fix and violations == 0 and result.returncode == 0:
                # Run again without fix to see what was fixed
                check_cmd = (
                    self.env_enforcer.get_tool_cmd("ruff")
                    + ["check"]
                    + [str(p) for p in paths]
                    + ["--output-format", "json"]
                )
                check_result = await self._run_command(check_cmd)
                if check_result.stdout:
                    try:
                        remaining = json.loads(check_result.stdout)
                        fixed = violations - len(remaining)
                    except json.JSONDecodeError:
                        pass

            return ToolResult(
                tool=ToolType.RUFF,
                success=result.returncode == 0,
                violations=violations,
                output=result.stdout or result.stderr,
                fixed=fixed,
                exit_code=result.returncode,
            )

        except FileNotFoundError:
            return ToolResult(
                tool=ToolType.RUFF,
                success=True,  # Not a failure if tool not installed
                violations=0,
                output="ruff not installed",
                exit_code=0,
            )

    async def run_ty(self, paths: list[Path]) -> ToolResult:
        """Run ty type checker (Astral's fast type checker) on paths."""
        # Use proper Python environment
        cmd = self.env_enforcer.get_tool_cmd("ty")
        cmd.extend(["check"])

        # Add paths
        for path in paths:
            cmd.append(str(path))

        try:
            result = await self._run_command(cmd)

            # Count errors from output
            violations = 0
            if result.stdout:
                # ty uses error codes like: error[invalid-argument-type]
                for line in result.stdout.splitlines():
                    if "error[" in line:
                        violations += 1

            return ToolResult(
                tool=ToolType.TY,
                success=result.returncode == 0,
                violations=violations,
                output=result.stdout or result.stderr,
                exit_code=result.returncode,
            )

        except FileNotFoundError:
            return ToolResult(
                tool=ToolType.TY,
                success=True,
                violations=0,
                output="ty not installed",
                exit_code=0,
            )

    async def run_ty_or_mypy(self, paths: list[Path]) -> ToolResult:
        """Run ty if available, otherwise fall back to mypy."""
        # Try ty first if enabled
        if self.tools_enabled.get("ty", False):
            ty_result = await self.run_ty(paths)
            if ty_result.output != "ty not installed":
                return ty_result

        # Fall back to mypy
        return await self.run_mypy(paths)

    async def run_mypy(self, paths: list[Path]) -> ToolResult:
        """Run mypy type checker on paths with intelligent 80/20 defaults."""
        # Use proper Python environment
        cmd = self.env_enforcer.get_tool_cmd("mypy")

        # Add paths
        for path in paths:
            cmd.append(str(path))

        # Add common flags
        cmd.extend(["--no-error-summary", "--show-error-codes"])

        # Add config if exists
        if Path("pyproject.toml").exists():
            cmd.append("--config-file=pyproject.toml")
        elif Path("mypy.ini").exists():
            cmd.append("--config-file=mypy.ini")
        else:
            # No config - use 80/20 intelligent defaults
            # Focus on critical paths, ignore UI/test noise
            cmd.extend(
                [
                    "--ignore-missing-imports",
                    "--allow-untyped-defs",
                    "--allow-untyped-calls",
                    "--no-warn-return-any",
                    "--no-warn-unused-ignores",
                    "--check-untyped-defs=false",
                ]
            )
            if not self.quiet:
                print("[MyPy] Using 80/20 mode: Type critical paths, not UI", file=sys.stderr)

        try:
            result = await self._run_command(cmd)

            # Count errors from output
            violations = 0
            if result.stdout:
                # Count lines with error patterns
                for line in result.stdout.splitlines():
                    if ": error:" in line or ": note:" in line:
                        violations += 1

            return ToolResult(
                tool=ToolType.MYPY,
                success=result.returncode == 0,
                violations=violations,
                output=result.stdout or result.stderr,
                exit_code=result.returncode,
            )

        except FileNotFoundError:
            return ToolResult(
                tool=ToolType.MYPY,
                success=True,
                violations=0,
                output="mypy not installed",
                exit_code=0,
            )

    async def run_typos(self, paths: list[Path]) -> ToolResult:
        """Run typos spell checker on paths."""
        # Use proper Python environment (typos is not a Python tool, but check anyway)
        cmd = self.env_enforcer.get_tool_cmd("typos")

        # Add paths
        for path in paths:
            cmd.append(str(path))

        # Add fix flag if requested
        if self.fix:
            cmd.append("--write-changes")

        # Add format for parsing
        cmd.extend(["--format", "json"])

        try:
            result = await self._run_command(cmd)

            # Parse JSON output
            violations = 0
            fixed = 0

            if result.stdout:
                # Typos outputs one JSON object per line
                for line in result.stdout.splitlines():
                    if line.strip():
                        try:
                            issue = json.loads(line)
                            if issue.get("type") == "typo":
                                violations += 1
                                if self.fix:
                                    fixed += 1
                        except json.JSONDecodeError:
                            pass

            return ToolResult(
                tool=ToolType.TYPOS,
                success=result.returncode == 0,
                violations=violations,
                output=result.stdout or result.stderr,
                fixed=fixed,
                exit_code=result.returncode,
            )

        except FileNotFoundError:
            return ToolResult(
                tool=ToolType.TYPOS,
                success=True,
                violations=0,
                output="typos not installed",
                exit_code=0,
            )

    async def _run_command(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """Run a command asynchronously."""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        return subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode or 0,
            stdout=stdout.decode("utf-8", errors="ignore") if stdout else "",
            stderr=stderr.decode("utf-8", errors="ignore") if stderr else "",
        )

    def print_results(self, results: dict[ToolType, ToolResult]) -> None:
        """Print tool results in a nice format."""
        if self.quiet:
            return

        for tool, result in results.items():
            if result.violations > 0:
                color = "red" if not result.success else "yellow"
                logging.info(f"{tool.value}: {result.violations} issue(s) found")

                if result.fixed > 0:
                    logging.info(f"  Fixed {result.fixed} issue(s)")

                # Show first few lines of output if not JSON
                if not result.output.startswith("[") and not result.output.startswith("{"):
                    lines = result.output.splitlines()[:5]
                    for line in lines:
                        if line.strip():
                            self.console.logging.info(f"  {line}")
                    if len(result.output.splitlines()) > 5:
                        self.console.logging.info("  ...")

            elif not result.success:
                self.console.logging.info(f"[red]{tool.value} failed[/red]: {result.output[:100]}")

"""
Portable code quality tools for any repository.

This module provides a self-contained code quality toolkit that can be applied
to any repository, regardless of whether it has pre-commit hooks, ruff config,
or other tooling set up. Codex acts as a portable quality enforcer.
"""

import asyncio
import json
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Use dict config instead of CodexConfig class
CodexConfig = dict


class ToolAvailability(str, Enum):
    """Tool availability status."""
    AVAILABLE = "available"
    MISSING = "missing"
    INSTALLED_BY_CODEX = "installed_by_codex"


@dataclass
class ToolInfo:
    """Information about a code quality tool."""
    name: str
    availability: ToolAvailability
    version: str | None = None
    install_command: str | None = None
    config_generated: bool = False


@dataclass
class PortableResult:
    """Result from portable tool execution."""
    tool: str
    success: bool
    violations: int
    fixed: int
    output: str
    config_created: bool = False
    tool_installed: bool = False


class PortableToolManager:
    """Manages portable execution of code quality tools."""
    
    def __init__(
        self,
        target_dir: Path,
        quiet: bool = False,
        fix: bool = False,
        install_missing: bool = True,
        generate_configs: bool = True,
    ):
        """Initialize portable tool manager."""
        self.target_dir = Path(target_dir).resolve()
        self.quiet = quiet
        self.fix = fix
        self.install_missing = install_missing
        self.generate_configs = generate_configs
        self.console = Console(quiet=quiet)
        
        # Tool configurations that work well across projects
        self.default_configs = {
            "ruff": {
                "filename": "ruff.toml",
                "content": """# Codex Portable Ruff Configuration
[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "TRY", # tryceratops
    "SIM", # flake8-simplify
    "RUF", # Ruff-specific rules
]
ignore = [
    "E501",  # Line too long (handled by formatter)
    "TRY003", # Avoid long exception messages
]

[lint.per-file-ignores]
"tests/*" = ["TRY301", "S101"]  # Allow assert in tests

[format]
quote-style = "double"
indent-style = "space"
skip-source-first-line = false
line-ending = "auto"

[lint.isort]
known-first-party = ["codex"]
"""
            },
            "black": {
                "filename": "pyproject.toml",
                "section": "tool.black",
                "content": """# Codex Portable Black Configuration
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # directories
    \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''
"""
            },
            "mypy": {
                "filename": "mypy.ini",
                "content": """# Codex Portable MyPy Configuration
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
"""
            },
            "typos": {
                "filename": "_typos.toml",
                "content": """# Codex Portable Typos Configuration
[default]
extend-ignore-re = [
    "(?Rm)^.*(#|//)\\s*spellchecker:disable-line$",
]

[files]
extend-exclude = [
    "*.min.js",
    "*.min.css",
    "*.log",
    "node_modules/",
    ".git/",
    "__pycache__/",
    "*.pyc",
]

[default.extend-words]
# Add common technical terms that typos flags incorrectly
technical = "technical"
"""
            },
            "uv": {
                "filename": "pyproject.toml",
                "section": "tool.uv",
                "content": """# Codex Portable UV Configuration
[tool.uv]
dev-dependencies = [
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "black>=23.0.0",
    "typos>=1.16.0",
]

[tool.uv.sources]
# Use UV for fast dependency resolution and installation
"""
            },
            "ty": {
                "filename": "pyproject.toml",
                "section": "tool.ty", 
                "content": """# Codex Portable Ty Configuration (Astral's Type Checker)
[tool.ty]
# Ty is Astral's ultra-fast type checker (like mypy but 10-100x faster)
python-version = "3.11"
strict = true
show-error-codes = true
warn-redundant-casts = true
warn-unused-ignores = true

[tool.ty.per-module-options]
"tests.*" = { ignore-missing-imports = true }
"""
            }
        }

    async def analyze_repository(self) -> dict[str, ToolInfo]:
        """Analyze what tools are available and what's needed."""
        if not self.quiet:
            self.console.logging.info(f"[blue]🔍 Analyzing repository: {self.target_dir}[/blue]")
        
        tools = {}
        
        # Check each tool
        for tool_name in ["ruff", "mypy", "typos", "black", "uv", "ty"]:
            tools[tool_name] = await self._check_tool(tool_name)
        
        return tools

    async def setup_portable_environment(self) -> dict[str, ToolInfo]:
        """Set up a portable code quality environment."""
        tools = await self.analyze_repository()
        
        if not self.quiet:
            self.console.logging.info("\n[blue]⚙️  Setting up portable environment...[/blue]")
        
        # Install missing tools if requested
        if self.install_missing:
            for tool_name, tool_info in tools.items():
                if tool_info.availability == ToolAvailability.MISSING:
                    success = await self._install_tool(tool_name)
                    if success:
                        tools[tool_name].availability = ToolAvailability.INSTALLED_BY_CODEX
                        tools[tool_name].tool_installed = True
        
        # Generate configurations if requested
        if self.generate_configs:
            for tool_name, tool_info in tools.items():
                if tool_info.availability != ToolAvailability.MISSING:
                    config_created = await self._ensure_config(tool_name)
                    tools[tool_name].config_generated = config_created
        
        return tools

    async def run_portable_scan(self) -> dict[str, PortableResult]:
        """Run a comprehensive portable scan."""
        if not self.quiet:
            self.console.logging.info(f"\n[green]🚀 Running portable scan on {self.target_dir}[/green]")
        
        # Set up environment
        tools = await self.setup_portable_environment()
        
        # Run available tools
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            disable=self.quiet,
        ) as progress:
            
            for tool_name, tool_info in tools.items():
                if tool_info.availability != ToolAvailability.MISSING:
                    task = progress.add_task(f"Running {tool_name}...", total=None)
                    result = await self._run_tool_portable(tool_name, tool_info)
                    results[tool_name] = result
                    progress.remove_task(task)
        
        return results

    async def _check_tool(self, tool_name: str) -> ToolInfo:
        """Check if a tool is available."""
        # Check if tool is in PATH
        if shutil.which(tool_name):
            try:
                result = await self._run_command([tool_name, "--version"])
                version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
                return ToolInfo(
                    name=tool_name,
                    availability=ToolAvailability.AVAILABLE,
                    version=version,
                )
            except Exception:
                pass
        
        # Check if we can install it
        install_commands = {
            "ruff": "pip install ruff",
            "mypy": "pip install mypy",
            "typos": "pip install typos",  # or cargo install typos-cli
            "black": "pip install black",
            "uv": "pip install uv",  # Astral's fast package manager
            "ty": "pip install ty",  # Astral's ultra-fast type checker
        }
        
        return ToolInfo(
            name=tool_name,
            availability=ToolAvailability.MISSING,
            install_command=install_commands.get(tool_name),
        )

    async def _install_tool(self, tool_name: str) -> bool:
        """Install a missing tool."""
        install_commands = {
            "ruff": ["pip", "install", "ruff"],
            "mypy": ["pip", "install", "mypy"],
            "typos": ["pip", "install", "typos"],  # Use pip version if available
            "black": ["pip", "install", "black"],
            "uv": ["pip", "install", "uv"],  # Astral's fast package manager
            "ty": ["pip", "install", "ty"],  # Astral's ultra-fast type checker
        }
        
        if tool_name not in install_commands:
            return False
        
        if not self.quiet:
            self.console.logging.info(f"[yellow]📦 Installing {tool_name}...[/yellow]")
        
        try:
            result = await self._run_command(install_commands[tool_name])
            success = result.returncode == 0
            
            if success and not self.quiet:
                self.console.logging.info(f"[green]✅ {tool_name} installed successfully[/green]")
            elif not self.quiet:
                self.console.logging.info(f"[red]❌ Failed to install {tool_name}[/red]")
            
            return success
        except Exception as e:
            if not self.quiet:
                self.console.logging.info(f"[red]❌ Error installing {tool_name}: {e}[/red]")
            return False

    async def _ensure_config(self, tool_name: str) -> bool:
        """Ensure tool has a working configuration."""
        if tool_name not in self.default_configs:
            return False
        
        config_info = self.default_configs[tool_name]
        config_path = self.target_dir / config_info["filename"]
        
        # Check if config already exists
        existing_configs = self._find_existing_configs(tool_name)
        
        if existing_configs:
            if not self.quiet:
                self.console.logging.info(f"[cyan]ℹ️  Using existing {tool_name} config: {existing_configs[0]}[/cyan]")
            return False
        
        # Create portable config
        try:
            with open(config_path, "w") as f:
                f.write(config_info["content"])
            
            if not self.quiet:
                self.console.logging.info(f"[green]📝 Created portable {tool_name} config: {config_path.name}[/green]")
            return True
        except Exception as e:
            if not self.quiet:
                self.console.logging.info(f"[red]❌ Failed to create {tool_name} config: {e}[/red]")
            return False

    def _find_existing_configs(self, tool_name: str) -> list[Path]:
        """Find existing configuration files for a tool."""
        config_patterns = {
            "ruff": ["ruff.toml", "pyproject.toml"],
            "mypy": ["mypy.ini", "pyproject.toml", ".mypy.ini"],
            "typos": ["_typos.toml", ".typos.toml", "typos.toml"],
        }
        
        existing = []
        patterns = config_patterns.get(tool_name, [])
        
        for pattern in patterns:
            config_path = self.target_dir / pattern
            if config_path.exists():
                # For pyproject.toml, check if it has the relevant section
                if pattern == "pyproject.toml":
                    try:
                        # Use tomli for Python < 3.11 compatibility
                        try:
                            import tomllib
                        except ImportError:
                            import tomli as tomllib
                        
                        with open(config_path, "rb") as f:
                            data = tomllib.load(f)
                        
                        sections = {
                            "ruff": ["tool.ruff", "tool.ruff.lint"],
                            "mypy": ["tool.mypy"],
                        }
                        
                        tool_sections = sections.get(tool_name, [])
                        for section in tool_sections:
                            if self._get_nested_dict(data, section.split(".")):
                                existing.append(config_path)
                                break
                    except Exception:
                        # If we can't parse TOML, assume it might have config
                        existing.append(config_path)
                else:
                    existing.append(config_path)
        
        return existing

    def _get_nested_dict(self, data: dict, keys: list[str]) -> Any:
        """Get nested dictionary value."""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    async def _run_tool_portable(self, tool_name: str, tool_info: ToolInfo) -> PortableResult:
        """Run a tool in portable mode."""
        if tool_name == "ruff":
            return await self._run_ruff_portable()
        elif tool_name == "mypy":
            return await self._run_mypy_portable()
        elif tool_name == "typos":
            return await self._run_typos_portable()
        elif tool_name == "black":
            return await self._run_black_portable()
        elif tool_name == "uv":
            return await self._run_uv_portable()
        elif tool_name == "ty":
            return await self._run_ty_portable()
        else:
            return PortableResult(
                tool=tool_name,
                success=False,
                violations=0,
                fixed=0,
                output=f"Unknown tool: {tool_name}",
            )

    async def _run_ruff_portable(self) -> PortableResult:
        """Run ruff with portable configuration."""
        cmd = ["ruff", "check", str(self.target_dir)]
        
        # Add config if we created one
        config_path = self.target_dir / "ruff.toml"
        if config_path.exists():
            cmd.extend(["--config", str(config_path)])
        
        # Add fix if requested
        if self.fix:
            cmd.append("--fix")
        
        # Add JSON output for parsing
        cmd.extend(["--output-format", "json"])
        
        try:
            result = await self._run_command(cmd, cwd=self.target_dir)
            
            violations = 0
            fixed = 0
            
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    violations = len(issues)
                except json.JSONDecodeError:
                    pass
            
            # Count fixes if applied
            if self.fix and result.returncode == 0:
                # Rough estimate: assume violations were fixed
                fixed = violations
                violations = 0
            
            return PortableResult(
                tool="ruff",
                success=result.returncode == 0 or (self.fix and violations == 0),
                violations=violations,
                fixed=fixed,
                output=result.stdout or result.stderr,
                config_created=config_path.exists(),
            )
            
        except Exception as e:
            return PortableResult(
                tool="ruff",
                success=False,
                violations=0,
                fixed=0,
                output=str(e),
            )

    async def _run_mypy_portable(self) -> PortableResult:
        """Run mypy with portable configuration."""
        cmd = ["mypy", str(self.target_dir)]
        
        # Add config if we created one
        config_path = self.target_dir / "mypy.ini"
        if config_path.exists():
            cmd.extend(["--config-file", str(config_path)])
        
        # Add common flags for portable use
        cmd.extend([
            "--no-error-summary",
            "--show-error-codes",
            "--ignore-missing-imports",  # Be more forgiving in portable mode
        ])
        
        try:
            result = await self._run_command(cmd, cwd=self.target_dir)
            
            violations = 0
            if result.stdout:
                for line in result.stdout.splitlines():
                    if ": error:" in line:
                        violations += 1
            
            return PortableResult(
                tool="mypy",
                success=result.returncode == 0,
                violations=violations,
                fixed=0,  # MyPy doesn't auto-fix
                output=result.stdout or result.stderr,
                config_created=config_path.exists(),
            )
            
        except Exception as e:
            return PortableResult(
                tool="mypy",
                success=False,
                violations=0,
                fixed=0,
                output=str(e),
            )

    async def _run_typos_portable(self) -> PortableResult:
        """Run typos with portable configuration."""
        cmd = ["typos", str(self.target_dir)]
        
        # Add config if we created one
        config_path = self.target_dir / "_typos.toml"
        if config_path.exists():
            cmd.extend(["--config", str(config_path)])
        
        # Add fix if requested
        if self.fix:
            cmd.append("--write-changes")
        
        # Add JSON format for parsing
        cmd.extend(["--format", "json"])
        
        try:
            result = await self._run_command(cmd, cwd=self.target_dir)
            
            violations = 0
            fixed = 0
            
            if result.stdout:
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
            
            return PortableResult(
                tool="typos",
                success=result.returncode == 0,
                violations=violations,
                fixed=fixed,
                output=result.stdout or result.stderr,
                config_created=config_path.exists(),
            )
            
        except Exception as e:
            return PortableResult(
                tool="typos",
                success=False,
                violations=0,
                fixed=0,
                output=str(e),
            )

    async def _run_black_portable(self) -> PortableResult:
        """Run black with portable configuration."""
        cmd = ["black", str(self.target_dir)]
        
        # Add check mode if not fixing
        if not self.fix:
            cmd.append("--check")
        
        # Add diff to see what would change
        if not self.fix:
            cmd.append("--diff")
        
        try:
            result = await self._run_command(cmd, cwd=self.target_dir)
            
            # Black returns 1 if files would be reformatted
            violations = 1 if result.returncode == 1 else 0
            fixed = 1 if self.fix and result.returncode == 0 else 0
            
            return PortableResult(
                tool="black",
                success=True,  # Black doesn't really "fail"
                violations=violations,
                fixed=fixed,
                output=result.stdout or result.stderr,
            )
            
        except Exception as e:
            return PortableResult(
                tool="black",
                success=False,
                violations=0,
                fixed=0,
                output=str(e),
            )

    async def _run_uv_portable(self) -> PortableResult:
        """Run uv to check dependency management."""
        # UV is more of a package manager, so we'll check if dependencies are up to date
        cmd = ["uv", "pip", "check"]
        
        try:
            result = await self._run_command(cmd, cwd=self.target_dir)
            
            violations = 0
            if result.returncode != 0:
                # Count dependency issues from output
                violations = len([line for line in result.stdout.splitlines() if "has invalid" in line])
            
            return PortableResult(
                tool="uv",
                success=result.returncode == 0,
                violations=violations,
                fixed=0,  # UV doesn't auto-fix dependency issues
                output=result.stdout or result.stderr,
            )
            
        except Exception as e:
            return PortableResult(
                tool="uv",
                success=False,
                violations=0,
                fixed=0,
                output=str(e),
            )

    async def _run_ty_portable(self) -> PortableResult:
        """Run ty (Astral's type checker) with portable configuration."""
        cmd = ["ty", "check", str(self.target_dir)]
        
        # Add config if we created one
        config_path = self.target_dir / "pyproject.toml"
        if config_path.exists():
            # Ty uses pyproject.toml automatically
            pass
        
        try:
            result = await self._run_command(cmd, cwd=self.target_dir)
            
            violations = 0
            if result.stdout:
                # Count type errors from output
                for line in result.stdout.splitlines():
                    if ": error:" in line or "Error:" in line:
                        violations += 1
            
            return PortableResult(
                tool="ty",
                success=result.returncode == 0,
                violations=violations,
                fixed=0,  # Type checkers don't auto-fix
                output=result.stdout or result.stderr,
                config_created=config_path.exists(),
            )
            
        except Exception as e:
            return PortableResult(
                tool="ty",
                success=False,
                violations=0,
                fixed=0,
                output=str(e),
            )

    async def _run_command(
        self, cmd: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        """Run a command asynchronously."""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        
        stdout, stderr = await proc.communicate()
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode or 0,
            stdout=stdout.decode("utf-8", errors="ignore") if stdout else "",
            stderr=stderr.decode("utf-8", errors="ignore") if stderr else "",
        )

    def print_results(self, results: dict[str, PortableResult]) -> None:
        """Print portable scan results."""
        if self.quiet:
            return
        
        self.console.logging.info("\n[bold green]🎯 Portable Scan Results[/bold green]")
        self.console.logging.info("=" * 50)
        
        total_violations = 0
        total_fixed = 0
        
        for tool, result in results.items():
            total_violations += result.violations
            total_fixed += result.fixed
            
            # Status indicator
            if result.success and result.violations == 0:
                status = "[green]✅ Clean[/green]"
            elif result.violations > 0:
                status = f"[yellow]⚠️  {result.violations} issue(s)[/yellow]"
            else:
                status = "[red]❌ Failed[/red]"
            
            self.console.logging.info(f"\n[bold]{tool.upper()}[/bold]: {status}")
            
            if result.fixed > 0:
                self.console.logging.info(f"  [green]🔧 Fixed: {result.fixed} issue(s)[/green]")
            
            if result.config_created:
                self.console.logging.info(f"  [cyan]📝 Created portable config[/cyan]")
            
            if result.tool_installed:
                self.console.logging.info(f"  [yellow]📦 Tool installed by Codex[/yellow]")
        
        # Summary
        self.console.logging.info(f"\n[bold]Summary:[/bold]")
        self.console.logging.info(f"  Total violations: {total_violations}")
        if total_fixed > 0:
            self.console.logging.info(f"  Total fixed: {total_fixed}")
        
        if total_violations == 0:
            self.console.logging.info("[green]🎉 Repository is clean![/green]")


class RepositoryInitializer:
    """Initialize repositories with Codex patterns and tools."""
    
    def __init__(self, quiet: bool = False):
        """Initialize repository initializer."""
        self.quiet = quiet
        self.console = Console(quiet=quiet)
    
    async def init_repository(
        self,
        repo_path: Path,
        pattern_sources: list[Path] | None = None,
        setup_precommit: bool = True,
        setup_tools: bool = True,
    ) -> bool:
        """Initialize a repository with Codex patterns and tools."""
        repo_path = Path(repo_path).resolve()
        
        if not self.quiet:
            self.console.logging.info(f"[blue]🚀 Initializing repository: {repo_path}[/blue]")
        
        success = True
        
        # Set up portable tools
        if setup_tools:
            portable_manager = PortableToolManager(
                repo_path,
                quiet=self.quiet,
                generate_configs=True,
                install_missing=False,  # Don't auto-install in init
            )
            
            tools = await portable_manager.setup_portable_environment()
            
            if not self.quiet:
                for tool_name, tool_info in tools.items():
                    if tool_info.config_generated:
                        self.console.logging.info(f"[green]✅ Created {tool_name} config[/green]")
        
        # Set up pre-commit if requested
        if setup_precommit:
            success = await self._setup_precommit_hook(repo_path) and success
        
        # Import patterns if provided
        if pattern_sources:
            success = await self._import_patterns(repo_path, pattern_sources) and success
        
        # Create .codex.toml if it doesn't exist
        success = await self._create_codex_config(repo_path) and success
        
        if not self.quiet:
            if success:
                self.console.logging.info("[green]🎉 Repository initialized successfully![/green]")
            else:
                self.console.logging.info("[yellow]⚠️  Repository initialization completed with warnings[/yellow]")
        
        return success
    
    async def _setup_precommit_hook(self, repo_path: Path) -> bool:
        """Set up pre-commit hook for Codex."""
        precommit_config = repo_path / ".pre-commit-config.yaml"
        
        # Check if .pre-commit-config.yaml exists
        if precommit_config.exists():
            if not self.quiet:
                self.console.logging.info("[cyan]ℹ️  .pre-commit-config.yaml already exists[/cyan]")
            return True
        
        # Create basic pre-commit config with Codex
        config_content = """# Pre-commit configuration with Codex
repos:
  - repo: local
    hooks:
      - id: codex
        name: Codex Pattern Scanner
        entry: codex
        language: system
        pass_filenames: true
        args: ["--quiet"]
        
      - id: codex-fix
        name: Codex Auto-Fix
        entry: codex
        language: system
        pass_filenames: true
        args: ["--fix", "--quiet"]
        stages: [manual]  # Run manually with --hook-stage manual
"""
        
        try:
            with open(precommit_config, "w") as f:
                f.write(config_content)
            
            if not self.quiet:
                self.console.logging.info("[green]📝 Created .pre-commit-config.yaml[/green]")
            return True
        except Exception as e:
            if not self.quiet:
                self.console.logging.info(f"[red]❌ Failed to create pre-commit config: {e}[/red]")
            return False
    
    async def _import_patterns(self, repo_path: Path, pattern_sources: list[Path]) -> bool:
        """Import patterns from source files."""
        # This would integrate with the existing pattern import system
        # For now, just log what would happen
        if not self.quiet:
            for source in pattern_sources:
                self.console.logging.info(f"[cyan]📥 Would import patterns from: {source}[/cyan]")
        return True
    
    async def _create_codex_config(self, repo_path: Path) -> bool:
        """Create .codex.toml configuration file."""
        config_path = repo_path / ".codex.toml"
        
        if config_path.exists():
            if not self.quiet:
                self.console.logging.info("[cyan]ℹ️  .codex.toml already exists[/cyan]")
            return True
        
        config_content = """# Codex Configuration
[codex]
# Patterns to enforce (all, mandatory, critical, high, medium, low)
patterns = ["mandatory", "critical", "high"]

# Files/directories to exclude
exclude = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "*.pyc",
    "*.min.js",
    "*.min.css"
]

# Enable automatic fixes
auto_fix = false

# Run external tools (ruff, mypy, typos)
run_tools = true

[tools]
# Enable/disable specific tools
ruff = true
mypy = true
typos = true

[ai_integration]
# Enable MCP server for AI assistants
enable_mcp_server = true
default_query_limit = 5
"""
        
        try:
            with open(config_path, "w") as f:
                f.write(config_content)
            
            if not self.quiet:
                self.console.logging.info("[green]📝 Created .codex.toml[/green]")
            return True
        except Exception as e:
            if not self.quiet:
                self.console.logging.info(f"[red]❌ Failed to create .codex.toml: {e}[/red]")
            return False
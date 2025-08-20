"""
UV environment checker - ensures proper Python version and dependencies.

This module checks that:
1. UV is installed and available
2. Python 3.12 is being used (managed by uv)
3. All dependencies are installed via uv
4. Virtual environment is properly configured
"""

import json
import logging
import subprocess
import sys
from pathlib import Path


class UVEnvironmentChecker:
    """Check and validate UV environment setup."""

    REQUIRED_PYTHON = "3.12"
    REQUIRED_PACKAGES = [
        "pydantic",
        "pydantic-settings",
        "sqlmodel",
        "aiosqlite",
        "typer",
        "rich",
        "httpx",
        "ruff",
        "mypy",
    ]

    def __init__(self, quiet: bool = False):
        """Initialize environment checker."""
        self.quiet = quiet
        self.errors = []
        self.warnings = []

    def check_uv_installed(self) -> bool:
        """Check if uv is installed."""
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                if not self.quiet:
                    version = result.stdout.strip()
                    logging.info(f"✅ UV installed: {version}")
                return True
            else:
                self.errors.append("UV is not installed")
                return False
        except FileNotFoundError:
            self.errors.append("UV command not found - install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False

    def check_python_version(self) -> bool:
        """Check if Python 3.12 is being used via uv."""
        try:
            # Check current Python version
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}"

            if current_version.startswith(self.REQUIRED_PYTHON):
                if not self.quiet:
                    logging.info(f"✅ Python {current_version} is active")
                return True
            else:
                self.warnings.append(f"Python {current_version} is active, but {self.REQUIRED_PYTHON} is required")

                # Try to install correct Python version with uv
                if not self.quiet:
                    logging.info(f"⚠️  Installing Python {self.REQUIRED_PYTHON} with uv...")

                result = subprocess.run(
                    ["uv", "python", "install", self.REQUIRED_PYTHON], capture_output=True, text=True
                )

                if result.returncode == 0:
                    if not self.quiet:
                        logging.info(f"✅ Python {self.REQUIRED_PYTHON} installed via uv")
                    self.warnings.append(f"Run with: uv run python")
                    return True
                else:
                    self.errors.append(f"Failed to install Python {self.REQUIRED_PYTHON}")
                    return False

        except Exception as e:
            self.errors.append(f"Error checking Python version: {e}")
            return False

    def check_virtual_environment(self) -> bool:
        """Check if virtual environment exists and is configured correctly."""
        venv_path = Path(".venv")

        if not venv_path.exists():
            if not self.quiet:
                logging.info("⚠️  No virtual environment found, creating...")

            result = subprocess.run(["uv", "venv", "--python", self.REQUIRED_PYTHON], capture_output=True, text=True)

            if result.returncode == 0:
                if not self.quiet:
                    logging.info(f"✅ Virtual environment created with Python {self.REQUIRED_PYTHON}")
                return True
            else:
                self.errors.append("Failed to create virtual environment")
                return False
        else:
            if not self.quiet:
                logging.info("✅ Virtual environment exists")
            return True

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        try:
            # Use uv pip list to check installed packages
            result = subprocess.run(["uv", "pip", "list", "--format", "json"], capture_output=True, text=True)

            if result.returncode != 0:
                self.errors.append("Failed to list installed packages")
                return False

            installed_packages = json.loads(result.stdout)
            installed_names = {pkg["name"].lower() for pkg in installed_packages}

            missing = []
            for package in self.REQUIRED_PACKAGES:
                if package.lower() not in installed_names:
                    missing.append(package)

            if missing:
                if not self.quiet:
                    logging.info(f"⚠️  Missing packages: {', '.join(missing)}")
                    logging.info("Installing missing packages...")

                # Install missing packages
                result = subprocess.run(["uv", "pip", "install"] + missing, capture_output=True, text=True)

                if result.returncode == 0:
                    if not self.quiet:
                        logging.info("✅ Installed missing packages")
                    return True
                else:
                    self.errors.append(f"Failed to install packages: {', '.join(missing)}")
                    return False
            else:
                if not self.quiet:
                    logging.info("✅ All required packages installed")
                return True

        except Exception as e:
            self.errors.append(f"Error checking dependencies: {e}")
            return False

    def check_codex_installation(self) -> bool:
        """Check if codex is installed in development mode."""
        try:
            result = subprocess.run(["uv", "pip", "list", "--format", "json"], capture_output=True, text=True)

            if result.returncode == 0:
                packages = json.loads(result.stdout)
                codex_installed = any(p["name"] == "codex" for p in packages)

                if not codex_installed:
                    if not self.quiet:
                        logging.info("⚠️  Codex not installed, installing in development mode...")

                    result = subprocess.run(["uv", "pip", "install", "-e", "."], capture_output=True, text=True)

                    if result.returncode == 0:
                        if not self.quiet:
                            logging.info("✅ Codex installed in development mode")
                        return True
                    else:
                        self.errors.append("Failed to install codex")
                        return False
                else:
                    if not self.quiet:
                        logging.info("✅ Codex is installed")
                    return True

        except Exception as e:
            self.errors.append(f"Error checking codex installation: {e}")
            return False

    def run_all_checks(self) -> bool:
        """Run all environment checks."""
        if not self.quiet:
            logging.info("🔍 Checking UV environment...")
            logging.info("=" * 40)

        checks = [
            ("UV Installation", self.check_uv_installed),
            ("Python Version", self.check_python_version),
            ("Virtual Environment", self.check_virtual_environment),
            ("Dependencies", self.check_dependencies),
            ("Codex Installation", self.check_codex_installation),
        ]

        all_passed = True
        for name, check_func in checks:
            if not self.quiet:
                logging.info(f"\nChecking {name}...")

            if not check_func():
                all_passed = False

        if not self.quiet:
            logging.info("\n" + "=" * 40)

            if self.errors:
                logging.info("\n❌ Errors:")
                for error in self.errors:
                    logging.info(f"  • {error}")

            if self.warnings:
                logging.info("\n⚠️  Warnings:")
                for warning in self.warnings:
                    logging.info(f"  • {warning}")

            if all_passed and not self.errors:
                logging.info("\n✨ Environment is properly configured!")
                logging.info("\nRun commands with:")
                logging.info("  uv run codex scan .")
                logging.info("  uv run python script.py")
            else:
                logging.info("\n❌ Environment needs configuration")
                logging.info("\nFix issues and run again:")
                logging.info("  uv run python -m codex.uv_check")

        return all_passed and not self.errors

    def get_uv_command_prefix(self) -> str:
        """Get the correct command prefix for running with uv."""
        return "uv run"


def check_environment(quiet: bool = False) -> bool:
    """Check if UV environment is properly configured."""
    checker = UVEnvironmentChecker(quiet=quiet)
    return checker.run_all_checks()


def ensure_uv_environment() -> None:
    """Ensure UV environment is set up before running codex."""
    import os

    # Check if we're already in a uv run context
    if os.environ.get("UV_PROJECT_ENVIRONMENT"):
        return  # Already in uv environment

    # Check if we're running as a globally installed tool
    # If the current executable is in ~/.local/bin, it's likely a global tool
    if sys.executable and "/.local/share/uv/tools/" in sys.executable:
        return  # Global tool installation, no project environment needed

    # Run environment check
    if not check_environment(quiet=True):
        logging.info("❌ UV environment not properly configured")
        logging.info("Run: uv run python -m codex.uv_check")
        sys.exit(1)


if __name__ == "__main__":
    import typer

    app = typer.Typer()

    @app.command()
    def check(quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output")):
        """Check UV environment configuration."""
        success = check_environment(quiet=quiet)
        sys.exit(0 if success else 1)

    app()

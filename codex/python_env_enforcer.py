"""
Python environment enforcement for Codex.

Ensures:
1. Python is from a virtual environment (not system/brew)
2. Python version is 3.12+
3. UV is being used for package management
4. Tools are run with the correct Python
"""

import os
import subprocess
import sys


class PythonEnvironmentEnforcer:
    """Enforces proper Python environment setup."""

    @staticmethod
    def check_python_version() -> tuple[bool, str]:
        """Check if Python version is 3.12+."""
        version = sys.version_info
        if version.major == 3 and version.minor >= 12:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python {version.major}.{version.minor} (need 3.12+)"

    @staticmethod
    def check_virtual_env() -> tuple[bool, str]:
        """Check if running in a virtual environment."""
        # Check common venv indicators
        in_venv = any(
            [
                hasattr(sys, "real_prefix"),  # virtualenv
                sys.base_prefix != sys.prefix,  # venv/virtualenv
                os.environ.get("VIRTUAL_ENV"),  # virtualenv/venv
                os.environ.get("UV_PROJECT_ENVIRONMENT"),  # UV
                ".venv" in sys.executable or "venv" in sys.executable,  # Path check
            ]
        )

        if in_venv:
            # Check it's not from brew or system
            if "brew" in sys.executable.lower() or "homebrew" in sys.executable.lower():
                return False, f"Using Homebrew Python: {sys.executable}"
            elif "/usr/bin/python" in sys.executable or "/usr/local/bin/python" in sys.executable:
                return False, f"Using system Python: {sys.executable}"
            return True, f"Virtual environment: {sys.executable}"

        return False, f"Not in virtual environment: {sys.executable}"

    @staticmethod
    def check_uv_available() -> tuple[bool, str]:
        """Check if UV is available and being used."""
        try:
            # Check UV environment variable
            if os.environ.get("UV_PROJECT_ENVIRONMENT"):
                return True, "UV environment detected"

            # Check if uv command exists
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return True, f"UV available: {result.stdout.strip()}"
            return False, "UV not found (install with: pip install uv)"
        except (subprocess.SubprocessError, FileNotFoundError):
            return False, "UV not installed"

    @staticmethod
    def suggest_setup() -> str:
        """Suggest proper environment setup."""
        return """
🔧 Recommended Python Environment Setup:

1. Install UV (fast Python package manager):
   curl -LsSf https://astral.sh/uv/install.sh | sh

2. Create Python 3.12 virtual environment:
   uv venv --python 3.12

3. Activate the environment:
   source .venv/bin/activate  # Unix/Mac
   .venv\\Scripts\\activate     # Windows

4. Install dependencies with UV:
   uv pip install -r requirements.txt

5. Run Codex:
   uv run codex scan

Why this matters:
• Python 3.12+ has better performance and type hints
• Virtual environments prevent dependency conflicts
• UV is 10-100x faster than pip
• Consistent environment = consistent results
"""

    @classmethod
    def enforce_environment(cls, strict: bool = False) -> bool:
        """
        Enforce proper Python environment.

        Returns True if environment is OK, False otherwise.
        If strict=True, exits the program on failure.
        """
        checks = []
        all_pass = True

        # Check Python version
        version_ok, version_msg = cls.check_python_version()
        checks.append(("Python 3.12+", version_ok, version_msg))
        all_pass = all_pass and version_ok

        # Check virtual environment
        venv_ok, venv_msg = cls.check_virtual_env()
        checks.append(("Virtual Environment", venv_ok, venv_msg))
        all_pass = all_pass and venv_ok

        # Check UV
        uv_ok, uv_msg = cls.check_uv_available()
        checks.append(("UV Package Manager", uv_ok, uv_msg))
        # UV is recommended but not required

        # Print status
        if not all_pass or not uv_ok:
            print("\n📋 Python Environment Check:", file=sys.stderr)
            for check_name, ok, msg in checks:
                symbol = "✅" if ok else "❌"
                print(f"  {symbol} {check_name}: {msg}", file=sys.stderr)

            if not all_pass:
                print(cls.suggest_setup(), file=sys.stderr)

                if strict:
                    print("\n❌ Environment check failed. Exiting.", file=sys.stderr)
                    sys.exit(1)

        return all_pass

    @staticmethod
    def get_proper_python_cmd() -> list[str]:
        """Get the proper Python command to use."""
        # Prefer UV if available
        if os.environ.get("UV_PROJECT_ENVIRONMENT"):
            return ["uv", "run", "python"]

        # Check if uv exists
        try:
            subprocess.run(["uv", "--version"], capture_output=True, timeout=1)
            return ["uv", "run", "python"]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Fall back to current Python
        return [sys.executable]

    @staticmethod
    def get_tool_cmd(tool: str) -> list[str]:
        """Get the proper command for running a tool."""
        # Prefer UV if available
        if os.environ.get("UV_PROJECT_ENVIRONMENT"):
            return ["uv", "run", tool]

        # Check if uv exists
        try:
            subprocess.run(["uv", "--version"], capture_output=True, timeout=1)
            return ["uv", "run", tool]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Fall back to direct tool
        return [tool]


def ensure_proper_environment():
    """Ensure proper Python environment for Codex."""
    enforcer = PythonEnvironmentEnforcer()

    # Check environment (non-strict by default)
    env_ok = enforcer.enforce_environment(strict=False)

    if not env_ok:
        print("\n⚠️  Consider fixing environment issues for best results", file=sys.stderr)

    return env_ok

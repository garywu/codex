#!/usr/bin/env python3
"""
Test CLI commands for the new FTS functionality.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and show results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("\nOutput:")
                print(result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("\nError:")
                print(result.stderr)
    
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

def test_cli_commands():
    """Test the new CLI commands."""
    print("🧪 Testing Codex CLI Commands")
    
    # Set up environment
    os.chdir("/Users/admin/Work/codex")
    
    # Test help
    run_command("python -m codex --help", "Help command")
    
    # Test new commands exist
    run_command("python -m codex query --help", "Query command help")
    run_command("python -m codex context --help", "Context command help") 
    run_command("python -m codex explain --help", "Explain command help")
    run_command("python -m codex validate --help", "Validate command help")
    run_command("python -m codex import-patterns --help", "Import patterns help")
    run_command("python -m codex serve --help", "Serve command help")
    run_command("python -m codex stats --help", "Stats command help")
    run_command("python -m codex export --help", "Export command help")

if __name__ == "__main__":
    test_cli_commands()
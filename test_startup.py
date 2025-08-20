#!/usr/bin/env python3
"""
Test startup configuration files and scripts.
"""

import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def test_startup_files():
    """Test all startup configuration files."""
    print("🧪 Testing Codex Startup Configuration Files")
    print("="*60)
    
    codex_root = Path("/Users/admin/Work/codex")
    
    # Test startup wrapper script
    print("\n1. 📜 Testing Startup Wrapper Script")
    print("-" * 40)
    
    wrapper_script = codex_root / "scripts" / "startup_wrapper.sh"
    
    if wrapper_script.exists():
        print(f"✅ Script exists: {wrapper_script}")
        
        # Check if executable
        if os.access(wrapper_script, os.X_OK):
            print("✅ Script is executable")
        else:
            print("❌ Script is not executable")
            print(f"   Fix: chmod +x {wrapper_script}")
        
        # Check script content
        content = wrapper_script.read_text()
        if "codex.mcp_server" in content:
            print("✅ Script references MCP server")
        else:
            print("❌ Script missing MCP server reference")
        
        if "/Users/admin/Work/codex" in content:
            print("✅ Script has correct codex path")
        else:
            print("❌ Script has incorrect path")
    else:
        print(f"❌ Script not found: {wrapper_script}")
    
    # Test macOS launchd plist
    print("\n2. 🍎 Testing macOS launchd Configuration")
    print("-" * 40)
    
    plist_file = codex_root / "config" / "com.codex.mcp-server.plist"
    
    if plist_file.exists():
        print(f"✅ Plist exists: {plist_file}")
        
        try:
            # Parse XML
            tree = ET.parse(plist_file)
            root = tree.getroot()
            
            # Check key elements
            plist_dict = {}
            current_key = None
            
            for elem in root.find('.//dict'):
                if elem.tag == 'key':
                    current_key = elem.text
                elif elem.tag in ['string', 'true', 'false'] and current_key:
                    plist_dict[current_key] = elem.text if elem.tag == 'string' else elem.tag
                    current_key = None
            
            # Validate key properties
            if plist_dict.get('Label') == 'com.codex.mcp-server':
                print("✅ Correct service label")
            else:
                print(f"❌ Wrong label: {plist_dict.get('Label')}")
            
            if wrapper_script.name in plist_dict.get('Program', ''):
                print("✅ References startup wrapper script")
            else:
                print(f"❌ Wrong program: {plist_dict.get('Program')}")
            
            if plist_dict.get('RunAtLoad') == 'true':
                print("✅ Configured to run at load")
            else:
                print("❌ Not configured to run at load")
            
        except ET.ParseError as e:
            print(f"❌ Invalid XML: {e}")
        except Exception as e:
            print(f"❌ Error parsing plist: {e}")
    else:
        print(f"❌ Plist not found: {plist_file}")
    
    # Test Linux systemd service
    print("\n3. 🐧 Testing Linux systemd Configuration")
    print("-" * 40)
    
    service_file = codex_root / "config" / "codex-mcp.service"
    
    if service_file.exists():
        print(f"✅ Service file exists: {service_file}")
        
        content = service_file.read_text()
        
        # Check key properties
        if "[Unit]" in content and "[Service]" in content and "[Install]" in content:
            print("✅ Has required systemd sections")
        else:
            print("❌ Missing systemd sections")
        
        if "codex.mcp_server" in content:
            print("✅ References MCP server module")
        else:
            print("❌ Missing MCP server reference")
        
        if "Restart=always" in content:
            print("✅ Configured for auto-restart")
        else:
            print("❌ Missing auto-restart configuration")
        
        if "WantedBy=" in content:
            print("✅ Has install target")
        else:
            print("❌ Missing install target")
    else:
        print(f"❌ Service file not found: {service_file}")
    
    # Test directory structure
    print("\n4. 📁 Testing Directory Structure")
    print("-" * 40)
    
    required_dirs = [
        "scripts",
        "config", 
        "logs",
        "data"
    ]
    
    for dir_name in required_dirs:
        dir_path = codex_root / dir_name
        if dir_path.exists():
            print(f"✅ Directory exists: {dir_name}/")
        else:
            print(f"❌ Directory missing: {dir_name}/")
            print(f"   Fix: mkdir -p {dir_path}")
    
    # Test log directory permissions
    log_dir = codex_root / "logs"
    if log_dir.exists():
        if os.access(log_dir, os.W_OK):
            print("✅ Log directory is writable")
        else:
            print("❌ Log directory not writable")
    
    # Test if commands would work
    print("\n5. 🔧 Testing Command Compatibility")
    print("-" * 40)
    
    system = platform.system()
    print(f"Platform: {system}")
    
    if system == "Darwin":
        # Test launchctl availability
        try:
            result = subprocess.run(["launchctl", "help"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ launchctl available")
            else:
                print("❌ launchctl not working")
        except FileNotFoundError:
            print("❌ launchctl not found")
    
    elif system == "Linux":
        # Test systemctl availability
        try:
            result = subprocess.run(["systemctl", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ systemctl available")
            else:
                print("❌ systemctl not working")
        except FileNotFoundError:
            print("❌ systemctl not found")
    
    # Test Python module availability
    print("\n6. 🐍 Testing Python Module")
    print("-" * 40)
    
    try:
        # Test if we can import the module (without running it)
        sys.path.insert(0, str(codex_root))
        
        # Test basic imports (without the problematic dependencies)
        import sqlite3
        print("✅ sqlite3 available")
        
        import json
        print("✅ json available")
        
        import pathlib
        print("✅ pathlib available")
        
        # Test if codex directory structure is correct
        codex_module = codex_root / "codex"
        if codex_module.exists():
            print("✅ codex module directory exists")
            
            mcp_server = codex_module / "mcp_server.py"
            if mcp_server.exists():
                print("✅ mcp_server.py exists")
            else:
                print("❌ mcp_server.py missing")
        else:
            print("❌ codex module directory missing")
    
    except Exception as e:
        print(f"❌ Python module test failed: {e}")
    
    print("\n" + "="*60)
    print("✅ STARTUP CONFIGURATION TEST COMPLETE")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Fix any issues shown above")
    print("2. Run: codex install-startup")
    print("3. Run: codex startup-status")
    print("4. Check logs in ~/Work/codex/logs/")
    
    print("\n🚀 Installation Commands:")
    print("# Install as user service (recommended)")
    print("codex install-startup --user")
    print("")
    print("# Install as system service (requires sudo)")
    print("codex install-startup --system")
    print("")
    print("# Check status")
    print("codex startup-status")
    print("")
    print("# View logs")
    print("tail -f ~/Work/codex/logs/codex-mcp.log")


if __name__ == "__main__":
    test_startup_files()
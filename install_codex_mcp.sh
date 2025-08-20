#!/bin/bash
#
# Codex MCP Server Comprehensive Installation Script
#
# This script handles:
# 1. macOS launchd service installation/removal
# 2. Claude Desktop MCP configuration
# 3. Pattern database setup
# 4. Dependency verification
# 5. Service testing and validation
#
# Usage:
#   ./install_codex_mcp.sh install    # Install everything
#   ./install_codex_mcp.sh uninstall  # Remove everything
#   ./install_codex_mcp.sh status     # Check status
#   ./install_codex_mcp.sh claude     # Configure Claude Desktop only
#   ./install_codex_mcp.sh launchd    # Configure launchd only
#

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="${SCRIPT_DIR}"
SERVICE_NAME="com.codex.mcp-server"
PLIST_FILE="${HOME}/Library/LaunchAgents/${SERVICE_NAME}.plist"
CLAUDE_CONFIG_DIR="${HOME}/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="${CLAUDE_CONFIG_DIR}/claude_desktop_config.json"
LOG_DIR="${CODEX_ROOT}/logs"
DATA_DIR="${CODEX_ROOT}/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "\n${BLUE}$1${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..60})${NC}"
}

# Check if we're on macOS
check_macos() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        log_error "This script is designed for macOS only"
        exit 1
    fi
}

# Verify dependencies
check_dependencies() {
    log_header "🔍 Checking Dependencies"

    # Check Python 3
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_success "Python found: $PYTHON_VERSION"
    else
        log_error "Python 3 not found. Please install Python 3.11 or later"
        exit 1
    fi

    # Check if Codex module is available
    if python3 -c "import sys; sys.path.insert(0, '${CODEX_ROOT}'); import codex.mcp_server" 2>/dev/null; then
        log_success "Codex MCP server module available"
    else
        log_warning "Codex MCP server module not fully available (dependencies may be missing)"
        log_info "This is normal if you haven't installed all dependencies yet"
    fi

    # Check launchctl
    if command -v launchctl &> /dev/null; then
        log_success "launchctl available"
    else
        log_error "launchctl not found"
        exit 1
    fi

    # Check directory structure
    if [[ -d "${CODEX_ROOT}/codex" ]]; then
        log_success "Codex module directory exists"
    else
        log_error "Codex module directory not found at ${CODEX_ROOT}/codex"
        exit 1
    fi
}

# Create necessary directories
setup_directories() {
    log_header "📁 Setting Up Directories"

    for dir in "${LOG_DIR}" "${DATA_DIR}" "$(dirname "${PLIST_FILE}")" "${CLAUDE_CONFIG_DIR}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        else
            log_info "Directory already exists: $dir"
        fi
    done

    # Set permissions
    chmod 755 "${CODEX_ROOT}/scripts/startup_wrapper.sh" 2>/dev/null || true
    chmod 755 "${LOG_DIR}" "${DATA_DIR}"

    log_success "Directory setup complete"
}

# Install launchd service
install_launchd() {
    log_header "🚀 Installing launchd Service"

    # Stop existing service if running
    if launchctl list | grep -q "${SERVICE_NAME}"; then
        log_info "Stopping existing service..."
        launchctl stop "${SERVICE_NAME}" 2>/dev/null || true
        launchctl unload "${PLIST_FILE}" 2>/dev/null || true
    fi

    # Copy plist file
    local plist_source="${CODEX_ROOT}/config/com.codex.mcp-server.plist"

    if [[ ! -f "$plist_source" ]]; then
        log_error "Source plist file not found: $plist_source"
        exit 1
    fi

    cp "$plist_source" "$PLIST_FILE"
    log_success "Copied plist file to $PLIST_FILE"

    # Load and start service
    if launchctl load "$PLIST_FILE"; then
        log_success "Loaded launchd service"

        # Give it a moment to start
        sleep 2

        if launchctl start "${SERVICE_NAME}"; then
            log_success "Started MCP server service"
        else
            log_warning "Service loaded but failed to start (check logs)"
        fi
    else
        log_error "Failed to load launchd service"
        exit 1
    fi
}

# Uninstall launchd service
uninstall_launchd() {
    log_header "🗑️  Removing launchd Service"

    # Stop and unload service
    if launchctl list | grep -q "${SERVICE_NAME}"; then
        log_info "Stopping service..."
        launchctl stop "${SERVICE_NAME}" 2>/dev/null || true
        launchctl unload "${PLIST_FILE}" 2>/dev/null || true
        log_success "Stopped and unloaded service"
    else
        log_info "Service not currently loaded"
    fi

    # Remove plist file
    if [[ -f "$PLIST_FILE" ]]; then
        rm "$PLIST_FILE"
        log_success "Removed plist file"
    else
        log_info "Plist file not found"
    fi
}

# Configure Claude Desktop MCP
install_claude_mcp() {
    log_header "🤖 Configuring Claude Desktop MCP"

    local config_content

    # Check if Claude config file exists
    if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
        log_info "Existing Claude Desktop config found"

        # Backup existing config
        local backup_file="${CLAUDE_CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CLAUDE_CONFIG_FILE" "$backup_file"
        log_success "Backed up existing config to $backup_file"

        # Read existing config
        config_content=$(cat "$CLAUDE_CONFIG_FILE")
    else
        log_info "Creating new Claude Desktop config"
        config_content="{}"
    fi

    # Create MCP configuration
    local mcp_config=$(cat <<EOF
{
  "mcpServers": {
    "codex-patterns": {
      "command": "python3",
      "args": ["-m", "codex.mcp_server"],
      "cwd": "${CODEX_ROOT}",
      "env": {
        "PYTHONPATH": "${CODEX_ROOT}",
        "CODEX_LOG_LEVEL": "INFO"
      }
    }
  }
}
EOF
    )

    # Merge configurations using Python
    python3 -c "
import json
import sys

# Read existing config
try:
    with open('${CLAUDE_CONFIG_FILE}', 'r') as f:
        existing = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    existing = {}

# Read new MCP config
new_mcp = json.loads('''${mcp_config}''')

# Merge configurations
if 'mcpServers' not in existing:
    existing['mcpServers'] = {}

existing['mcpServers']['codex-patterns'] = new_mcp['mcpServers']['codex-patterns']

# Write back
with open('${CLAUDE_CONFIG_FILE}', 'w') as f:
    json.dump(existing, f, indent=2)

print('MCP configuration updated')
"

    log_success "Claude Desktop MCP configuration installed"
    log_info "Config location: $CLAUDE_CONFIG_FILE"
    log_warning "Please restart Claude Desktop to load the new configuration"
}

# Remove Claude Desktop MCP configuration
uninstall_claude_mcp() {
    log_header "🗑️  Removing Claude Desktop MCP Configuration"

    if [[ ! -f "$CLAUDE_CONFIG_FILE" ]]; then
        log_info "Claude Desktop config file not found"
        return
    fi

    # Backup and remove codex-patterns entry
    local backup_file="${CLAUDE_CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CLAUDE_CONFIG_FILE" "$backup_file"
    log_success "Backed up config to $backup_file"

    # Remove codex-patterns using Python
    python3 -c "
import json

try:
    with open('${CLAUDE_CONFIG_FILE}', 'r') as f:
        config = json.load(f)

    if 'mcpServers' in config and 'codex-patterns' in config['mcpServers']:
        del config['mcpServers']['codex-patterns']

        # Remove mcpServers section if empty
        if not config['mcpServers']:
            del config['mcpServers']

        with open('${CLAUDE_CONFIG_FILE}', 'w') as f:
            json.dump(config, f, indent=2)

        print('Removed codex-patterns from Claude Desktop config')
    else:
        print('codex-patterns not found in config')

except Exception as e:
    print(f'Error updating config: {e}')
"

    log_success "Removed Codex MCP configuration from Claude Desktop"
}

# Import initial patterns
import_patterns() {
    log_header "📥 Importing Pattern Database"

    local pattern_files=(
        "${HOME}/work/project-init.json"
        "${HOME}/work/project-init-updated.json"
        "${CODEX_ROOT}/../project-init.json"
    )

    local imported=false

    for pattern_file in "${pattern_files[@]}"; do
        if [[ -f "$pattern_file" ]]; then
            log_info "Found pattern file: $pattern_file"

            # Try to import patterns using our demo script
            if python3 -c "
import sys
sys.path.insert(0, '${CODEX_ROOT}')

try:
    from codex.pattern_extractor import PatternExtractor
    from codex.fts_database import FTSDatabase

    db = FTSDatabase('${DATA_DIR}/patterns_fts.db')
    extractor = PatternExtractor()
    patterns = extractor.extract_from_project_init('${pattern_file}')

    for pattern in patterns:
        db.add_pattern(pattern)

    print(f'Imported {len(patterns)} patterns from ${pattern_file}')

except Exception as e:
    print(f'Error importing patterns: {e}')
    import traceback
    traceback.print_exc()
" 2>/dev/null; then
                log_success "Imported patterns from $pattern_file"
                imported=true
                break
            else
                log_warning "Failed to import patterns from $pattern_file"
            fi
        fi
    done

    if [[ "$imported" == false ]]; then
        log_warning "No pattern files found or imported"
        log_info "You can import patterns later with: codex import-patterns <file>"
    fi
}

# Check service status
check_status() {
    log_header "📊 Service Status"

    # Check launchd service
    if launchctl list | grep -q "${SERVICE_NAME}"; then
        local status_info=$(launchctl list "${SERVICE_NAME}" 2>/dev/null)
        if echo "$status_info" | grep -q '"PID" = [0-9]'; then
            local pid=$(echo "$status_info" | grep '"PID"' | sed 's/.*= \([0-9]*\);/\1/')
            log_success "launchd service running (PID: $pid)"
        else
            log_warning "launchd service loaded but not running"
        fi
    else
        log_error "launchd service not loaded"
    fi

    # Check plist file
    if [[ -f "$PLIST_FILE" ]]; then
        log_success "Plist file exists: $PLIST_FILE"
    else
        log_error "Plist file missing: $PLIST_FILE"
    fi

    # Check Claude Desktop config
    if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
        if grep -q "codex-patterns" "$CLAUDE_CONFIG_FILE"; then
            log_success "Claude Desktop MCP configuration found"
        else
            log_warning "Claude Desktop config exists but no codex-patterns entry"
        fi
    else
        log_warning "Claude Desktop config file not found"
    fi

    # Check log files
    log_header "📁 Log Files"
    if [[ -d "$LOG_DIR" ]]; then
        local log_files=("${LOG_DIR}"/*.log)
        if [[ -f "${log_files[0]}" ]]; then
            for log_file in "${log_files[@]}"; do
                if [[ -f "$log_file" ]]; then
                    local size=$(stat -f%z "$log_file" 2>/dev/null || echo "0")
                    log_info "$(basename "$log_file"): ${size} bytes"
                fi
            done
        else
            log_info "No log files found (service may not have started yet)"
        fi
    else
        log_warning "Log directory not found: $LOG_DIR"
    fi

    # Check database
    if [[ -f "${DATA_DIR}/patterns_fts.db" ]]; then
        local db_size=$(stat -f%z "${DATA_DIR}/patterns_fts.db" 2>/dev/null || echo "0")
        log_success "Pattern database exists: ${db_size} bytes"
    else
        log_warning "Pattern database not found"
    fi
}

# Test MCP connection
test_mcp() {
    log_header "🧪 Testing MCP Connection"

    # Test if we can connect to the MCP server
    local test_script=$(cat <<'EOF'
import json
import subprocess
import sys
import time

# Try to test the MCP server using stdio
test_input = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}

try:
    # Start the MCP server
    proc = subprocess.Popen(
        ["python3", "-m", "codex.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=sys.argv[1]
    )

    # Send test request
    input_line = json.dumps(test_input) + "\n"
    proc.stdin.write(input_line)
    proc.stdin.flush()

    # Wait a bit for response
    time.sleep(1)

    # Check if process is still running
    if proc.poll() is None:
        print("✅ MCP server started successfully")
        proc.terminate()
        proc.wait()
    else:
        stdout, stderr = proc.communicate()
        print(f"❌ MCP server failed to start")
        if stderr:
            print(f"Error: {stderr}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error testing MCP server: {e}")
    sys.exit(1)
EOF
    )

    if python3 -c "$test_script" "$CODEX_ROOT" 2>/dev/null; then
        log_success "MCP server test passed"
    else
        log_error "MCP server test failed"
        log_info "Check logs for details: tail -f ${LOG_DIR}/codex-mcp-error.log"
    fi
}

# Main installation function
install_all() {
    log_header "🚀 Installing Codex MCP Server"

    check_dependencies
    setup_directories
    install_launchd
    install_claude_mcp
    import_patterns

    log_header "✅ Installation Complete"
    log_success "Codex MCP Server is now installed and running"
    log_info "Next steps:"
    echo "  1. Restart Claude Desktop to load MCP configuration"
    echo "  2. Test with: ./install_codex_mcp.sh status"
    echo "  3. View logs: tail -f ${LOG_DIR}/codex-mcp.log"
    echo "  4. Query patterns: codex query 'HTTP client'"
}

# Main uninstallation function
uninstall_all() {
    log_header "🗑️  Uninstalling Codex MCP Server"

    uninstall_launchd
    uninstall_claude_mcp

    log_header "✅ Uninstallation Complete"
    log_success "Codex MCP Server has been removed"
    log_info "Note: Pattern database and logs are preserved"
    log_info "To remove completely: rm -rf ${LOG_DIR} ${DATA_DIR}"
}

# Main script logic
main() {
    check_macos

    case "${1:-install}" in
        "install")
            install_all
            ;;
        "uninstall")
            uninstall_all
            ;;
        "status")
            check_status
            ;;
        "test")
            test_mcp
            ;;
        "claude")
            log_header "🤖 Installing Claude Desktop MCP Only"
            check_dependencies
            setup_directories
            install_claude_mcp
            ;;
        "launchd")
            log_header "🚀 Installing launchd Service Only"
            check_dependencies
            setup_directories
            install_launchd
            ;;
        "import")
            log_header "📥 Importing Patterns Only"
            setup_directories
            import_patterns
            ;;
        *)
            echo "Usage: $0 {install|uninstall|status|test|claude|launchd|import}"
            echo ""
            echo "Commands:"
            echo "  install   - Install everything (launchd + Claude Desktop MCP)"
            echo "  uninstall - Remove everything"
            echo "  status    - Check installation status"
            echo "  test      - Test MCP server connection"
            echo "  claude    - Install Claude Desktop MCP configuration only"
            echo "  launchd   - Install launchd service only"
            echo "  import    - Import pattern database only"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"

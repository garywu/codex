#!/bin/bash
"""
Codex MCP Server Startup Wrapper
Handles environment setup and server startup with proper logging.
"""

# Configuration
CODEX_HOME="/Users/admin/Work/codex"
LOG_DIR="/Users/admin/Work/codex/logs"
PID_FILE="/Users/admin/Work/codex/logs/codex-mcp.pid"
LOG_FILE="/Users/admin/Work/codex/logs/codex-mcp.log"
ERROR_LOG="/Users/admin/Work/codex/logs/codex-mcp-error.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Function to cleanup on exit
cleanup() {
    log "Codex MCP Server shutting down..."
    if [ -f "$PID_FILE" ]; then
        rm "$PID_FILE"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Change to codex directory
cd "$CODEX_HOME" || {
    log "ERROR: Failed to change to Codex directory: $CODEX_HOME"
    exit 1
}

# Check if Python environment is available
if ! command -v python3 &> /dev/null; then
    log "ERROR: python3 not found in PATH"
    exit 1
fi

# Check if codex module is available
if ! python3 -c "import codex.mcp_server" 2>/dev/null; then
    log "ERROR: Codex module not found or not properly installed"
    exit 1
fi

# Save PID
echo $$ > "$PID_FILE"

log "Starting Codex MCP Server..."
log "Working directory: $(pwd)"
log "Python version: $(python3 --version)"
log "PID: $$"

# Start the MCP server with proper error handling
exec python3 -m codex.mcp_server 2>>"$ERROR_LOG" | tee -a "$LOG_FILE"

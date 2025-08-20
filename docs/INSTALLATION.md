# Codex MCP Server - Complete Installation Guide

This guide covers automatic installation of the Codex MCP Server for seamless AI assistant integration.

## 🚀 Quick Installation

For most users, simply run the comprehensive installer:

```bash
cd /Users/admin/Work/codex
./install_codex_mcp.sh install
```

This will:
- ✅ Install launchd service (auto-start at login)
- ✅ Configure Claude Desktop MCP integration
- ✅ Import pattern database from project-init.json
- ✅ Set up logging and monitoring
- ✅ Test the complete system

## 📋 Installation Options

### Complete Installation (Recommended)
```bash
./install_codex_mcp.sh install
```
Installs everything: launchd service + Claude Desktop MCP + patterns

### Individual Components
```bash
# Install only launchd service
./install_codex_mcp.sh launchd

# Install only Claude Desktop MCP configuration
./install_codex_mcp.sh claude

# Import patterns only
./install_codex_mcp.sh import
```

### Check Status
```bash
./install_codex_mcp.sh status
```

### Test Installation
```bash
./install_codex_mcp.sh test
```

### Complete Removal
```bash
./install_codex_mcp.sh uninstall
```

## 🔧 Manual Installation Methods

### Method 1: CLI Commands (Requires Dependencies)
```bash
# Import patterns first
codex import-patterns ~/work/project-init.json

# Install startup service
codex install-startup --user

# Check status
codex startup-status
```

### Method 2: Manual launchd Setup
```bash
# Copy plist file
cp config/com.codex.mcp-server.plist ~/Library/LaunchAgents/

# Load service
launchctl load ~/Library/LaunchAgents/com.codex.mcp-server.plist

# Start service
launchctl start com.codex.mcp-server
```

### Method 3: Manual Claude Desktop Setup
```bash
# Create Claude config directory
mkdir -p "$HOME/Library/Application Support/Claude"

# Copy MCP configuration
cp config/claude_desktop_config.json "$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Restart Claude Desktop
```

## 🔍 Verification

After installation, verify everything is working:

### 1. Check Service Status
```bash
./install_codex_mcp.sh status
```

Should show:
- ✅ launchd service running
- ✅ Plist file exists
- ✅ Claude Desktop MCP configuration found
- ✅ Pattern database exists
- ℹ️  Log files present

### 2. Test MCP Connection
```bash
./install_codex_mcp.sh test
```

Should show:
- ✅ MCP server started successfully

### 3. Test Pattern Queries (if CLI works)
```bash
# Test basic functionality
codex query "HTTP client"
codex context --file src/api.py
codex validate --code "import requests"
```

### 4. Test Claude Desktop Integration
1. Restart Claude Desktop
2. In a conversation, check if Codex tools are available
3. Try querying patterns through Claude

## 📁 File Locations

After installation, files are located at:

```
/Users/admin/Work/codex/
├── config/
│   ├── com.codex.mcp-server.plist      # launchd service config
│   ├── codex-mcp.service               # Linux systemd config
│   └── claude_desktop_config.json     # Claude Desktop MCP template
├── scripts/
│   └── startup_wrapper.sh             # Service startup script
├── logs/                               # Service logs
│   ├── codex-mcp.log                  # Main log
│   ├── codex-mcp-error.log           # Error log
│   ├── codex-mcp-stdout.log          # Standard output
│   └── codex-mcp-stderr.log          # Standard error
├── data/                               # Pattern database
│   └── patterns_fts.db               # SQLite FTS database
└── install_codex_mcp.sh              # This installer
```

**System Files:**
- `~/Library/LaunchAgents/com.codex.mcp-server.plist` - launchd service
- `~/Library/Application Support/Claude/claude_desktop_config.json` - Claude Desktop config

## 🔧 Configuration

### Service Configuration
The launchd service is configured to:
- Start automatically when you log in
- Restart if it crashes
- Log to `~/Work/codex/logs/`
- Run with your user permissions

### Claude Desktop MCP Configuration
The MCP integration provides these tools:
- `query_patterns` - Natural language pattern search
- `get_file_context` - File-specific recommendations
- `explain_pattern` - Detailed pattern explanations
- `validate_code` - Code snippet validation
- `semantic_search` - Intent-based discovery

### Environment Variables
```bash
PYTHONPATH=/Users/admin/Work/codex
CODEX_LOG_LEVEL=INFO
PATH=/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin
```

## 🐛 Troubleshooting

### Service Won't Start

1. **Check dependencies**:
   ```bash
   python3 -c "import sqlite3, json; print('OK')"
   ```

2. **Check permissions**:
   ```bash
   ls -la scripts/startup_wrapper.sh
   # Should show: -rwxr-xr-x
   ```

3. **Check logs**:
   ```bash
   tail -f logs/codex-mcp-error.log
   ```

4. **Restart service**:
   ```bash
   ./install_codex_mcp.sh uninstall
   ./install_codex_mcp.sh install
   ```

### Claude Desktop Not Connecting

1. **Restart Claude Desktop** completely
2. **Check configuration**:
   ```bash
   cat "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
   ```
3. **Verify service is running**:
   ```bash
   ./install_codex_mcp.sh status
   ```

### Pattern Database Issues

1. **Reimport patterns**:
   ```bash
   ./install_codex_mcp.sh import
   ```

2. **Check database**:
   ```bash
   ls -la data/patterns_fts.db
   sqlite3 data/patterns_fts.db "SELECT COUNT(*) FROM patterns;"
   ```

### Permission Issues

1. **Fix script permissions**:
   ```bash
   chmod +x scripts/startup_wrapper.sh
   chmod +x install_codex_mcp.sh
   ```

2. **Fix directory permissions**:
   ```bash
   chmod -R 755 logs/ data/ config/
   ```

### High Resource Usage

1. **Monitor process**:
   ```bash
   top -p $(pgrep -f "codex.mcp_server")
   ```

2. **Check log size**:
   ```bash
   du -sh logs/
   ```

3. **Rotate logs if needed**:
   ```bash
   mv logs/codex-mcp.log logs/codex-mcp.log.old
   launchctl stop com.codex.mcp-server
   launchctl start com.codex.mcp-server
   ```

## 🔄 Service Management

### Start/Stop Service
```bash
# Stop
launchctl stop com.codex.mcp-server

# Start
launchctl start com.codex.mcp-server

# Restart
launchctl stop com.codex.mcp-server && launchctl start com.codex.mcp-server
```

### View Logs
```bash
# Real-time main log
tail -f logs/codex-mcp.log

# Real-time error log
tail -f logs/codex-mcp-error.log

# All recent logs
tail -f logs/*.log
```

### Check Service Details
```bash
# Service info
launchctl list com.codex.mcp-server

# Service definition
launchctl print gui/$(id -u)/com.codex.mcp-server
```

## 🚀 Next Steps

After successful installation:

1. **Test pattern queries**:
   ```bash
   codex query "HTTP client"
   codex explain use-httpx
   ```

2. **Import your organization's patterns**:
   ```bash
   codex import-patterns /path/to/your/project-init.json
   ```

3. **Configure your AI assistants** to use the MCP server

4. **Set up monitoring** and log rotation if needed

5. **Train your team** on the available patterns and tools

## 📚 Advanced Configuration

### Custom Pattern Sources
Add your own pattern sources by:
1. Creating project-init.json files
2. Importing with `codex import-patterns`
3. Setting up automatic sync

### Multi-Project Setup
For multiple projects:
1. Install Codex once (this installation)
2. Import patterns from each project
3. Use file-specific context queries
4. Set up project-specific pattern priorities

### Integration with CI/CD
```bash
# Pre-commit hook
codex scan --quiet || exit 1

# CI validation
codex validate src/ --format json > violations.json
```

## 🔒 Security Considerations

- Service runs with **user permissions** (not root)
- Pattern database is **local only**
- No network connections required
- Logs may contain code snippets - secure appropriately
- MCP server binds to stdio only (not network ports)

## 📊 Monitoring

Monitor the service health:
```bash
# Check if running
pgrep -f "codex.mcp_server"

# Monitor resource usage
top -p $(pgrep -f "codex.mcp_server")

# Check database size
ls -lh data/patterns_fts.db

# Monitor query performance
grep "Query.*ms" logs/codex-mcp.log
```

# Codex MCP Server - Automatic Startup Installation

This guide covers setting up the Codex MCP server to start automatically at system boot.

## Quick Start

For most users, simply run:

```bash
# Install as user service (recommended)
codex install-startup

# Check status
codex startup-status

# View logs
tail -f ~/Work/codex/logs/codex-mcp.log
```

## Installation Options

### User Service (Recommended)
Runs when you log in, stops when you log out:

```bash
codex install-startup --user
```

**macOS**: Installs to `~/Library/LaunchAgents/`  
**Linux**: Installs to `~/.config/systemd/user/`

### System Service
Runs at boot for all users (requires sudo):

```bash
codex install-startup --system
```

**macOS**: Installs to `/Library/LaunchDaemons/`  
**Linux**: Installs to `/etc/systemd/system/`

## Platform-Specific Details

### macOS (launchd)

The service uses launchd with the following configuration:

- **Service Name**: `com.codex.mcp-server`
- **Auto-restart**: Yes (if crashed)
- **Keep alive**: Yes
- **Logs**: `~/Work/codex/logs/`

**Manual management**:
```bash
# Start manually
launchctl start com.codex.mcp-server

# Stop manually  
launchctl stop com.codex.mcp-server

# Check status
launchctl print gui/$(id -u)/com.codex.mcp-server
```

### Linux (systemd)

The service uses systemd with the following configuration:

- **Service Name**: `codex-mcp.service`
- **Auto-restart**: Yes (always)
- **Resource limits**: 512MB memory, 1024 file descriptors
- **Logs**: journald + `~/Work/codex/logs/`

**Manual management**:
```bash
# Start manually
systemctl --user start codex-mcp.service

# Stop manually
systemctl --user stop codex-mcp.service

# Check status
systemctl --user status codex-mcp.service

# View logs
journalctl --user -u codex-mcp.service -f
```

## Service Management Commands

### Check Status
```bash
codex startup-status
```

Shows:
- Installation status (user/system)
- Running status (active/inactive)
- Log file locations and sizes

### Uninstall
```bash
# Remove user service
codex uninstall-startup

# Remove system service
codex uninstall-startup --system
```

### View Logs
```bash
# Real-time logs
tail -f ~/Work/codex/logs/codex-mcp.log

# Error logs
tail -f ~/Work/codex/logs/codex-mcp-error.log

# System logs (Linux)
journalctl --user -u codex-mcp.service -f

# System logs (macOS)
log stream --predicate 'process == "codex"'
```

## Configuration Files

### macOS launchd plist
```xml
<!-- ~/Library/LaunchAgents/com.codex.mcp-server.plist -->
<key>Label</key>
<string>com.codex.mcp-server</string>

<key>Program</key>
<string>/Users/admin/Work/codex/scripts/startup_wrapper.sh</string>

<key>RunAtLoad</key>
<true/>

<key>KeepAlive</key>
<dict>
    <key>Crashed</key>
    <true/>
</dict>
```

### Linux systemd service
```ini
# ~/.config/systemd/user/codex-mcp.service
[Unit]
Description=Codex MCP Server for AI Pattern Queries
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m codex.mcp_server
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

## Troubleshooting

### Service Won't Start

1. **Check Python environment**:
   ```bash
   python3 -c "import codex.mcp_server; print('OK')"
   ```

2. **Check permissions**:
   ```bash
   ls -la ~/Work/codex/scripts/startup_wrapper.sh
   # Should be executable: -rwxr-xr-x
   ```

3. **Check logs**:
   ```bash
   cat ~/Work/codex/logs/codex-mcp-error.log
   ```

### Service Crashes

1. **Check resource limits**:
   - Memory usage: Monitor with `top` or `htop`
   - File descriptors: Check with `lsof -p <pid>`

2. **Check dependencies**:
   ```bash
   python3 -c "import sqlite3, json, pathlib; print('Dependencies OK')"
   ```

3. **Restart manually**:
   ```bash
   codex uninstall-startup
   codex install-startup
   ```

### Logs Not Appearing

1. **Create log directory**:
   ```bash
   mkdir -p ~/Work/codex/logs
   chmod 755 ~/Work/codex/logs
   ```

2. **Check disk space**:
   ```bash
   df -h ~/Work/codex/logs
   ```

### Permission Issues

1. **Fix script permissions**:
   ```bash
   chmod +x ~/Work/codex/scripts/startup_wrapper.sh
   ```

2. **Fix directory permissions**:
   ```bash
   chmod -R 755 ~/Work/codex
   ```

## Security Considerations

### User Service (Recommended)
- ✅ Runs with user permissions
- ✅ No root access required
- ✅ Isolated to user session
- ❌ Stops when user logs out

### System Service
- ⚠️ Runs with elevated permissions
- ⚠️ Requires sudo for installation
- ✅ Runs for all users
- ✅ Starts at boot, independent of user login

## Environment Variables

The service sets these environment variables:

- `PYTHONPATH`: `/Users/admin/Work/codex`
- `CODEX_LOG_LEVEL`: `INFO`
- `PATH`: Includes `/usr/local/bin`, `/opt/homebrew/bin`

To customize, edit the configuration files directly:

**macOS**: Edit the `<key>EnvironmentVariables</key>` section in the plist  
**Linux**: Edit the `Environment=` lines in the service file

## AI Assistant Integration

Once the service is running, AI assistants can connect via:

**MCP Protocol** (recommended):
- Tools available for pattern queries
- Automatic context generation
- Code validation
- Real-time pattern recommendations

**CLI Interface**:
- `codex query "HTTP client"`
- `codex context --file src/api.py`
- `codex validate src/main.py`

## Performance Monitoring

The service is lightweight but you can monitor performance:

```bash
# Check service status
codex startup-status

# Monitor resource usage
top -p $(pgrep -f "codex.mcp_server")

# Check database size
ls -lh ~/Work/codex/data/patterns_fts.db

# Monitor logs
tail -f ~/Work/codex/logs/codex-mcp.log | grep -E "Query|Error|Performance"
```

## Next Steps

After installation:

1. **Import patterns**:
   ```bash
   codex import-patterns ~/work/project-init.json
   ```

2. **Test functionality**:
   ```bash
   codex query "HTTP client"
   codex context --file src/api.py
   ```

3. **Configure AI assistants** to use the MCP server

4. **Monitor logs** for any issues

5. **Set up pattern database** with your organization's standards
# Master Orchestrator Setup Guide

This guide explains how to use the Master Orchestrator to run all AI Employee components in a single unified system.

## Overview

The orchestrator manages all watcher processes and the approval handler, providing:
- **Single Command Startup** - No need for multiple terminal windows
- **Automatic Restart** - Failed processes are automatically restarted
- **Health Monitoring** - Checks process health every 30 seconds
- **Graceful Shutdown** - Clean termination of all processes with Ctrl+C
- **Dashboard Integration** - Updates system status automatically

## Managed Processes

The orchestrator manages these components:

1. **File System Watcher** - Monitors `/Inbox` for new files
2. **Gmail Watcher** - Monitors Gmail for important unread emails
3. **WhatsApp Watcher** - Monitors WhatsApp Web for urgent messages
4. **Approval Handler** - Executes approved actions (Safety Valve)

## Prerequisites

Before running the orchestrator, ensure:

- ✅ Vault structure initialized (`python setup_vault.py`)
- ✅ All watchers are configured and tested individually
- ✅ Gmail credentials set up (`credentials/token.json`)
- ✅ WhatsApp session authenticated (`whatsapp_session/`)
- ✅ Python dependencies installed (`pip install -r requirements.txt`)

## Usage

### Basic Usage

Start the orchestrator:

```bash
cd /path/to/Personal-AI-Employee
python orchestrator.py
```

Or specify vault path explicitly:

```bash
python orchestrator.py /path/to/AI_Employee_Vault
```

### What You'll See

```
============================================================
AI Employee Master Orchestrator
============================================================
Vault path: /path/to/AI_Employee_Vault

Starting File System Watcher...
Started File System Watcher (PID: 12345)
Starting Gmail Inbox Watcher...
Started Gmail Inbox Watcher (PID: 12346)
Starting WhatsApp Web Watcher...
Started WhatsApp Web Watcher (PID: 12347)
Starting Approval Handler (Safety Valve)...
Started Approval Handler (Safety Valve) (PID: 12348)

============================================================
All watchers started successfully
Press Ctrl+C to stop
============================================================
```

### Stopping the Orchestrator

Press `Ctrl+C` to initiate graceful shutdown:

```
Received signal 2, initiating graceful shutdown...
============================================================
Shutting down all processes...
============================================================
Stopping File System Watcher...
Stopped File System Watcher
Stopping Gmail Inbox Watcher...
Stopped Gmail Inbox Watcher
Stopping WhatsApp Web Watcher...
Stopped WhatsApp Web Watcher
Stopping Approval Handler (Safety Valve)...
Stopped Approval Handler (Safety Valve)
All processes stopped
```

## Features

### Automatic Restart with Crash Detection

If a process crashes (e.g., due to network timeout), the orchestrator will:

1. Detect the failure within 30 seconds (or immediately on startup)
2. Display a **[CRASH DETECTED]** alert with instructions
3. Log the event to `Logs/system.log`
4. Capture full error traceback in `Logs/process_debug.log`
5. Wait before restart (exponential backoff)
6. Restart the process automatically
7. Continue monitoring

**Example crash alert:**

```
================================================================================
🚨 [CRASH DETECTED]
================================================================================
Process: Gmail Inbox Watcher
Script: gmail_watcher.py
Restart Count: 2

⚠️  ACTION REQUIRED:
   Check the debug log for error details:
   tail -100 AI_Employee_Vault/Logs/process_debug.log
================================================================================
```

**Example log entry:**

```
2026-02-16 18:30:15 - Orchestrator - ERROR - 🚨 [CRASH DETECTED] Gmail Inbox Watcher has died!
2026-02-16 18:30:15 - Orchestrator - ERROR -    Check AI_Employee_Vault/Logs/process_debug.log for error traceback and details
2026-02-16 18:30:15 - Orchestrator - INFO - Waiting 2s before restart...
2026-02-16 18:30:17 - Orchestrator - INFO - Started Gmail Inbox Watcher (PID: 12350)
2026-02-16 18:30:17 - Orchestrator - INFO - ✓ Gmail Inbox Watcher startup verified (running after 2s)
2026-02-16 18:30:17 - Orchestrator - INFO - Gmail Inbox Watcher restarted successfully (restart #2)
```

### Immediate Crash Detection

The orchestrator now verifies that processes start successfully:

1. After launching a process, waits 2 seconds
2. Checks if the process is still running
3. If it crashed immediately, displays detailed error information

**Example immediate crash alert:**

```
================================================================================
⚠️  IMMEDIATE CRASH DETECTED
================================================================================
Process: WhatsApp Web Watcher
Script: whatsapp_watcher.py
Exit Code: 1
Debug Log: AI_Employee_Vault/Logs/process_debug.log
================================================================================
```

This helps identify configuration issues, missing dependencies, or import errors immediately.

### Dashboard Integration

When the orchestrator starts, it updates `Dashboard.md`:

```markdown
| 2026-02-16 18:25:00 | System_Status | ✓ Online | System Online: All Watchers Active |
```

When stopped:

```markdown
| 2026-02-16 19:45:00 | System_Status | ✓ Online | System Offline: Orchestrator Stopped |
```

### Health Monitoring

Every 30 seconds, the orchestrator:
- Checks if each process is still running
- Verifies process health
- Restarts failed processes
- Logs all events

### Exponential Backoff

If a process keeps failing, restart delays increase:
- 1st restart: 2 seconds
- 2nd restart: 4 seconds
- 3rd restart: 8 seconds
- 4th restart: 16 seconds
- 5th+ restart: 32 seconds (max 60 seconds)

This prevents rapid restart loops that could cause system issues.

## Logs

### System Log

All orchestrator events are logged to `Logs/system.log`:

```bash
tail -f AI_Employee_Vault/Logs/system.log
```

### Consolidated Debug Log (NEW)

**All subprocess output** (stdout and stderr) from every watcher is captured in a single consolidated log:

```bash
tail -f AI_Employee_Vault/Logs/process_debug.log
```

This log contains:
- All print statements from watchers
- Python tracebacks and error messages
- Crash details and stack traces
- Process start/stop markers with timestamps

**When to check this log:**
- When a process crashes or restarts repeatedly
- When you see `[CRASH DETECTED]` alerts
- When debugging subprocess issues
- When processes fail to start

**Example usage:**
```bash
# View last 100 lines
tail -100 AI_Employee_Vault/Logs/process_debug.log

# Follow in real-time
tail -f AI_Employee_Vault/Logs/process_debug.log

# Search for errors
grep -i "error\|traceback\|exception" AI_Employee_Vault/Logs/process_debug.log
```

### Individual Process Logs

Each watcher maintains its own log:
- `Logs/FilesystemWatcher.log`
- `Logs/GmailWatcher.log`
- `Logs/WhatsAppWatcher.log`
- `Logs/ApprovalHandler.log`

## Production Deployment

### Running as a Service (Linux)

Create `/etc/systemd/system/ai-employee.service`:

```ini
[Unit]
Description=AI Employee Master Orchestrator
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Personal-AI-Employee
ExecStart=/usr/bin/python3 /path/to/Personal-AI-Employee/orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ai-employee
sudo systemctl start ai-employee
```

Check status:

```bash
sudo systemctl status ai-employee
```

View logs:

```bash
sudo journalctl -u ai-employee -f
```

### Running as a Service (macOS)

Create `~/Library/LaunchAgents/com.aiemployee.orchestrator.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiemployee.orchestrator</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/Personal-AI-Employee/orchestrator.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/Personal-AI-Employee</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/Personal-AI-Employee/AI_Employee_Vault/Logs/orchestrator.out</string>
    <key>StandardErrorPath</key>
    <string>/path/to/Personal-AI-Employee/AI_Employee_Vault/Logs/orchestrator.err</string>
</dict>
</plist>
```

Load:

```bash
launchctl load ~/Library/LaunchAgents/com.aiemployee.orchestrator.plist
```

### Running in Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY AI_Employee_Vault/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application
COPY . .

# Run orchestrator
CMD ["python", "orchestrator.py", "/app/AI_Employee_Vault"]
```

Build and run:

```bash
docker build -t ai-employee .
docker run -d --name ai-employee \
  -v $(pwd)/AI_Employee_Vault:/app/AI_Employee_Vault \
  ai-employee
```

## Troubleshooting

### Process keeps restarting

**Step 1: Check the consolidated debug log for error details:**
```bash
tail -100 AI_Employee_Vault/Logs/process_debug.log
```

This will show you the actual Python traceback and error message.

**Step 2: Check system log for restart patterns:**
```bash
tail -f AI_Employee_Vault/Logs/system.log
```

**Common causes:**
- Missing credentials (Gmail, WhatsApp)
- Network connectivity issues
- Permission problems
- Missing dependencies
- Import errors (ModuleNotFoundError)
- Configuration issues

**Example debug log output:**
```
================================================================================
STARTING: Gmail Inbox Watcher (gmail_watcher.py)
Time: 2026-02-16 18:30:15
Command: /usr/bin/python3 /path/to/gmail_watcher.py /path/to/credentials /path/to/vault
================================================================================

Traceback (most recent call last):
  File "/path/to/gmail_watcher.py", line 10, in <module>
    from base_watcher import BaseWatcher
ModuleNotFoundError: No module named 'base_watcher'
```

This clearly shows the root cause (missing module import).

### WhatsApp QR code needed

**Solution:**
1. Stop orchestrator (Ctrl+C)
2. Run WhatsApp watcher manually without headless:
   ```bash
   python AI_Employee_Vault/whatsapp_watcher.py whatsapp_session
   ```
3. Scan QR code
4. Stop manual watcher (Ctrl+C)
5. Restart orchestrator

### Gmail token expired

**Solution:**
```bash
cd AI_Employee_Vault
python setup_gmail.py credentials
```

Then restart orchestrator.

### Process won't stop

**Force kill:**
```bash
pkill -f orchestrator.py
```

Or find and kill individual processes:
```bash
ps aux | grep watcher
kill <PID>
```

### Dashboard not updating

**Check permissions:**
```bash
ls -la AI_Employee_Vault/Dashboard.md
```

Ensure file is writable.

## Advanced Configuration

### Adjust Check Interval

Edit `orchestrator.py` line 285:

```python
check_interval = 30  # seconds
```

Change to your preferred interval.

### Disable Specific Watchers

Comment out unwanted processes in `orchestrator.py` `__init__` method:

```python
self.processes: Dict[str, ProcessConfig] = {
    "filesystem": ProcessConfig(...),
    "gmail": ProcessConfig(...),
    # "whatsapp": ProcessConfig(...),  # Disabled
    "approval": ProcessConfig(...),
}
```

### Custom Process Arguments

Modify process args in `orchestrator.py`:

```python
"gmail": ProcessConfig(
    name="gmail",
    script="gmail_watcher.py",
    args=[str(self.credentials_path), str(self.vault_path), "--custom-arg"],
    description="Gmail Inbox Watcher"
),
```

## Monitoring

### Check System Status

While orchestrator is running, check status in another terminal:

```bash
# View system log
tail -f AI_Employee_Vault/Logs/system.log

# Check Dashboard
cat AI_Employee_Vault/Dashboard.md

# View process list
ps aux | grep -E "watcher|approval_handler"
```

### Performance Metrics

Monitor resource usage:

```bash
# CPU and memory
top -p $(pgrep -f orchestrator.py)

# Detailed stats
htop -p $(pgrep -f orchestrator.py)
```

## Best Practices

### Development
- Test each watcher individually before using orchestrator
- Use orchestrator for integration testing
- Monitor logs during initial runs

### Production
- Run as a system service (systemd/launchd)
- Set up log rotation
- Monitor disk space for logs
- Configure alerts for repeated failures

### Maintenance
- Review `system.log` weekly
- Check restart counts
- Update credentials before expiry
- Test failover scenarios

## FAQ

**Q: Can I run the orchestrator in the background?**
A: Yes, use `nohup` or run as a service:
```bash
nohup python orchestrator.py > /dev/null 2>&1 &
```

**Q: How do I know if everything is working?**
A: Check Dashboard.md for "System Online" status and monitor `Logs/system.log`.

**Q: What happens if my computer restarts?**
A: Set up as a system service to auto-start on boot.

**Q: Can I run multiple orchestrators?**
A: No, only one orchestrator should manage the vault at a time.

**Q: How do I update a watcher while orchestrator is running?**
A: Stop orchestrator, update the watcher, restart orchestrator.

---

**Status:** Ready to use
**Next Step:** Test with `python orchestrator.py`
**Production:** Set up as system service for always-on operation

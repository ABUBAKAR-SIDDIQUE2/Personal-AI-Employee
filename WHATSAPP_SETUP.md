# WhatsApp Integration Setup Guide

This guide walks you through setting up WhatsApp Web monitoring for your AI Employee (Silver Tier).

## Overview

The WhatsApp watcher monitors your WhatsApp Web for **urgent messages** containing specific keywords and automatically creates action items in `/Needs_Action` for processing.

**Monitored Keywords:** urgent, invoice, payment, help, asap, emergency, critical

## Prerequisites

- Python 3.13+ installed
- Active WhatsApp account with phone
- Chrome/Chromium browser (installed automatically by Playwright)

## Step 1: Install Dependencies

```bash
cd AI_Employee_Vault
pip install -r requirements.txt
```

This installs Playwright, the browser automation library.

## Step 2: Install Browser

Playwright needs to download the Chromium browser:

```bash
playwright install chromium
```

This downloads ~300MB and only needs to be done once.

## Step 3: Create Session Directory

Create a directory to store your WhatsApp Web session:

```bash
mkdir whatsapp_session
```

Your structure should look like:

```
AI_Employee_Vault/
├── whatsapp_session/    # Browser session data (created)
├── whatsapp_watcher.py
└── ...
```

## Step 4: First Run - QR Code Authentication

Run the watcher for the first time **without headless mode** so you can scan the QR code:

```bash
python whatsapp_watcher.py whatsapp_session
```

This will:
1. Open a Chrome browser window
2. Navigate to web.whatsapp.com
3. Display a QR code

**Scan the QR code with your phone:**
1. Open WhatsApp on your phone
2. Tap Menu (⋮) or Settings
3. Tap "Linked Devices"
4. Tap "Link a Device"
5. Scan the QR code displayed in the browser

After scanning, the browser will load your chats and the watcher will start monitoring.

**Important:** Keep the terminal running for at least 30 seconds to ensure the session is saved.

## Step 5: Subsequent Runs

After the first authentication, you can run in headless mode (no visible browser):

```bash
python whatsapp_watcher.py whatsapp_session --headless
```

The watcher will:
1. Use the saved session (no QR code needed)
2. Check for unread messages every 60 seconds
3. Filter for messages containing urgent keywords
4. Create action files in `/Needs_Action`
5. Log all activity in `/Logs`

## Step 6: Process Messages with Claude Code

When urgent messages are detected, process them with your Digital FTE:

```
Act as my Digital FTE. Check /Needs_Action and process the urgent WhatsApp message.
```

## Configuration

### Adjust Check Interval

Edit `whatsapp_watcher.py` line 37:

```python
check_interval=60  # 60 seconds = 1 minute
```

Change to your preferred interval (in seconds).

### Customize Urgent Keywords

Edit the `URGENT_KEYWORDS` list in `whatsapp_watcher.py` line 30:

```python
URGENT_KEYWORDS = ['urgent', 'invoice', 'payment', 'help', 'asap', 'emergency', 'critical']
```

Add or remove keywords as needed. Keywords are case-insensitive.

### Run in Visible Mode (for debugging)

Omit the `--headless` flag to see the browser:

```bash
python whatsapp_watcher.py whatsapp_session
```

This is useful for troubleshooting or monitoring the watcher's behavior.

## Workflow Example

```
1. Urgent WhatsApp message arrives: "URGENT: Need invoice for payment"
   ↓
2. whatsapp_watcher.py detects it (within 60 seconds)
   ↓
3. Action file created: WHATSAPP_20260216_150000_Client_Name.md
   ↓
4. Metadata includes: sender, message text, keywords matched
   ↓
5. Claude Code processes the message
   ↓
6. Dashboard.md updated with "Processed urgent WhatsApp from Client Name"
   ↓
7. Files archived to /Done/
```

## Troubleshooting

### "QR code not scanned in time"

**Solution:** The watcher waits 60 seconds for QR code scan. If you need more time:
1. Stop the watcher (Ctrl+C)
2. Run again without `--headless`
3. Scan the QR code promptly

### "WhatsApp Web not loaded"

**Solution:**
- Check your internet connection
- Ensure WhatsApp Web is not blocked by firewall
- Try running without `--headless` to see what's happening

### Session expired / QR code appears again

**Solution:** WhatsApp Web sessions can expire. Simply:
1. Stop the watcher
2. Delete the session directory: `rm -rf whatsapp_session`
3. Create it again: `mkdir whatsapp_session`
4. Run the watcher and scan the QR code again

### No messages detected

**Checklist:**
- [ ] Message contains one of the urgent keywords
- [ ] Message is unread in WhatsApp Web
- [ ] Watcher is running (`python whatsapp_watcher.py whatsapp_session --headless`)
- [ ] Check interval has passed (default: 60 seconds)
- [ ] Check logs: `cat AI_Employee_Vault/Logs/WhatsAppWatcher.log`

### Browser crashes or hangs

**Solution:**
- Ensure you have enough RAM (Chrome needs ~500MB)
- Close other browser instances
- Run with `--headless` to reduce memory usage
- Restart the watcher

### "Playwright not found"

**Solution:** Install Playwright and browsers:
```bash
pip install playwright
playwright install chromium
```

## Security Notes

### What Access Does the Watcher Have?

The WhatsApp watcher:
- ✓ Reads your messages (read-only)
- ✓ Monitors unread message indicators
- ✗ Cannot send messages
- ✗ Cannot delete messages
- ✗ Cannot modify your account

### Where Is Session Data Stored?

Session data is stored locally in the `whatsapp_session/` directory. This includes:
- Browser cookies
- Local storage
- WhatsApp Web authentication tokens

**Never commit this directory to version control** - it's already in `.gitignore`.

### Unlinking the Device

To revoke access:
1. Open WhatsApp on your phone
2. Go to Settings > Linked Devices
3. Find "Chrome" or "Chromium"
4. Tap and select "Log Out"
5. Delete the session directory: `rm -rf whatsapp_session`

## Advanced Usage

### Running as a Background Service

#### Linux (systemd)

Create `/etc/systemd/system/whatsapp-watcher.service`:

```ini
[Unit]
Description=AI Employee WhatsApp Watcher
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/AI_Employee_Vault
ExecStart=/path/to/venv/bin/python whatsapp_watcher.py whatsapp_session --headless
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable whatsapp-watcher
sudo systemctl start whatsapp-watcher
```

#### macOS (launchd)

Create `~/Library/LaunchAgents/com.aiemployee.whatsapp.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiemployee.whatsapp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/AI_Employee_Vault/whatsapp_watcher.py</string>
        <string>whatsapp_session</string>
        <string>--headless</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load:

```bash
launchctl load ~/Library/LaunchAgents/com.aiemployee.whatsapp.plist
```

### Multiple WhatsApp Accounts

To monitor multiple WhatsApp accounts, create separate session directories:

```bash
mkdir whatsapp_session_personal
mkdir whatsapp_session_work

# Run separate watchers
python whatsapp_watcher.py whatsapp_session_personal --headless &
python whatsapp_watcher.py whatsapp_session_work --headless &
```

Each will maintain its own authentication and track messages independently.

### Custom Message Filtering

For more advanced filtering, edit the `check_for_updates()` method in `whatsapp_watcher.py`. You can add logic to:
- Filter by specific sender names
- Match regex patterns
- Check message timestamps
- Prioritize certain contacts

## Performance Considerations

### Resource Usage

- **Memory:** ~500MB per watcher instance (Chromium browser)
- **CPU:** Low (~1-2% when idle, ~10% during checks)
- **Network:** Minimal (only loads WhatsApp Web once)

### Optimization Tips

1. **Increase check interval** for less frequent monitoring (reduces CPU usage)
2. **Use headless mode** to reduce memory usage
3. **Limit processed chats** by adjusting the slice in line 172: `[:10]`

## Limitations

1. **WhatsApp Web must be active** - If WhatsApp Web is logged out on your phone, the watcher won't work
2. **Internet required** - Both your computer and phone need internet
3. **Phone must be on** - WhatsApp Web requires your phone to be connected
4. **Rate limiting** - WhatsApp may rate-limit if you check too frequently (keep interval ≥30 seconds)

## FAQ

**Q: Can I run this on a server without a display?**
A: Yes, use `--headless` mode. Playwright works on headless servers.

**Q: Will this drain my phone battery?**
A: No more than normal WhatsApp Web usage. The phone acts as a relay.

**Q: Can I use this with WhatsApp Business?**
A: Yes, it works with both regular WhatsApp and WhatsApp Business.

**Q: What happens if my phone dies?**
A: The watcher will fail to load messages. Restart it once your phone is back online.

**Q: Is this against WhatsApp's terms of service?**
A: This uses the official WhatsApp Web interface, same as using it in a browser manually. However, use responsibly and don't spam or automate sending messages.

## Next Steps

With WhatsApp monitoring active, consider:

1. **Combine with Gmail watcher** - Monitor both email and WhatsApp simultaneously
2. **Add more keywords** - Customize for your specific use case
3. **Build automated responses** - Create templates for common urgent requests
4. **Integrate with task management** - Auto-create tasks from urgent messages

---

**Need Help?** Check the main README.md or open an issue on GitHub.

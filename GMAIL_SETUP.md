# Gmail Integration Setup Guide

This guide walks you through setting up Gmail monitoring for your AI Employee (Silver Tier).

## Overview

The Gmail watcher monitors your inbox for **important unread emails** and automatically creates action items in `/Needs_Action` for processing.

## Prerequisites

- Python 3.13+ installed
- Active Gmail account
- Google Cloud Platform account (free tier is sufficient)

## Step 1: Install Dependencies

```bash
cd AI_Employee_Vault
pip install -r requirements.txt
```

This installs:
- `google-auth-oauthlib` - OAuth2 authentication
- `google-auth-httplib2` - HTTP library for Google APIs
- `google-api-python-client` - Gmail API client

## Step 2: Create Google Cloud Project

### 2.1 Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 2.2 Create a New Project

1. Click the project dropdown at the top
2. Click "New Project"
3. Name it: `AI-Employee-Gmail`
4. Click "Create"

### 2.3 Enable Gmail API

1. In the search bar, type "Gmail API"
2. Click on "Gmail API"
3. Click "Enable"

## Step 3: Create OAuth Credentials

### 3.1 Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" (unless you have a Google Workspace)
3. Click "Create"
4. Fill in required fields:
   - **App name:** AI Employee Gmail Watcher
   - **User support email:** Your email
   - **Developer contact:** Your email
5. Click "Save and Continue"
6. Skip "Scopes" (click "Save and Continue")
7. Add your email as a test user
8. Click "Save and Continue"

### 3.2 Create OAuth Client ID

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop app" as application type
4. Name it: `AI Employee Desktop Client`
5. Click "Create"
6. Click "Download JSON" on the popup
7. Save the file as `credentials.json`

## Step 4: Set Up Credentials Directory

Create a credentials folder in your vault:

```bash
cd AI_Employee_Vault
mkdir credentials
mv ~/Downloads/credentials.json credentials/
```

Your structure should look like:

```
AI_Employee_Vault/
├── credentials/
│   └── credentials.json
├── gmail_watcher.py
├── setup_gmail.py
└── ...
```

## Step 5: Run OAuth Authentication

Run the setup script to authenticate:

```bash
python setup_gmail.py credentials
```

This will:
1. Open your browser
2. Ask you to sign in to Google
3. Request permission to read your Gmail (read-only access)
4. Generate `token.json` in the credentials folder

**Important:** The app will show a warning that it's not verified. This is normal for personal projects. Click "Advanced" > "Go to AI Employee Gmail Watcher (unsafe)" to proceed.

After successful authentication, you'll see:

```
✓ Successfully connected to Gmail!
✓ Authenticated as: your.email@gmail.com
✓ Total messages: 1234
```

## Step 6: Start the Gmail Watcher

Run the watcher to begin monitoring:

```bash
python gmail_watcher.py credentials
```

You should see:

```
Starting Gmail watcher...
Monitoring: Important unread emails
Check interval: 5 minutes
Press Ctrl+C to stop
```

## Step 7: Test the Integration

### 7.1 Send a Test Email

1. From another account, send yourself an email
2. Mark it as "Important" (star icon in Gmail)
3. Keep it unread

### 7.2 Wait for Detection

Within 5 minutes, the watcher will:
1. Detect the important unread email
2. Create a file in `/Needs_Action` like: `EMAIL_20260216_143000_Test_Subject.md`
3. Log the action in `/Logs`

### 7.3 Process with AI

Open Claude Code and instruct:

```
Act as my Digital FTE. Check /Needs_Action and process the new email.
```

## Configuration

### Adjust Check Interval

Edit `gmail_watcher.py` line 27:

```python
check_interval=300  # 300 seconds = 5 minutes
```

Change to your preferred interval (in seconds).

### Modify Email Query

Edit the query in `check_for_updates()` method:

```python
# Current: Important unread emails
query = "is:unread is:important"

# Examples:
query = "is:unread label:urgent"  # Unread emails with "urgent" label
query = "is:unread from:boss@company.com"  # Unread from specific sender
query = "is:unread subject:invoice"  # Unread with "invoice" in subject
```

See [Gmail search operators](https://support.google.com/mail/answer/7190) for more options.

## Troubleshooting

### "No valid credentials available"

**Solution:** Run `python setup_gmail.py credentials` to authenticate.

### "Token has been expired or revoked"

**Solution:** Delete `credentials/token.json` and re-run setup:

```bash
rm credentials/token.json
python setup_gmail.py credentials
```

### "Access blocked: This app's request is invalid"

**Solution:** Ensure you've enabled Gmail API in Google Cloud Console.

### "The app is not verified"

**Solution:** This is expected for personal projects. Click "Advanced" > "Go to [app name] (unsafe)" to proceed. Your credentials are only stored locally.

### No emails detected

**Checklist:**
- [ ] Email is marked as "Important" (star in Gmail)
- [ ] Email is unread
- [ ] Watcher is running (`python gmail_watcher.py credentials`)
- [ ] Check interval has passed (default: 5 minutes)
- [ ] Check logs: `cat AI_Employee_Vault/Logs/GmailWatcher.log`

## Security Notes

### What Access Does the App Have?

The Gmail watcher uses **read-only** access (`gmail.readonly` scope). It can:
- ✓ Read your emails
- ✓ Search your inbox
- ✗ Send emails
- ✗ Delete emails
- ✗ Modify emails

### Where Are Credentials Stored?

- `credentials.json` - OAuth client configuration (not sensitive)
- `token.json` - Your access token (sensitive - keep private)

Both files are stored locally in the `credentials/` folder. Never commit these to version control.

### Revoking Access

To revoke access:
1. Go to https://myaccount.google.com/permissions
2. Find "AI Employee Gmail Watcher"
3. Click "Remove Access"
4. Delete `credentials/token.json`

## Advanced Usage

### Running as a Background Service

#### Linux (systemd)

Create `/etc/systemd/system/gmail-watcher.service`:

```ini
[Unit]
Description=AI Employee Gmail Watcher
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/AI_Employee_Vault
ExecStart=/path/to/venv/bin/python gmail_watcher.py credentials
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable gmail-watcher
sudo systemctl start gmail-watcher
```

#### macOS (launchd)

Create `~/Library/LaunchAgents/com.aiemployee.gmail.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiemployee.gmail</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/AI_Employee_Vault/gmail_watcher.py</string>
        <string>credentials</string>
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
launchctl load ~/Library/LaunchAgents/com.aiemployee.gmail.plist
```

## Next Steps

With Gmail monitoring active, consider:

1. **Create more watchers** - Slack, calendar, RSS feeds
2. **Build automated processor** - Auto-respond to certain email types
3. **Add prioritization** - Route urgent emails differently
4. **Integrate with task management** - Create tasks from emails automatically

---

**Need Help?** Check the main README.md or open an issue on GitHub.

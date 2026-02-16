# Personal AI Employee (Silver Tier)

A local-first autonomous agent system that uses Obsidian as a visual dashboard and Python watchers to monitor, process, and archive tasks automatically.

## Project Overview

The Personal AI Employee is a modular system designed to act as a digital full-time employee (FTE) that:

- **Monitors** various sources (file system, Gmail, APIs) for new tasks
- **Processes** incoming items using AI-powered decision making
- **Archives** completed work with full audit trails
- **Reports** activity through an Obsidian-based dashboard

**Current Implementation (Silver Tier):**
- ✅ Local file system monitoring
- ✅ Gmail inbox monitoring (important unread emails)
- ✅ Manual AI processing via Claude Code
- ✅ Structured workflow management
- ✅ Complete transparency and auditability

## Prerequisites

Before setting up the Personal AI Employee, ensure you have:

- **Python 3.13+** - [Download here](https://www.python.org/downloads/)
- **Obsidian v1.10.6+** - [Download here](https://obsidian.md/)
- **Claude Code** - [Installation guide](https://github.com/anthropics/claude-code)

## Installation

### 1. Clone or Navigate to the Project

```bash
cd /path/to/Personal-AI-Employee/AI_Employee_Vault
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**On Linux/Mac:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** Silver Tier requires Google API libraries for Gmail integration. All dependencies will be installed from requirements.txt.

### 5. Open Vault in Obsidian

1. Launch Obsidian
2. Click "Open folder as vault"
3. Select the `AI_Employee_Vault` directory
4. Open `Dashboard.md` to view system status

## Folder Structure

```
AI_Employee_Vault/
├── Inbox/              # Drop zone for raw files awaiting processing
├── Needs_Action/       # Tasks ready for AI agent to process
├── Done/               # Archived completed tasks
├── Logs/               # System logs and audit trails
├── Plans/              # Agent reasoning and decision documentation
├── credentials/        # Gmail OAuth credentials (create during setup)
├── Dashboard.md        # Real-time system status and activity log
├── Company_Handbook.md # Rules of engagement and operational guidelines
├── base_watcher.py     # Abstract base class for all watchers
├── filesystem_watcher.py # File system monitoring implementation
├── gmail_watcher.py    # Gmail inbox monitoring implementation
├── setup_gmail.py      # Gmail OAuth setup helper
└── requirements.txt    # Python dependencies
```

### Folder Purposes

- **`/Inbox`**: Drop files here for automatic detection and processing
- **`/Needs_Action`**: Watchers place detected items here with metadata
- **`/Done`**: Completed tasks are archived here for audit purposes
- **`/Logs`**: System logs, watcher activity, and audit trails
- **`/Plans`**: AI reasoning, decision-making documentation, and execution plans
- **`Dashboard.md`**: Central hub showing recent activity, pending tasks, and system health
- **`Company_Handbook.md`**: Operational rules and guidelines for the AI agent

## Usage Guide

### Step 1: Start the Filesystem Watcher

The watcher monitors the `/Inbox` folder and automatically processes new files.

```bash
python filesystem_watcher.py
```

You should see output like:
```
Starting filesystem watcher...
Monitoring: /path/to/AI_Employee_Vault/Inbox
Press Ctrl+C to stop
```

Leave this running in a terminal window.

### Step 2: Test File Detection

Open a new terminal and drop a test file into the Inbox:

```bash
echo "Test task for AI Employee" > AI_Employee_Vault/Inbox/test_task.txt
```

The watcher will:
1. Detect the new file within 10 seconds
2. Copy it to `/Needs_Action` with a `FILE_` prefix and timestamp
3. Create a metadata `.md` file with file details
4. Log the action in `/Logs`

### Step 3: Process Tasks with Claude Code

Launch Claude Code in the vault directory:

```bash
cd AI_Employee_Vault
claude
```

Then instruct the AI agent to work:

```
I want you to act as my Digital FTE. Please check the /Needs_Action folder and process any pending tasks.
```

The AI will:
1. Audit `/Needs_Action` for pending tasks
2. Read and analyze each task
3. Execute appropriate actions
4. Update `Dashboard.md` with activity logs
5. Archive completed tasks to `/Done`

### Step 4: Monitor Progress in Obsidian

Open `Dashboard.md` in Obsidian to see:
- Recent activity with timestamps
- Pending tasks count
- System health metrics
- Completion statistics

## Gmail Integration (Silver Tier)

### Setup Gmail Monitoring

The Gmail watcher monitors your inbox for important unread emails and creates action items automatically.

**Step 1: Install Gmail Dependencies**

```bash
pip install -r requirements.txt
```

**Step 2: Set Up Gmail OAuth**

Follow the detailed guide in [GMAIL_SETUP.md](GMAIL_SETUP.md) to:
1. Create a Google Cloud project
2. Enable Gmail API
3. Download OAuth credentials
4. Authenticate with your Gmail account

Quick setup:

```bash
# Create credentials directory
mkdir AI_Employee_Vault/credentials

# Place your credentials.json in the credentials folder
# Then run the setup script
python setup_gmail.py credentials
```

**Step 3: Start Gmail Watcher**

```bash
python gmail_watcher.py credentials
```

The watcher will:
1. Check for important unread emails every 5 minutes
2. Create action files in `/Needs_Action` with email metadata
3. Log all activity in `/Logs`

**Step 4: Process Emails with Claude Code**

When new emails are detected, process them with your Digital FTE:

```
Act as my Digital FTE. Check /Needs_Action and process the new email.
```

### Step 5: Monitor Progress in Obsidian

## Agent Skills

The Digital FTE has three core skills:

1. **Audit_Needs_Action**: Lists all files in `/Needs_Action` to identify pending work
2. **Update_Dashboard**: Appends timestamped activity logs to `Dashboard.md`
3. **Archive_Task**: Moves completed files from `/Needs_Action` to `/Done`

## Workflow Examples

### File System Workflow

```
1. User drops invoice.pdf into /Inbox
   ↓
2. filesystem_watcher.py detects it
   ↓
3. File copied to /Needs_Action/FILE_20260216_120530_invoice.pdf
   ↓
4. Metadata file created: FILE_20260216_120530_invoice.pdf.md
   ↓
5. Claude Code processes the invoice
   ↓
6. Dashboard.md updated with "Processed invoice"
   ↓
7. Files archived to /Done/
```

### Gmail Workflow

```
1. Important email arrives in Gmail inbox
   ↓
2. gmail_watcher.py detects it (within 5 minutes)
   ↓
3. Email action file created: EMAIL_20260216_143000_Meeting_Request.md
   ↓
4. Metadata includes: sender, subject, body, suggested actions
   ↓
5. Claude Code reads and processes the email
   ↓
6. Dashboard.md updated with "Processed email from sender@example.com"
   ↓
7. Files archived to /Done/
```

## Customization

### Adjust Watcher Check Interval

Edit `filesystem_watcher.py` line 26:

```python
def __init__(self, vault_path: str, check_interval: int = 10):
```

Change `check_interval` to your preferred seconds between checks.

### Create Custom Watchers

Extend `BaseWatcher` to monitor other sources:

```python
from base_watcher import BaseWatcher

class SlackWatcher(BaseWatcher):
    def check_for_updates(self):
        # Check Slack for mentions
        pass

    def create_action_file(self, item):
        # Create task from Slack message
        pass
```

See `gmail_watcher.py` for a complete implementation example.

## Troubleshooting

**Watcher not detecting files:**
- Ensure the watcher is running (`python filesystem_watcher.py`)
- Check that files are placed in `/Inbox`, not subdirectories
- Verify folder permissions

**Claude Code not processing tasks:**
- Ensure you're in the vault directory when launching Claude
- Explicitly instruct Claude to "act as Digital FTE" and "check /Needs_Action"
- Verify files exist in `/Needs_Action`

**Dashboard not updating:**
- Check that `Dashboard.md` exists and is not read-only
- Verify Claude has write permissions to the vault

**Gmail watcher issues:**
- See detailed troubleshooting in [GMAIL_SETUP.md](GMAIL_SETUP.md)
- Ensure credentials are properly configured
- Check that token.json is valid and not expired
- Verify Gmail API is enabled in Google Cloud Console

## Roadmap

**Bronze Tier (Complete):**
- ✅ File system monitoring
- ✅ Manual AI processing
- ✅ Basic workflow management
- ✅ Structured vault architecture

**Silver Tier (Complete):**
- ✅ Gmail inbox monitoring
- ✅ OAuth2 authentication
- ✅ Email action file generation
- ✅ Multi-source monitoring

**Gold Tier (Planned):**
- Automated action processor (removes manual intervention)
- Slack/Teams integration
- Calendar monitoring
- Natural language task creation
- Proactive task suggestions
- Advanced reasoning and planning
- Integration with external tools (Jira, Notion, etc.)

## License

This project is for personal use and educational purposes.

## Contributing

This is a personal project, but suggestions and improvements are welcome via issues or pull requests.

---

**Built with Claude Code** | Version 2.0 - Silver Tier

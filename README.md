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
- ✅ WhatsApp Web monitoring (urgent messages)
- ✅ Email sending via MCP server
- ✅ LinkedIn posting (Mock Mode with approval)
- ✅ Human-in-the-Loop approval workflow
- ✅ Planning skill (ReAct reasoning pattern)
- ✅ Master orchestrator (single command to run everything)
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

**Note:** Silver Tier requires Google API libraries for Gmail integration and Playwright for WhatsApp monitoring. All dependencies will be installed from requirements.txt.

After installing dependencies, run:
```bash
playwright install chromium
```

### 5. Open Vault in Obsidian

1. Launch Obsidian
2. Click "Open folder as vault"
3. Select the `AI_Employee_Vault` directory
4. Open `Dashboard.md` to view system status

## Folder Structure

```
AI_Employee_Vault/
├── Agent_Skills/        # AI agent skill definitions
│   ├── planning_skill.md    # ReAct reasoning methodology
│   └── social_media.md      # LinkedIn content strategy
├── Inbox/              # Drop zone for raw files awaiting processing
├── Needs_Action/       # Tasks ready for AI agent to process
├── Pending_Approval/   # Actions awaiting human approval
├── Approved/           # Approved actions (watched by approval_handler)
├── Rejected/           # Rejected actions with feedback
├── Done/               # Archived completed tasks
├── Logs/               # System logs and audit trails
├── Plans/              # Agent reasoning and decision documentation
├── credentials/        # Gmail OAuth credentials (create during setup)
├── whatsapp_session/   # WhatsApp Web session data (create during setup)
├── Dashboard.md        # Real-time system status and activity log
├── Company_Handbook.md # Rules of engagement and operational guidelines
├── base_watcher.py     # Abstract base class for all watchers
├── filesystem_watcher.py # File system monitoring implementation
├── gmail_watcher.py    # Gmail inbox monitoring implementation
├── whatsapp_watcher.py # WhatsApp Web monitoring implementation
├── email_server.py     # Email MCP server for sending emails
├── linkedin_manager.py # LinkedIn posting manager (Mock Mode)
├── approval_handler.py # Approval workflow executor (Safety Valve)
├── setup_gmail.py      # Gmail OAuth setup helper
└── requirements.txt    # Python dependencies
```

### Folder Purposes

- **`/Inbox`**: Drop files here for automatic detection and processing
- **`/Needs_Action`**: Watchers place detected items here with metadata
- **`/Pending_Approval`**: Actions awaiting human approval (emails, LinkedIn posts)
- **`/Approved`**: Approved actions being executed by approval_handler
- **`/Rejected`**: Rejected actions with feedback for improvement
- **`/Done`**: Completed tasks are archived here for audit purposes
- **`/Logs`**: System logs, watcher activity, and audit trails
- **`/Plans`**: AI reasoning, decision-making documentation, and execution plans
- **`/Agent_Skills`**: Skill definitions for the AI agent (planning, social media)
- **`Dashboard.md`**: Central hub showing recent activity, pending tasks, and system health
- **`Company_Handbook.md`**: Operational rules and guidelines for the AI agent
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

## WhatsApp Integration (Silver Tier)

### Setup WhatsApp Monitoring

The WhatsApp watcher monitors WhatsApp Web for urgent messages containing specific keywords and creates action items automatically.

**Monitored Keywords:** urgent, invoice, payment, help, asap, emergency, critical

**Step 1: Install Dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

**Step 2: Create Session Directory**

```bash
mkdir AI_Employee_Vault/whatsapp_session
```

**Step 3: First Run - Scan QR Code**

Run without headless mode to scan the QR code:

```bash
python whatsapp_watcher.py whatsapp_session
```

A browser window will open with WhatsApp Web. Scan the QR code with your phone:
1. Open WhatsApp on your phone
2. Go to Settings > Linked Devices
3. Tap "Link a Device"
4. Scan the QR code

**Step 4: Subsequent Runs**

After authentication, run in headless mode:

```bash
python whatsapp_watcher.py whatsapp_session --headless
```

The watcher will:
1. Check for unread messages every 60 seconds
2. Filter for messages with urgent keywords
3. Create action files in `/Needs_Action`
4. Log all activity in `/Logs`

For detailed setup instructions, see [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md).

**Step 5: Process Messages with Claude Code**

When urgent messages are detected, process them with your Digital FTE:

```
Act as my Digital FTE. Check /Needs_Action and process the urgent WhatsApp message.
```

## Silver Tier Features

The Silver Tier adds advanced capabilities including email sending, LinkedIn posting, approval workflows, and unified orchestration.

### 1. Email Sending (MCP Server)

**Setup:**

1. **Configure Email MCP Server:**
   ```bash
   pip install mcp
   ```

2. **Create MCP configuration:**
   ```bash
   mkdir -p ~/.config/claude-code
   ```

3. **Add to `~/.config/claude-code/mcp.json`:**
   ```json
   {
     "mcpServers": {
       "email": {
         "command": "python3",
         "args": ["/absolute/path/to/AI_Employee_Vault/email_server.py"],
         "env": {}
       }
     }
   }
   ```

4. **Restart Claude Code** to load the email server

See [EMAIL_MCP_SETUP.md](EMAIL_MCP_SETUP.md) for detailed instructions.

### 2. LinkedIn Posting

**Setup:**

LinkedIn posting uses Mock Mode (queue to file) for manual posting:

1. Posts are drafted by the AI
2. Saved to `/Pending_Approval` for review
3. Approved posts move to `/Approved`
4. Queued to `LINKEDIN_QUEUE.md` for manual posting

See [LINKEDIN_SETUP.md](LINKEDIN_SETUP.md) for detailed instructions.

### 3. Human-in-the-Loop Approval Workflow

**How It Works:**

The approval workflow ensures human oversight for sensitive actions like sending emails or posting to LinkedIn.

**Workflow:**
```
1. AI creates action file in /Pending_Approval
   ↓
2. Human reviews and approves (moves to /Approved)
   ↓
3. approval_handler.py detects file in /Approved
   ↓
4. Action executed automatically
   ↓
5. File moved to /Done, action logged
```

**Start the Approval Handler:**
```bash
cd AI_Employee_Vault
python approval_handler.py
```

**Approve an Action:**
```bash
# Review the file first
cat Pending_Approval/APPROVAL_Email_Client_20260216.md

# If approved, move to Approved folder
mv Pending_Approval/APPROVAL_Email_Client_20260216.md Approved/
```

The approval handler will automatically execute the action and log it.

### 4. Master Orchestrator (Unified System)

**Run Everything with One Command:**

Instead of running multiple terminal windows, use the orchestrator:

```bash
cd /path/to/Personal-AI-Employee
python orchestrator.py
```

This starts:
- File system watcher
- Gmail watcher
- WhatsApp watcher
- Approval handler

**Features:**
- Automatic restart if a process crashes
- Health monitoring every 30 seconds
- Graceful shutdown with Ctrl+C
- Dashboard integration
- Comprehensive logging to `Logs/system.log`

See [ORCHESTRATOR_SETUP.md](ORCHESTRATOR_SETUP.md) for detailed instructions.

### 5. Planning Skill (Brain)

The AI uses ReAct (Reasoning + Acting) pattern for complex tasks:

1. Analyzes task in `/Needs_Action`
2. Creates plan in `/Plans` with reasoning
3. Executes according to plan
4. Logs all decisions

See `/Agent_Skills/planning_skill.md` for methodology.

### 6. Social Media Skill

The AI can draft professional LinkedIn posts following best practices:

- Achievement posts with metrics
- Insight posts with lessons learned
- Value posts with actionable tips
- Proper formatting and hashtags

See `/Agent_Skills/social_media.md` for guidelines.

## Complete Setup Guide (Silver Tier)

### Step 1: Install All Dependencies

```bash
cd AI_Employee_Vault
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Set Up Gmail

**Create Google Cloud Project:**

1. Go to https://console.cloud.google.com/
2. Create new project: "AI-Employee-Gmail"
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as `credentials.json`

**Authenticate:**

```bash
mkdir credentials
mv ~/Downloads/credentials.json credentials/
python setup_gmail.py credentials
```

Follow the OAuth flow in your browser. This creates `credentials/token.json`.

See [GMAIL_SETUP.md](GMAIL_SETUP.md) for detailed instructions.

### Step 3: Set Up WhatsApp

**First-time authentication:**

```bash
mkdir whatsapp_session
python whatsapp_watcher.py whatsapp_session
```

Scan the QR code with your phone. Session is saved for future use.

See [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md) for detailed instructions.

### Step 4: Configure Email MCP (Optional)

If you want to send emails from Claude Code:

```bash
mkdir -p ~/.config/claude-code
```

Create `~/.config/claude-code/mcp.json` with email server configuration (see Email Sending section above).

### Step 5: Start the System

**Option A: Use Orchestrator (Recommended)**

```bash
python orchestrator.py
```

This starts all watchers and the approval handler in one command.

**Option B: Run Components Individually**

```bash
# Terminal 1: File system watcher
python AI_Employee_Vault/filesystem_watcher.py AI_Employee_Vault

# Terminal 2: Gmail watcher
python AI_Employee_Vault/gmail_watcher.py credentials AI_Employee_Vault

# Terminal 3: WhatsApp watcher
python AI_Employee_Vault/whatsapp_watcher.py whatsapp_session AI_Employee_Vault --headless

# Terminal 4: Approval handler
python AI_Employee_Vault/approval_handler.py AI_Employee_Vault
```

### Step 6: Monitor in Obsidian

Open `AI_Employee_Vault` in Obsidian and view `Dashboard.md` for real-time status.

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

### WhatsApp Workflow

```
1. Urgent WhatsApp message arrives: "URGENT: Need invoice for payment"
   ↓
2. whatsapp_watcher.py detects it (within 60 seconds)
   ↓
3. Action file created: WHATSAPP_20260216_150000_Client_Name.md
   ↓
4. Metadata includes: sender, message text, keywords matched
   ↓
5. Claude Code reads and processes the message
   ↓
6. Dashboard.md updated with "Processed urgent WhatsApp from Client Name"
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

**WhatsApp watcher issues:**
- See detailed troubleshooting in [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md)
- Ensure Playwright and Chromium are installed: `playwright install chromium`
- If QR code appears again, session may have expired - rescan to authenticate
- Check that WhatsApp Web is not logged out on your phone
- Verify browser has enough memory (~500MB required)

## Roadmap

**Bronze Tier (Complete):**
- ✅ File system monitoring
- ✅ Manual AI processing
- ✅ Basic workflow management
- ✅ Structured vault architecture

**Silver Tier (Complete):**
- ✅ Gmail inbox monitoring
- ✅ WhatsApp Web monitoring
- ✅ OAuth2 authentication
- ✅ Email action file generation
- ✅ Multi-source monitoring
- ✅ Persistent browser sessions

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

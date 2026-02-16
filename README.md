# Personal AI Employee (Bronze Tier)

A local-first autonomous agent system that uses Obsidian as a visual dashboard and Python watchers to monitor, process, and archive tasks automatically.

## Project Overview

The Personal AI Employee is a modular system designed to act as a digital full-time employee (FTE) that:

- **Monitors** various sources (file system, APIs, emails) for new tasks
- **Processes** incoming items using AI-powered decision making
- **Archives** completed work with full audit trails
- **Reports** activity through an Obsidian-based dashboard

This Bronze Tier implementation focuses on:
- Local file system monitoring
- Manual AI processing via Claude Code
- Structured workflow management
- Complete transparency and auditability

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

Note: The Bronze Tier uses only Python standard library, so no external packages are strictly required. The requirements.txt file includes optional dependencies for future enhancements.

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
├── Dashboard.md        # Real-time system status and activity log
├── Company_Handbook.md # Rules of engagement and operational guidelines
├── base_watcher.py     # Abstract base class for all watchers
├── filesystem_watcher.py # File system monitoring implementation
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

## Agent Skills

The Digital FTE has three core skills:

1. **Audit_Needs_Action**: Lists all files in `/Needs_Action` to identify pending work
2. **Update_Dashboard**: Appends timestamped activity logs to `Dashboard.md`
3. **Archive_Task**: Moves completed files from `/Needs_Action` to `/Done`

## Workflow Example

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

class EmailWatcher(BaseWatcher):
    def check_for_updates(self):
        # Check email inbox
        pass

    def create_action_file(self, item):
        # Create task from email
        pass
```

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

## Roadmap

**Bronze Tier (Current):**
- ✅ File system monitoring
- ✅ Manual AI processing
- ✅ Basic workflow management

**Silver Tier (Planned):**
- Email monitoring
- API endpoint watchers
- Automated task routing
- Multi-agent coordination

**Gold Tier (Future):**
- Natural language task creation
- Proactive task suggestions
- Integration with external tools
- Advanced reasoning and planning

## License

This project is for personal use and educational purposes.

## Contributing

This is a personal project, but suggestions and improvements are welcome via issues or pull requests.

---

**Built with Claude Code** | Version 1.0 - Bronze Tier

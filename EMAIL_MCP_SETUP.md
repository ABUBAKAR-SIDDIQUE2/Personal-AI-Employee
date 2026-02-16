# Email MCP Server Configuration

## Installation

First, install the MCP library:

```bash
cd AI_Employee_Vault
pip install mcp
```

## Configuration

Add the following to your Claude Code MCP configuration file.

### Configuration File Location

Create or edit: `~/.config/claude-code/mcp.json`

If the directory doesn't exist, create it:
```bash
mkdir -p ~/.config/claude-code
```

### Configuration JSON

Add this server configuration to your `mcp.json`:

```json
{
  "mcpServers": {
    "email": {
      "command": "python3",
      "args": [
        "/home/abubakar/Coding/hackathon-q4/Personal-AI-Employee/AI_Employee_Vault/email_server.py"
      ],
      "env": {}
    }
  }
}
```

**Important:** Replace the path with the absolute path to your `email_server.py` file.

To get the absolute path, run:
```bash
cd AI_Employee_Vault
realpath email_server.py
```

### If You Have Multiple MCP Servers

If you already have other MCP servers configured, add the email server to the existing configuration:

```json
{
  "mcpServers": {
    "github": {
      "command": "...",
      "args": ["..."]
    },
    "email": {
      "command": "python3",
      "args": [
        "/home/abubakar/Coding/hackathon-q4/Personal-AI-Employee/AI_Employee_Vault/email_server.py"
      ],
      "env": {}
    }
  }
}
```

## Testing the Server

After adding the configuration:

1. **Restart Claude Code** (exit and relaunch)

2. **Verify the server is loaded:**
   - The email MCP server should appear in your available tools
   - You should see: `send_email`, `draft_email`, `get_email_address`

3. **Test the connection:**
   ```
   Use the get_email_address tool to verify authentication
   ```

4. **Send a test email:**
   ```
   Use send_email to send a test message to yourself
   ```

## Available Tools

Once configured, you'll have access to:

### 1. send_email
```python
send_email(
    to_email="recipient@example.com",
    subject="Email subject",
    body="Email body content"
)
```

### 2. draft_email
```python
draft_email(
    to_email="recipient@example.com",
    subject="Email subject",
    body="Email body content"
)
```

### 3. get_email_address
```python
get_email_address()
```

## Troubleshooting

### "Gmail token not found"
- Ensure you've run `setup_gmail.py` or `gmail_watcher.py` first
- Check that `credentials/token.json` exists

### "Permission denied"
- Make sure `email_server.py` is executable:
  ```bash
  chmod +x email_server.py
  ```

### "Module 'mcp' not found"
- Install the MCP library:
  ```bash
  pip install mcp
  ```

### Server not appearing in Claude Code
- Verify the path in `mcp.json` is absolute and correct
- Restart Claude Code completely
- Check Claude Code logs for errors

## Security Notes

- The email server reuses your existing Gmail OAuth token
- No new authentication required
- Credentials are stored locally in `credentials/token.json`
- Never commit `mcp.json` with absolute paths to version control

---

**Status:** Ready to configure
**Next Step:** Add configuration to `~/.config/claude-code/mcp.json` and restart Claude Code

#!/usr/bin/env python3
"""
Email MCP Server for AI Employee

A custom Model Context Protocol server that provides email sending capabilities
using the Gmail API. Reuses existing credentials from gmail_watcher setup.
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: fastmcp not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import base64
    from email.mime.text import MIMEText
except ImportError:
    print("Error: Google API libraries not installed.", file=sys.stderr)
    print("Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client", file=sys.stderr)
    sys.exit(1)


# Initialize FastMCP server
mcp = FastMCP("email-server")

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Global Gmail service (initialized on first use)
_gmail_service = None


def get_gmail_service():
    """
    Get or create Gmail API service instance using existing credentials.

    Returns:
        Gmail API service object
    """
    global _gmail_service

    if _gmail_service is not None:
        return _gmail_service

    # Find credentials in the vault
    vault_path = Path(__file__).parent
    credentials_dir = vault_path / "credentials"
    token_file = credentials_dir / "token.json"
    credentials_file = credentials_dir / "credentials.json"

    if not token_file.exists():
        raise FileNotFoundError(
            f"Gmail token not found at {token_file}. "
            "Please run gmail_watcher.py or setup_gmail.py first to authenticate."
        )

    # Load credentials
    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save refreshed credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    # Build service
    _gmail_service = build('gmail', 'v1', credentials=creds)
    return _gmail_service


def create_message(to: str, subject: str, body: str) -> dict:
    """
    Create a MIME message for Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text)

    Returns:
        Dictionary with base64 encoded message
    """
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject

    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}


@mcp.tool()
def send_email(to_email: str, subject: str, body: str) -> str:
    """
    Send an email using Gmail API.

    Args:
        to_email: Recipient email address (e.g., "user@example.com")
        subject: Email subject line
        body: Email body content (plain text)

    Returns:
        Success message with email ID or error message
    """
    try:
        # Get Gmail service
        service = get_gmail_service()

        # Create message
        message = create_message(to_email, subject, body)

        # Send message
        result = service.users().messages().send(
            userId='me',
            body=message
        ).execute()

        message_id = result.get('id', 'unknown')
        return f"✓ Email sent successfully to {to_email} (Message ID: {message_id})"

    except FileNotFoundError as e:
        return f"✗ Error: {str(e)}"
    except HttpError as e:
        return f"✗ Gmail API error: {e.reason}"
    except Exception as e:
        return f"✗ Unexpected error: {str(e)}"


@mcp.tool()
def draft_email(to_email: str, subject: str, body: str) -> str:
    """
    Create a draft email in Gmail (does not send).

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body content (plain text)

    Returns:
        Success message with draft ID or error message
    """
    try:
        # Get Gmail service
        service = get_gmail_service()

        # Create message
        message = create_message(to_email, subject, body)

        # Create draft
        draft = {'message': message}
        result = service.users().drafts().create(
            userId='me',
            body=draft
        ).execute()

        draft_id = result.get('id', 'unknown')
        return f"✓ Draft created successfully for {to_email} (Draft ID: {draft_id})"

    except FileNotFoundError as e:
        return f"✗ Error: {str(e)}"
    except HttpError as e:
        return f"✗ Gmail API error: {e.reason}"
    except Exception as e:
        return f"✗ Unexpected error: {str(e)}"


@mcp.tool()
def get_email_address() -> str:
    """
    Get the authenticated user's email address.

    Returns:
        Email address or error message
    """
    try:
        service = get_gmail_service()
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress', 'Unknown')
        return f"Authenticated as: {email}"
    except Exception as e:
        return f"✗ Error getting email address: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

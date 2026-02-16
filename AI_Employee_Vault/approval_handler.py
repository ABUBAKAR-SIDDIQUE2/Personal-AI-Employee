#!/usr/bin/env python3
"""
Approval Handler for AI Employee Safety Valve

Watches the /Approved folder and executes approved actions with human oversight.
This implements the "Human-in-the-Loop" pattern for sensitive operations.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import yaml

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: watchdog not installed. Run: pip install watchdog", file=sys.stderr)
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
    sys.exit(1)

# Import LinkedIn manager
try:
    from linkedin_manager import LinkedInManager
except ImportError:
    print("Warning: linkedin_manager not found. LinkedIn posting will not work.", file=sys.stderr)
    LinkedInManager = None


class ApprovalHandler(FileSystemEventHandler):
    """
    Handles approved action files and executes them with proper logging.
    """

    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __init__(self, vault_path: str):
        """
        Initialize the approval handler.

        Args:
            vault_path: Path to the AI Employee vault root directory
        """
        self.vault_path = Path(vault_path)
        self.approved_path = self.vault_path / "Approved"
        self.done_path = self.vault_path / "Done"
        self.logs_path = self.vault_path / "Logs"
        self.credentials_path = self.vault_path / "credentials"

        # Create directories if they don't exist
        self.approved_path.mkdir(exist_ok=True)
        self.done_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)

        # Set up logging
        self._setup_logging()

        # Gmail service (initialized on first use)
        self._gmail_service = None

        # LinkedIn manager (initialized on first use)
        self._linkedin_manager = None

        self.logger.info(f"ApprovalHandler initialized - watching {self.approved_path}")

    def _setup_logging(self) -> None:
        """Configure logging for the approval handler."""
        self.logger = logging.getLogger("ApprovalHandler")
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # File handler
        log_file = self.logs_path / "ApprovalHandler.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def _get_gmail_service(self):
        """
        Get or create Gmail API service instance.

        Returns:
            Gmail API service object
        """
        if self._gmail_service is not None:
            return self._gmail_service

        token_file = self.credentials_path / "token.json"

        if not token_file.exists():
            raise FileNotFoundError(
                f"Gmail token not found at {token_file}. "
                "Please run setup_gmail.py first to authenticate."
            )

        # Load credentials
        creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        # Build service
        self._gmail_service = build('gmail', 'v1', credentials=creds)
        return self._gmail_service

    def _parse_frontmatter(self, file_path: Path) -> tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter and content from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Tuple of (frontmatter dict, content string)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for frontmatter
        if not content.startswith('---'):
            return {}, content

        # Split frontmatter and content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1])
            body_content = parts[2].strip()
            return frontmatter or {}, body_content
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML frontmatter: {e}")
            return {}, content

    def _send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email using Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content

        Returns:
            True if successful, False otherwise
        """
        try:
            service = self._get_gmail_service()

            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            message_body = {'raw': raw_message}

            # Send message
            result = service.users().messages().send(
                userId='me',
                body=message_body
            ).execute()

            message_id = result.get('id', 'unknown')
            self.logger.info(f"Email sent successfully to {to} (Message ID: {message_id})")
            return True

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e.reason}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending email: {e}", exc_info=True)
            return False

    def _get_linkedin_manager(self):
        """
        Get or create LinkedIn manager instance.

        Returns:
            LinkedInManager instance
        """
        if self._linkedin_manager is None:
            if LinkedInManager is None:
                raise ImportError("LinkedInManager not available")
            self._linkedin_manager = LinkedInManager(str(self.vault_path), mode="mock")
        return self._linkedin_manager

    def _post_linkedin(self, text: str) -> bool:
        """
        Post to LinkedIn (queues to LINKEDIN_QUEUE.md in mock mode).

        Args:
            text: Post content

        Returns:
            True if successful, False otherwise
        """
        try:
            manager = self._get_linkedin_manager()
            success = manager.post_update(text)

            if success:
                self.logger.info(f"LinkedIn post queued successfully")
            else:
                self.logger.error(f"Failed to queue LinkedIn post")

            return success

        except Exception as e:
            self.logger.error(f"Error posting to LinkedIn: {e}", exc_info=True)
            return False

    def _log_action(self, action: str, details: str, status: str) -> None:
        """
        Log an action to the actions log file.

        Args:
            action: Action type (e.g., "send_email")
            details: Action details
            status: Status (success/failed)
        """
        actions_log = self.logs_path / "actions.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = f"[{timestamp}] {action} | {status} | {details}\n"

        with open(actions_log, 'a') as f:
            f.write(log_entry)

    def _process_approval_file(self, file_path: Path) -> None:
        """
        Process an approved action file.

        Args:
            file_path: Path to the approval file
        """
        try:
            self.logger.info(f"Processing approval file: {file_path.name}")

            # Parse frontmatter and content
            frontmatter, body_content = self._parse_frontmatter(file_path)

            # Get action type
            action = frontmatter.get('action', '').lower()

            if action == 'send_email':
                # Extract email parameters
                to_email = frontmatter.get('to', '')
                subject = frontmatter.get('subject', '')

                # Validate required fields
                if not to_email or not subject:
                    self.logger.error(f"Missing required fields in {file_path.name}")
                    self._log_action(
                        action="send_email",
                        details=f"File: {file_path.name} - Missing to/subject",
                        status="FAILED"
                    )
                    return

                # Send email
                success = self._send_email(to_email, subject, body_content)

                if success:
                    # Log success
                    self._log_action(
                        action="send_email",
                        details=f"To: {to_email} | Subject: {subject}",
                        status="SUCCESS"
                    )

                    # Move to Done
                    destination = self.done_path / file_path.name
                    file_path.rename(destination)
                    self.logger.info(f"Moved {file_path.name} to /Done")
                else:
                    # Log failure
                    self._log_action(
                        action="send_email",
                        details=f"To: {to_email} | Subject: {subject}",
                        status="FAILED"
                    )
                    self.logger.error(f"Failed to send email from {file_path.name}")

            elif action == 'linkedin_post':
                # Post to LinkedIn (queues in mock mode)
                success = self._post_linkedin(body_content)

                if success:
                    # Log success
                    preview = body_content[:50] + "..." if len(body_content) > 50 else body_content
                    self._log_action(
                        action="linkedin_post",
                        details=f"Post: {preview}",
                        status="SUCCESS (Queued)"
                    )

                    # Move to Done
                    destination = self.done_path / file_path.name
                    file_path.rename(destination)
                    self.logger.info(f"Moved {file_path.name} to /Done")
                else:
                    # Log failure
                    self._log_action(
                        action="linkedin_post",
                        details=f"File: {file_path.name}",
                        status="FAILED"
                    )
                    self.logger.error(f"Failed to queue LinkedIn post from {file_path.name}")

            else:
                self.logger.warning(f"Unknown action type: {action} in {file_path.name}")
                self._log_action(
                    action=action or "unknown",
                    details=f"File: {file_path.name}",
                    status="FAILED - Unknown action"
                )

        except Exception as e:
            self.logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
            self._log_action(
                action="unknown",
                details=f"File: {file_path.name} - Error: {str(e)}",
                status="FAILED"
            )

    def on_created(self, event):
        """
        Called when a file is created in the watched directory.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process markdown files
        if file_path.suffix.lower() != '.md':
            return

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        # Process the approval file
        self._process_approval_file(file_path)

    def on_moved(self, event):
        """
        Called when a file is moved into the watched directory.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)

        # Only process markdown files
        if dest_path.suffix.lower() != '.md':
            return

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        # Process the approval file
        self._process_approval_file(dest_path)


def main():
    """
    Main entry point for the approval handler.
    """
    import sys

    # Get vault path from command line or use default
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        vault_path = Path(__file__).parent

    print("=" * 60)
    print("AI Employee Approval Handler")
    print("=" * 60)
    print(f"Vault path: {vault_path}")
    print(f"Watching: {Path(vault_path) / 'Approved'}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Create handler and observer
    handler = ApprovalHandler(vault_path)
    observer = Observer()
    observer.schedule(handler, str(handler.approved_path), recursive=False)

    # Start watching
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping approval handler...")
        observer.stop()

    observer.join()
    print("Approval handler stopped.")


if __name__ == "__main__":
    main()

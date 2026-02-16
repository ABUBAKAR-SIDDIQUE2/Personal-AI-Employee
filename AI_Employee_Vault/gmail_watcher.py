"""
Gmail Watcher for AI Employee Sensory System

Monitors Gmail inbox for important unread emails and creates action items
for the AI agent to process.
"""

import os
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError(
        "Gmail watcher requires Google API libraries. "
        "Install with: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )

from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail inbox for important unread emails and creates action items.

    Monitors emails matching: is:unread AND is:important
    Creates markdown action files with email metadata and content.
    """

    # Gmail API scopes required
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(
        self,
        vault_path: str,
        credentials_path: str,
        check_interval: int = 300
    ):
        """
        Initialize the Gmail watcher.

        Args:
            vault_path: Path to the AI Employee vault root directory
            credentials_path: Path to directory containing credentials.json and token.json
            check_interval: Time in seconds between checks (default: 300 = 5 minutes)
        """
        super().__init__(vault_path, check_interval)

        self.credentials_path = Path(credentials_path)
        self.token_file = self.credentials_path / "token.json"
        self.credentials_file = self.credentials_path / "credentials.json"

        # Validate credentials path
        if not self.credentials_path.exists():
            raise ValueError(f"Credentials path does not exist: {credentials_path}")

        # Track processed email IDs
        self.processed_ids_file = self.logs_path / "processed_emails.txt"
        self.processed_ids = self._load_processed_ids()

        # Gmail service (initialized on first use)
        self._service = None

        self.logger.info(f"Initialized GmailWatcher with credentials from {credentials_path}")

    def _load_processed_ids(self) -> set:
        """
        Load the set of already processed email IDs.

        Returns:
            Set of processed email ID strings
        """
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, 'r') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                self.logger.warning(f"Could not load processed IDs: {e}")
                return set()
        return set()

    def _save_processed_id(self, email_id: str) -> None:
        """
        Save a processed email ID to the tracking file.

        Args:
            email_id: Gmail message ID to mark as processed
        """
        try:
            with open(self.processed_ids_file, 'a') as f:
                f.write(f"{email_id}\n")
            self.processed_ids.add(email_id)
        except Exception as e:
            self.logger.error(f"Could not save processed ID: {e}")

    def _get_credentials(self) -> Optional[Credentials]:
        """
        Load or refresh Gmail API credentials.

        Returns:
            Valid Credentials object or None if authentication fails
        """
        creds = None

        # Load token if it exists
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)
                self.logger.debug("Loaded credentials from token.json")
            except Exception as e:
                self.logger.warning(f"Could not load token.json: {e}")

        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info("Refreshed expired credentials")
            except Exception as e:
                self.logger.error(f"Could not refresh credentials: {e}")
                creds = None

        if not creds or not creds.valid:
            self.logger.error(
                "No valid credentials available. "
                "Please run OAuth flow to generate token.json"
            )
            return None

        return creds

    def _get_service(self):
        """
        Get or create Gmail API service instance.

        Returns:
            Gmail API service object
        """
        if self._service is None:
            creds = self._get_credentials()
            if not creds:
                raise ValueError("Cannot create Gmail service without valid credentials")

            try:
                self._service = build('gmail', 'v1', credentials=creds)
                self.logger.info("Connected to Gmail API")
            except Exception as e:
                self.logger.error(f"Failed to build Gmail service: {e}")
                raise

        return self._service

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new important unread emails.

        Returns:
            List of email message dictionaries with metadata
        """
        new_emails = []

        try:
            service = self._get_service()

            # Query for unread AND important messages
            query = "is:unread is:important"

            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10  # Limit to prevent overwhelming the system
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                self.logger.debug("No new important unread emails found")
                return []

            self.logger.info(f"Found {len(messages)} important unread email(s)")

            # Fetch full details for each message
            for msg in messages:
                msg_id = msg['id']

                # Skip if already processed
                if msg_id in self.processed_ids:
                    self.logger.debug(f"Skipping already processed email: {msg_id}")
                    continue

                try:
                    # Get full message details
                    message = service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='full'
                    ).execute()

                    email_data = self._parse_email(message)
                    if email_data:
                        new_emails.append(email_data)

                except HttpError as e:
                    self.logger.error(f"Error fetching message {msg_id}: {e}")
                    continue

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)

        return new_emails

    def _parse_email(self, message: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse Gmail message into structured data.

        Args:
            message: Gmail API message object

        Returns:
            Dictionary with email metadata and content
        """
        try:
            headers = message['payload']['headers']
            header_dict = {h['name'].lower(): h['value'] for h in headers}

            # Extract key fields
            email_data = {
                'id': message['id'],
                'thread_id': message['threadId'],
                'from': header_dict.get('from', 'Unknown'),
                'subject': header_dict.get('subject', '(No Subject)'),
                'date': header_dict.get('date', ''),
                'snippet': message.get('snippet', ''),
                'body': self._extract_body(message['payload'])
            }

            # Parse date
            if email_data['date']:
                try:
                    email_data['datetime'] = parsedate_to_datetime(email_data['date'])
                except Exception:
                    email_data['datetime'] = datetime.now()
            else:
                email_data['datetime'] = datetime.now()

            return email_data

        except Exception as e:
            self.logger.error(f"Error parsing email: {e}", exc_info=True)
            return None

    def _extract_body(self, payload: Dict) -> str:
        """
        Extract email body from message payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body text (plain text preferred, HTML as fallback)
        """
        body = ""

        # Check for direct body data
        if 'body' in payload and 'data' in payload['body']:
            import base64
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            return body

        # Check for multipart message
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                # Prefer plain text
                if mime_type == 'text/plain' and 'data' in part.get('body', {}):
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    return body

                # Fallback to HTML
                if mime_type == 'text/html' and 'data' in part.get('body', {}) and not body:
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')

                # Recursively check nested parts
                if 'parts' in part:
                    nested_body = self._extract_body(part)
                    if nested_body:
                        return nested_body

        return body or "(No body content)"

    def create_action_file(self, item: Dict[str, Any]) -> None:
        """
        Create a Markdown action file for an email.

        Args:
            item: Email data dictionary from check_for_updates()
        """
        try:
            email_id = item['id']
            subject = item['subject']
            from_addr = item['from']
            received = item['datetime']
            snippet = item['snippet']
            body = item['body']

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in subject)
            safe_subject = safe_subject[:50]  # Limit length
            filename = f"EMAIL_{timestamp}_{safe_subject}.md"
            filepath = self.needs_action_path / filename

            # Create markdown content
            content = self._generate_email_markdown(
                from_addr=from_addr,
                subject=subject,
                received=received,
                snippet=snippet,
                body=body,
                email_id=email_id,
                thread_id=item['thread_id']
            )

            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Created email action file: {filename}")

            # Mark as processed
            self._save_processed_id(email_id)

            # Log the action
            self.log_action(
                action="Email detected and processed",
                details=f"From: {from_addr} | Subject: {subject}"
            )

        except Exception as e:
            self.logger.error(f"Error creating action file for email: {e}", exc_info=True)
            raise

    def _generate_email_markdown(
        self,
        from_addr: str,
        subject: str,
        received: datetime,
        snippet: str,
        body: str,
        email_id: str,
        thread_id: str
    ) -> str:
        """
        Generate markdown content for email action file.

        Args:
            from_addr: Sender email address
            subject: Email subject
            received: Received timestamp
            snippet: Email snippet
            body: Full email body
            email_id: Gmail message ID
            thread_id: Gmail thread ID

        Returns:
            Formatted markdown string
        """
        content = f"""---
type: email
from: {from_addr}
subject: {subject}
received: {received.strftime('%Y-%m-%d %H:%M:%S')}
priority: high
status: pending
email_id: {email_id}
thread_id: {thread_id}
---

# Important Email: {subject}

## Email Details

- **From:** {from_addr}
- **Subject:** {subject}
- **Received:** {received.strftime('%Y-%m-%d at %H:%M:%S')}
- **Priority:** High (marked as important)

## Preview

{snippet}

## Full Content

```
{body[:2000]}{"..." if len(body) > 2000 else ""}
```

## Suggested Actions

- [ ] Reply to sender
- [ ] Archive email
- [ ] Forward to relevant party
- [ ] Add to task list
- [ ] Schedule follow-up

## Notes

This email was automatically detected as important and unread.

---
*Generated by GmailWatcher*
"""
        return content


def main():
    """
    Main entry point for running the Gmail watcher.
    """
    import sys

    # Get paths from command line
    if len(sys.argv) < 2:
        print("Usage: python gmail_watcher.py <credentials_path> [vault_path]")
        print("  credentials_path: Directory containing credentials.json and token.json")
        print("  vault_path: Path to AI_Employee_Vault (default: current directory)")
        sys.exit(1)

    credentials_path = sys.argv[1]

    if len(sys.argv) > 2:
        vault_path = sys.argv[2]
    else:
        vault_path = Path(__file__).parent

    # Create and run the watcher
    try:
        watcher = GmailWatcher(
            vault_path=str(vault_path),
            credentials_path=credentials_path,
            check_interval=300  # Check every 5 minutes
        )
        print(f"Starting Gmail watcher...")
        print(f"Monitoring: Important unread emails")
        print(f"Check interval: 5 minutes")
        print(f"Press Ctrl+C to stop")
        watcher.run()
    except KeyboardInterrupt:
        print("\nWatcher stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

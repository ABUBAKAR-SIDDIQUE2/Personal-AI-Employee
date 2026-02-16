"""
WhatsApp Watcher for AI Employee Sensory System

Monitors WhatsApp Web for urgent messages containing specific keywords
and creates action items for the AI agent to process.
"""

import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
except ImportError:
    raise ImportError(
        "WhatsApp watcher requires Playwright. "
        "Install with: pip install playwright && playwright install chromium"
    )

from base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for urgent messages and creates action items.

    Monitors messages containing keywords: urgent, invoice, payment, help
    Uses persistent browser context to maintain WhatsApp Web session.
    """

    # Keywords to filter urgent messages
    URGENT_KEYWORDS = ['urgent', 'invoice', 'payment', 'help', 'asap', 'emergency', 'critical']

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        check_interval: int = 60,
        headless: bool = True
    ):
        """
        Initialize the WhatsApp watcher.

        Args:
            vault_path: Path to the AI Employee vault root directory
            session_path: Path to store browser session data (for persistent login)
            check_interval: Time in seconds between checks (default: 60)
            headless: Run browser in headless mode (default: True)
        """
        super().__init__(vault_path, check_interval)

        self.session_path = Path(session_path)
        self.headless = headless

        # Create session directory if it doesn't exist
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Track processed message IDs
        self.processed_ids_file = self.logs_path / "processed_whatsapp.txt"
        self.processed_ids = self._load_processed_ids()

        # Playwright instances (initialized on first use)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        self.logger.info(f"Initialized WhatsAppWatcher with session at {session_path}")

    def _load_processed_ids(self) -> set:
        """
        Load the set of already processed message IDs.

        Returns:
            Set of processed message ID strings
        """
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, 'r') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                self.logger.warning(f"Could not load processed IDs: {e}")
                return set()
        return set()

    def _save_processed_id(self, message_id: str) -> None:
        """
        Save a processed message ID to the tracking file.

        Args:
            message_id: Message identifier to mark as processed
        """
        try:
            with open(self.processed_ids_file, 'a') as f:
                f.write(f"{message_id}\n")
            self.processed_ids.add(message_id)
        except Exception as e:
            self.logger.error(f"Could not save processed ID: {e}")

    def _init_browser(self) -> None:
        """Initialize Playwright browser with persistent context."""
        if self._playwright is None:
            try:
                self._playwright = sync_playwright().start()

                # Launch persistent context to maintain WhatsApp Web session
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ],
                    viewport={'width': 1280, 'height': 720}
                )

                # Get the page
                if len(self._context.pages) > 0:
                    self._page = self._context.pages[0]
                else:
                    self._page = self._context.new_page()

                self.logger.info("Browser initialized successfully")

            except Exception as e:
                self.logger.error(f"Failed to initialize browser: {e}")
                raise

    def _navigate_to_whatsapp(self) -> bool:
        """
        Navigate to WhatsApp Web and wait for it to load.

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            if self._page is None:
                self._init_browser()

            # Navigate to WhatsApp Web
            self._page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)

            # Wait for either QR code or chat list to appear
            try:
                # Check if already logged in (chat list appears)
                self._page.wait_for_selector('[data-testid="chat-list"]', timeout=10000)
                self.logger.info("WhatsApp Web loaded - already authenticated")
                return True
            except:
                # QR code appeared - need to scan
                try:
                    self._page.wait_for_selector('canvas[aria-label*="Scan"]', timeout=5000)
                    self.logger.warning("QR code detected - please scan to authenticate")
                    self.logger.warning("Waiting 60 seconds for QR code scan...")

                    # Wait for authentication (chat list appears after scan)
                    self._page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
                    self.logger.info("Authentication successful!")
                    return True
                except:
                    self.logger.error("Failed to authenticate - QR code not scanned in time")
                    return False

        except Exception as e:
            self.logger.error(f"Error navigating to WhatsApp Web: {e}")
            return False

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check WhatsApp Web for new urgent messages.

        Returns:
            List of message dictionaries with metadata
        """
        urgent_messages = []

        try:
            # Ensure browser is initialized and navigated
            if not self._navigate_to_whatsapp():
                self.logger.error("Cannot check for updates - WhatsApp Web not loaded")
                return []

            # Wait for chat list to be ready
            self._page.wait_for_selector('[data-testid="chat-list"]', timeout=10000)

            # Find all chats with unread messages
            # WhatsApp uses spans with aria-label for unread counts
            unread_chats = self._page.query_selector_all('[aria-label*="unread message"]')

            if not unread_chats:
                self.logger.debug("No unread messages found")
                return []

            self.logger.info(f"Found {len(unread_chats)} chat(s) with unread messages")

            # Process each unread chat
            for chat_element in unread_chats[:10]:  # Limit to 10 chats to prevent overwhelming
                try:
                    # Get the parent chat item
                    chat_item = chat_element.evaluate_handle(
                        'element => element.closest("[data-testid=\\"cell-frame-container\\"]")'
                    ).as_element()

                    if not chat_item:
                        continue

                    # Extract chat name
                    chat_name_elem = chat_item.query_selector('[data-testid="cell-frame-title"]')
                    chat_name = chat_name_elem.inner_text() if chat_name_elem else "Unknown"

                    # Extract message preview
                    message_preview_elem = chat_item.query_selector('[data-testid="last-msg-text"]')
                    message_preview = message_preview_elem.inner_text() if message_preview_elem else ""

                    # Check if message contains urgent keywords
                    message_lower = message_preview.lower()
                    matching_keywords = [kw for kw in self.URGENT_KEYWORDS if kw in message_lower]

                    if not matching_keywords:
                        self.logger.debug(f"Skipping message from {chat_name} - no urgent keywords")
                        continue

                    # Create unique message ID
                    message_id = f"{chat_name}_{message_preview[:50]}_{datetime.now().strftime('%Y%m%d%H%M')}"
                    message_id = re.sub(r'[^a-zA-Z0-9_]', '_', message_id)

                    # Skip if already processed
                    if message_id in self.processed_ids:
                        self.logger.debug(f"Skipping already processed message: {message_id}")
                        continue

                    # Click on chat to get full message
                    chat_item.click()
                    time.sleep(2)  # Wait for messages to load

                    # Get the last few messages from this chat
                    messages = self._extract_recent_messages()

                    # Create message data
                    message_data = {
                        'id': message_id,
                        'sender': chat_name,
                        'preview': message_preview,
                        'full_messages': messages,
                        'keywords': matching_keywords,
                        'timestamp': datetime.now()
                    }

                    urgent_messages.append(message_data)
                    self.logger.info(f"Found urgent message from {chat_name} with keywords: {matching_keywords}")

                except Exception as e:
                    self.logger.error(f"Error processing chat: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)

        return urgent_messages

    def _extract_recent_messages(self) -> str:
        """
        Extract recent messages from the currently open chat.

        Returns:
            String containing recent messages
        """
        try:
            # Wait for messages to load
            self._page.wait_for_selector('[data-testid="msg-container"]', timeout=5000)

            # Get all message containers
            message_containers = self._page.query_selector_all('[data-testid="msg-container"]')

            # Get last 5 messages
            recent_messages = []
            for container in message_containers[-5:]:
                try:
                    # Get message text
                    text_elem = container.query_selector('.copyable-text span')
                    if text_elem:
                        message_text = text_elem.inner_text()

                        # Check if incoming or outgoing
                        is_incoming = container.query_selector('[data-testid="msg-in"]') is not None
                        prefix = "Them: " if is_incoming else "You: "

                        recent_messages.append(f"{prefix}{message_text}")
                except:
                    continue

            return "\n".join(recent_messages) if recent_messages else "Could not extract messages"

        except Exception as e:
            self.logger.error(f"Error extracting messages: {e}")
            return "Error extracting messages"

    def create_action_file(self, item: Dict[str, Any]) -> None:
        """
        Create a Markdown action file for an urgent WhatsApp message.

        Args:
            item: Message data dictionary from check_for_updates()
        """
        try:
            message_id = item['id']
            sender = item['sender']
            preview = item['preview']
            full_messages = item['full_messages']
            keywords = item['keywords']
            timestamp = item['timestamp']

            # Generate filename
            safe_sender = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sender)
            safe_sender = safe_sender[:30]  # Limit length
            filename = f"WHATSAPP_{timestamp.strftime('%Y%m%d_%H%M%S')}_{safe_sender}.md"
            filepath = self.needs_action_path / filename

            # Create markdown content
            content = self._generate_whatsapp_markdown(
                sender=sender,
                preview=preview,
                full_messages=full_messages,
                keywords=keywords,
                timestamp=timestamp,
                message_id=message_id
            )

            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Created WhatsApp action file: {filename}")

            # Mark as processed
            self._save_processed_id(message_id)

            # Log the action
            self.log_action(
                action="Urgent WhatsApp message detected",
                details=f"From: {sender} | Keywords: {', '.join(keywords)}"
            )

        except Exception as e:
            self.logger.error(f"Error creating action file for message: {e}", exc_info=True)
            raise

    def _generate_whatsapp_markdown(
        self,
        sender: str,
        preview: str,
        full_messages: str,
        keywords: List[str],
        timestamp: datetime,
        message_id: str
    ) -> str:
        """
        Generate markdown content for WhatsApp action file.

        Args:
            sender: Message sender name
            preview: Message preview text
            full_messages: Full message conversation
            keywords: Matched urgent keywords
            timestamp: Message timestamp
            message_id: Unique message identifier

        Returns:
            Formatted markdown string
        """
        content = f"""---
type: whatsapp
sender: {sender}
status: pending
priority: high
keywords: {', '.join(keywords)}
received: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
message_id: {message_id}
---

# Urgent WhatsApp Message: {sender}

## Message Details

- **From:** {sender}
- **Received:** {timestamp.strftime('%Y-%m-%d at %H:%M:%S')}
- **Priority:** High (contains urgent keywords: {', '.join(keywords)})
- **Status:** Pending

## Preview

{preview}

## Recent Conversation

```
{full_messages}
```

## Suggested Actions

- [ ] Reply to sender
- [ ] Mark as resolved
- [ ] Forward to relevant party
- [ ] Add to task list
- [ ] Schedule follow-up

## Notes

This message was automatically detected as urgent based on keyword matching.

---
*Generated by WhatsAppWatcher*
"""
        return content

    def __del__(self):
        """Cleanup browser resources."""
        try:
            if self._context:
                self._context.close()
            if self._playwright:
                self._playwright.stop()
        except:
            pass


def main():
    """
    Main entry point for running the WhatsApp watcher.
    """
    import sys

    # Get paths from command line
    if len(sys.argv) < 2:
        print("Usage: python whatsapp_watcher.py <session_path> [vault_path] [--headless]")
        print("  session_path: Directory to store browser session data")
        print("  vault_path: Path to AI_Employee_Vault (default: current directory)")
        print("  --headless: Run browser in headless mode (default: visible)")
        sys.exit(1)

    session_path = sys.argv[1]

    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        vault_path = sys.argv[2]
    else:
        vault_path = Path(__file__).parent

    headless = '--headless' in sys.argv

    # Create and run the watcher
    try:
        watcher = WhatsAppWatcher(
            vault_path=str(vault_path),
            session_path=session_path,
            check_interval=60,  # Check every minute
            headless=headless
        )
        print(f"Starting WhatsApp watcher...")
        print(f"Session path: {session_path}")
        print(f"Monitoring: Urgent messages with keywords: {', '.join(WhatsAppWatcher.URGENT_KEYWORDS)}")
        print(f"Check interval: 60 seconds")
        print(f"Headless mode: {headless}")
        print(f"Press Ctrl+C to stop")

        if not headless:
            print("\nNote: Browser window will open. If you see a QR code, scan it with your phone.")
            print("The session will be saved and you won't need to scan again.")

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

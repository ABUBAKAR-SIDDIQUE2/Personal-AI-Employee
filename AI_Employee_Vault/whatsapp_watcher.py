"""
WhatsApp Watcher for AI Employee Sensory System

Monitors WhatsApp Web for urgent messages containing specific keywords
and creates action items for the AI agent to process.

Uses Firefox for better compatibility with WhatsApp Web.
Uses Click-and-Read strategy with brute-force text extraction.
Includes aggressive clicking with multiple fallback strategies.
Includes rotating debug snapshot storage (keeps last 4 snapshots).
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
except ImportError:
    raise ImportError(
        "WhatsApp watcher requires Playwright. "
        "Install with: pip install playwright && playwright install firefox"
    )

from base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for urgent messages and creates action items.

    Monitors messages containing keywords: urgent, invoice, payment, help
    Uses persistent browser context to maintain WhatsApp Web session.
    Uses Firefox for better WhatsApp Web compatibility.
    Uses Click-and-Read strategy with brute-force text extraction.
    Includes aggressive clicking with scroll, force click, JS click, and parent click fallbacks.
    Maintains rotating debug snapshot storage (keeps last 4 snapshots).
    """

    # Keywords to filter urgent messages (includes test keywords)
    URGENT_KEYWORDS = ['urgent', 'invoice', 'payment', 'help', 'asap', 'emergency', 'critical', 'hello', 'test']

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
            headless: Run browser in headless mode (default: True, but overridden on first run)
        """
        super().__init__(vault_path, check_interval)

        # Force console logging to stdout with DEBUG level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)

        self.session_path = Path(session_path)

        # Create session directory if it doesn't exist
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Create debug snapshots directory
        self.snapshots_path = self.logs_path / "whatsapp_debug_snapshots"
        self.snapshots_path.mkdir(parents=True, exist_ok=True)

        # Check if this is first run (session directory is empty or has no Firefox profile)
        self.is_first_run = self._is_first_run()

        # Force headless=False on first run to allow QR code scanning
        if self.is_first_run:
            self.headless = False
            self.logger.info("First run detected - forcing visible browser for QR code authentication")
        else:
            self.headless = headless

        # Track processed message IDs (urgent messages that were acted upon)
        self.processed_ids_file = self.logs_path / "processed_whatsapp.txt"
        self.processed_ids = self._load_processed_ids()

        # Track ignored message IDs (non-urgent messages that were checked and skipped)
        self.ignored_ids_file = self.logs_path / "ignored_whatsapp.txt"
        self.ignored_ids = self._load_ignored_ids()

        # Playwright instances (initialized on first use)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        self.logger.info(f"Initialized WhatsAppWatcher with session at {session_path}")
        self.logger.info(f"Headless mode: {self.headless}")
        self.logger.info(f"Debug snapshots directory: {self.snapshots_path}")
        self.logger.info(f"Loaded {len(self.processed_ids)} processed IDs and {len(self.ignored_ids)} ignored IDs")
        self.logger.info("Using Click-and-Read strategy with brute-force text extraction")
        self.logger.info("Aggressive clicking enabled: scroll + force + JS + parent fallbacks")
        self.logger.info("Rotating snapshot storage enabled: keeping last 4 snapshots")

    def _is_first_run(self) -> bool:
        """Check if this is the first run (no existing session)."""
        if not self.session_path.exists():
            return True

        session_files = list(self.session_path.iterdir())
        if not session_files:
            return True

        firefox_markers = ['prefs.js', 'cookies.sqlite', 'places.sqlite']
        has_firefox_profile = any(
            (self.session_path / marker).exists() for marker in firefox_markers
        )

        return not has_firefox_profile

    def _load_processed_ids(self) -> set:
        """Load the set of already processed message IDs."""
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, 'r') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                self.logger.warning(f"Could not load processed IDs: {e}")
                return set()
        return set()

    def _load_ignored_ids(self) -> set:
        """Load the set of ignored (non-urgent) message IDs."""
        if self.ignored_ids_file.exists():
            try:
                with open(self.ignored_ids_file, 'r') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                self.logger.warning(f"Could not load ignored IDs: {e}")
                return set()
        return set()

    def _save_processed_id(self, message_id: str) -> None:
        """Save a processed message ID to the tracking file."""
        try:
            with open(self.processed_ids_file, 'a') as f:
                f.write(f"{message_id}\n")
            self.processed_ids.add(message_id)
            self.logger.debug(f"Saved processed ID: {message_id}")
        except Exception as e:
            self.logger.error(f"Could not save processed ID: {e}")

    def _save_ignored_id(self, message_id: str) -> None:
        """Save an ignored (non-urgent) message ID to the tracking file."""
        try:
            with open(self.ignored_ids_file, 'a') as f:
                f.write(f"{message_id}\n")
            self.ignored_ids.add(message_id)
            self.logger.debug(f"Saved ignored ID: {message_id}")
        except Exception as e:
            self.logger.error(f"Could not save ignored ID: {e}")

    def _init_browser(self) -> None:
        """Initialize Playwright browser with persistent context using Firefox."""
        if self._playwright is None:
            try:
                self._playwright = sync_playwright().start()

                self._context = self._playwright.firefox.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    viewport={'width': 1280, 'height': 720}
                )

                if len(self._context.pages) > 0:
                    self._page = self._context.pages[0]
                else:
                    self._page = self._context.new_page()

                self.logger.info("Firefox browser initialized successfully")

            except Exception as e:
                self.logger.error(f"Failed to initialize Firefox browser: {e}")
                raise

    def _wait_for_chat_list(self, timeout: int = 10000) -> bool:
        """Wait for WhatsApp chat list to appear using multiple fallback selectors."""
        selectors = [
            '[data-testid="chat-list"]',
            '[aria-label="Chat list"]',
            '[aria-label="New chat"]',
            'div[role="grid"]'
        ]

        for selector in selectors:
            try:
                self._page.wait_for_selector(selector, timeout=timeout)
                self.logger.info(f"Chat list detected using selector: {selector}")
                return True
            except:
                continue

        return False

    def _navigate_to_whatsapp(self) -> bool:
        """Navigate to WhatsApp Web and wait for it to load."""
        try:
            if self._page is None:
                self._init_browser()

            self._page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)

            try:
                if self._wait_for_chat_list(timeout=10000):
                    self.logger.info("WhatsApp Web loaded - already authenticated")
                    return True
            except:
                pass

            try:
                self._page.wait_for_selector('canvas[aria-label*="Scan"]', timeout=5000)
                self.logger.warning("QR code detected - manual authentication required")

                print("\n" + "="*70)
                print(">>> ACTION REQUIRED: WhatsApp QR Code Authentication")
                print("="*70)
                print("1. Scan the QR code displayed in the browser window")
                print("2. Wait for your chats to fully load in WhatsApp Web")
                print("3. Once you see your chat list, press ENTER here to continue")
                print("="*70)

                input(">>> Press ENTER after scanning QR code and chats have loaded: ")

                if self._wait_for_chat_list(timeout=5000):
                    self.logger.info("Authentication successful - chat list detected!")
                    time.sleep(2)
                    return True
                else:
                    self.logger.error("Chat list not found after manual confirmation")
                    return False

            except Exception as e:
                self.logger.error(f"Error during QR code authentication: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error navigating to WhatsApp Web: {e}")
            return False

    def _verify_chat_opened(self, timeout_ms: int = 3000) -> bool:
        """Verify that a chat has actually opened by checking for div#main."""
        try:
            self.logger.debug(f"Verifying chat opened (timeout: {timeout_ms}ms)...")
            main_locator = self._page.locator('div#main >> visible=true')
            main_locator.wait_for(timeout=timeout_ms)
            self.logger.debug("✓ Chat verified - div#main is visible")
            return True
        except Exception as e:
            self.logger.debug(f"✗ Chat verification failed: {e}")
            return False

    def _aggressive_click(self, badge) -> bool:
        """
        Attempt to click a badge using multiple aggressive strategies.

        Strategies (in order):
        1. Scroll into view + force click
        2. JavaScript direct click
        3. Parent container click

        Args:
            badge: The badge element to click

        Returns:
            True if any click attempt succeeded, False if all failed
        """
        # ATTEMPT 1: Scroll into view + Force Click
        try:
            self.logger.debug("Attempt 1: Scroll into view + force click...")
            badge.scroll_into_view_if_needed()
            time.sleep(0.5)  # Brief pause after scroll
            badge.click(force=True, timeout=2000)
            self.logger.debug("✓ Force click succeeded")
            return True
        except Exception as e:
            self.logger.debug(f"✗ Force click failed: {e}")

        # ATTEMPT 2: JavaScript Click (The Nuclear Option)
        try:
            self.logger.debug("Attempt 2: JavaScript direct click...")
            badge.evaluate('element => element.click()')
            self.logger.debug("✓ JavaScript click succeeded")
            return True
        except Exception as e:
            self.logger.debug(f"✗ JavaScript click failed: {e}")

        # ATTEMPT 3: Parent Container Click
        try:
            self.logger.debug("Attempt 3: Parent container click...")
            parent = badge.evaluate_handle('element => element.closest("[data-testid=\\"cell-frame-container\\"]")')
            if parent:
                parent_elem = parent.as_element()
                if parent_elem:
                    parent_elem.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    parent_elem.click(force=True, timeout=2000)
                    self.logger.debug("✓ Parent click succeeded")
                    return True
        except Exception as e:
            self.logger.debug(f"✗ Parent click failed: {e}")

        # All attempts failed
        self.logger.error("All click attempts failed (force, JS, parent)")
        return False

    def _extract_sender_name_from_header(self) -> str:
        """Extract the sender/chat name from the conversation header inside div#main."""
        try:
            main_elem = self._page.query_selector('div#main')
            if main_elem:
                header = main_elem.query_selector('header')
                if header:
                    title_elem = header.query_selector('[title]')
                    if title_elem:
                        title = title_elem.get_attribute('title')
                        if title and title.strip():
                            self.logger.debug(f"Extracted sender from div#main header [title]: {title}")
                            return title.strip()

                    header_text = header.inner_text()
                    if header_text and header_text.strip():
                        first_line = header_text.split('\n')[0].strip()
                        if first_line:
                            self.logger.debug(f"Extracted sender from div#main header text: {first_line}")
                            return first_line
        except Exception as e:
            self.logger.debug(f"Strategy 1 (div#main header) failed: {e}")

        selectors = [
            'header [title]',
            '[data-testid="conversation-info-header-chat-title"]',
            'header h2',
            'header span[title]',
            'header span[dir="auto"]'
        ]

        for selector in selectors:
            try:
                elem = self._page.query_selector(selector)
                if elem:
                    title = elem.get_attribute('title')
                    if title and title.strip():
                        self.logger.debug(f"Extracted sender using {selector} (title attribute): {title}")
                        return title.strip()

                    text = elem.inner_text()
                    if text and text.strip():
                        self.logger.debug(f"Extracted sender using {selector} (inner text): {text}")
                        return text.strip()
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue

        self.logger.warning("Could not extract sender name from header")
        return "Unknown"

    def _extract_recent_messages(self) -> str:
        """
        Extract message text from the chat using brute-force approach.
        Uses specific div#main >> visible=true selector.
        """
        try:
            self.logger.debug("Attempting brute-force text extraction from div#main...")

            try:
                main_locator = self._page.locator('div#main >> visible=true')
                main_locator.wait_for(timeout=5000)

                text_content = main_locator.inner_text()

                if text_content and text_content.strip():
                    cleaned = ' '.join(text_content.split())
                    self.logger.debug(f"Successfully extracted {len(cleaned)} characters from div#main")
                    self.logger.debug(f"Text preview: {cleaned[:200]}...")
                    return cleaned
                else:
                    self.logger.warning("div#main found but text content is empty")

            except Exception as e:
                self.logger.warning(f"Strategy 1 (div#main >> visible=true) failed: {e}")

            try:
                self.logger.debug("Trying fallback: div[role='application']...")
                app_locator = self._page.locator('div[role="application"]')
                app_locator.wait_for(timeout=3000)

                text_content = app_locator.inner_text()

                if text_content and text_content.strip():
                    cleaned = ' '.join(text_content.split())
                    self.logger.debug(f"Successfully extracted {len(cleaned)} characters from application div")
                    return cleaned

            except Exception as e:
                self.logger.warning(f"Strategy 2 (application div) failed: {e}")

            self.logger.error("All text extraction strategies failed")
            self._save_debug_snapshot("extraction_failed")

            return "Error: Could not extract messages"

        except Exception as e:
            self.logger.error(f"Critical error in _extract_recent_messages: {e}", exc_info=True)
            self._save_debug_snapshot("extraction_exception")
            return "Error: Exception during extraction"

    def _cleanup_old_snapshots(self) -> None:
        """
        Clean up old debug snapshots, keeping only the 4 most recent files.
        """
        try:
            # Get all PNG files in the snapshots directory
            snapshot_files = list(self.snapshots_path.glob('*.png'))

            # If we have 4 or fewer files, no cleanup needed
            if len(snapshot_files) <= 4:
                return

            # Sort by modification time (oldest first)
            snapshot_files.sort(key=lambda x: x.stat().st_mtime)

            # Calculate how many to delete (keep last 4)
            files_to_delete = snapshot_files[:-4]

            # Delete old files
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    self.logger.debug(f"Deleted old snapshot: {file_path.name}")
                except Exception as e:
                    self.logger.warning(f"Could not delete {file_path.name}: {e}")

            if deleted_count > 0:
                self.logger.info(f"Deleted {deleted_count} old snapshot(s) to maintain storage limit (keeping last 4)")

        except Exception as e:
            self.logger.error(f"Error during snapshot cleanup: {e}")

    def _save_debug_snapshot(self, reason: str) -> None:
        """
        Save a screenshot for debugging when extraction fails.
        Automatically cleans up old snapshots to keep only the 4 most recent.

        Args:
            reason: Reason for the snapshot (used in filename)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = self.snapshots_path / f"{reason}_{timestamp}.png"

            self._page.screenshot(path=str(screenshot_path))

            self.logger.warning(f"📸 Debug snapshot saved: {screenshot_path}")
            print(f"\n⚠️  DEBUG SNAPSHOT SAVED")
            print(f"    Reason: {reason}")
            print(f"    Location: {screenshot_path}")
            print(f"    Please inspect this screenshot to see what the bot sees.\n")

            # Clean up old snapshots (keep only last 4)
            self._cleanup_old_snapshots()

        except Exception as e:
            self.logger.error(f"Failed to save debug snapshot: {e}")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """Check WhatsApp Web for new urgent messages using aggressive click strategy."""
        urgent_messages = []

        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting check for updates...")

            if not self._navigate_to_whatsapp():
                self.logger.error("Cannot check for updates - WhatsApp Web not loaded")
                return []

            if not self._wait_for_chat_list(timeout=10000):
                self.logger.error("Chat list not found - cannot check for updates")
                return []

            self.logger.info("Searching for unread message badges...")
            unread_badges = self._page.query_selector_all('[aria-label*="unread message"]')

            if not unread_badges:
                self.logger.info("No unread messages found")
                return []

            self.logger.info(f"Found {len(unread_badges)} unread badge(s)")

            for idx, badge in enumerate(unread_badges[:10], 1):
                try:
                    self.logger.info(f"Processing badge {idx}/{min(len(unread_badges), 10)}...")

                    # AGGRESSIVE CLICK STRATEGY
                    self.logger.debug("Attempting aggressive click...")
                    click_success = self._aggressive_click(badge)

                    if not click_success:
                        self.logger.error("All click attempts failed - skipping this badge")
                        self._save_debug_snapshot("click_failed")
                        continue

                    # VERIFY: Check if chat actually opened
                    if not self._verify_chat_opened(timeout_ms=3000):
                        self.logger.warning("Chat did not open after click - retrying...")

                        # RETRY: Try aggressive click again
                        click_success = self._aggressive_click(badge)

                        if not click_success or not self._verify_chat_opened(timeout_ms=3000):
                            self.logger.error("Chat did not open after retry - skipping this badge")
                            self._save_debug_snapshot("phantom_click")
                            continue
                        else:
                            self.logger.info("✓ Chat opened successfully after retry")
                    else:
                        self.logger.debug("✓ Chat opened successfully on first attempt")

                    # Wait for content to stabilize
                    time.sleep(1)

                    # EXTRACT DATA
                    sender = self._extract_sender_name_from_header()
                    self.logger.info(f"Chat opened: {sender}")

                    self.logger.debug("Extracting messages using brute-force method...")
                    messages = self._extract_recent_messages()

                    if not messages or messages.startswith("Error:"):
                        self.logger.warning(f"Could not extract messages from {sender} - skipping")
                        continue

                    self.logger.debug(f"Extracted {len(messages)} characters of text")
                    self.logger.debug(f"Text preview: {messages[:150]}...")

                    # Create unique message ID
                    message_id = f"{sender}_{messages[:50]}_{datetime.now().strftime('%Y%m%d%H%M')}"
                    message_id = re.sub(r'[^a-zA-Z0-9_]', '_', message_id)

                    # Check if already processed or ignored
                    if message_id in self.processed_ids:
                        self.logger.info(f"Message from {sender} already processed - skipping")
                        continue

                    if message_id in self.ignored_ids:
                        self.logger.info(f"Message from {sender} already ignored - skipping")
                        continue

                    # KEYWORD CHECK
                    messages_lower = messages.lower()
                    matching_keywords = [kw for kw in self.URGENT_KEYWORDS if kw in messages_lower]

                    if not matching_keywords:
                        self.logger.info(f"Message from {sender} checked - NOT URGENT (no keywords matched)")
                        self.logger.debug(f"  Message content: {messages[:100]}")
                        self._save_ignored_id(message_id)
                        continue

                    # Message is URGENT!
                    self.logger.info(f"🚨 URGENT MESSAGE from {sender} - Keywords: {matching_keywords}")

                    message_data = {
                        'id': message_id,
                        'sender': sender,
                        'preview': messages[:200],
                        'full_messages': messages,
                        'keywords': matching_keywords,
                        'timestamp': datetime.now()
                    }

                    urgent_messages.append(message_data)
                    self.logger.info(f"Added urgent message from {sender} to processing queue")

                except Exception as e:
                    self.logger.error(f"Error processing badge {idx}: {e}", exc_info=True)
                    continue

            self.logger.info(f"Check complete. Found {len(urgent_messages)} urgent message(s)")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)

        return urgent_messages

    def create_action_file(self, item: Dict[str, Any]) -> None:
        """Create a Markdown action file for an urgent WhatsApp message."""
        try:
            message_id = item['id']
            sender = item['sender']
            preview = item['preview']
            full_messages = item['full_messages']
            keywords = item['keywords']
            timestamp = item['timestamp']

            safe_sender = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sender)
            safe_sender = safe_sender[:30]
            filename = f"WHATSAPP_{timestamp.strftime('%Y%m%d_%H%M%S')}_{safe_sender}.md"
            filepath = self.needs_action_path / filename

            content = self._generate_whatsapp_markdown(
                sender=sender,
                preview=preview,
                full_messages=full_messages,
                keywords=keywords,
                timestamp=timestamp,
                message_id=message_id
            )

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"✅ Created WhatsApp action file: {filename}")

            self._save_processed_id(message_id)

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
        """Generate markdown content for WhatsApp action file."""
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

## Full Content

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
Content extracted using brute-force method from WhatsApp Web main panel.

---
*Generated by WhatsAppWatcher (Firefox) - Aggressive Click + Brute-Force Extraction*
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
    """Main entry point for running the WhatsApp watcher."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python whatsapp_watcher.py <session_path> [vault_path] [--headless]")
        print("  session_path: Directory to store browser session data")
        print("  vault_path: Path to AI_Employee_Vault (default: current directory)")
        print("  --headless: Run browser in headless mode (default: visible on first run)")
        sys.exit(1)

    session_path = sys.argv[1]

    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        vault_path = sys.argv[2]
    else:
        vault_path = Path(__file__).parent

    headless = '--headless' in sys.argv

    try:
        watcher = WhatsAppWatcher(
            vault_path=str(vault_path),
            session_path=session_path,
            check_interval=60,
            headless=headless
        )
        print("\n" + "="*70)
        print("WhatsApp Watcher - Aggressive Click + Brute-Force Extraction")
        print("="*70)
        print(f"Session path: {session_path}")
        print(f"Keywords: {', '.join(WhatsAppWatcher.URGENT_KEYWORDS)}")
        print(f"Check interval: 60 seconds")
        print(f"Headless mode: {watcher.headless}")
        print(f"Console logging: ENABLED (DEBUG level)")
        print(f"Extraction method: Brute-force (div#main >> visible=true)")
        print(f"Click strategy: Aggressive (scroll + force + JS + parent)")
        print(f"Snapshot storage: Rotating (keeps last 4)")
        print("="*70)
        print("Press Ctrl+C to stop\n")

        if not watcher.headless:
            print("Note: Browser window will open. If you see a QR code, scan it with your phone.")
            print("The session will be saved and you won't need to scan again.\n")

        watcher.run()
    except KeyboardInterrupt:
        print("\n\nWatcher stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

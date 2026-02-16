"""
Base Watcher Template for AI Employee Sensory System

This module provides an abstract base class for implementing watchers
that monitor various sources and create action items in the vault.
"""

import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import List, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.

    Watchers continuously monitor a source for new items and create
    action files in the Needs_Action folder for processing.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the base watcher.

        Args:
            vault_path: Path to the AI Employee vault root directory
            check_interval: Time in seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.logs_path = self.vault_path / "Logs"

        # Validate paths
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

        if not self.needs_action_path.exists():
            raise ValueError(f"Needs_Action folder not found: {self.needs_action_path}")

        # Set up logging
        self._setup_logging()
        self.logger.info(f"Initialized {self.__class__.__name__} with {check_interval}s interval")

    def _setup_logging(self) -> None:
        """Configure logging for this watcher."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        self.logs_path.mkdir(exist_ok=True)

        # File handler
        log_file = self.logs_path / f"{self.__class__.__name__}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check the monitored source for new items.

        This method must be implemented by subclasses to define
        what source to monitor and how to detect new items.

        Returns:
            List of new items found. Each item can be any type
            that the subclass defines (dict, object, etc.)
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Any) -> None:
        """
        Create a Markdown action file for a detected item.

        This method must be implemented by subclasses to define
        how to format the item data into a Markdown file.

        The file should be saved to self.needs_action_path with
        a unique filename and contain all relevant information
        for the AI agent to process.

        Args:
            item: The item to create an action file for
        """
        pass

    def _generate_filename(self, prefix: str = "action") -> str:
        """
        Generate a unique filename with timestamp.

        Args:
            prefix: Prefix for the filename (default: "action")

        Returns:
            Filename string in format: prefix_YYYYMMDD_HHMMSS.md
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.md"

    def run(self) -> None:
        """
        Main loop that continuously checks for updates.

        This method runs indefinitely, checking for new items at
        the specified interval and creating action files for each.

        Press Ctrl+C to stop the watcher gracefully.
        """
        self.logger.info(f"Starting {self.__class__.__name__} monitoring loop")

        try:
            while True:
                try:
                    # Check for new items
                    self.logger.debug("Checking for updates...")
                    new_items = self.check_for_updates()

                    if new_items:
                        self.logger.info(f"Found {len(new_items)} new item(s)")

                        # Process each new item
                        for item in new_items:
                            try:
                                self.create_action_file(item)
                                self.logger.info(f"Created action file for item")
                            except Exception as e:
                                self.logger.error(f"Error creating action file: {e}", exc_info=True)
                    else:
                        self.logger.debug("No new items found")

                except Exception as e:
                    self.logger.error(f"Error during check cycle: {e}", exc_info=True)

                # Wait before next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info(f"Stopping {self.__class__.__name__} - received shutdown signal")
        except Exception as e:
            self.logger.critical(f"Fatal error in run loop: {e}", exc_info=True)
            raise

    def log_action(self, action: str, details: Optional[str] = None) -> None:
        """
        Log an action to both the logger and a structured log file.

        Args:
            action: Description of the action taken
            details: Optional additional details
        """
        log_entry = f"{action}"
        if details:
            log_entry += f" - {details}"

        self.logger.info(log_entry)

        # Also write to a structured audit log
        audit_log = self.logs_path / "audit_log.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(audit_log, "a") as f:
            f.write(f"| {timestamp} | {self.__class__.__name__} | {action} | {details or '-'} |\n")

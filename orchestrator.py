#!/usr/bin/env python3
"""
Master Orchestrator for AI Employee

Manages all watcher processes and the approval handler in a single unified system.
Provides automatic restart, health monitoring, and graceful shutdown.
"""

import sys
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ProcessConfig:
    """Configuration for a managed process."""

    def __init__(self, name: str, script: str, args: List[str], description: str):
        """
        Initialize process configuration.

        Args:
            name: Process identifier
            script: Python script filename
            args: Command-line arguments
            description: Human-readable description
        """
        self.name = name
        self.script = script
        self.args = args
        self.description = description
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.last_restart = None


class Orchestrator:
    """
    Master orchestrator for AI Employee system.

    Manages all watcher processes and approval handler with automatic restart,
    health monitoring, and graceful shutdown capabilities.
    """

    def __init__(self, vault_path: str):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the AI Employee vault root directory
        """
        self.vault_path = Path(vault_path)
        self.logs_path = self.vault_path / "Logs"
        self.dashboard_path = self.vault_path / "Dashboard.md"
        self.credentials_path = self.vault_path / "credentials"
        self.whatsapp_session_path = self.vault_path / "whatsapp_session"

        # Create logs directory
        self.logs_path.mkdir(exist_ok=True)

        # Set up logging
        self._setup_logging()

        # Define managed processes
        self.processes: Dict[str, ProcessConfig] = {
            "filesystem": ProcessConfig(
                name="filesystem",
                script="filesystem_watcher.py",
                args=[str(self.vault_path)],
                description="File System Watcher"
            ),
            "gmail": ProcessConfig(
                name="gmail",
                script="gmail_watcher.py",
                args=[str(self.credentials_path), str(self.vault_path)],
                description="Gmail Inbox Watcher"
            ),
            "whatsapp": ProcessConfig(
                name="whatsapp",
                script="whatsapp_watcher.py",
                args=[str(self.whatsapp_session_path), str(self.vault_path), "--headless"],
                description="WhatsApp Web Watcher"
            ),
            "approval": ProcessConfig(
                name="approval",
                script="approval_handler.py",
                args=[str(self.vault_path)],
                description="Approval Handler (Safety Valve)"
            )
        }

        # Shutdown flag
        self.shutdown_requested = False

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("Orchestrator initialized")

    def _setup_logging(self) -> None:
        """Configure logging for the orchestrator."""
        self.logger = logging.getLogger("Orchestrator")
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # File handler
        log_file = self.logs_path / "system.log"
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

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    def _update_dashboard(self, message: str) -> None:
        """
        Update the Dashboard with a status message.

        Args:
            message: Status message to append
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Read current dashboard
            if self.dashboard_path.exists():
                with open(self.dashboard_path, 'r') as f:
                    content = f.read()

                # Find the Recent Activity table and add entry
                if "| Timestamp | Action | Status | Details |" in content:
                    # Insert after the header row
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('| 2026-') or (i > 0 and '|---' in lines[i-1]):
                            # Insert new entry
                            new_entry = f"| {timestamp} | System_Status | ✓ Online | {message} |"
                            lines.insert(i, new_entry)
                            break

                    # Update Last Updated timestamp
                    for i, line in enumerate(lines):
                        if line.startswith('*Last Updated:'):
                            lines[i] = f"*Last Updated: {timestamp}*"
                            break

                    # Write back
                    with open(self.dashboard_path, 'w') as f:
                        f.write('\n'.join(lines))

                    self.logger.info(f"Dashboard updated: {message}")

        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")

    def _start_process(self, config: ProcessConfig) -> bool:
        """
        Start a managed process.

        Args:
            config: Process configuration

        Returns:
            True if started successfully, False otherwise
        """
        try:
            script_path = self.vault_path / config.script

            if not script_path.exists():
                self.logger.error(f"Script not found: {script_path}")
                return False

            # Start process
            config.process = subprocess.Popen(
                [sys.executable, str(script_path)] + config.args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.vault_path)
            )

            config.restart_count += 1
            config.last_restart = datetime.now()

            self.logger.info(f"Started {config.description} (PID: {config.process.pid})")
            return True

        except Exception as e:
            self.logger.error(f"Error starting {config.description}: {e}")
            return False

    def _stop_process(self, config: ProcessConfig) -> None:
        """
        Stop a managed process gracefully.

        Args:
            config: Process configuration
        """
        if config.process is None:
            return

        try:
            self.logger.info(f"Stopping {config.description}...")

            # Try graceful termination first
            config.process.terminate()

            # Wait up to 5 seconds for graceful shutdown
            try:
                config.process.wait(timeout=5)
                self.logger.info(f"Stopped {config.description}")
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.logger.warning(f"Force killing {config.description}")
                config.process.kill()
                config.process.wait()

            config.process = None

        except Exception as e:
            self.logger.error(f"Error stopping {config.description}: {e}")

    def _check_process_health(self, config: ProcessConfig) -> bool:
        """
        Check if a process is still running.

        Args:
            config: Process configuration

        Returns:
            True if running, False if dead
        """
        if config.process is None:
            return False

        # Check if process is still alive
        return config.process.poll() is None

    def _restart_process(self, config: ProcessConfig) -> None:
        """
        Restart a failed process.

        Args:
            config: Process configuration
        """
        self.logger.warning(f"{config.description} has died, restarting...")

        # Stop if somehow still running
        self._stop_process(config)

        # Wait a bit before restart (exponential backoff)
        wait_time = min(2 ** min(config.restart_count, 5), 60)  # Max 60 seconds
        self.logger.info(f"Waiting {wait_time}s before restart...")
        time.sleep(wait_time)

        # Restart
        if self._start_process(config):
            self.logger.info(f"{config.description} restarted successfully (restart #{config.restart_count})")
        else:
            self.logger.error(f"Failed to restart {config.description}")

    def start_all(self) -> None:
        """Start all managed processes."""
        self.logger.info("=" * 60)
        self.logger.info("AI Employee Master Orchestrator")
        self.logger.info("=" * 60)
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info("")

        # Start all processes
        for name, config in self.processes.items():
            self.logger.info(f"Starting {config.description}...")
            if not self._start_process(config):
                self.logger.error(f"Failed to start {config.description}")
            time.sleep(1)  # Stagger starts

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("All watchers started successfully")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("=" * 60)
        self.logger.info("")

        # Update dashboard
        self._update_dashboard("System Online: All Watchers Active")

    def stop_all(self) -> None:
        """Stop all managed processes."""
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("Shutting down all processes...")
        self.logger.info("=" * 60)

        # Stop all processes
        for name, config in self.processes.items():
            self._stop_process(config)

        self.logger.info("All processes stopped")

        # Update dashboard
        self._update_dashboard("System Offline: Orchestrator Stopped")

    def monitor_loop(self) -> None:
        """
        Main monitoring loop.

        Checks process health every 30 seconds and restarts failed processes.
        """
        check_interval = 30  # seconds

        while not self.shutdown_requested:
            try:
                # Wait for check interval
                for _ in range(check_interval):
                    if self.shutdown_requested:
                        break
                    time.sleep(1)

                if self.shutdown_requested:
                    break

                # Check health of all processes
                for name, config in self.processes.items():
                    if not self._check_process_health(config):
                        self.logger.error(f"{config.description} is not running!")
                        self._restart_process(config)

            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}", exc_info=True)
                time.sleep(5)

    def run(self) -> None:
        """
        Run the orchestrator.

        Starts all processes and enters the monitoring loop.
        """
        try:
            # Start all processes
            self.start_all()

            # Enter monitoring loop
            self.monitor_loop()

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            # Always stop all processes on exit
            self.stop_all()

    def status(self) -> None:
        """Print status of all managed processes."""
        print("\n" + "=" * 60)
        print("AI Employee System Status")
        print("=" * 60)

        for name, config in self.processes.items():
            status = "RUNNING" if self._check_process_health(config) else "STOPPED"
            pid = config.process.pid if config.process else "N/A"
            restarts = config.restart_count - 1  # Subtract initial start

            print(f"\n{config.description}:")
            print(f"  Status: {status}")
            print(f"  PID: {pid}")
            print(f"  Restarts: {restarts}")
            if config.last_restart:
                print(f"  Last Start: {config.last_restart.strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n" + "=" * 60)


def main():
    """
    Main entry point for the orchestrator.
    """
    import sys

    # Get vault path from command line or use default
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        vault_path = Path(__file__).parent / "AI_Employee_Vault"

    # Create and run orchestrator
    orchestrator = Orchestrator(str(vault_path))

    try:
        orchestrator.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

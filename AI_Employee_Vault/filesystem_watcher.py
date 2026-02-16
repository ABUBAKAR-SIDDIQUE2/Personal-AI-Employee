"""
Filesystem Watcher for AI Employee Sensory System

Monitors the /Inbox folder for new files and creates action items
with metadata for the AI agent to process.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

from base_watcher import BaseWatcher


class FilesystemWatcher(BaseWatcher):
    """
    Watches the /Inbox folder for new files and creates action items.

    When a file is detected:
    1. Copies the file to /Needs_Action with FILE_ prefix
    2. Creates a metadata .md file with file details
    """

    def __init__(self, vault_path: str, check_interval: int = 10):
        """
        Initialize the filesystem watcher.

        Args:
            vault_path: Path to the AI Employee vault root directory
            check_interval: Time in seconds between checks (default: 10)
        """
        super().__init__(vault_path, check_interval)

        self.inbox_path = self.vault_path / "Inbox"

        # Validate inbox exists
        if not self.inbox_path.exists():
            raise ValueError(f"Inbox folder not found: {self.inbox_path}")

        # Track processed files to avoid duplicates
        self.tracking_file = self.logs_path / "processed_files.json"
        self.processed_files = self._load_processed_files()

        self.logger.info(f"Monitoring inbox: {self.inbox_path}")

    def _load_processed_files(self) -> set:
        """
        Load the set of already processed files from tracking file.

        Returns:
            Set of processed file paths
        """
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed', []))
            except Exception as e:
                self.logger.warning(f"Could not load tracking file: {e}")
                return set()
        return set()

    def _save_processed_files(self) -> None:
        """Save the set of processed files to tracking file."""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump({'processed': list(self.processed_files)}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save tracking file: {e}")

    def check_for_updates(self) -> List[Path]:
        """
        Check the /Inbox folder for new files.

        Returns:
            List of Path objects for new files found
        """
        new_files = []

        try:
            # Get all files in inbox (not directories)
            inbox_files = [f for f in self.inbox_path.iterdir() if f.is_file()]

            for file_path in inbox_files:
                # Use absolute path string as identifier
                file_id = str(file_path.absolute())

                # Check if we've already processed this file
                if file_id not in self.processed_files:
                    new_files.append(file_path)
                    self.logger.info(f"Detected new file: {file_path.name}")

        except Exception as e:
            self.logger.error(f"Error scanning inbox: {e}", exc_info=True)

        return new_files

    def create_action_file(self, item: Path) -> None:
        """
        Process a file from inbox: copy it and create metadata.

        Args:
            item: Path object for the file to process
        """
        try:
            file_path = item
            original_name = file_path.name
            file_size = file_path.stat().st_size
            timestamp = datetime.now()

            # Generate new filename with FILE_ prefix
            new_filename = f"FILE_{timestamp.strftime('%Y%m%d_%H%M%S')}_{original_name}"
            destination = self.needs_action_path / new_filename

            # Copy file to Needs_Action
            shutil.copy2(file_path, destination)
            self.logger.info(f"Copied file to: {destination}")

            # Create metadata markdown file
            metadata_filename = f"FILE_{timestamp.strftime('%Y%m%d_%H%M%S')}_{original_name}.md"
            metadata_path = self.needs_action_path / metadata_filename

            metadata_content = self._generate_metadata_content(
                original_name=original_name,
                new_filename=new_filename,
                file_size=file_size,
                timestamp=timestamp,
                source_path=file_path
            )

            with open(metadata_path, 'w') as f:
                f.write(metadata_content)

            self.logger.info(f"Created metadata file: {metadata_path}")

            # Mark file as processed
            file_id = str(file_path.absolute())
            self.processed_files.add(file_id)
            self._save_processed_files()

            # Log the action
            self.log_action(
                action="File processed from Inbox",
                details=f"{original_name} -> {new_filename}"
            )

        except Exception as e:
            self.logger.error(f"Error processing file {item}: {e}", exc_info=True)
            raise

    def _generate_metadata_content(
        self,
        original_name: str,
        new_filename: str,
        file_size: int,
        timestamp: datetime,
        source_path: Path
    ) -> str:
        """
        Generate the markdown content for the metadata file.

        Args:
            original_name: Original filename
            new_filename: New filename with FILE_ prefix
            file_size: Size of file in bytes
            timestamp: When the file was detected
            source_path: Original path in Inbox

        Returns:
            Formatted markdown string
        """
        # Convert file size to human-readable format
        size_str = self._format_file_size(file_size)

        # Get file extension
        extension = source_path.suffix.lower()

        # Determine file type
        file_type = self._determine_file_type(extension)

        content = f"""---
type: file_ingestion
status: pending
priority: normal
created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
---

# New File Detected: {original_name}

## File Information

- **Original Name:** {original_name}
- **Stored As:** {new_filename}
- **File Type:** {file_type}
- **Extension:** {extension or 'none'}
- **Size:** {size_str} ({file_size:,} bytes)
- **Detected:** {timestamp.strftime('%Y-%m-%d at %H:%M:%S')}
- **Source:** `{source_path}`
- **Location:** `/Needs_Action/{new_filename}`

## Suggested Actions

- [ ] Review file contents
- [ ] Determine processing requirements
- [ ] Extract relevant information
- [ ] Move to appropriate destination when complete

## Notes

This file was automatically detected in the Inbox and is ready for processing.

---
*Generated by FilesystemWatcher*
"""
        return content

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Convert bytes to human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _determine_file_type(self, extension: str) -> str:
        """
        Determine file type category from extension.

        Args:
            extension: File extension (e.g., '.pdf')

        Returns:
            File type category string
        """
        extension = extension.lower()

        type_mapping = {
            # Documents
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.txt': 'Text File',
            '.md': 'Markdown Document',
            '.rtf': 'Rich Text Document',

            # Spreadsheets
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.csv': 'CSV Data',

            # Images
            '.jpg': 'Image (JPEG)',
            '.jpeg': 'Image (JPEG)',
            '.png': 'Image (PNG)',
            '.gif': 'Image (GIF)',
            '.bmp': 'Image (BMP)',
            '.svg': 'Image (SVG)',

            # Code
            '.py': 'Python Script',
            '.js': 'JavaScript File',
            '.html': 'HTML File',
            '.css': 'CSS File',
            '.json': 'JSON Data',
            '.xml': 'XML File',
            '.yaml': 'YAML File',
            '.yml': 'YAML File',

            # Archives
            '.zip': 'ZIP Archive',
            '.tar': 'TAR Archive',
            '.gz': 'GZIP Archive',
            '.rar': 'RAR Archive',

            # Other
            '.log': 'Log File',
        }

        return type_mapping.get(extension, 'Unknown File Type')


def main():
    """
    Main entry point for running the filesystem watcher.
    """
    import sys

    # Get vault path from command line or use default
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        # Default to current directory's AI_Employee_Vault
        vault_path = Path(__file__).parent

    # Create and run the watcher
    try:
        watcher = FilesystemWatcher(vault_path=str(vault_path), check_interval=10)
        print(f"Starting filesystem watcher...")
        print(f"Monitoring: {watcher.inbox_path}")
        print(f"Press Ctrl+C to stop")
        watcher.run()
    except KeyboardInterrupt:
        print("\nWatcher stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Vault Setup Script for AI Employee

Ensures all required directories exist in the AI_Employee_Vault.
Run this once before starting the orchestrator or any watchers.
"""

import sys
from pathlib import Path


def setup_vault(vault_path: str) -> None:
    """
    Create all required directories for the AI Employee vault.

    Args:
        vault_path: Path to the AI_Employee_Vault directory
    """
    vault = Path(vault_path)

    # Ensure vault directory itself exists
    if not vault.exists():
        print(f"❌ Error: Vault directory does not exist: {vault}")
        print(f"   Please create it first or check the path.")
        sys.exit(1)

    print("=" * 70)
    print("AI Employee Vault Setup")
    print("=" * 70)
    print(f"Vault path: {vault.absolute()}")
    print()

    # Define all required directories
    required_dirs = [
        # Core workflow folders
        "Inbox",
        "Needs_Action",
        "Pending_Approval",
        "Approved",
        "Rejected",
        "Done",
        "Plans",

        # Logs and debugging
        "Logs",
        "Logs/whatsapp_debug_snapshots",

        # Agent configuration
        "Agent_Skills",

        # Credentials and sessions (optional, but good to have)
        "credentials",
        "whatsapp_session",
    ]

    created_count = 0
    existing_count = 0

    for dir_name in required_dirs:
        dir_path = vault / dir_name

        if dir_path.exists():
            print(f"✓ Already exists: {dir_name}")
            existing_count += 1
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {dir_name}")
                created_count += 1
            except Exception as e:
                print(f"❌ Failed to create {dir_name}: {e}")
                sys.exit(1)

    print()
    print("=" * 70)
    print(f"Setup complete!")
    print(f"  Created: {created_count} directories")
    print(f"  Already existed: {existing_count} directories")
    print("=" * 70)
    print()

    if created_count > 0:
        print("✅ Your vault is now ready to use!")
        print("   You can start the orchestrator with: python orchestrator.py")
    else:
        print("✅ All directories already exist. Your vault is ready!")


def main():
    """Main entry point for the setup script."""
    # Get vault path from command line or use default
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        # Default to AI_Employee_Vault in the same directory as this script
        vault_path = Path(__file__).parent / "AI_Employee_Vault"

    setup_vault(str(vault_path))


if __name__ == "__main__":
    main()

"""
Gmail OAuth Setup Helper

This script helps you authenticate with Gmail API and generate the token.json
file needed for the GmailWatcher to function.

Run this script once to complete the OAuth flow, then use gmail_watcher.py
to monitor your inbox.
"""

import os
import sys
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def setup_gmail_auth(credentials_dir: str) -> bool:
    """
    Run OAuth flow to authenticate with Gmail API.

    Args:
        credentials_dir: Directory containing credentials.json

    Returns:
        True if authentication successful, False otherwise
    """
    credentials_path = Path(credentials_dir)
    credentials_file = credentials_path / "credentials.json"
    token_file = credentials_path / "token.json"

    # Check if credentials.json exists
    if not credentials_file.exists():
        print(f"Error: credentials.json not found in {credentials_dir}")
        print("\nPlease follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download credentials.json to this directory")
        return False

    creds = None

    # Check if token already exists
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            print("Found existing token.json")
        except Exception as e:
            print(f"Warning: Could not load existing token: {e}")

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("Token refreshed successfully!")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None

        if not creds:
            print("\nStarting OAuth authentication flow...")
            print("A browser window will open. Please:")
            print("1. Sign in to your Google account")
            print("2. Grant access to Gmail (read-only)")
            print("3. Return to this terminal\n")

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file),
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("\nAuthentication successful!")
            except Exception as e:
                print(f"\nError during authentication: {e}")
                return False

        # Save credentials
        try:
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"Credentials saved to {token_file}")
        except Exception as e:
            print(f"Error saving token: {e}")
            return False

    # Test the connection
    print("\nTesting Gmail API connection...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress', 'Unknown')
        print(f"✓ Successfully connected to Gmail!")
        print(f"✓ Authenticated as: {email}")
        print(f"✓ Total messages: {profile.get('messagesTotal', 0)}")
        return True
    except Exception as e:
        print(f"✗ Error testing connection: {e}")
        return False


def main():
    """Main entry point for Gmail setup."""
    print("=" * 60)
    print("Gmail OAuth Setup for AI Employee")
    print("=" * 60)
    print()

    # Get credentials directory
    if len(sys.argv) > 1:
        credentials_dir = sys.argv[1]
    else:
        # Default to a credentials folder in the vault
        vault_path = Path(__file__).parent
        credentials_dir = vault_path / "credentials"
        credentials_dir.mkdir(exist_ok=True)

    print(f"Credentials directory: {credentials_dir}")
    print()

    # Run setup
    success = setup_gmail_auth(str(credentials_dir))

    print()
    print("=" * 60)
    if success:
        print("✓ Setup complete!")
        print()
        print("Next steps:")
        print(f"1. Run the Gmail watcher:")
        print(f"   python gmail_watcher.py {credentials_dir}")
        print()
        print("2. The watcher will monitor for important unread emails")
        print("3. New emails will appear in /Needs_Action")
    else:
        print("✗ Setup failed. Please check the errors above.")
        print()
        print("For help, see: GMAIL_SETUP.md")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

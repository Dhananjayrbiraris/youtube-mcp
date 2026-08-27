"""Interactive OAuth 2.0 Authorization Script for YouTube Studio MCP.

Authenticates your YouTube account using credentials from your .env file
and automatically saves the generated refresh token directly back into .env.

Usage:
    uv run run_auth.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.auth import authenticate_interactive, get_client_id, get_client_secret, ENV_FILE


def main() -> None:
    print("=" * 65)
    print("YouTube Studio & Channel Analytics MCP - Authentication Setup")
    print("=" * 65)
    print(f"Reading environment configuration from:\n  {ENV_FILE}\n")

    client_id = get_client_id()
    client_secret = get_client_secret()

    if not client_id or not client_secret:
        print("[!] ERROR: 'YOUTUBE_CLIENT_ID' or 'YOUTUBE_CLIENT_SECRET' is missing in .env!")
        print("\nPlease follow these simple steps:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Enable 'YouTube Data API v3' and 'YouTube Analytics API'.")
        print("3. Configure 'OAuth consent screen' (External) and add your email to 'Test users'.")
        print("4. Go to 'Credentials' > 'Create Credentials' > 'OAuth client ID' > 'Desktop App'.")
        print("5. Copy your Client ID and Client Secret, and paste them into your '.env' file:")
        print(f"   File: {ENV_FILE}")
        print("   YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com")
        print("   YOUTUBE_CLIENT_SECRET=your_client_secret")
        print("\nOnce saved in .env, run this command again:")
        print("  uv run run_auth.py")
        sys.exit(1)

    print(f"[*] Found Client ID: {client_id[:16]}... in .env")
    print("[*] Launching browser for Google OAuth authorization...")
    print("[*] Please log into your YouTube account and approve access.\n")

    try:
        creds = authenticate_interactive()
        print("\n" + "=" * 65)
        print("[+] SUCCESS! Authentication complete.")
        print(f"[+] Refresh token has been automatically saved into:\n  {ENV_FILE}")
        print("=" * 65)
        print("\nYour YouTube MCP Server is now fully authenticated and ready to run!")
    except Exception as e:
        print(f"\n[!] Authentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

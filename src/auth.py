"""Authentication manager for YouTube Data API and YouTube Analytics API.

Handles OAuth 2.0 credentials, reading configuration from .env,
token persistence, and automatic token refreshing.
"""

from __future__ import annotations

import os
import re
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import find_dotenv, load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Load environment variables from .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(dotenv_path=str(ENV_FILE), override=True)
else:
    load_dotenv(find_dotenv(usecwd=True), override=True)

# OAuth 2.0 Scopes required for YouTube Studio & Channel Analytics
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
DEFAULT_TOKEN_FILE = PROJECT_ROOT / "token.json"
DEFAULT_CLIENT_SECRETS_FILE = PROJECT_ROOT / "client_secrets.json"


def get_client_id() -> Optional[str]:
    """Gets Google OAuth Client ID from environment variable."""
    return os.environ.get("YOUTUBE_CLIENT_ID", "").strip() or None


def get_client_secret() -> Optional[str]:
    """Gets Google OAuth Client Secret from environment variable."""
    return os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip() or None


def get_refresh_token() -> Optional[str]:
    """Gets OAuth Refresh Token from environment variable."""
    return os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip() or None


def save_refresh_token_to_env(refresh_token: str, env_path: Optional[Path] = None) -> None:
    """Updates or adds YOUTUBE_REFRESH_TOKEN in the .env file."""
    target_file = env_path or ENV_FILE

    if not target_file.exists():
        target_file.write_text(f"YOUTUBE_REFRESH_TOKEN={refresh_token}\n", encoding="utf-8")
        return

    content = target_file.read_text(encoding="utf-8")
    pattern = r"^YOUTUBE_REFRESH_TOKEN=.*$"

    if re.search(pattern, content, flags=re.MULTILINE):
        new_content = re.sub(
            pattern,
            f"YOUTUBE_REFRESH_TOKEN={refresh_token}",
            content,
            flags=re.MULTILINE,
        )
    else:
        new_content = content.rstrip() + f"\nYOUTUBE_REFRESH_TOKEN={refresh_token}\n"

    target_file.write_text(new_content, encoding="utf-8")
    os.environ["YOUTUBE_REFRESH_TOKEN"] = refresh_token


def load_credentials() -> Credentials:
    """Loads valid user credentials from .env environment variables (or token.json fallback).

    Raises:
        RuntimeError / FileNotFoundError: If required credentials are not found.
    """
    client_id = get_client_id()
    client_secret = get_client_secret()
    refresh_tok = get_refresh_token()

    # 1. Pure .env mode with refresh token
    if client_id and client_secret and refresh_tok:
        creds = Credentials(
            token=None,
            refresh_token=refresh_tok,
            token_uri=TOKEN_URI,
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        try:
            creds.refresh(Request())
            return creds
        except Exception as exc:
            raise RuntimeError(
                f"Failed to refresh YouTube OAuth token using .env credentials: {exc}.\n"
                f"Please re-run 'uv run run_auth.py' to re-authenticate."
            ) from exc

    # 2. Fallback to token.json if present
    if DEFAULT_TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(DEFAULT_TOKEN_FILE), SCOPES)
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(DEFAULT_TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                if creds.refresh_token:
                    save_refresh_token_to_env(creds.refresh_token)
            return creds
        except Exception:
            pass

    # 3. Not configured yet
    if not client_id or not client_secret:
        raise FileNotFoundError(
            "YouTube OAuth credentials missing in .env!\n"
            "Please set 'YOUTUBE_CLIENT_ID' and 'YOUTUBE_CLIENT_SECRET' in your .env file,\n"
            "then run 'uv run run_auth.py' to authenticate."
        )

    raise FileNotFoundError(
        "YouTube OAuth refresh token not found in .env!\n"
        "Please run 'uv run run_auth.py' to authenticate your channel in one click."
    )


def create_auth_flow(port: int = 8088) -> InstalledAppFlow:
    """Creates the InstalledAppFlow instance from .env credentials or client_secrets.json."""
    client_id = get_client_id()
    client_secret = get_client_secret()

    if client_id and client_secret:
        client_config: Dict[str, Any] = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": AUTH_URI,
                "token_uri": TOKEN_URI,
                "redirect_uris": [f"http://localhost:{port}", "http://localhost"],
            }
        }
        return InstalledAppFlow.from_client_config(client_config, SCOPES)
    elif DEFAULT_CLIENT_SECRETS_FILE.exists():
        return InstalledAppFlow.from_client_secrets_file(str(DEFAULT_CLIENT_SECRETS_FILE), SCOPES)
    else:
        raise FileNotFoundError(
            "Google OAuth Client ID & Secret not configured in .env!\n"
            "Please open .env and provide:\n"
            "  YOUTUBE_CLIENT_ID=your_client_id_here\n"
            "  YOUTUBE_CLIENT_SECRET=your_client_secret_here\n"
        )


def authenticate_interactive(
    port: int = 8088,
    env_path: Optional[Path] = None,
) -> Credentials:
    """Run OAuth setup from .env credentials or client_secrets.json fallback.

    Saves the resulting refresh token directly into .env and token.json.
    """
    flow = create_auth_flow(port=port)

    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )

    print("\n" + "=" * 70, flush=True)
    print("👉 If the browser does not open automatically, copy and open this URL:", flush=True)
    print(f"\n{auth_url}\n", flush=True)
    print("=" * 70 + "\n", flush=True)
    print(f"[*] Waiting for authorization callback on http://localhost:{port}...", flush=True)

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    creds = flow.run_local_server(
        port=port,
        prompt="consent",
        access_type="offline",
        authorization_prompt_message="",
    )

    # Save refresh token into .env
    if creds.refresh_token:
        save_refresh_token_to_env(creds.refresh_token, env_path=env_path)

    # Also save token.json
    DEFAULT_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    return creds

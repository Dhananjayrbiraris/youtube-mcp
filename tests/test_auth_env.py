"""Tests for .env-based credential loading and saving."""

from __future__ import annotations

import os
from pathlib import Path
from src.auth import get_client_id, get_client_secret, get_refresh_token, save_refresh_token_to_env


def test_save_and_read_refresh_token_env(tmp_path: Path):
    test_env = tmp_path / ".env"
    test_env.write_text(
        "YOUTUBE_CLIENT_ID=test_id_123.apps.googleusercontent.com\n"
        "YOUTUBE_CLIENT_SECRET=test_secret_456\n"
        "YOUTUBE_REFRESH_TOKEN=\n",
        encoding="utf-8",
    )

    save_refresh_token_to_env("sample_generated_refresh_token_789", env_path=test_env)

    content = test_env.read_text(encoding="utf-8")
    assert "YOUTUBE_REFRESH_TOKEN=sample_generated_refresh_token_789" in content
    assert "YOUTUBE_CLIENT_ID=test_id_123" in content

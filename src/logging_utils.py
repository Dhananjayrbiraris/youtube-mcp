"""Shared logging and error serialization helpers for the YouTube MCP project."""

from __future__ import annotations

import json
import logging
import os
from typing import Any


def configure_logging(level: str | None = None) -> logging.Logger:
    """Configure a project-scoped logger with a consistent format."""
    log_level_name = (level or os.getenv("YOUTUBE_MCP_LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    logger = logging.getLogger("youtube_mcp")
    logger.setLevel(log_level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        logger.addHandler(handler)

    return logger


def build_error_response(exc: Exception) -> str:
    """Serialize exceptions into a consistent JSON payload for MCP tool responses."""
    payload: dict[str, Any] = {
        "error": exc.__class__.__name__,
        "message": str(exc),
    }
    return json.dumps(payload, indent=2)

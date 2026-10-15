"""Tests for YouTube formatters and date resolution logic."""

from __future__ import annotations

import pytest

from src.formatters import (
    format_analytics_report,
    parse_iso8601_duration,
    summarize_analytics,
)
from src.youtube_client import YouTubeStudioClient


def test_format_analytics_report():
    raw_api_response = {
        "columnHeaders": [
            {"name": "day", "columnType": "DIMENSION"},
            {"name": "views", "columnType": "METRIC"},
            {"name": "estimatedMinutesWatched", "columnType": "METRIC"},
        ],
        "rows": [
            ["2026-08-01", 1500, 4500],
            ["2026-08-02", 2000, 6000],
        ],
    }
    formatted = format_analytics_report(raw_api_response)
    assert len(formatted) == 2
    assert formatted[0] == {"day": "2026-08-01", "views": 1500, "estimatedMinutesWatched": 4500}
    assert formatted[1] == {"day": "2026-08-02", "views": 2000, "estimatedMinutesWatched": 6000}


def test_summarize_analytics():
    records = [
        {
            "day": "2026-08-01",
            "views": 1000,
            "estimatedMinutesWatched": 120,
            "subscribersGained": 10,
            "subscribersLost": 2,
            "impressions": 10000,
        },
        {
            "day": "2026-08-02",
            "views": 1500,
            "estimatedMinutesWatched": 180,
            "subscribersGained": 15,
            "subscribersLost": 3,
            "impressions": 15000,
        },
    ]
    summary = summarize_analytics(records)
    assert summary["total_records"] == 2
    assert summary["total_views"] == 2500
    assert summary["total_estimatedMinutesWatched"] == 300
    assert summary["total_watch_time_hours"] == 5.0
    assert summary["total_subscribersGained"] == 25
    assert summary["total_subscribersLost"] == 5
    assert summary["net_subscribers"] == 20
    assert summary["overall_ctr_percentage"] == 10.0


def test_parse_iso8601_duration():
    assert parse_iso8601_duration("PT1H2M30S") == "1:02:30"
    assert parse_iso8601_duration("PT15M45S") == "15:45"
    assert parse_iso8601_duration("PT59S") == "0:59"
    assert parse_iso8601_duration("PT12H0M0S") == "12:00:00"


def test_parse_date_range():
    start, end = YouTubeStudioClient._parse_date_range(time_period="7d")
    assert len(start) == 10
    assert len(end) == 10
    assert start < end

    start_custom, end_custom = YouTubeStudioClient._parse_date_range(
        start_date="2026-01-01", end_date="2026-01-31"
    )
    assert start_custom == "2026-01-01"
    assert end_custom == "2026-01-31"


def test_summarize_analytics_uses_api_ctr_when_available():
    records = [
        {"views": 200, "impressions": 10000, "impressionClickThroughRate": 1.0},
        {"views": 300, "impressions": 15000, "impressionClickThroughRate": 2.0},
    ]

    summary = summarize_analytics(records)

    assert summary["overall_ctr_percentage"] == 1.6


def test_parse_date_range_rejects_unsupported_period():
    with pytest.raises(ValueError, match="Unsupported time period"):
        YouTubeStudioClient._parse_date_range(time_period="not-a-real-period")


def test_get_analytics_by_dimension_rejects_invalid_dimension():
    client = YouTubeStudioClient.__new__(YouTubeStudioClient)
    with pytest.raises(ValueError, match="Unsupported dimension"):
        YouTubeStudioClient.get_analytics_by_dimension(client, dimension="totally_invalid_dimension")


def test_get_video_comments_rejects_invalid_order():
    client = YouTubeStudioClient.__new__(YouTubeStudioClient)
    with pytest.raises(ValueError, match="Unsupported order"):
        YouTubeStudioClient.get_video_comments(client, video_id="abc123", order="bad-order")

"""Formatters and helpers for YouTube API responses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def format_analytics_report(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Converts the raw column-and-row YouTube Analytics API response into a list of dicts.

    YouTube Analytics API returns:
    {
      "columnHeaders": [{"name": "day", "columnType": "DIMENSION"}, {"name": "views", "columnType": "METRIC"}],
      "rows": [["2026-08-01", 1234], ["2026-08-02", 5678]]
    }
    This turns it into:
    [
      {"day": "2026-08-01", "views": 1234},
      {"day": "2026-08-02", "views": 5678}
    ]
    """
    column_headers = response.get("columnHeaders", [])
    col_names = [col.get("name") for col in column_headers]
    rows = response.get("rows", [])

    results = []
    for row in rows:
        record = {}
        for idx, col_name in enumerate(col_names):
            if idx < len(row):
                record[col_name] = row[idx]
        results.append(record)

    return results


def summarize_analytics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates totals and averages from formatted analytics records."""
    if not records:
        return {"total_records": 0}

    totals: Dict[str, Any] = {"total_records": len(records)}
    metric_keys = [
        "views",
        "estimatedMinutesWatched",
        "subscribersGained",
        "subscribersLost",
        "likes",
        "shares",
        "comments",
        "impressions",
        "dislikes",
    ]

    for key in metric_keys:
        if any(key in r for r in records):
            val_sum = sum(float(r.get(key, 0) or 0) for r in records)
            totals[f"total_{key}"] = int(val_sum) if val_sum.is_integer() else round(val_sum, 2)

    # Calculate watch time in hours
    if "total_estimatedMinutesWatched" in totals:
        totals["total_watch_time_hours"] = round(
            totals["total_estimatedMinutesWatched"] / 60.0, 2
        )

    # Net subscriber growth
    if "total_subscribersGained" in totals or "total_subscribersLost" in totals:
        gained = totals.get("total_subscribersGained", 0)
        lost = totals.get("total_subscribersLost", 0)
        totals["net_subscribers"] = gained - lost

    # Average CTR if impressions and views exist
    if totals.get("total_impressions", 0) > 0 and totals.get("total_views", 0) > 0:
        totals["overall_ctr_percentage"] = round(
            (totals["total_views"] / totals["total_impressions"]) * 100.0, 2
        )

    return totals


def parse_iso8601_duration(duration_str: Optional[str]) -> str:
    """Converts ISO 8601 duration (e.g. PT1H12M34S, PT4M20S) to readable HH:MM:SS or MM:SS."""
    if not duration_str or not duration_str.startswith("PT"):
        return duration_str or "00:00"

    duration = duration_str[2:]
    hours = 0
    minutes = 0
    seconds = 0

    if "H" in duration:
        h_part, duration = duration.split("H")
        hours = int(h_part)
    if "M" in duration:
        m_part, duration = duration.split("M")
        minutes = int(m_part)
    if "S" in duration:
        s_part = duration.replace("S", "")
        seconds = int(s_part)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"

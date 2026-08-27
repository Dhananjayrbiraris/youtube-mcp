"""YouTube Studio & Channel Analytics MCP Server.

Provides tools for AI assistants to inspect, analyze, and diagnose YouTube channels,
video performance, audience demographics, and studio analytics.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

try:
    # Modern MCP Python SDK v2.x
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer(
        "youtube-studio-mcp",
        instructions=(
            "You are connected to the YouTube Studio & Channel Analytics MCP Server. "
            "Use this server to fetch your channel's metrics, audience retention, "
            "traffic source breakdowns, top-performing videos, comments, and video metadata."
        ),
    )
except ImportError:
    # MCP Python SDK v1.x fallback
    from mcp.server.fastmcp import FastMCP  # type: ignore
    mcp = FastMCP(
        "youtube-studio-mcp",
        instructions=(
            "You are connected to the YouTube Studio & Channel Analytics MCP Server. "
            "Use this server to fetch your channel's metrics, audience retention, "
            "traffic source breakdowns, top-performing videos, comments, and video metadata."
        ),
    )

from src.youtube_client import YouTubeStudioClient

_client: Optional[YouTubeStudioClient] = None


def get_client() -> YouTubeStudioClient:
    """Lazily initializes and returns the YouTube client."""
    global _client
    if _client is None:
        _client = YouTubeStudioClient()
    return _client


@mcp.tool()
def get_channel_overview() -> str:
    """Fetches high-level metadata and lifetime statistics for your YouTube channel.

    Returns channel title, handle, subscriber count, total lifetime views,
    video count, creation date, topic categories, and channel description.
    """
    client = get_client()
    data = client.get_channel_overview()
    return json.dumps(data, indent=2)


@mcp.tool()
def get_channel_analytics(
    time_period: Optional[str] = "28d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dimensions: Optional[str] = "day",
) -> str:
    """Queries core YouTube Studio channel analytics for a specified timeframe.

    Args:
        time_period: Preset time period ('7d', '28d', '90d', '365d', 'last_month'). Defaults to '28d'.
        start_date: Explicit start date in YYYY-MM-DD format (overrides time_period if both start & end are provided).
        end_date: Explicit end date in YYYY-MM-DD format.
        dimensions: Dimension to group by, e.g. 'day' (default) or None for a single aggregate row.

    Returns:
        Summary metrics (total views, watch time hours, avg view duration,
        subscribers gained/lost, net growth, likes, shares, comments, impressions, CTR)
        and daily time-series data points.
    """
    client = get_client()
    data = client.get_channel_analytics(
        start_date=start_date,
        end_date=end_date,
        time_period=time_period,
        dimensions=dimensions,
    )
    return json.dumps(data, indent=2)


@mcp.tool()
def get_analytics_by_dimension(
    dimension: str,
    time_period: Optional[str] = "28d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_results: int = 20,
) -> str:
    """Fetches channel analytics broken down by a specific dimension.

    Args:
        dimension: The dimension to analyze. Supported values:
                   - 'trafficSource' (YouTube search, suggested videos, browse features, external, etc.)
                   - 'deviceType' (mobile phone, computer, TV, tablet)
                   - 'country' (top geographic viewer locations)
                   - 'ageGroup' (demographics: 18-24, 25-34, 35-44, etc.)
                   - 'gender' (viewer gender percentage)
                   - 'operatingSystem' (Android, Windows, iOS, etc.)
                   - 'day' or 'month'
        time_period: Preset time period ('7d', '28d', '90d', '365d', 'last_month'). Defaults to '28d'.
        start_date: Optional explicit start date (YYYY-MM-DD).
        end_date: Optional explicit end date (YYYY-MM-DD).
        max_results: Maximum number of rows to return (default: 20).

    Returns:
        A ranked list of metrics for each dimension value.
    """
    client = get_client()
    data = client.get_analytics_by_dimension(
        dimension=dimension,
        start_date=start_date,
        end_date=end_date,
        time_period=time_period,
        max_results=max_results,
    )
    return json.dumps(data, indent=2)


@mcp.tool()
def get_top_performing_videos(
    time_period: Optional[str] = "28d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    order_by: str = "views",
    max_results: int = 10,
) -> str:
    """Identifies and ranks your top-performing videos within a time period.

    Args:
        time_period: Preset time period ('7d', '28d', '90d', '365d', 'last_month'). Defaults to '28d'.
        start_date: Optional explicit start date (YYYY-MM-DD).
        end_date: Optional explicit end date (YYYY-MM-DD).
        order_by: Metric to rank by: 'views', 'estimatedMinutesWatched', 'subscribersGained', or 'likes'.
        max_results: Number of top videos to return (default: 10).

    Returns:
        Ranked list of videos with title, duration, period views, watch time,
        subscribers gained, and lifetime views.
    """
    client = get_client()
    data = client.get_top_performing_videos(
        start_date=start_date,
        end_date=end_date,
        time_period=time_period,
        order_by=order_by,
        max_results=max_results,
    )
    return json.dumps(data, indent=2)


@mcp.tool()
def get_video_analytics(
    video_id: str,
    time_period: Optional[str] = "28d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """Performs deep-dive analytics on a single specific video.

    Args:
        video_id: The 11-character YouTube video ID (e.g. 'dQw4w9WgXcQ').
        time_period: Preset time period ('7d', '28d', '90d', '365d', 'last_month'). Defaults to '28d'.
        start_date: Optional explicit start date (YYYY-MM-DD).
        end_date: Optional explicit end date (YYYY-MM-DD).

    Returns:
        Video metadata, daily trajectory, total period views & watch time,
        and traffic source breakdown for this specific video.
    """
    client = get_client()
    data = client.get_video_analytics(
        video_id=video_id,
        start_date=start_date,
        end_date=end_date,
        time_period=time_period,
    )
    return json.dumps(data, indent=2)


@mcp.tool()
def list_channel_videos(
    max_results: int = 25,
    page_token: Optional[str] = None,
) -> str:
    """Lists your channel's uploaded videos in reverse chronological order.

    Args:
        max_results: Number of videos to retrieve (max 50 per page).
        page_token: Optional page token for pagination.

    Returns:
        List of videos with video ID, title, publish date, duration,
        views, likes, comments, and privacy status.
    """
    client = get_client()
    data = client.list_channel_videos(
        max_results=max_results,
        page_token=page_token,
    )
    return json.dumps(data, indent=2)


@mcp.tool()
def get_video_details(video_ids: str) -> str:
    """Fetches full metadata, description, tags, and statistics for specified video IDs.

    Args:
        video_ids: Comma-separated list of YouTube video IDs (e.g. 'vid1,vid2').

    Returns:
        Complete video details including title, description, tags, topic categories,
        view/like/comment counts, duration, and content settings.
    """
    client = get_client()
    data = client.get_video_details(video_ids=video_ids)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_video_comments(
    video_id: Optional[str] = None,
    max_results: int = 20,
    order: str = "relevance",
) -> str:
    """Fetches comment threads and audience discussions for a video or the whole channel.

    Args:
        video_id: Optional specific YouTube video ID. If omitted, retrieves recent comments across the channel.
        max_results: Number of comment threads to fetch (max 100).
        order: Sort order: 'relevance' (top comments) or 'time' (newest first).

    Returns:
        List of comments with author, comment text, likes, timestamp, and sample replies.
    """
    client = get_client()
    data = client.get_video_comments(
        video_id=video_id,
        max_results=max_results,
        order=order,
    )
    return json.dumps(data, indent=2)


def main() -> None:
    """Entrypoint to run the MCP server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()

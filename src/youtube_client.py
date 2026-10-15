"""YouTube API client integrating Data API v3 and YouTube Analytics API v2."""

from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from src.auth import load_credentials
from src.formatters import (
    format_analytics_report,
    parse_iso8601_duration,
    summarize_analytics,
)
from src.logging_utils import configure_logging

logger = configure_logging()


class YouTubeStudioClient:
    """High-level client for YouTube Studio and Channel analytics."""

    SUPPORTED_TIME_PERIODS = {"7d", "28d", "90d", "365d", "1y", "last_month"}
    SUPPORTED_DIMENSIONS = {
        "traffic_source": "insightTrafficSourceType",
        "trafficsource": "insightTrafficSourceType",
        "insighttrafficsourcetype": "insightTrafficSourceType",
        "device_type": "deviceType",
        "devicetype": "deviceType",
        "country": "country",
        "geo": "country",
        "age_group": "ageGroup",
        "agegroup": "ageGroup",
        "gender": "gender",
        "operating_system": "operatingSystem",
        "operatingsystem": "operatingSystem",
        "day": "day",
        "month": "month",
    }
    SUPPORTED_ORDER_BY = {
        "views": "views",
        "estimatedminuteswatched": "estimatedMinutesWatched",
        "estimated_minutes_watched": "estimatedMinutesWatched",
        "subscribersgained": "subscribersGained",
        "subscribers_gained": "subscribersGained",
        "likes": "likes",
    }
    SUPPORTED_COMMENT_ORDERS = {"relevance", "time"}

    def __init__(self) -> None:
        self._credentials = load_credentials()
        self.data_api: Resource = build(
            "youtube",
            "v3",
            credentials=self._credentials,
        )
        self.analytics_api: Resource = build(
            "youtubeAnalytics",
            "v2",
            credentials=self._credentials,
        )
        self._channel_id: Optional[str] = None
        self._uploads_playlist_id: Optional[str] = None

    @staticmethod
    def _validate_time_period(time_period: Optional[str]) -> str:
        """Raises a clear error for unsupported date shortcuts."""
        normalized = (time_period or "28d").lower().strip()
        if normalized not in YouTubeStudioClient.SUPPORTED_TIME_PERIODS:
            supported = ", ".join(sorted(YouTubeStudioClient.SUPPORTED_TIME_PERIODS))
            raise ValueError(
                f"Unsupported time period '{time_period}'. Supported values: {supported}."
            )
        return normalized

    @staticmethod
    def _validate_max_results(value: int, *, field_name: str, maximum: int = 100) -> int:
        """Ensures max_results inputs are within a sane range."""
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"{field_name} must be an integer greater than 0.")
        if value > maximum:
            raise ValueError(f"{field_name} must be <= {maximum}.")
        return value

    @staticmethod
    def _normalize_dimension(dimension: str) -> str:
        """Maps public aliases to the Google Analytics API dimension names."""
        if not dimension or not str(dimension).strip():
            raise ValueError("Dimension is required.")

        normalized = str(dimension).strip().lower()
        if normalized not in YouTubeStudioClient.SUPPORTED_DIMENSIONS:
            allowed = ", ".join(sorted(YouTubeStudioClient.SUPPORTED_DIMENSIONS))
            raise ValueError(
                f"Unsupported dimension '{dimension}'. "
                f"Allowed values: {allowed}."
            )
        return YouTubeStudioClient.SUPPORTED_DIMENSIONS[normalized]

    @staticmethod
    def _normalize_order(order: str, *, allowed: Dict[str, str], field_name: str) -> str:
        """Normalizes a user-provided sort order and validates it."""
        if not order or not str(order).strip():
            raise ValueError(f"{field_name} is required.")
        normalized = str(order).strip().lower()
        if normalized not in allowed:
            allowed_values = ", ".join(sorted(allowed))
            raise ValueError(
                f"Unsupported {field_name} '{order}'. "
                f"Allowed values: {allowed_values}."
            )
        return allowed[normalized]

    def _execute_with_retry(self, request: Any, *, retries: int = 3) -> Any:
        """Retries transient Google API failures before surfacing the error."""
        for attempt in range(retries + 1):
            try:
                logger.debug("Executing YouTube API request (attempt=%s)", attempt + 1)
                return request.execute()
            except HttpError as exc:
                status = getattr(exc.resp, "status", None)
                if status not in {429, 500, 502, 503, 504} or attempt >= retries:
                    logger.exception("YouTube API request failed with status=%s", status)
                    raise
                logger.warning(
                    "Transient YouTube API failure detected (status=%s); retrying in %ss",
                    status,
                    2 ** attempt,
                )
                time.sleep(2 ** attempt)

    def _get_channel_info_cached(self) -> Tuple[str, str]:
        """Return cached channel and uploads metadata for the authenticated account."""
        if self._channel_id and self._uploads_playlist_id:
            return self._channel_id, self._uploads_playlist_id

        res = (
            self.data_api.channels()
            .list(mine=True, part="id,contentDetails")
            .execute()
        )
        items = res.get("items", [])
        if not items:
            raise RuntimeError("No YouTube channel found for the authenticated Google account.")

        self._channel_id = items[0]["id"]
        self._uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return self._channel_id, self._uploads_playlist_id

    @staticmethod
    def _parse_date_range(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_period: Optional[str] = "28d",
    ) -> Tuple[str, str]:
        """Resolves dates into YYYY-MM-DD format.

        Supports shortcuts like '7d', '28d', '90d', '365d', 'last_month', or explicit dates.
        """
        today = date.today()
        # YouTube Analytics data usually has a 1-2 day processing lag
        yesterday = today - timedelta(days=1)

        if start_date and end_date:
            return start_date, end_date

        end_str = end_date or yesterday.isoformat()
        period = YouTubeStudioClient._validate_time_period(time_period)

        if period == "7d":
            start_dt = yesterday - timedelta(days=7)
        elif period == "28d":
            start_dt = yesterday - timedelta(days=28)
        elif period == "90d":
            start_dt = yesterday - timedelta(days=90)
        elif period == "365d" or period == "1y":
            start_dt = yesterday - timedelta(days=365)
        elif period == "last_month":
            # First day of previous month to last day of previous month
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            start_dt = last_month_end.replace(day=1)
            end_str = last_month_end.isoformat()

        start_str = start_date or start_dt.isoformat()
        return start_str, end_str

    def get_channel_overview(self) -> Dict[str, Any]:
        """Fetches comprehensive channel metadata, lifetime statistics, and branding settings."""
        res = (
            self.data_api.channels()
            .list(
                mine=True,
                part="snippet,contentDetails,statistics,brandingSettings,topicDetails,status",
            )
            .execute()
        )
        items = res.get("items", [])
        if not items:
            raise RuntimeError("No YouTube channel found for the authenticated account.")

        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        branding = item.get("brandingSettings", {})

        return {
            "channel_id": item.get("id"),
            "title": snippet.get("title"),
            "custom_url": snippet.get("customUrl"),
            "handle": snippet.get("customUrl"),
            "description": snippet.get("description"),
            "published_at": snippet.get("publishedAt"),
            "country": snippet.get("country"),
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
            "hidden_subscriber_count": stats.get("hiddenSubscriberCount", False),
            "topic_categories": item.get("topicDetails", {}).get("topicCategories", []),
            "keywords": branding.get("channel", {}).get("keywords", ""),
            "thumbnails": snippet.get("thumbnails", {}),
        }

    def get_channel_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_period: Optional[str] = "28d",
        metrics: Optional[str] = None,
        dimensions: Optional[str] = "day",
    ) -> Dict[str, Any]:
        """Queries YouTube Analytics API for core channel performance metrics."""
        start_str, end_str = self._parse_date_range(start_date, end_date, time_period)

        default_metrics = (
            "views,estimatedMinutesWatched,averageViewDuration,"
            "subscribersGained,subscribersLost,likes,shares,comments,"
            "impressions,impressionClickThroughRate"
        )
        query_metrics = metrics or default_metrics

        if dimensions is not None:
            normalized_dimension = str(dimensions).strip().lower()
            if normalized_dimension not in {"day", "month"}:
                raise ValueError("Unsupported dimensions value. Allowed values: day, month.")

        kwargs: Dict[str, Any] = {
            "ids": "channel==MINE",
            "startDate": start_str,
            "endDate": end_str,
            "metrics": query_metrics,
        }
        if dimensions:
            kwargs["dimensions"] = normalized_dimension
            if normalized_dimension == "day":
                kwargs["sort"] = "day"

        response = self._execute_with_retry(self.analytics_api.reports().query(**kwargs))
        records = format_analytics_report(response)
        summary = summarize_analytics(records)

        return {
            "start_date": start_str,
            "end_date": end_str,
            "time_period": time_period,
            "summary": summary,
            "data_points": records,
        }

    def get_analytics_by_dimension(
        self,
        dimension: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_period: Optional[str] = "28d",
        metrics: Optional[str] = None,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """Fetches analytics broken down by a specific dimension.

        Supported dimension aliases:
        - trafficSource (insightTrafficSourceType)
        - deviceType (deviceType)
        - country (country)
        - ageGroup (ageGroup)
        - gender (gender)
        - operatingSystem (operatingSystem)
        - day (day)
        - month (month)
        """
        start_str, end_str = self._parse_date_range(start_date, end_date, time_period)
        self._validate_max_results(max_results, field_name="max_results", maximum=50)
        api_dimension = self._normalize_dimension(dimension)

        # Dimension-specific metrics configuration
        if api_dimension in ("ageGroup", "gender"):
            query_metrics = metrics or "viewerPercentage"
            sort = "-viewerPercentage"
        else:
            query_metrics = metrics or "views,estimatedMinutesWatched,subscribersGained,likes"
            sort = "-views"

        kwargs: Dict[str, Any] = {
            "ids": "channel==MINE",
            "startDate": start_str,
            "endDate": end_str,
            "metrics": query_metrics,
            "dimensions": api_dimension,
            "sort": sort,
            "maxResults": max_results,
        }

        # Age and gender require specific dimensions
        if api_dimension == "ageGroup":
            kwargs["dimensions"] = "ageGroup"
        elif api_dimension == "gender":
            kwargs["dimensions"] = "gender"

        response = self._execute_with_retry(self.analytics_api.reports().query(**kwargs))
        records = format_analytics_report(response)

        return {
            "dimension": api_dimension,
            "start_date": start_str,
            "end_date": end_str,
            "total_items": len(records),
            "results": records,
        }

    def get_top_performing_videos(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_period: Optional[str] = "28d",
        max_results: int = 10,
        order_by: str = "views",
    ) -> Dict[str, Any]:
        """Identifies top-performing videos within the specified period."""
        start_str, end_str = self._parse_date_range(start_date, end_date, time_period)
        self._validate_max_results(max_results, field_name="max_results", maximum=50)
        order_by = self._normalize_order(
            order_by,
            allowed=self.SUPPORTED_ORDER_BY,
            field_name="order_by",
        )

        sort_metric = f"-{order_by}"

        response = self._execute_with_retry(
            self.analytics_api.reports()
            .query(
                ids="channel==MINE",
                startDate=start_str,
                endDate=end_str,
                metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes,comments",
                dimensions="video",
                sort=sort_metric,
                maxResults=max_results,
            )
        )

        records = format_analytics_report(response)
        video_ids = [r["video"] for r in records if "video" in r]

        # Fetch video snippets and titles
        video_details_map = {}
        if video_ids:
            videos_res = (
                self.data_api.videos()
                .list(id=",".join(video_ids), part="snippet,contentDetails,statistics")
                .execute()
            )
            for v in videos_res.get("items", []):
                vid_id = v["id"]
                snippet = v.get("snippet", {})
                content = v.get("contentDetails", {})
                stats = v.get("statistics", {})
                video_details_map[vid_id] = {
                    "title": snippet.get("title"),
                    "published_at": snippet.get("publishedAt"),
                    "duration": parse_iso8601_duration(content.get("duration")),
                    "lifetime_views": int(stats.get("viewCount", 0)),
                    "lifetime_likes": int(stats.get("likeCount", 0)),
                    "lifetime_comments": int(stats.get("commentCount", 0)),
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                }

        # Merge details into records
        merged = []
        for r in records:
            vid_id = r.get("video")
            details = video_details_map.get(vid_id, {})
            merged.append({
                "video_id": vid_id,
                "video_url": f"https://www.youtube.com/watch?v={vid_id}" if vid_id else None,
                "title": details.get("title", "Unknown Title"),
                "published_at": details.get("publishedAt"),
                "duration": details.get("duration"),
                "period_views": r.get("views"),
                "period_watch_time_minutes": r.get("estimatedMinutesWatched"),
                "period_watch_time_hours": round((r.get("estimatedMinutesWatched") or 0) / 60.0, 2),
                "avg_view_duration_sec": r.get("averageViewDuration"),
                "subscribers_gained": r.get("subscribersGained"),
                "period_likes": r.get("likes"),
                "period_comments": r.get("comments"),
                "lifetime_views": details.get("lifetime_views"),
            })

        return {
            "start_date": start_str,
            "end_date": end_str,
            "time_period": time_period,
            "sorted_by": order_by,
            "top_videos": merged,
        }

    def get_video_analytics(
        self,
        video_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_period: Optional[str] = "28d",
    ) -> Dict[str, Any]:
        """Provide in-depth analytics for a single video and its traffic."""
        start_str, end_str = self._parse_date_range(start_date, end_date, time_period)
        if not video_id or not str(video_id).strip():
            raise ValueError("video_id is required.")

        # 1. Video daily performance
        daily_res = self._execute_with_retry(
            self.analytics_api.reports()
            .query(
                ids="channel==MINE",
                filters=f"video=={video_id}",
                startDate=start_str,
                endDate=end_str,
                metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,shares,comments",
                dimensions="day",
                sort="day",
            )
        )
        daily_records = format_analytics_report(daily_res)
        summary = summarize_analytics(daily_records)

        # 2. Video traffic sources
        traffic_res = self._execute_with_retry(
            self.analytics_api.reports()
            .query(
                ids="channel==MINE",
                filters=f"video=={video_id}",
                startDate=start_str,
                endDate=end_str,
                metrics="views,estimatedMinutesWatched",
                dimensions="insightTrafficSourceType",
                sort="-views",
            )
        )
        traffic_records = format_analytics_report(traffic_res)

        # 3. Video metadata & snippet
        video_meta = self.get_video_details([video_id])
        meta = video_meta[0] if video_meta else {}

        return {
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "metadata": meta,
            "start_date": start_str,
            "end_date": end_str,
            "summary": summary,
            "traffic_sources": traffic_records,
            "daily_trends": daily_records,
        }

    def list_channel_videos(
        self,
        max_results: int = 25,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List uploaded channel videos with current statistics and privacy status."""
        _, uploads_id = self._get_channel_info_cached()

        kwargs: Dict[str, Any] = {
            "playlistId": uploads_id,
            "part": "snippet,contentDetails,status",
            "maxResults": min(max_results, 50),
        }
        if page_token:
            kwargs["pageToken"] = page_token

        playlist_res = self.data_api.playlistItems().list(**kwargs).execute()
        items = playlist_res.get("items", [])
        next_page = playlist_res.get("nextPageToken")
        total_results = playlist_res.get("pageInfo", {}).get("totalResults", len(items))

        video_ids = [it["contentDetails"]["videoId"] for it in items if "contentDetails" in it]

        # Fetch detailed stats for all videos in this batch
        stats_map = {}
        if video_ids:
            videos_res = (
                self.data_api.videos()
                .list(id=",".join(video_ids), part="contentDetails,statistics,status")
                .execute()
            )
            for v in videos_res.get("items", []):
                stats_map[v["id"]] = {
                    "duration": parse_iso8601_duration(v.get("contentDetails", {}).get("duration")),
                    "views": int(v.get("statistics", {}).get("viewCount", 0)),
                    "likes": int(v.get("statistics", {}).get("likeCount", 0)),
                    "comments": int(v.get("statistics", {}).get("commentCount", 0)),
                    "privacy_status": v.get("status", {}).get("privacyStatus"),
                }

        results = []
        for it in items:
            vid_id = it["contentDetails"]["videoId"]
            snippet = it.get("snippet", {})
            st = stats_map.get(vid_id, {})

            results.append({
                "video_id": vid_id,
                "video_url": f"https://www.youtube.com/watch?v={vid_id}",
                "title": snippet.get("title"),
                "description": (
                    snippet.get("description", "")[:200]
                    + ("..." if len(snippet.get("description", "")) > 200 else "")
                ),
                "published_at": snippet.get("publishedAt"),
                "duration": st.get("duration"),
                "views": st.get("views", 0),
                "likes": st.get("likes", 0),
                "comments": st.get("comments", 0),
                "privacy_status": st.get("privacy_status"),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            })

        return {
            "total_uploads": total_results,
            "next_page_token": next_page,
            "videos": results,
        }

    def get_video_details(self, video_ids: Union[List[str], str]) -> List[Dict[str, Any]]:
        """Fetch metadata and statistics for the specified YouTube video IDs."""
        if isinstance(video_ids, str):
            ids_list = [v.strip() for v in video_ids.split(",") if v.strip()]
        else:
            ids_list = video_ids

        if not ids_list:
            return []

        res = (
            self.data_api.videos()
            .list(
                id=",".join(ids_list),
                part="snippet,contentDetails,statistics,status,topicDetails",
            )
            .execute()
        )

        results = []
        for item in res.get("items", []):
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            stats = item.get("statistics", {})
            status = item.get("status", {})

            results.append({
                "video_id": item["id"],
                "video_url": f"https://www.youtube.com/watch?v={item['id']}",
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId"),
                "published_at": snippet.get("publishedAt"),
                "duration": parse_iso8601_duration(content.get("duration")),
                "dimension": content.get("dimension"),  # 2d or 3d
                "definition": content.get("definition"),  # hd or sd
                "caption": content.get("caption"),  # true/false
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "privacy_status": status.get("privacyStatus"),
                "made_for_kids": status.get("madeForKids", False),
                "topic_categories": item.get("topicDetails", {}).get("topicCategories", []),
            })

        return results

    def get_video_comments(
        self,
        video_id: Optional[str] = None,
        max_results: int = 20,
        order: str = "relevance",
    ) -> Dict[str, Any]:
        """Retrieve top comment threads and replies for a video or channel."""
        self._validate_max_results(max_results, field_name="max_results", maximum=100)
        normalized_order = self._normalize_order(
            order,
            allowed={k: k for k in self.SUPPORTED_COMMENT_ORDERS},
            field_name="order",
        )

        kwargs: Dict[str, Any] = {
            "part": "snippet,replies",
            "maxResults": max_results,
            "order": normalized_order,
        }

        if video_id:
            kwargs["videoId"] = video_id
        else:
            kwargs["allThreadsRelatedToChannelId"], _ = self._get_channel_info_cached()

        res = self._execute_with_retry(self.data_api.commentThreads().list(**kwargs))
        items = res.get("items", [])

        comments = []
        for item in items:
            top_snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            total_reply_count = item.get("snippet", {}).get("totalReplyCount", 0)

            replies = []
            if "replies" in item:
                for rep in item["replies"].get("comments", []):
                    rep_snippet = rep.get("snippet", {})
                    replies.append({
                        "author": rep_snippet.get("authorDisplayName"),
                        "text": rep_snippet.get("textDisplay"),
                        "like_count": rep_snippet.get("likeCount", 0),
                        "published_at": rep_snippet.get("publishedAt"),
                    })

            comments.append({
                "comment_id": item.get("id"),
                "video_id": item.get("snippet", {}).get("videoId"),
                "author": top_snippet.get("authorDisplayName"),
                "author_channel_url": top_snippet.get("authorChannelUrl"),
                "text": top_snippet.get("textDisplay"),
                "like_count": top_snippet.get("likeCount", 0),
                "published_at": top_snippet.get("publishedAt"),
                "updated_at": top_snippet.get("updatedAt"),
                "reply_count": total_reply_count,
                "sample_replies": replies,
            })

        return {
            "target": f"video:{video_id}" if video_id else "channel",
            "total_retrieved": len(comments),
            "comments": comments,
        }

"""
YouTube Data API v3 操作モジュール

戦略:
- search.list (100ユニット) は使わない
- channels.list (1ユニット) でチャンネル情報取得
- playlistItems.list (1ユニット) でアップロード用プレイリスト経由で新着動画取得
- videos.list (1ユニット) で動画詳細（再生数等）取得
- 30チャンネルで1日あたり約100ユニット以下に収まる設計
"""

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    pass


class QuotaExceededError(YouTubeAPIError):
    pass


class YouTubeAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
        if not self.api_key:
            raise YouTubeAPIError("YOUTUBE_API_KEY が設定されていません")
        self._quota_used = 0

    @property
    def quota_used(self) -> int:
        return self._quota_used

    def _request(self, endpoint: str, params: dict, cost: int = 1) -> dict:
        """YouTube API にリクエストを送信する"""
        params["key"] = self.api_key
        url = f"{YOUTUBE_API_BASE}/{endpoint}"

        try:
            resp = requests.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            raise YouTubeAPIError(f"API リクエスト失敗: {e}")

        if resp.status_code == 403:
            data = resp.json()
            errors = data.get("error", {}).get("errors", [])
            for err in errors:
                if err.get("reason") == "quotaExceeded":
                    raise QuotaExceededError("YouTube API クォータ超過")
            raise YouTubeAPIError(f"API 403 エラー: {data}")

        if resp.status_code != 200:
            raise YouTubeAPIError(
                f"API エラー (HTTP {resp.status_code}): {resp.text[:500]}"
            )

        self._quota_used += cost
        return resp.json()

    def resolve_channel_id(self, handle: str) -> Optional[str]:
        """
        ハンドル (@xxx) からチャンネルIDを解決する。
        channels.list の forHandle パラメータを使用（1ユニット）。
        """
        clean_handle = handle.lstrip("@")
        data = self._request(
            "channels",
            {"part": "id", "forHandle": clean_handle},
            cost=1,
        )
        items = data.get("items", [])
        if items:
            return items[0]["id"]
        logger.warning(f"チャンネルが見つかりません: {handle}")
        return None

    def get_channel_info(self, channel_id: str) -> Optional[dict]:
        """
        チャンネルの基本情報を取得する。
        アップロード用プレイリストIDも含む。
        """
        data = self._request(
            "channels",
            {
                "part": "contentDetails,statistics,snippet",
                "id": channel_id,
            },
            cost=1,
        )
        items = data.get("items", [])
        if not items:
            return None

        item = items[0]
        uploads_playlist = (
            item.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
        return {
            "channel_id": channel_id,
            "title": item.get("snippet", {}).get("title", ""),
            "subscriber_count": int(
                item.get("statistics", {}).get("subscriberCount", 0)
            ),
            "uploads_playlist_id": uploads_playlist,
        }

    def get_recent_videos(
        self, uploads_playlist_id: str, max_results: int = 10
    ) -> list[dict]:
        """
        アップロード用プレイリストから最新の動画IDリストを取得する。
        playlistItems.list = 1ユニット/リクエスト。
        """
        data = self._request(
            "playlistItems",
            {
                "part": "snippet",
                "playlistId": uploads_playlist_id,
                "maxResults": max_results,
            },
            cost=1,
        )
        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            if video_id:
                videos.append(
                    {
                        "video_id": video_id,
                        "title": snippet.get("title", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "channel_title": snippet.get("channelTitle", ""),
                    }
                )
        return videos

    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """
        動画の詳細情報（再生数、いいね数、コメント数）を一括取得する。
        videos.list = 1ユニット/リクエスト。最大50件まで一括取得可能。
        """
        if not video_ids:
            return []

        results = []
        # 50件ずつバッチ処理
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            data = self._request(
                "videos",
                {
                    "part": "statistics,snippet",
                    "id": ",".join(batch),
                },
                cost=1,
            )
            for item in data.get("items", []):
                stats = item.get("statistics", {})
                snippet = item.get("snippet", {})
                results.append(
                    {
                        "video_id": item["id"],
                        "title": snippet.get("title", ""),
                        "channel_title": snippet.get("channelTitle", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "view_count": int(stats.get("viewCount", 0)),
                        "like_count": int(stats.get("likeCount", 0)),
                        "comment_count": int(stats.get("commentCount", 0)),
                    }
                )
        return results

    def get_channel_recent_video_stats(
        self, uploads_playlist_id: str, max_results: int = 30
    ) -> list[dict]:
        """
        チャンネルの直近N本の動画の再生数を取得する。
        平均再生数の計算に使用。
        2リクエスト（playlistItems + videos）= 2ユニット。
        """
        # まず動画IDリストを取得
        videos = self.get_recent_videos(uploads_playlist_id, max_results)
        if not videos:
            return []

        video_ids = [v["video_id"] for v in videos]
        return self.get_video_details(video_ids)

    def get_new_videos_since(
        self, uploads_playlist_id: str, since: datetime, max_results: int = 10
    ) -> list[dict]:
        """
        指定日時以降の新着動画を取得し、詳細情報付きで返す。
        """
        videos = self.get_recent_videos(uploads_playlist_id, max_results)

        # since 以降のものだけフィルタ
        recent = []
        for v in videos:
            try:
                pub = datetime.fromisoformat(
                    v["published_at"].replace("Z", "+00:00")
                )
                if pub >= since:
                    recent.append(v)
            except (ValueError, KeyError):
                continue

        if not recent:
            return []

        video_ids = [v["video_id"] for v in recent]
        return self.get_video_details(video_ids)

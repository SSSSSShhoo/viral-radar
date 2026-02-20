"""
バズり検知ロジック

バズりスコアの算出:
- チャンネルの直近30本の平均再生数を基準とする
- 公開後の日数を考慮した再生数の伸び率（velocity）で判定
- buzz_score = 動画のvelocity / チャンネル平均velocity

通知条件:
- buzz_score >= 2.0（通常の2倍以上の速度で伸びている）
- かつ view_count >= 10,000（最低再生数フィルタ）
- 1日最大10件まで
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"
STATS_FILE = DATA_DIR / "channel_stats.json"

# バズり検知のしきい値
BUZZ_SCORE_THRESHOLD = 2.0
MIN_VIEW_COUNT = 10_000
MAX_NOTIFICATIONS = 10


@dataclass
class BuzzVideo:
    video_id: str
    title: str
    channel_name: str
    view_count: int
    like_count: int
    comment_count: int
    published_at: str
    days_since_publish: float
    buzz_score: float
    channel_avg_views: float

    @property
    def url(self) -> str:
        return f"https://youtube.com/watch?v={self.video_id}"

    @property
    def days_label(self) -> str:
        d = self.days_since_publish
        if d < 1:
            return "公開当日"
        return f"{d:.0f}日で"


def load_channel_stats() -> dict:
    """チャンネル別の平均再生数キャッシュを読み込む"""
    if not STATS_FILE.exists():
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.warning("channel_stats.json の読み込みに失敗。空データで開始。")
        return {}


def save_channel_stats(stats: dict) -> None:
    """チャンネル別の平均再生数キャッシュを保存する"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def calculate_channel_avg_views(video_stats: list[dict]) -> float:
    """直近N本の動画から平均再生数を計算する"""
    if not video_stats:
        return 0.0
    views = [v.get("view_count", 0) for v in video_stats]
    return sum(views) / len(views)


def calculate_buzz_score(
    video: dict,
    channel_avg_views: float,
    now: datetime | None = None,
) -> float:
    """
    バズりスコアを計算する。

    buzz_score = 動画のvelocity / チャンネル平均velocity
    - velocity = 再生数 / 公開からの日数
    - 平均velocity = 平均再生数 / 7 (7日想定)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    try:
        pub = datetime.fromisoformat(
            video["published_at"].replace("Z", "+00:00")
        )
    except (ValueError, KeyError):
        return 0.0

    days_since_publish = (now - pub).total_seconds() / 86400
    if days_since_publish <= 0:
        days_since_publish = 0.5  # 公開当日は0.5日として計算

    view_count = video.get("view_count", 0)
    velocity = view_count / days_since_publish
    avg_velocity = channel_avg_views / 7 if channel_avg_views > 0 else 0

    if avg_velocity <= 0:
        return 0.0

    return velocity / avg_velocity


def detect_buzz_videos(
    new_videos: list[dict],
    channel_avg_views: float,
    channel_name: str,
    now: datetime | None = None,
) -> list[BuzzVideo]:
    """
    新着動画リストからバズり動画を検知する。
    """
    if now is None:
        now = datetime.now(timezone.utc)

    buzz_videos = []

    for video in new_videos:
        score = calculate_buzz_score(video, channel_avg_views, now)
        view_count = video.get("view_count", 0)

        if score >= BUZZ_SCORE_THRESHOLD and view_count >= MIN_VIEW_COUNT:
            try:
                pub = datetime.fromisoformat(
                    video["published_at"].replace("Z", "+00:00")
                )
                days = (now - pub).total_seconds() / 86400
                if days <= 0:
                    days = 0.5
            except (ValueError, KeyError):
                days = 1.0

            buzz_videos.append(
                BuzzVideo(
                    video_id=video["video_id"],
                    title=video["title"],
                    channel_name=channel_name,
                    view_count=view_count,
                    like_count=video.get("like_count", 0),
                    comment_count=video.get("comment_count", 0),
                    published_at=video.get("published_at", ""),
                    days_since_publish=days,
                    buzz_score=score,
                    channel_avg_views=channel_avg_views,
                )
            )

    return buzz_videos


def rank_and_limit(buzz_videos: list[BuzzVideo]) -> list[BuzzVideo]:
    """バズりスコア順にソートし、上位N件に制限する"""
    sorted_videos = sorted(
        buzz_videos, key=lambda v: v.buzz_score, reverse=True
    )
    return sorted_videos[:MAX_NOTIFICATIONS]

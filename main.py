"""
海外バイラルレーダー メイン実行スクリプト

英語圏の旅行系YouTuberの新着動画を監視し、
異常に伸びている動画を検知してLINEで通知する。

実行フロー:
1. 監視対象チャンネルのリストを読み込む
2. 各チャンネルのチャンネルIDを解決（キャッシュあり）
3. 各チャンネルの平均再生数を取得/更新
4. 直近7日の新着動画を取得
5. バズりスコアを計算
6. しきい値を超えた動画をLINE通知
"""

import logging
import sys
from datetime import datetime, timezone, timedelta

from channels import CHANNELS
from youtube_api import YouTubeAPI, YouTubeAPIError, QuotaExceededError
from buzz_detector import (
    BuzzVideo,
    calculate_channel_avg_views,
    detect_buzz_videos,
    load_channel_stats,
    save_channel_stats,
    rank_and_limit,
)
from notifier import format_notification, send_line_message, LINENotifyError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 新着動画を何日前まで遡って取得するか
LOOKBACK_DAYS = 7

# 平均再生数の更新間隔（日）
STATS_UPDATE_INTERVAL_DAYS = 7


def resolve_channel_ids(api: YouTubeAPI, channels: list[dict], stats: dict) -> None:
    """
    チャンネルIDが未設定のチャンネルについて、ハンドルからIDを解決する。
    解決したIDは channels リストと stats キャッシュの両方に保存する。
    """
    for ch in channels:
        if ch.get("channel_id"):
            continue

        # キャッシュに保存されているか確認
        handle = ch["handle"]
        cached = stats.get(handle, {})
        if cached.get("channel_id"):
            ch["channel_id"] = cached["channel_id"]
            logger.info(f"キャッシュからID取得: {handle} -> {cached['channel_id']}")
            continue

        # APIで解決
        channel_id = api.resolve_channel_id(handle)
        if channel_id:
            ch["channel_id"] = channel_id
            if handle not in stats:
                stats[handle] = {}
            stats[handle]["channel_id"] = channel_id
            logger.info(f"ID解決: {handle} -> {channel_id}")
        else:
            logger.warning(f"ID解決失敗: {handle}")


def get_uploads_playlist_id(api: YouTubeAPI, channel_id: str, stats: dict, handle: str) -> str | None:
    """アップロード用プレイリストIDを取得する（キャッシュあり）"""
    cached = stats.get(handle, {})
    if cached.get("uploads_playlist_id"):
        return cached["uploads_playlist_id"]

    info = api.get_channel_info(channel_id)
    if not info:
        return None

    playlist_id = info.get("uploads_playlist_id")
    if playlist_id:
        if handle not in stats:
            stats[handle] = {}
        stats[handle]["uploads_playlist_id"] = playlist_id

    return playlist_id


def should_update_avg_views(stats: dict, handle: str) -> bool:
    """平均再生数の更新が必要か判定する"""
    cached = stats.get(handle, {})
    last_updated = cached.get("avg_views_updated")
    if not last_updated:
        return True

    try:
        last_dt = datetime.fromisoformat(last_updated)
        now = datetime.now(timezone.utc)
        return (now - last_dt).days >= STATS_UPDATE_INTERVAL_DAYS
    except ValueError:
        return True


def update_channel_avg_views(
    api: YouTubeAPI, uploads_playlist_id: str, stats: dict, handle: str
) -> float:
    """チャンネルの平均再生数を更新する"""
    video_stats = api.get_channel_recent_video_stats(uploads_playlist_id, max_results=30)

    if not video_stats:
        logger.warning(f"動画データなし。平均再生数を更新しません: {handle}")
        return stats.get(handle, {}).get("avg_views", 0)

    avg_views = calculate_channel_avg_views(video_stats)

    if handle not in stats:
        stats[handle] = {}
    stats[handle]["avg_views"] = avg_views
    stats[handle]["avg_views_updated"] = datetime.now(timezone.utc).isoformat()
    stats[handle]["sample_size"] = len(video_stats)

    return avg_views


def main() -> None:
    logger.info("=== 海外バイラルレーダー 実行開始 ===")

    try:
        api = YouTubeAPI()
    except YouTubeAPIError as e:
        logger.error(f"YouTube API 初期化失敗: {e}")
        sys.exit(1)

    stats = load_channel_stats()
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=LOOKBACK_DAYS)

    # 日付文字列（JST）
    jst = timezone(timedelta(hours=9))
    date_str = now.astimezone(jst).strftime("%Y/%m/%d")

    # 1. チャンネルID解決
    logger.info("チャンネルID解決中...")
    resolve_channel_ids(api, CHANNELS, stats)
    save_channel_stats(stats)

    # 2. 各チャンネルの新着動画をチェック
    all_buzz_videos: list[BuzzVideo] = []

    for ch in CHANNELS:
        handle = ch["handle"]
        channel_id = ch.get("channel_id")
        name = ch["name"]

        if not channel_id:
            logger.warning(f"スキップ (ID未解決): {name} ({handle})")
            continue

        try:
            # アップロード用プレイリストID取得
            playlist_id = get_uploads_playlist_id(api, channel_id, stats, handle)
            if not playlist_id:
                logger.warning(f"プレイリストID取得失敗: {name}")
                continue

            # 平均再生数の取得/更新
            if should_update_avg_views(stats, handle):
                logger.info(f"平均再生数を更新: {name}")
                avg_views = update_channel_avg_views(api, playlist_id, stats, handle)
            else:
                avg_views = stats.get(handle, {}).get("avg_views", 0)

            # 新着動画取得
            new_videos = api.get_new_videos_since(playlist_id, since)
            if not new_videos:
                logger.info(f"新着動画なし: {name}")
                continue

            logger.info(f"{name}: {len(new_videos)}本の新着動画")

            # バズり検知
            buzz = detect_buzz_videos(new_videos, avg_views, name, now)
            if buzz:
                logger.info(f"  -> バズり検知: {len(buzz)}本")
                all_buzz_videos.extend(buzz)

        except QuotaExceededError:
            logger.error("YouTube API クォータ超過。処理を中断します。")
            break
        except YouTubeAPIError as e:
            logger.error(f"{name} の処理中にエラー: {e}")
            continue

    # キャッシュ保存
    save_channel_stats(stats)

    # 3. ランキング＆通知
    ranked = rank_and_limit(all_buzz_videos)

    # 既に通知済みの動画を除外
    notified = stats.get("_notified_videos", {})
    new_buzz = [v for v in ranked if v.video_id not in notified]
    logger.info(
        f"バズり動画合計: {len(all_buzz_videos)}本 -> "
        f"ランキング: {len(ranked)}本 -> 新規: {len(new_buzz)}本"
    )

    if not new_buzz and all_buzz_videos:
        # バズ動画はあるが全て通知済み → 通知スキップ
        logger.info("全て通知済み。LINE通知をスキップします。")
    else:
        message = format_notification(new_buzz, date_str)
        logger.info(f"通知メッセージ:\n{message}")

        # LINE通知送信
        try:
            send_line_message(message)
            logger.info("LINE通知送信完了")
        except LINENotifyError as e:
            logger.error(f"LINE通知送信失敗: {e}")
            sys.exit(1)

        # 通知成功後、動画IDを記録
        for v in new_buzz:
            notified[v.video_id] = now.isoformat()

    # 古い通知記録を削除（14日以上前）
    cutoff = (now - timedelta(days=LOOKBACK_DAYS * 2)).isoformat()
    stats["_notified_videos"] = {
        vid: ts for vid, ts in notified.items()
        if ts > cutoff
    }
    save_channel_stats(stats)

    logger.info(f"API クォータ使用量: {api.quota_used} ユニット")
    logger.info("=== 海外バイラルレーダー 実行完了 ===")


if __name__ == "__main__":
    main()

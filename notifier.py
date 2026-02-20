"""
LINE Messaging API 通知モジュール

LINE Messaging API の Push Message を使って、バズり動画の情報を送信する。
既存のニュースツールと同じチャネルを流用。
"""

import logging
import os
from datetime import datetime, timezone, timedelta

import requests

from buzz_detector import BuzzVideo

logger = logging.getLogger(__name__)

LINE_API_URL = "https://api.line.me/v2/bot/message/push"


class LINENotifyError(Exception):
    pass


def _get_buzz_emoji(score: float) -> str:
    """バズ度に応じた火の絵文字を返す"""
    if score >= 8.0:
        return "\U0001f525\U0001f525\U0001f525"
    elif score >= 5.0:
        return "\U0001f525\U0001f525"
    else:
        return "\U0001f525"


def _format_view_count(count: int) -> str:
    """再生数を見やすくフォーマットする"""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.0f}K"
    return str(count)


def format_notification(buzz_videos: list[BuzzVideo], date_str: str) -> str:
    """
    バズり動画リストからLINE通知メッセージを組み立てる。
    """
    if not buzz_videos:
        return (
            f"\U0001f4e1 海外バイラルレーダー ({date_str})\n"
            "\u2501" * 14 + "\n\n"
            "今日はバズり動画が検知されませんでした。\n"
            "しきい値: 通常の3倍以上 & 5万再生以上"
        )

    lines = [
        f"\U0001f525 海外バイラルレーダー ({date_str})",
        "\u2501" * 14,
        "",
        f"\U0001f680 今週のバズ動画 TOP{len(buzz_videos)}",
        "",
    ]

    number_emojis = [
        "1\ufe0f\u20e3", "2\ufe0f\u20e3", "3\ufe0f\u20e3",
        "4\ufe0f\u20e3", "5\ufe0f\u20e3", "6\ufe0f\u20e3",
        "7\ufe0f\u20e3", "8\ufe0f\u20e3", "9\ufe0f\u20e3",
        "\U0001f51f",
    ]

    for i, video in enumerate(buzz_videos):
        emoji = number_emojis[i] if i < len(number_emojis) else f"#{i + 1}"
        buzz_emoji = _get_buzz_emoji(video.buzz_score)

        lines.append(
            f"{emoji} {buzz_emoji} バズ度: {video.buzz_score:.1f}x"
        )
        lines.append(f'"{video.title}"')
        lines.append(f"\U0001f4fa {video.channel_name}")
        lines.append(
            f"\U0001f440 {_format_view_count(video.view_count)}回 "
            f"({video.days_label})"
        )
        lines.append(
            f"\U0001f4ca 通常の{video.buzz_score:.1f}倍の速度"
        )
        lines.append(f"\U0001f517 {video.url}")
        lines.append("")

    lines.append("\u2501" * 14)

    return "\n".join(lines)


def send_line_message(
    message: str,
    channel_access_token: str | None = None,
    user_id: str | None = None,
) -> None:
    """LINE Messaging API でプッシュメッセージを送信する"""
    token = channel_access_token or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    uid = user_id or os.environ.get("LINE_USER_ID")

    if not token:
        raise LINENotifyError("LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
    if not uid:
        raise LINENotifyError("LINE_USER_ID が設定されていません")

    # LINEメッセージは5000文字制限があるので分割
    messages = _split_message(message, max_length=4900)

    for msg in messages:
        payload = {
            "to": uid,
            "messages": [{"type": "text", "text": msg}],
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            resp = requests.post(
                LINE_API_URL, json=payload, headers=headers, timeout=30
            )
        except requests.RequestException as e:
            raise LINENotifyError(f"LINE API リクエスト失敗: {e}")

        if resp.status_code != 200:
            raise LINENotifyError(
                f"LINE API エラー (HTTP {resp.status_code}): {resp.text[:500]}"
            )

    logger.info(f"LINE通知送信完了 ({len(messages)}メッセージ)")


def _split_message(text: str, max_length: int = 4900) -> list[str]:
    """長いメッセージを分割する"""
    if len(text) <= max_length:
        return [text]

    parts = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            if current:
                parts.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        parts.append(current)

    return parts

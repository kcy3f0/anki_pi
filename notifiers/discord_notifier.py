# notifiers/discord_notifier.py
from __future__ import annotations
import logging
import re
import threading
from urllib.parse import urlparse

import requests
from domain.events import (
    NotificationEvent,
    CardReviewedEvent,
    ProgressResetEvent,
    DataClearedEvent,
    CardsImportedEvent,
    ExamCreatedEvent,
    ExamDeletedEvent,
    ExamsImportedEvent,
)

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Discord Webhook 通知發送器（非同步執行緒）。"""

    def __init__(self, webhook_url: str):
        self.webhook_url = self._validate_webhook_url(webhook_url)

    def _validate_webhook_url(self, url: str) -> str:
        """驗證 Discord Webhook URL 格式。"""
        if not url:
            raise ValueError("Discord Webhook URL 不能為空")

        parsed = urlparse(url)
        if not (parsed.scheme in ("http", "https") and parsed.netloc):
            raise ValueError("無效的 Discord Webhook URL 格式")

        # 驗證是否為 Discord 官方網域（安全性檢查）
        if not re.match(r".*discord(app)?\.com.*webhook.*", url, re.I):
            logger.warning("Webhook URL 似乎不是 Discord 官方網域: %s", url)

        return url

    def notify(self, event: NotificationEvent) -> None:
        if not self.webhook_url:
            return

        content = self._format_event(event)
        if not content:
            return

        def run_send():
            try:
                requests.post(self.webhook_url, json={"content": content}, timeout=5)
            except requests.RequestException as e:
                logger.error("Discord Webhook 發送失敗: %s", e, exc_info=True)
            except Exception as e:
                logger.error("Discord Webhook 未知錯誤: %s", e, exc_info=True)

        threading.Thread(target=run_send, daemon=True).start()

    def _format_event(self, event: NotificationEvent) -> str | None:
        if isinstance(event, CardReviewedEvent):
            rating_map = {
                1: "忘記 (Again)",
                2: "困難 (Hard)",
                3: "普通 (Good)",
                4: "簡單 (Easy)",
            }
            return f"🧠 記憶卡複習通知：\n- 單字：{event.front}\n- 評分：{rating_map.get(event.rating, '未知')}\n- 牌組：{', '.join(event.deck_names)}\n- 下次複習時間：{event.next_review}"
        elif isinstance(event, ProgressResetEvent):
            return "⚠️ 所有記憶卡的學習進度已重置！"
        elif isinstance(event, DataClearedEvent):
            return "🔥 所有卡片、牌組與資料夾的資料已被清空！"
        elif isinstance(event, CardsImportedEvent):
            return f"📋 批次匯入成功！\n- 新增單字卡：{event.imported} 張\n- 合併重複卡：{event.merged} 張"
        elif isinstance(event, ExamCreatedEvent):
            return f"📅 新增考試行程通知：\n- 考試：{event.name}\n- 日期：{event.date.astimezone().strftime('%Y/%m/%d')}"
        elif isinstance(event, ExamDeletedEvent):
            return f"🗑️ 考試行程已刪除：{event.name}"
        elif isinstance(event, ExamsImportedEvent):
            return f"📋 批次匯入考試行程成功！共匯入 {event.count} 筆考試。"
        return None

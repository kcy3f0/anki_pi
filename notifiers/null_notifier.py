# notifiers/null_notifier.py
from __future__ import annotations
from domain.events import NotificationEvent


class NullNotifier:
    """測試/停用用：不發送任何通知。"""

    def __init__(self):
        self.events: list[NotificationEvent] = []

    def notify(self, event: NotificationEvent) -> None:
        self.events.append(event)

    def get_events(self) -> list[NotificationEvent]:
        return self.events

    def clear(self) -> None:
        self.events.clear()

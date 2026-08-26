# domain/events.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class NotificationEvent(Protocol):
    """所有通知事件的標記介面。"""

    pass


@dataclass(frozen=True)
class CardReviewedEvent:
    card_id: int
    front: str
    rating: int
    deck_names: list[str]
    next_review: datetime


@dataclass(frozen=True)
class ProgressResetEvent:
    pass


@dataclass(frozen=True)
class DataClearedEvent:
    pass


@dataclass(frozen=True)
class CardsImportedEvent:
    imported: int
    merged: int


@dataclass(frozen=True)
class ExamCreatedEvent:
    name: str
    date: datetime


@dataclass(frozen=True)
class ExamDeletedEvent:
    name: str


@dataclass(frozen=True)
class ExamsImportedEvent:
    count: int

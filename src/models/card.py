from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Card:
    id: Optional[int]
    front: str
    back: str
    next_review: str
    state: int = 1
    step: int = 0
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    last_review: Optional[str] = None
    reps: int = 0
    lapses: int = 0
    card_type: str = 'recognize'

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row['id'],
            front=row['front'],
            back=row['back'],
            next_review=row['next_review'],
            state=row['state'],
            step=row['step'],
            stability=row['stability'],
            difficulty=row['difficulty'],
            last_review=row['last_review'],
            reps=row['reps'],
            lapses=row['lapses'],
            card_type=row['card_type']
        )

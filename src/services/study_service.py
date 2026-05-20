import random
from datetime import datetime, timezone, timedelta
from fsrs import Scheduler, Card as FSRSCard, Rating, State
from ..models.database import get_db_connection
from ..models.card import Card
from ..utils.date_helpers import parse_iso, format_iso, now_utc_iso

class StudyService:
    def __init__(self):
        self.scheduler = Scheduler()

    def fetch_next_card(self, deck_ids):
        now_utc = datetime.now(timezone.utc)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if not deck_ids:
                return None, 0

            placeholders = ','.join('?' for _ in deck_ids)
            params = [now_utc.isoformat()] + deck_ids

            cursor.execute(f"""
                SELECT DISTINCT c.id
                FROM cards c
                JOIN card_decks cd ON c.id = cd.card_id
                WHERE c.next_review <= ? AND cd.deck_id IN ({placeholders})
            """, params)

            due_card_rows = cursor.fetchall()
            due_count = len(due_card_rows)

            if due_count > 0:
                random_card_id = random.choice(due_card_rows)['id']
                cursor.execute("SELECT * FROM cards WHERE id = ?", (random_card_id,))
                card_row = cursor.fetchone()
                card = Card.from_row(card_row)
            else:
                card = None

        if card:
            card_dict = vars(card)
            card_dict['english_word'] = card.front
            
            is_reverse = False
            if card.card_type == 'spell':
                is_reverse = random.choice([True, False])

            if is_reverse:
                hint = f"{card.front[0]}...{card.front[-1]}" if len(card.front) > 2 else f"{card.front[0]}..."
                card_dict['front'] = f"{card.back} ({hint})"
                card_dict['back'] = card.front
            
            return card_dict, due_count
        return None, 0

    def process_answer(self, card_id, quality):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
            row = cursor.fetchone()
            if not row:
                return None

            c = Card.from_row(row)
            
            # Map to FSRS Card
            fsrs_card = FSRSCard()
            fsrs_card.state = State(c.state)
            fsrs_card.step = c.step
            fsrs_card.stability = c.stability
            fsrs_card.difficulty = c.difficulty
            fsrs_card.due = parse_iso(c.next_review)
            fsrs_card.last_review = parse_iso(c.last_review)

            now = datetime.now(timezone.utc)
            rating = Rating(int(quality))
            new_fsrs_card, _ = self.scheduler.review_card(fsrs_card, rating, now)
            
            # Manual increment since FSRS Card doesn't track these internally in this version
            new_reps = c.reps + 1
            new_lapses = c.lapses
            if rating == Rating.Again:
                new_lapses += 1

            cursor.execute("""
                UPDATE cards 
                SET state = ?, step = ?, stability = ?, difficulty = ?, next_review = ?, last_review = ?, reps = ?, lapses = ? 
                WHERE id = ?
            """, (
                new_fsrs_card.state.value, 
                new_fsrs_card.step, 
                new_fsrs_card.stability, 
                new_fsrs_card.difficulty, 
                format_iso(new_fsrs_card.due), 
                format_iso(new_fsrs_card.last_review), 
                new_reps, 
                new_lapses, 
                card_id
            ))
            conn.commit()
            return True

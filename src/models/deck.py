from .database import get_db_connection
from .card import Card

class DeckRepository:
    @staticmethod
    def get_cards_in_deck(deck_id: int):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*
                FROM cards c
                JOIN card_decks cd ON c.id = cd.card_id
                WHERE cd.deck_id = ?
                ORDER BY c.next_review
            """, (deck_id,))
            return [Card.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_all_decks():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decks ORDER BY name")
            return cursor.fetchall()

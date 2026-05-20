from ..models.database import get_db_connection
from ..utils.date_helpers import now_utc_iso

class AdminService:
    @staticmethod
    def reset_all_progress():
        now_iso = now_utc_iso()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cards 
                SET state = 1, step = 0, stability = NULL, difficulty = NULL, last_review = NULL, reps = 0, lapses = 0, next_review = ?
            """, (now_iso,))
            conn.commit()
            return True

    @staticmethod
    def delete_all_cards():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cards")
            conn.commit()
            return True

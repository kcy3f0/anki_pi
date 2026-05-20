import io
import csv
from datetime import datetime, timezone
from ..models.database import get_db_connection
from ..utils.date_helpers import now_utc_iso

class ImportService:
    def import_csv_paste(self, csv_data, deck_id, card_type='recognize'):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            file_like_object = io.StringIO(csv_data)
            rows = list(csv.reader(file_like_object))
            
            count = 0
            now_iso = now_utc_iso()
            for row in rows:
                if len(row) >= 2 and row[0].strip():
                    front = row[0].strip()
                    back = row[1].strip()

                    # Check if card exists (Global Check)
                    cursor.execute("SELECT * FROM cards WHERE front = ?", (front,))
                    existing_card = cursor.fetchone()

                    if existing_card:
                        # Merge logic
                        card_id = existing_card['id']
                        cursor.execute("INSERT OR IGNORE INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, deck_id))

                        current_back = existing_card['back']
                        new_card_type = existing_card['card_type']
                        if card_type == 'spell' and existing_card['card_type'] == 'recognize':
                            new_card_type = 'spell'

                        merged_back = current_back
                        if back.strip() not in current_back:
                            merged_back = f"{current_back}\n\n{back.strip()}"

                        cursor.execute("UPDATE cards SET back = ?, card_type = ? WHERE id = ?", (merged_back, new_card_type, card_id))
                    else:
                        # Insert New
                        cursor.execute("""
                            INSERT INTO cards (front, back, next_review, card_type) 
                            VALUES (?, ?, ?, ?)
                        """, (front, back, now_iso, card_type))
                        card_id = cursor.lastrowid
                        cursor.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, deck_id))

                    count += 1
            
            conn.commit()
            return count

from datetime import datetime, timezone
from collections import defaultdict
from ..models.database import get_db_connection
from ..services.notification_service import NotificationService

def check_and_remind():
    now_utc = datetime.now(timezone.utc)
    notification_service = NotificationService()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get Due Counts Grouped by Folder -> Deck
        query = """
            SELECT
                f.name as folder_name,
                d.name as deck_name,
                COUNT(DISTINCT c.id) as count
            FROM cards c
            JOIN card_decks cd ON c.id = cd.card_id
            JOIN decks d ON cd.deck_id = d.id
            JOIN deck_folders df ON d.id = df.deck_id
            JOIN folders f ON df.folder_id = f.id
            WHERE c.next_review <= ?
            GROUP BY f.name, d.name
            ORDER BY f.name, d.name
        """

        cursor.execute(query, (now_utc.isoformat(),))
        rows = cursor.fetchall()

        total_count = sum(row['count'] for row in rows)

        if total_count == 0:
            return

        folder_data = defaultdict(dict)
        for row in rows:
            folder_data[row['folder_name']][row['deck_name']] = row['count']

        message = notification_service.format_reminder_message(total_count, folder_data)
        notification_service.send_discord_message(message)

if __name__ == "__main__":
    check_and_remind()

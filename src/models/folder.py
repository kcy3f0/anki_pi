from .database import get_db_connection

class FolderRepository:
    @staticmethod
    def get_all_folders():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM folders ORDER BY name")
            return cursor.fetchall()

    @staticmethod
    def get_decks_in_folder(folder_id: int):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*
                FROM decks d
                JOIN deck_folders df ON d.id = df.deck_id
                WHERE df.folder_id = ?
                ORDER BY d.name
            """, (folder_id,))
            return cursor.fetchall()

import pytest
from src.services.import_service import ImportService
from src.models.database import get_db_connection
from src.models.migrations import init_db
import os

@pytest.fixture(autouse=True)
def setup_db():
    import uuid
    db_name = f"test_import_{uuid.uuid4().hex}.db"
    os.environ["DB_NAME"] = db_name
    init_db()
    yield
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
        except PermissionError:
            pass

def test_import_merges_duplicates():
    service = ImportService()
    
    # 1. Setup: Insert initial card
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO decks (name) VALUES ('Test Deck')")
        deck_id = cursor.lastrowid
        cursor.execute("INSERT INTO cards (front, back, next_review) VALUES ('apple', '蘋果', '2020-01-01')")
        card_id = cursor.lastrowid
        cursor.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, deck_id))
        conn.commit()

    # 2. Import same card with different back
    csv_data = "apple,red fruit"
    count = service.import_csv_paste(csv_data, deck_id)
    
    assert count == 1

    # 3. Verify merged content
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT back FROM cards WHERE front = 'apple'")
        row = cursor.fetchone()
        assert "蘋果" in row['back']
        assert "red fruit" in row['back']

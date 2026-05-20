import pytest
from datetime import datetime, timezone, timedelta
from src.services.study_service import StudyService
from src.models.database import get_db_connection
from src.models.migrations import init_db
import os

@pytest.fixture(autouse=True)
def setup_db():
    import uuid
    db_name = f"test_study_{uuid.uuid4().hex}.db"
    os.environ["DB_NAME"] = db_name
    init_db()
    yield
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
        except PermissionError:
            pass

def test_process_answer_updates_card():
    service = StudyService()
    
    # Insert a test card
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO cards (front, back, next_review, state, reps) 
            VALUES ('test', '測試', ?, 1, 0)
        """, (now,))
        card_id = cursor.lastrowid
        conn.commit()

    # Process answer (Rating 3 = Good)
    success = service.process_answer(card_id, 3)
    assert success is True

    # Verify updates
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        assert row['reps'] == 1
        assert row['last_review'] is not None
        # Verify next_review is updated (should be in the future or now)
        assert row['next_review'] is not None

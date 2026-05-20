import pytest
from src.app import create_app
from src.models.database import get_db_connection
import os

@pytest.fixture
def app():
    os.environ["DB_NAME"] = "test_mgmt.db"
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    yield app
    if os.path.exists("test_mgmt.db"):
        os.remove("test_mgmt.db")

@pytest.fixture
def client(app):
    return app.test_client()

def test_delete_all_cards(client):
    # Setup: Insert a card
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cards (front, back, next_review) VALUES ('t1', 'b1', '2000-01-01')")
        conn.commit()
    
    # Call delete endpoint
    response = client.post('/delete_all_cards', follow_redirects=True)
    assert response.status_code == 200
    
    # Verify DB is empty
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM cards")
        assert cursor.fetchone()['count'] == 0

def test_reset_progress(client):
    # Setup: Insert a reviewed card
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cards (front, back, next_review, reps) VALUES ('t1', 'b1', '2000-01-01', 5)")
        conn.commit()
    
    # Call reset endpoint
    response = client.post('/reset_progress', follow_redirects=True)
    assert response.status_code == 200
    
    # Verify card is reset
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reps, state FROM cards")
        row = cursor.fetchone()
        assert row['reps'] == 0
        assert row['state'] == 1 # New

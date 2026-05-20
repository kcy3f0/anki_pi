import pytest
from src.app import create_app
from src.models.database import get_db_connection
import os
import json

@pytest.fixture
def app():
    os.environ["DB_NAME"] = "test_integration.db"
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    yield app
    if os.path.exists("test_integration.db"):
        os.remove("test_integration.db")

@pytest.fixture
def client(app):
    return app.test_client()

def test_api_answer_returns_next_card(client):
    # Setup: Insert a deck and a due card
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO decks (name) VALUES ('Test Deck')")
        deck_id = cursor.lastrowid
        cursor.execute("INSERT INTO cards (front, back, next_review) VALUES ('card1', 'back1', '2000-01-01')")
        card1_id = cursor.lastrowid
        cursor.execute("INSERT INTO cards (front, back, next_review) VALUES ('card2', 'back2', '2000-01-01')")
        card2_id = cursor.lastrowid
        cursor.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card1_id, deck_id))
        cursor.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card2_id, deck_id))
        conn.commit()

    # Call API to answer card1
    response = client.post('/api/study/answer', 
                           data=json.dumps({'card_id': card1_id, 'quality': 3, 'deck_id': deck_id}),
                           content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    # Should return the OTHER due card
    assert data['card']['id'] == card2_id
    assert data['due_count'] == 1

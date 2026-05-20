import pytest
import sqlite3
import os
from src.models.migrations import init_db, validate_schema
from src.models.database import get_db_connection

@pytest.fixture
def legacy_db():
    db_name = "legacy_test.db"
    if os.path.exists(db_name):
        os.remove(db_name)
    
    # Create a legacy schema (e.g., from an older version of the app)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            next_review DATE NOT NULL,
            interval INTEGER DEFAULT 0,
            repetition INTEGER DEFAULT 0,
            ef FLOAT DEFAULT 2.5
        )
    ''')
    cursor.execute("INSERT INTO cards (front, back, next_review) VALUES ('legacy', '舊資料', '2020-01-01')")
    conn.commit()
    conn.close()
    
    os.environ["DB_NAME"] = db_name
    yield db_name
    if os.path.exists(db_name):
        os.remove(db_name)

def test_migration_from_legacy_to_fsrs(legacy_db):
    # Run init_db which should perform migrations
    init_db()
    
    # Validate schema
    assert validate_schema() is True
    
    # Verify data preservation
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT front, back FROM cards WHERE front = 'legacy'")
        row = cursor.fetchone()
        assert row is not None
        assert row['back'] == '舊資料'

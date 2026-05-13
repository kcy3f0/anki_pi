import sqlite3
import datetime

conn = sqlite3.connect('flashcards.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        front TEXT NOT NULL,
        back TEXT NOT NULL,
        next_review DATE NOT NULL,
        interval INTEGER DEFAULT 0,
        repetition INTEGER DEFAULT 0,
        ef FLOAT DEFAULT 2.5,
        card_type TEXT NOT NULL DEFAULT 'recognize'
    )
''')

cursor.execute("INSERT INTO cards (front, back, next_review, interval, repetition, ef) VALUES ('test', '測試', ?, 10, 2, 2.5)", (datetime.datetime.now().date(),))
conn.commit()

import sys
from unittest.mock import MagicMock
sys.modules['flask'] = MagicMock()
sys.modules['flask_wtf.csrf'] = MagicMock()

import app
app.init_db()

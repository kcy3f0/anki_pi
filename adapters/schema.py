# adapters/schema.py
# 從 database.py init_db_schema() 提取的完整 CREATE TABLE 陳述式
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deck_folders (
    deck_id INTEGER NOT NULL,
    folder_id INTEGER NOT NULL,
    PRIMARY KEY (deck_id, folder_id),
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    next_review TEXT NOT NULL,
    state INTEGER DEFAULT 0,
    step INTEGER DEFAULT 0,
    stability REAL,
    difficulty REAL,
    last_review TEXT,
    reps INTEGER DEFAULT 0,
    lapses INTEGER DEFAULT 0,
    card_type TEXT DEFAULT 'recognize'
);

CREATE TABLE IF NOT EXISTS card_decks (
    card_id INTEGER NOT NULL,
    deck_id INTEGER NOT NULL,
    PRIMARY KEY (card_id, deck_id),
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    processed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exam_decks (
    exam_id INTEGER NOT NULL,
    deck_id INTEGER NOT NULL,
    PRIMARY KEY (exam_id, deck_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exam_folders (
    exam_id INTEGER NOT NULL,
    folder_id INTEGER NOT NULL,
    PRIMARY KEY (exam_id, folder_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS revlog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    review_time TEXT NOT NULL,
    review_rating INTEGER NOT NULL,
    review_state INTEGER NOT NULL,
    review_duration INTEGER DEFAULT 0,
    FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_revlog_card_id ON revlog(card_id);
"""

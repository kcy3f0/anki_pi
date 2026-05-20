import sqlite3
import os
from ..config import DB_NAME as DEFAULT_DB_NAME

def get_db_connection():
    db_name = os.getenv("DB_NAME", DEFAULT_DB_NAME)
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Performance Optimizations
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 30000000000")
    return conn

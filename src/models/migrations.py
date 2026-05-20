from datetime import datetime, timedelta, timezone
from collections import defaultdict
from .database import get_db_connection

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # --- Schema and Migration to Many-to-Many (Decks <-> Folders) ---
        cursor.execute("PRAGMA table_info(decks)")
        deck_columns = [column[1] for column in cursor.fetchall()]

        if 'folder_id' in deck_columns:
            # 1. Create the new junction table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deck_folders (
                    deck_id INTEGER NOT NULL,
                    folder_id INTEGER NOT NULL,
                    PRIMARY KEY (deck_id, folder_id),
                    FOREIGN KEY(deck_id) REFERENCES decks(id),
                    FOREIGN KEY(folder_id) REFERENCES folders(id)
                )
            ''')

            # 2. Migrate existing relationships
            cursor.execute("SELECT id, folder_id FROM decks WHERE folder_id IS NOT NULL")
            relations_to_migrate = cursor.fetchall()
            cursor.executemany("INSERT INTO deck_folders (deck_id, folder_id) VALUES (?, ?)", relations_to_migrate)

            # 3. Recreate the decks table without folder_id
            cursor.execute('''
                CREATE TABLE decks_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            cursor.execute("INSERT INTO decks_new (id, name) SELECT id, name FROM decks")
            cursor.execute("DROP TABLE decks")
            cursor.execute("ALTER TABLE decks_new RENAME TO decks")
            
            print("Deck-Folder structure migrated.")

        # --- Standard Table Creation ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        # Cleanup potential duplicates in deck_folders
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deck_folders'")
            if cursor.fetchone():
                cursor.execute("""
                    DELETE FROM deck_folders
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid)
                        FROM deck_folders
                        GROUP BY deck_id, folder_id
                    )
                """)
        except Exception as e:
            print(f"Warning during duplicate cleanup: {e}")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deck_folders (
                deck_id INTEGER NOT NULL,
                folder_id INTEGER NOT NULL,
                PRIMARY KEY (deck_id, folder_id),
                FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE,
                FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        ''')

        # --- Schema and Migration to Many-to-Many (Cards <-> Decks) ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cards'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(cards)")
            card_columns = [column[1] for column in cursor.fetchall()]

            if 'deck_id' in card_columns:
                print("Migrating cards to Many-to-Many schema with merge logic...")
                conn.commit()
                cursor.execute("PRAGMA foreign_keys = OFF")

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS card_decks (
                        card_id INTEGER NOT NULL,
                        deck_id INTEGER NOT NULL,
                        PRIMARY KEY (card_id, deck_id),
                        FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE,
                        FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE
                    )
                ''')

                if 'card_type' in card_columns:
                    cursor.execute("SELECT * FROM cards")
                else:
                    cursor.execute("SELECT *, 'recognize' as card_type FROM cards")

                old_cards = cursor.fetchall()
                grouped_cards = defaultdict(list)
                for card in old_cards:
                    grouped_cards[card['front'].strip()].append(dict(card))

                cursor.execute('''
                    CREATE TABLE cards_new (
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

                new_links = []
                cursor.execute("SELECT id FROM decks")
                valid_deck_ids = set(row['id'] for row in cursor.fetchall())

                for front, card_group in grouped_cards.items():
                    is_spell = any(c.get('card_type') == 'spell' for c in card_group)
                    final_type = 'spell' if is_spell else 'recognize'
                    unique_backs = []
                    seen_backs = set()
                    sorted_group = sorted(card_group, key=lambda x: 0 if x.get('card_type') == 'spell' else 1)
                    for c in sorted_group:
                        b = c['back'].strip()
                        if b and b not in seen_backs:
                            unique_backs.append(b)
                            seen_backs.add(b)
                    final_back = "\n\n".join(unique_backs)
                    total_interval = sum(c['interval'] for c in card_group)
                    total_rep = sum(c['repetition'] for c in card_group)
                    total_ef = sum(c['ef'] for c in card_group)
                    count = len(card_group)
                    avg_interval = int(total_interval / count)
                    avg_rep = int(total_rep / count)
                    avg_ef = total_ef / count
                    if count == 1:
                        next_review = card_group[0]['next_review']
                    else:
                        next_review = datetime.now().date() + timedelta(days=avg_interval)

                    cursor.execute("""
                        INSERT INTO cards_new (front, back, next_review, interval, repetition, ef, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (front, final_back, next_review, avg_interval, avg_rep, avg_ef, final_type))
                    new_card_id = cursor.lastrowid
                    for c in card_group:
                        if c['deck_id'] and c['deck_id'] in valid_deck_ids:
                            new_links.append((new_card_id, c['deck_id']))

                if new_links:
                    unique_links = list(set(new_links))
                    cursor.executemany("INSERT OR IGNORE INTO card_decks (card_id, deck_id) VALUES (?, ?)", unique_links)

                cursor.execute("DROP TABLE cards")
                cursor.execute("ALTER TABLE cards_new RENAME TO cards")
                conn.commit()
                cursor.execute("PRAGMA foreign_keys = ON")

        # --- Schema and Migration to FSRS ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cards'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(cards)")
            card_columns = [column[1] for column in cursor.fetchall()]

            if 'ef' in card_columns:
                print("Migrating cards from SM-2 to FSRS schema...")
                conn.commit()
                cursor.execute("PRAGMA foreign_keys = OFF")

                cursor.execute("SELECT * FROM cards")
                old_cards = cursor.fetchall()

                cursor.execute('''
                    CREATE TABLE cards_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        front TEXT NOT NULL,
                        back TEXT NOT NULL,
                        next_review DATE NOT NULL,
                        state INTEGER DEFAULT 1,
                        step INTEGER DEFAULT 0,
                        stability FLOAT DEFAULT NULL,
                        difficulty FLOAT DEFAULT NULL,
                        last_review DATE DEFAULT NULL,
                        reps INTEGER DEFAULT 0,
                        lapses INTEGER DEFAULT 0,
                        card_type TEXT NOT NULL DEFAULT 'recognize'
                    )
                ''')

                now_utc = datetime.now(timezone.utc).isoformat()
                for card in old_cards:
                    card_dict = dict(card)
                    interval = card_dict['interval']
                    repetition = card_dict['repetition']
                    ef = card_dict['ef']
                    state = 2
                    step = None
                    stability = None
                    difficulty = None
                    last_review = None
                    reps = card_dict['repetition']
                    lapses = 0
                    card_type = card_dict.get('card_type', 'recognize')
                    if repetition == 0:
                        state = 1
                        step = 0
                    else:
                        stability = float(interval)
                        difficulty = 10.0 - (ef - 1.3) / 1.2 * 9.0
                        difficulty = max(1.0, min(10.0, difficulty))
                        last_review = now_utc

                    cursor.execute('''
                        INSERT INTO cards_new (id, front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (card_dict['id'], card_dict['front'], card_dict['back'], card_dict['next_review'], state, step, stability, difficulty, last_review, reps, lapses, card_type))
                cursor.execute("DROP TABLE cards")
                cursor.execute("ALTER TABLE cards_new RENAME TO cards")
                conn.commit()
                cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                next_review DATE NOT NULL,
                state INTEGER DEFAULT 1,
                step INTEGER DEFAULT 0,
                stability FLOAT DEFAULT NULL,
                difficulty FLOAT DEFAULT NULL,
                last_review DATE DEFAULT NULL,
                reps INTEGER DEFAULT 0,
                lapses INTEGER DEFAULT 0,
                card_type TEXT NOT NULL DEFAULT 'recognize'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_decks (
                card_id INTEGER NOT NULL,
                deck_id INTEGER NOT NULL,
                PRIMARY KEY (card_id, deck_id),
                FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE,
                FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_next_review ON cards(next_review)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_card_decks_deck_id ON card_decks(deck_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_card_decks_card_id ON card_decks(card_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_card_decks_deck_card ON card_decks(deck_id, card_id)")

        conn.commit()

def validate_schema():
    expected_tables = {'cards', 'decks', 'folders', 'card_decks', 'deck_folders', 'settings'}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row['name'] for row in cursor.fetchall()}
        
        missing_tables = expected_tables - existing_tables
        if missing_tables:
            print(f"Warning: Missing tables: {missing_tables}")
            return False
            
        # Check cards columns
        cursor.execute("PRAGMA table_info(cards)")
        card_columns = {row['name'] for row in cursor.fetchall()}
        expected_card_columns = {'id', 'front', 'back', 'next_review', 'state', 'step', 'stability', 'difficulty', 'last_review', 'reps', 'lapses', 'card_type'}
        
        missing_card_columns = expected_card_columns - card_columns
        if missing_card_columns:
            print(f"Warning: Missing columns in cards table: {missing_card_columns}")
            return False
            
    return True

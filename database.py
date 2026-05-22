import sqlite3
import os
import csv
from datetime import datetime, timezone, timedelta
import requests
from fsrs import Scheduler, Card, Rating, State
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_db_datetime(dt_str):
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    # Try parsing 'YYYY-MM-DDTHH:MM:SS.ffffff+00:00' or similar
    if 'T' in dt_str:
        # Normalize +00:00 or Z
        if dt_str.endswith('+00:00'):
            dt_str = dt_str[:-6]
        elif dt_str.endswith('Z'):
            dt_str = dt_str[:-1]
        
        # Handle decimal seconds if any
        if '.' in dt_str:
            base, micro = dt_str.split('.')
            # Truncate micro to max 6 digits
            micro = micro[:6]
            dt_str = f"{base}.{micro}"
            try:
                return datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                return None
    else:
        # Handle 'YYYY-MM-DD'
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None

def format_datetime_for_db(dt):
    if not dt:
        return None
    return dt.isoformat()

def send_discord_message(content):
    url = Config.DISCORD_WEBHOOK_URL
    if not url:
        return
    try:
        requests.post(url, json={"content": content}, timeout=5)
    except Exception as e:
        print(f"Error sending Discord Webhook: {e}")

# Folder and Deck CRUD

def get_all_folders():
    conn = get_db_connection()
    folders = conn.execute("SELECT * FROM folders").fetchall()
    conn.close()
    return folders

def get_all_decks():
    conn = get_db_connection()
    decks = conn.execute("SELECT * FROM decks").fetchall()
    conn.close()
    return decks

def get_folders_with_decks():
    conn = get_db_connection()
    
    # 1. Fetch folders
    folders = conn.execute("SELECT * FROM folders").fetchall()
    folder_list = []
    
    now = datetime.now(timezone.utc)
    
    for f in folders:
        f_dict = dict(f)
        # Fetch decks assigned to this folder
        decks = conn.execute("""
            SELECT d.* FROM decks d
            JOIN deck_folders df ON d.id = df.deck_id
            WHERE df.folder_id = ?
        """, (f['id'],)).fetchall()
        
        deck_list = []
        for d in decks:
            d_dict = dict(d)
            # Count card stats in this deck
            stats = get_deck_card_stats(d['id'], now)
            d_dict.update(stats)
            deck_list.append(d_dict)
            
        f_dict['decks'] = deck_list
        folder_list.append(f_dict)
        
    # 2. Fetch unassigned decks (not in any folder)
    unassigned_decks = conn.execute("""
        SELECT d.* FROM decks d
        LEFT JOIN deck_folders df ON d.id = df.deck_id
        WHERE df.folder_id IS NULL
    """).fetchall()
    
    unassigned_list = []
    for d in unassigned_decks:
        d_dict = dict(d)
        stats = get_deck_card_stats(d['id'], now)
        d_dict.update(stats)
        unassigned_list.append(d_dict)
        
    conn.close()
    return folder_list, unassigned_list

def get_deck_card_stats(deck_id, now):
    conn = get_db_connection()
    # Fetch all cards in this deck
    rows = conn.execute("""
        SELECT c.reps, c.next_review FROM cards c
        JOIN card_decks cd ON c.id = cd.card_id
        WHERE cd.deck_id = ?
    """, (deck_id,)).fetchall()
    conn.close()
    
    new_count = 0
    due_count = 0
    for r in rows:
        reps = r['reps'] or 0
        next_review_str = r['next_review']
        next_review = parse_db_datetime(next_review_str)
        
        if reps == 0:
            new_count += 1
        elif next_review and next_review <= now:
            due_count += 1
            
    return {"new_count": new_count, "due_count": due_count}

def create_folder(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO folders (name) VALUES (?)", (name,))
    conn.commit()
    folder_id = cur.lastrowid
    conn.close()
    return folder_id

def delete_folder(folder_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    conn.execute("DELETE FROM deck_folders WHERE folder_id = ?", (folder_id,))
    conn.commit()
    conn.close()

def create_deck(name, folder_ids=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO decks (name) VALUES (?)", (name,))
    conn.commit()
    deck_id = cur.lastrowid
    
    if folder_ids:
        for fid in folder_ids:
            cur.execute("INSERT INTO deck_folders (deck_id, folder_id) VALUES (?, ?)", (deck_id, fid))
        conn.commit()
        
    conn.close()
    return deck_id

def update_deck(deck_id, name, folder_ids=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE decks SET name = ? WHERE id = ?", (name, deck_id))
    cur.execute("DELETE FROM deck_folders WHERE deck_id = ?", (deck_id,))
    if folder_ids:
        for fid in folder_ids:
            cur.execute("INSERT INTO deck_folders (deck_id, folder_id) VALUES (?, ?)", (deck_id, fid))
    conn.commit()
    conn.close()

def delete_deck(deck_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
    conn.execute("DELETE FROM deck_folders WHERE deck_id = ?", (deck_id,))
    conn.execute("DELETE FROM card_decks WHERE deck_id = ?", (deck_id,))
    conn.commit()
    conn.close()

def get_deck_folders(deck_id):
    conn = get_db_connection()
    rows = conn.execute("SELECT folder_id FROM deck_folders WHERE deck_id = ?", (deck_id,)).fetchall()
    conn.close()
    return [r['folder_id'] for r in rows]

# Card Management

def get_all_cards_paged(search="", page=1, limit=50):
    conn = get_db_connection()
    offset = (page - 1) * limit
    
    query = "SELECT * FROM cards"
    params = []
    if search:
        query += " WHERE front LIKE ? OR back LIKE ?"
        params.extend([f"%{search}%", f"%{search}%"])
        
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cards = conn.execute(query, params).fetchall()
    
    # Total count
    count_query = "SELECT COUNT(*) FROM cards"
    count_params = []
    if search:
        count_query += " WHERE front LIKE ? OR back LIKE ?"
        count_params.extend([f"%{search}%", f"%{search}%"])
    total = conn.execute(count_query, count_params).fetchone()[0]
    
    # Get deck mapping for each card
    card_list = []
    for c in cards:
        c_dict = dict(c)
        decks = conn.execute("""
            SELECT d.name FROM decks d
            JOIN card_decks cd ON d.id = cd.deck_id
            WHERE cd.card_id = ?
        """, (c['id'],)).fetchall()
        c_dict['deck_names'] = [d['name'] for d in decks]
        card_list.append(c_dict)
        
    conn.close()
    return card_list, total

def get_card_by_id(card_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row:
        c_dict = dict(row)
        decks = conn.execute("SELECT deck_id FROM card_decks WHERE card_id = ?", (card_id,)).fetchall()
        c_dict['deck_ids'] = [d['deck_id'] for d in decks]
        conn.close()
        return c_dict
    conn.close()
    return None

def add_card(front, back, card_type, deck_ids):
    conn = get_db_connection()
    cur = conn.cursor()
    
    front = front.strip()
    back = back.strip()
    
    # Check if duplicate front exists
    existing = cur.execute("SELECT * FROM cards WHERE front = ?", (front,)).fetchone()
    
    if existing:
        # Merge duplicates: append new back to existing back with double newline
        merged_back = existing['back'] + "\n\n" + back
        cur.execute("UPDATE cards SET back = ? WHERE id = ?", (merged_back, existing['id']))
        card_id = existing['id']
        
        # Link card to deck_ids if not already linked
        for did in deck_ids:
            link = cur.execute("SELECT 1 FROM card_decks WHERE card_id = ? AND deck_id = ?", (card_id, did)).fetchone()
            if not link:
                cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, did))
        conn.commit()
        conn.close()
        return card_id, True  # True means merged
    else:
        # Insert new card
        now_str = format_datetime_for_db(datetime.now(timezone.utc))
        cur.execute("""
            INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (front, back, now_str, 1, 0, None, None, None, 0, 0, card_type))
        card_id = cur.lastrowid
        
        # Link card to deck_ids
        for did in deck_ids:
            cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, did))
            
        conn.commit()
        conn.close()
        return card_id, False  # False means new

def update_card(card_id, front, back, card_type, deck_ids):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE cards 
        SET front = ?, back = ?, card_type = ?
        WHERE id = ?
    """, (front.strip(), back.strip(), card_type, card_id))
    
    # Update deck associations
    cur.execute("DELETE FROM card_decks WHERE card_id = ?", (card_id,))
    for did in deck_ids:
        cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, did))
        
    conn.commit()
    conn.close()

def delete_card(card_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.execute("DELETE FROM card_decks WHERE card_id = ?", (card_id,))
    conn.commit()
    conn.close()

# Batch CSV Import

def import_csv_data(csv_text, deck_ids):
    conn = get_db_connection()
    cur = conn.cursor()
    
    reader = csv.reader(csv_text.strip().splitlines())
    imported_count = 0
    merged_count = 0
    
    now_str = format_datetime_for_db(datetime.now(timezone.utc))
    
    for row in reader:
        if not row or len(row) < 2:
            continue
        front = row[0].strip()
        back = row[1].strip()
        card_type = row[2].strip() if len(row) > 2 else "recognize"
        if card_type not in ["recognize", "spell"]:
            card_type = "recognize"
            
        if not front or not back:
            continue
            
        # Check duplicate
        existing = cur.execute("SELECT * FROM cards WHERE front = ?", (front,)).fetchone()
        
        if existing:
            merged_back = existing['back'] + "\n\n" + back
            cur.execute("UPDATE cards SET back = ? WHERE id = ?", (merged_back, existing['id']))
            card_id = existing['id']
            merged_count += 1
        else:
            cur.execute("""
                INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (front, back, now_str, 1, 0, None, None, None, 0, 0, card_type))
            card_id = cur.lastrowid
            imported_count += 1
            
        # Link card to deck_ids
        for did in deck_ids:
            link = cur.execute("SELECT 1 FROM card_decks WHERE card_id = ? AND deck_id = ?", (card_id, did)).fetchone()
            if not link:
                cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, did))
                
    conn.commit()
    conn.close()
    
    # Send Discord notification
    if imported_count > 0 or merged_count > 0:
        msg = f"📋 批次匯入成功！\n- 新增單字卡：{imported_count} 張\n- 合併重複卡：{merged_count} 張"
        send_discord_message(msg)
        
    return imported_count, merged_count

# Spaced Repetition (FSRS) Study

def get_study_cards(deck_id=None, folder_id=None):
    """
    Get all cards that are new (reps = 0) or due (next_review <= now) for a deck or a folder.
    """
    conn = get_db_connection()
    now = datetime.now(timezone.utc)
    
    query = """
        SELECT DISTINCT c.* FROM cards c
        JOIN card_decks cd ON c.id = cd.card_id
    """
    params = []
    
    if deck_id:
        query += " WHERE cd.deck_id = ?"
        params.append(deck_id)
    elif folder_id:
        query += """
            JOIN deck_folders df ON cd.deck_id = df.deck_id
            WHERE df.folder_id = ?
        """
        params.append(folder_id)
        
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    new_cards = []
    due_cards = []
    
    for r in rows:
        c_dict = dict(r)
        reps = r['reps'] or 0
        next_review_str = r['next_review']
        next_review = parse_db_datetime(next_review_str)
        
        if reps == 0:
            new_cards.append(c_dict)
        elif next_review and next_review <= now:
            due_cards.append(c_dict)
            
    return new_cards, due_cards

def submit_card_review(card_id, rating_val):
    """
    Review a card using FSRS algorithm and update SQLite fields.
    rating_val: 1=Again, 2=Hard, 3=Good, 4=Easy
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    row = cur.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not row:
        conn.close()
        return None
        
    # Map db row to fsrs.Card
    card = Card()
    card.state = State(row['state'])
    card.step = row['step'] or 0
    card.stability = row['stability']
    card.difficulty = row['difficulty']
    card.last_review = parse_db_datetime(row['last_review'])
    card.due = parse_db_datetime(row['next_review'])
    
    # Initialize scheduler
    s = Scheduler()
    now = datetime.now(timezone.utc)
    
    # Calculate scheduling
    new_card, review_log = s.review_card(card, Rating(rating_val), now)
    
    # Calculate reps and lapses
    reps = (row['reps'] or 0) + 1
    lapses = row['lapses'] or 0
    if rating_val == 1: # Rating.Again
        lapses += 1
        
    # Format datetimes
    last_review_str = format_datetime_for_db(new_card.last_review)
    next_review_str = format_datetime_for_db(new_card.due)
    
    cur.execute("""
        UPDATE cards
        SET state = ?, step = ?, stability = ?, difficulty = ?, last_review = ?, next_review = ?, reps = ?, lapses = ?
        WHERE id = ?
    """, (
        new_card.state.value,
        new_card.step,
        new_card.stability,
        new_card.difficulty,
        last_review_str,
        next_review_str,
        reps,
        lapses,
        card_id
    ))
    
    # Track setting stats or send discord webhook
    conn.commit()
    
    # Fetch deck names for notification
    decks = conn.execute("""
        SELECT d.name FROM decks d
        JOIN card_decks cd ON d.id = cd.deck_id
        WHERE cd.card_id = ?
    """, (card_id,)).fetchall()
    deck_names = ", ".join([d['name'] for d in decks])
    
    conn.close()
    
    # Discord notification logic
    rating_map = {1: "忘記 (Again)", 2: "困難 (Hard)", 3: "普通 (Good)", 4: "簡單 (Easy)"}
    msg = f"🧠 記憶卡複習通知：\n- 單字：{row['front']}\n- 評分：{rating_map.get(rating_val, '未知')}\n- 牌組：{deck_names}\n- 下次複習時間：{next_review_str}"
    send_discord_message(msg)
    
    return next_review_str

# System/Settings Operations

def reset_all_learning_progress():
    conn = get_db_connection()
    now_str = format_datetime_for_db(datetime.now(timezone.utc))
    conn.execute("""
        UPDATE cards
        SET state = 1, step = 0, stability = NULL, difficulty = NULL, last_review = NULL, next_review = ?, reps = 0, lapses = 0
    """, (now_str,))
    conn.commit()
    conn.close()
    send_discord_message("⚠️ 所有記憶卡的學習進度已重置！")

def delete_all_app_data():
    conn = get_db_connection()
    conn.execute("DELETE FROM cards")
    conn.execute("DELETE FROM card_decks")
    conn.execute("DELETE FROM decks")
    conn.execute("DELETE FROM folders")
    conn.execute("DELETE FROM deck_folders")
    conn.execute("DELETE FROM sqlite_sequence") # Reset autoincrement ids
    conn.commit()
    conn.close()
    send_discord_message("🔥 所有卡片、牌組與資料夾的資料已被清空！")

def get_setting(key, default=None):
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    if row:
        return row['value']
    return default

def set_setting(key, value):
    conn = get_db_connection()
    cur = conn.cursor()
    # Check if exists
    row = cur.execute("SELECT 1 FROM settings WHERE key = ?", (key,)).fetchone()
    if row:
        cur.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    else:
        cur.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

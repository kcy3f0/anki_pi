import sqlite3
import os
import csv
import math
import random
from datetime import datetime, timezone, timedelta
import requests
from fsrs import Scheduler, Card, Rating, State
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=30.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

import re

def parse_db_datetime(dt_str):
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    
    tz_match = re.search(r'([+-]\d{2}:?\d{2}|Z)$', dt_str)
    tz_part = tz_match.group(1) if tz_match else ""
    if tz_part:
        dt_str = dt_str[:-len(tz_part)]
        
    if '.' in dt_str:
        base, micro = dt_str.split('.')
        micro = micro[:6]
        dt_str = f"{base}.{micro}"
        
    try:
        dt = datetime.fromisoformat(dt_str)
        if tz_part == 'Z' or tz_part == '+00:00' or not tz_part:
            return dt.replace(tzinfo=timezone.utc)
        else:
            tz_info = datetime.fromisoformat(f"2020-01-01T00:00:00{tz_part}").tzinfo
            return dt.replace(tzinfo=tz_info).astimezone(timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
                try:
                    return datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            return None

def format_datetime_for_db(dt):
    if not dt:
        return None
    return dt.isoformat()

import threading

def send_discord_message(content):
    url = Config.DISCORD_WEBHOOK_URL
    if not url:
        return
    def run_send():
        try:
            requests.post(url, json={"content": content}, timeout=5)
        except Exception as e:
            print(f"Error sending Discord Webhook: {e}")
    threading.Thread(target=run_send, daemon=True).start()

# Folder and Deck CRUD

def get_all_folders():
    conn = get_db_connection()
    try:
        return conn.execute("SELECT * FROM folders").fetchall()
    finally:
        conn.close()

def get_all_decks():
    conn = get_db_connection()
    try:
        return conn.execute("SELECT * FROM decks").fetchall()
    finally:
        conn.close()

def get_folders_with_decks():
    conn = get_db_connection()
    try:
        now = datetime.now(timezone.utc)
        now_str = format_datetime_for_db(now)
        
        folders = conn.execute("SELECT * FROM folders").fetchall()
        folder_list = []
        
        stats_query = """
            SELECT cd.deck_id, 
                   SUM(CASE WHEN c.reps = 0 OR c.reps IS NULL THEN 1 ELSE 0 END) as new_count,
                   SUM(CASE WHEN c.reps > 0 AND c.next_review <= ? THEN 1 ELSE 0 END) as due_count
            FROM card_decks cd
            JOIN cards c ON cd.card_id = c.id
            GROUP BY cd.deck_id
        """
        stats_rows = conn.execute(stats_query, (now_str,)).fetchall()
        deck_stats = {row['deck_id']: {"new_count": row['new_count'], "due_count": row['due_count']} for row in stats_rows}
        
        for f in folders:
            f_dict = dict(f)
            decks = conn.execute("""
                SELECT d.* FROM decks d
                JOIN deck_folders df ON d.id = df.deck_id
                WHERE df.folder_id = ?
            """, (f['id'],)).fetchall()
            
            deck_list = []
            for d in decks:
                d_dict = dict(d)
                stats = deck_stats.get(d['id'], {"new_count": 0, "due_count": 0})
                d_dict.update(stats)
                deck_list.append(d_dict)
                
            f_dict['decks'] = deck_list
            folder_list.append(f_dict)
            
        unassigned_decks = conn.execute("""
            SELECT d.* FROM decks d
            LEFT JOIN deck_folders df ON d.id = df.deck_id
            WHERE df.folder_id IS NULL
        """).fetchall()
        
        unassigned_list = []
        for d in unassigned_decks:
            d_dict = dict(d)
            stats = deck_stats.get(d['id'], {"new_count": 0, "due_count": 0})
            d_dict.update(stats)
            unassigned_list.append(d_dict)
            
        return folder_list, unassigned_list
    finally:
        conn.close()

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
    try:
        with conn:
            conn.execute("DELETE FROM deck_folders WHERE folder_id = ?", (folder_id,))
            conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    finally:
        conn.close()

def create_deck(name, folder_ids=None):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO decks (name) VALUES (?)", (name,))
            deck_id = cur.lastrowid
            
            if folder_ids:
                for fid in folder_ids:
                    cur.execute("INSERT INTO deck_folders (deck_id, folder_id) VALUES (?, ?)", (deck_id, fid))
            return deck_id
    finally:
        conn.close()

def update_deck(deck_id, name, folder_ids=None):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE decks SET name = ? WHERE id = ?", (name, deck_id))
            cur.execute("DELETE FROM deck_folders WHERE deck_id = ?", (deck_id,))
            if folder_ids:
                for fid in folder_ids:
                    cur.execute("INSERT INTO deck_folders (deck_id, folder_id) VALUES (?, ?)", (deck_id, fid))
    finally:
        conn.close()

def delete_deck(deck_id):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM deck_folders WHERE deck_id = ?", (deck_id,))
            conn.execute("DELETE FROM card_decks WHERE deck_id = ?", (deck_id,))
            conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
            conn.execute("DELETE FROM cards WHERE id NOT IN (SELECT DISTINCT card_id FROM card_decks)")
    finally:
        conn.close()

def get_deck_folders(deck_id):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT folder_id FROM deck_folders WHERE deck_id = ?", (deck_id,)).fetchall()
        return [r['folder_id'] for r in rows]
    finally:
        conn.close()

# Card Management

def get_all_cards_paged(search="", page=1, limit=50, deck_id=None):
    conn = get_db_connection()
    try:
        offset = (page - 1) * limit
        
        if deck_id:
            query = "SELECT c.* FROM cards c JOIN card_decks cd ON c.id = cd.card_id WHERE cd.deck_id = ?"
            params = [deck_id]
            if search:
                query += " AND (c.front LIKE ? OR c.back LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])
        else:
            query = "SELECT c.* FROM cards c"
            params = []
            if search:
                query += " WHERE c.front LIKE ? OR c.back LIKE ?"
                params.extend([f"%{search}%", f"%{search}%"])
            
        query += " ORDER BY c.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cards = conn.execute(query, params).fetchall()
        
        if deck_id:
            count_query = "SELECT COUNT(*) FROM cards c JOIN card_decks cd ON c.id = cd.card_id WHERE cd.deck_id = ?"
            count_params = [deck_id]
            if search:
                count_query += " AND (c.front LIKE ? OR c.back LIKE ?)"
                count_params.extend([f"%{search}%", f"%{search}%"])
        else:
            count_query = "SELECT COUNT(*) FROM cards"
            count_params = []
            if search:
                count_query += " WHERE front LIKE ? OR back LIKE ?"
                count_params.extend([f"%{search}%", f"%{search}%"])
                
        total = conn.execute(count_query, count_params).fetchone()[0]
        
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
            
        return card_list, total
    finally:
        conn.close()

def get_card_by_id(card_id):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if row:
            c_dict = dict(row)
            decks = conn.execute("SELECT deck_id FROM card_decks WHERE card_id = ?", (card_id,)).fetchall()
            c_dict['deck_ids'] = [d['deck_id'] for d in decks]
            return c_dict
        return None
    finally:
        conn.close()

def add_card(front, back, card_type, deck_ids):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            front = front.strip()
            back = back.strip()
            
            existing = cur.execute("SELECT * FROM cards WHERE front = ?", (front,)).fetchone()
            
            if existing:
                merged_back = existing['back'] + "\n\n" + back
                new_card_type = 'spell' if (existing['card_type'] == 'spell' or card_type == 'spell') else (existing['card_type'] or 'recognize')
                cur.execute("UPDATE cards SET back = ?, card_type = ? WHERE id = ?", (merged_back, new_card_type, existing['id']))
                card_id = existing['id']
                merged = True
            else:
                now_str = format_datetime_for_db(datetime.now(timezone.utc))
                cur.execute("""
                    INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (front, back, now_str, 0, 0, None, None, None, 0, 0, card_type))
                card_id = cur.lastrowid
                merged = False
                
            for did in deck_ids:
                link = cur.execute("SELECT 1 FROM card_decks WHERE card_id = ? AND deck_id = ?", (card_id, did)).fetchone()
                if not link:
                    cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, did))
                    
            return card_id, merged
    finally:
        conn.close()

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
    try:
        with conn:
            conn.execute("DELETE FROM card_decks WHERE card_id = ?", (card_id,))
            conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    finally:
        conn.close()

# Batch CSV Import

import io

def import_csv_data(csv_text, deck_ids, card_type="recognize"):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            try:
                reader = csv.reader(io.StringIO(csv_text.strip()))
            except csv.Error as e:
                raise ValueError(f"CSV 格式解析失敗：{str(e)}")
                
            imported_count = 0
            merged_count = 0
            now_str = format_datetime_for_db(datetime.now(timezone.utc))
            if card_type not in ["recognize", "spell"]:
                card_type = "recognize"
            
            for row in reader:
                try:
                    if not row or len(row) < 2:
                        continue
                    front = row[0].strip()
                    back = row[1].strip()
                    if not front or not back:
                        continue
                        
                    existing = cur.execute("SELECT * FROM cards WHERE front = ?", (front,)).fetchone()
                    if existing:
                        merged_back = existing['back'] + "\n\n" + back
                        new_card_type = 'spell' if (existing['card_type'] == 'spell' or card_type == 'spell') else (existing['card_type'] or 'recognize')
                        cur.execute("UPDATE cards SET back = ?, card_type = ? WHERE id = ?", (merged_back, new_card_type, existing['id']))
                        card_id = existing['id']
                        merged_count += 1
                    else:
                        cur.execute("""
                            INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (front, back, now_str, 0, 0, None, None, None, 0, 0, card_type))
                        card_id = cur.lastrowid
                        imported_count += 1
                        
                    for did in deck_ids:
                        link = cur.execute("SELECT 1 FROM card_decks WHERE card_id = ? AND deck_id = ?", (card_id, did)).fetchone()
                        if not link:
                            cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, did))
                except IndexError:
                    raise ValueError("CSV 檔案中有些行缺少必要的欄位！")
            
        if imported_count > 0 or merged_count > 0:
            msg = f"📋 批次匯入成功！\n- 新增單字卡：{imported_count} 張\n- 合併重複卡：{merged_count} 張"
            send_discord_message(msg)
            
        return imported_count, merged_count
    finally:
        conn.close()

# Spaced Repetition (FSRS) Study

def _get_earliest_exam_date(conn, deck_id, folder_id, now, exam_id=None):
    """Find the earliest upcoming exam date for a given deck, folder, or specific exam scope."""
    if exam_id:
        row = conn.execute("SELECT date as min_date FROM exams WHERE id = ?", (exam_id,)).fetchone()
        if row and row['min_date']:
            return parse_db_datetime(row['min_date'])
        return None

    now_str = format_datetime_for_db(now)

    if deck_id:
        row = conn.execute("""
            SELECT MIN(e.date) as min_date FROM exams e
            WHERE e.date > ? AND e.processed = 0
            AND (
                e.id IN (SELECT exam_id FROM exam_decks WHERE deck_id = ?)
                OR e.id IN (
                    SELECT exam_id FROM exam_folders WHERE folder_id IN (
                        SELECT folder_id FROM deck_folders WHERE deck_id = ?
                    )
                )
            )
        """, (now_str, deck_id, deck_id)).fetchone()
    elif folder_id:
        row = conn.execute("""
            SELECT MIN(e.date) as min_date FROM exams e
            WHERE e.date > ? AND e.processed = 0
            AND (
                e.id IN (
                    SELECT exam_id FROM exam_decks WHERE deck_id IN (
                        SELECT deck_id FROM deck_folders WHERE folder_id = ?
                    )
                )
                OR e.id IN (SELECT exam_id FROM exam_folders WHERE folder_id = ?)
            )
        """, (now_str, folder_id, folder_id)).fetchone()
    else:
        return None

    if row and row['min_date']:
        return parse_db_datetime(row['min_date'])
    return None

def get_study_cards(deck_id=None, folder_id=None, exam_id=None):
    """
    Get cards for today's study session.
    - due_cards: FSRS scheduled reviews (next_review <= now)
    - new_cards: unseen cards (reps = 0), dynamically limited by exam schedule
      If an exam exists, new cards are capped so all are seen 7 days before exam.
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
    elif exam_id:
        query += """
            WHERE cd.deck_id IN (
                SELECT deck_id FROM exam_decks WHERE exam_id = ?
                UNION
                SELECT deck_id FROM deck_folders WHERE folder_id IN (
                    SELECT folder_id FROM exam_folders WHERE exam_id = ?
                )
            )
        """
        params.extend([exam_id, exam_id])

    rows = conn.execute(query, params).fetchall()

    # Query exam date before closing connection
    earliest_exam_date = _get_earliest_exam_date(conn, deck_id, folder_id, now, exam_id=exam_id)

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

    # Dynamically limit new cards based on exam schedule
    if earliest_exam_date and new_cards:
        total_days = (earliest_exam_date.date() - now.date()).days
        if total_days > 0:
            cutoff_date = earliest_exam_date - timedelta(days=7)
            days_to_cutoff = (cutoff_date.date() - now.date()).days

            if days_to_cutoff > 0:
                # Before cutoff: distribute new cards across days until cutoff
                days_for_new = days_to_cutoff
            else:
                # Past cutoff: distribute across all remaining days before exam
                days_for_new = max(1, total_days)

            date_str = now.strftime('%Y-%m-%d')
            if deck_id:
                scope_key = f"deck_{deck_id}"
            elif folder_id:
                scope_key = f"folder_{folder_id}"
            elif exam_id:
                scope_key = f"exam_{exam_id}"
            else:
                scope_key = "all"
                
            setting_key = f"daily_new_{scope_key}_{date_str}"
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (setting_key,)).fetchone()
            
            current_new = len(new_cards)
            start_count = current_new
            
            if row:
                start_count = int(row['value'])
                if current_new > start_count:
                    start_count = current_new
                    conn.execute("UPDATE settings SET value = ? WHERE key = ?", (str(start_count), setting_key))
                    conn.commit()
            else:
                conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (setting_key, str(start_count)))
                conn.commit()

            quota = math.ceil(start_count / days_for_new)
            learned_today = start_count - current_new
            today_new_count = max(0, quota - learned_today)

            random.shuffle(new_cards)
            new_cards = new_cards[:today_new_count]

    conn.close()
    return new_cards, due_cards

def submit_card_review(card_id, rating_val):
    retention_val = get_setting('desired_retention', '0.9')
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            
            row = cur.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
            if not row:
                return None
                
            card = Card()
            db_state = row['state']
            reps = row['reps'] or 0
            if db_state == 0 or reps == 0:
                db_state = 1
            card.state = State(db_state)
            card.step = row['step'] or 0
            card.stability = row['stability']
            card.difficulty = row['difficulty']
            card.last_review = parse_db_datetime(row['last_review'])
            card.due = parse_db_datetime(row['next_review'])
            
            try:
                retention = float(retention_val)
            except (ValueError, TypeError):
                retention = 0.9
                
            weights_str = get_setting('fsrs_weights', '')
            try:
                parameters = tuple(float(w.strip()) for w in weights_str.split(',')) if weights_str else ()
            except ValueError:
                parameters = ()
                
            if len(parameters) == 21:
                s = Scheduler(parameters=parameters, desired_retention=retention)
            else:
                s = Scheduler(desired_retention=retention)
            now = datetime.now(timezone.utc)
            
            new_card, review_log = s.review_card(card, Rating(rating_val), now)
            
            reps = reps + 1
            lapses = row['lapses'] or 0
            if rating_val == 1:
                lapses += 1
                
            cur.execute("""
                INSERT INTO revlog (card_id, review_time, review_rating, review_state, review_duration)
                VALUES (?, ?, ?, ?, ?)
            """, (card_id, format_datetime_for_db(now), rating_val, db_state, 0))
                
            earliest_exam_row = cur.execute("""
                SELECT MIN(e.date) FROM exams e
                WHERE e.date > ? AND e.processed = 0
                  AND (
                      e.id IN (
                          SELECT exam_id FROM exam_decks
                          WHERE deck_id IN (SELECT deck_id FROM card_decks WHERE card_id = ?)
                      )
                      OR
                      e.id IN (
                          SELECT exam_id FROM exam_folders
                          WHERE folder_id IN (
                              SELECT folder_id FROM deck_folders
                              WHERE deck_id IN (SELECT deck_id FROM card_decks WHERE card_id = ?)
                          )
                      )
                  )
            """, (format_datetime_for_db(now), card_id, card_id)).fetchone()
            
            adjusted_due = new_card.due
            if earliest_exam_row and earliest_exam_row[0]:
                earliest_exam_date = parse_db_datetime(earliest_exam_row[0])
                if adjusted_due >= earliest_exam_date:
                    capped_due = earliest_exam_date - timedelta(days=1)
                    if capped_due < now:
                        capped_due = now
                    adjusted_due = capped_due

            last_review_str = format_datetime_for_db(new_card.last_review)
            next_review_str = format_datetime_for_db(adjusted_due)
            
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
            
            decks = cur.execute("""
                SELECT d.name FROM decks d
                JOIN card_decks cd ON d.id = cd.deck_id
                WHERE cd.card_id = ?
            """, (card_id,)).fetchall()
            deck_names = ", ".join([d['name'] for d in decks])
            
        rating_map = {1: "忘記 (Again)", 2: "困難 (Hard)", 3: "普通 (Good)", 4: "簡單 (Easy)"}
        msg = f"🧠 記憶卡複習通知：\n- 單字：{row['front']}\n- 評分：{rating_map.get(rating_val, '未知')}\n- 牌組：{deck_names}\n- 下次複習時間：{next_review_str}"
        send_discord_message(msg)
        
        return next_review_str
    finally:
        conn.close()

# System/Settings Operations

def reset_all_learning_progress():
    conn = get_db_connection()
    try:
        with conn:
            now_str = format_datetime_for_db(datetime.now(timezone.utc))
            conn.execute("""
                UPDATE cards
                SET state = 0, step = 0, stability = NULL, difficulty = NULL, last_review = NULL, next_review = ?, reps = 0, lapses = 0
            """, (now_str,))
    finally:
        conn.close()
    send_discord_message("⚠️ 所有記憶卡的學習進度已重置！")

def delete_all_app_data():
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM cards")
            conn.execute("DELETE FROM card_decks")
            conn.execute("DELETE FROM decks")
            conn.execute("DELETE FROM folders")
            conn.execute("DELETE FROM deck_folders")
            conn.execute("DELETE FROM exams")
            conn.execute("DELETE FROM exam_decks")
            conn.execute("DELETE FROM exam_folders")
            conn.execute("DELETE FROM sqlite_sequence")
    finally:
        conn.close()
    send_discord_message("🔥 所有卡片、牌組與資料夾的資料已被清空！")

def get_setting(key, default=None):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row:
            return row['value']
        return default
    finally:
        conn.close()

def set_setting(key, value):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            # Check if exists
            row = cur.execute("SELECT 1 FROM settings WHERE key = ?", (key,)).fetchone()
            if row:
                cur.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
            else:
                cur.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
    finally:
        conn.close()

# --- Exam Schedule & Vocabulary Adjustments ---

def parse_input_datetime(date_str):
    try:
        dt = datetime.fromisoformat(date_str.strip())
    except Exception:
        try:
            dt = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        except Exception:
            try:
                dt = datetime.strptime(date_str.strip()[:10], "%Y/%m/%d")
            except Exception:
                dt = datetime.now(timezone.utc)
                
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
        
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def distribute_exam_cards(exam_id):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()

            exam = cur.execute("SELECT date FROM exams WHERE id = ?", (exam_id,)).fetchone()
            if not exam:
                return

            exam_date = parse_db_datetime(exam['date'])
            if not exam_date:
                return

            rows = cur.execute("""
                SELECT id, reps, next_review FROM cards
                WHERE id IN (
                    SELECT DISTINCT cd.card_id FROM card_decks cd
                    WHERE cd.deck_id IN (
                        SELECT deck_id FROM exam_decks WHERE exam_id = ?
                        UNION
                        SELECT deck_id FROM deck_folders WHERE folder_id IN (
                            SELECT folder_id FROM exam_folders WHERE exam_id = ?
                        )
                    )
                )
            """, (exam_id, exam_id)).fetchall()

            now = datetime.now(timezone.utc)
            total_days = (exam_date.date() - now.date()).days

            if total_days <= 0:
                return

            new_card_ids = []
            late_card_ids = []

            for r in rows:
                reps = r['reps'] or 0
                next_review = parse_db_datetime(r['next_review'])

                if reps == 0:
                    new_card_ids.append(r['id'])
                elif next_review and next_review > exam_date:
                    late_card_ids.append(r['id'])

            if not new_card_ids and not late_card_ids:
                return

            cutoff_date = exam_date - timedelta(days=7)
            days_to_cutoff = (cutoff_date.date() - now.date()).days

            if days_to_cutoff > 0:
                days_for_new = days_to_cutoff
            else:
                days_for_new = max(1, total_days)

            updates = []
            if new_card_ids:
                random.shuffle(new_card_ids)
                for i, card_id in enumerate(new_card_ids):
                    day_offset = i % days_for_new
                    jitter_minutes = random.randint(0, 60)
                    scheduled_dt = now + timedelta(days=day_offset, minutes=jitter_minutes)

                    cap_date = cutoff_date if days_to_cutoff > 0 else exam_date
                    if scheduled_dt >= cap_date:
                        scheduled_dt = cap_date - timedelta(minutes=1)

                    scheduled_str = format_datetime_for_db(scheduled_dt)
                    updates.append((scheduled_str, card_id))

            if late_card_ids:
                random.shuffle(late_card_ids)
                slots = days_for_new
                for i, card_id in enumerate(late_card_ids):
                    day_offset = i % slots
                    jitter_minutes = random.randint(0, 60)
                    scheduled_dt = now + timedelta(days=day_offset, minutes=jitter_minutes)

                    cap_date = cutoff_date if days_to_cutoff > 0 else exam_date
                    if scheduled_dt >= cap_date:
                        scheduled_dt = cap_date - timedelta(minutes=1)

                    scheduled_str = format_datetime_for_db(scheduled_dt)
                    updates.append((scheduled_str, card_id))

            if updates:
                cur.executemany("UPDATE cards SET next_review = ? WHERE id = ?", updates)

    finally:
        conn.close()

def process_expired_exams():
    conn = get_db_connection()
    exams_to_distribute = []
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)
        now_str = format_datetime_for_db(now)
        
        # Find all expired exams that are not processed yet
        expired = cur.execute("SELECT id FROM exams WHERE date <= ? AND processed = 0", (now_str,)).fetchall()
        
        for row in expired:
            expired_id = row['id']
            
            # Get decks in the expired exam
            expired_decks = cur.execute("""
                SELECT deck_id FROM exam_decks WHERE exam_id = ?
                UNION
                SELECT deck_id FROM deck_folders WHERE folder_id IN (
                    SELECT folder_id FROM exam_folders WHERE exam_id = ?
                )
            """, (expired_id, expired_id)).fetchall()
            expired_deck_ids = [d['deck_id'] for d in expired_decks]
            
            # Mark as processed
            cur.execute("UPDATE exams SET processed = 1 WHERE id = ?", (expired_id,))
            conn.commit()
            
            # If there are decks, check overlapping upcoming exams
            if expired_deck_ids:
                upcoming = cur.execute("SELECT id FROM exams WHERE date > ? AND processed = 0 ORDER BY date ASC", (now_str,)).fetchall()
                for u_row in upcoming:
                    u_id = u_row['id']
                    u_decks = cur.execute("""
                        SELECT deck_id FROM exam_decks WHERE exam_id = ?
                        UNION
                        SELECT deck_id FROM deck_folders WHERE folder_id IN (
                            SELECT folder_id FROM exam_folders WHERE exam_id = ?
                        )
                    """, (u_id, u_id)).fetchall()
                    u_deck_ids = [d['deck_id'] for d in u_decks]
                    
                    # Check overlap
                    if any(d in expired_deck_ids for d in u_deck_ids):
                        exams_to_distribute.append(u_id)
                        break
    finally:
        conn.close()
        
    for u_id in exams_to_distribute:
        distribute_exam_cards(u_id)

def get_all_exams():
    conn = get_db_connection()
    try:
        exams = conn.execute("SELECT * FROM exams ORDER BY date ASC").fetchall()
        
        exam_list = []
        now = datetime.now(timezone.utc)
        
        for e in exams:
            e_dict = dict(e)
            exam_id = e['id']
            
            # Get associated decks
            decks = conn.execute("""
                SELECT d.id, d.name FROM decks d
                JOIN exam_decks ed ON d.id = ed.deck_id
                WHERE ed.exam_id = ?
            """, (exam_id,)).fetchall()
            e_dict['decks'] = [dict(d) for d in decks]
            
            # Get associated folders
            folders = conn.execute("""
                SELECT f.id, f.name FROM folders f
                JOIN exam_folders ef ON f.id = ef.folder_id
                WHERE ef.exam_id = ?
            """, (exam_id,)).fetchall()
            e_dict['folders'] = [dict(f) for f in folders]
            
            # Calculate stats and progress
            cards = conn.execute("""
                SELECT c.id, c.reps, c.next_review FROM cards c
                WHERE c.id IN (
                    SELECT cd.card_id FROM card_decks cd
                    WHERE cd.deck_id IN (
                        SELECT deck_id FROM exam_decks WHERE exam_id = ?
                        UNION
                        SELECT deck_id FROM deck_folders WHERE folder_id IN (
                            SELECT folder_id FROM exam_folders WHERE exam_id = ?
                        )
                    )
                )
            """, (exam_id, exam_id)).fetchall()
            
            total_cards = len(cards)
            learned_cards = sum(1 for c in cards if (c['reps'] or 0) > 0)
            
            e_dict['total_cards'] = total_cards
            e_dict['learned_cards'] = learned_cards
            e_dict['progress_percent'] = int((learned_cards / total_cards * 100)) if total_cards > 0 else 0
            
            # Countdown details
            exam_date = parse_db_datetime(e['date'])
            delta = exam_date - now
            e_dict['days_remaining'] = delta.days
            e_dict['seconds_remaining'] = int(delta.total_seconds())
            
            if delta.total_seconds() <= 0:
                e_dict['countdown_str'] = "已結束"
                e_dict['is_expired'] = True
            else:
                e_dict['is_expired'] = False
                days = delta.days
                hours = int((delta.total_seconds() % 86400) // 3600)
                if days > 0:
                    e_dict['countdown_str'] = f"剩餘 {days} 天 {hours} 小時"
                else:
                    minutes = int((delta.total_seconds() % 3600) // 60)
                    e_dict['countdown_str'] = f"剩餘 {hours} 小時 {minutes} 分鐘"
                    
            exam_list.append(e_dict)
            
        return exam_list
    finally:
        conn.close()

def create_exam(name, date_str, deck_ids=None, folder_ids=None):
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            utc_dt = parse_input_datetime(date_str)
            date_formatted = format_datetime_for_db(utc_dt)
            
            cur.execute("INSERT INTO exams (name, date) VALUES (?, ?)", (name.strip(), date_formatted))
            exam_id = cur.lastrowid
            
            if deck_ids:
                for did in deck_ids:
                    cur.execute("INSERT INTO exam_decks (exam_id, deck_id) VALUES (?, ?)", (exam_id, did))
                    
            if folder_ids:
                for fid in folder_ids:
                    cur.execute("INSERT INTO exam_folders (exam_id, folder_id) VALUES (?, ?)", (exam_id, fid))
    finally:
        conn.close()
    
    distribute_exam_cards(exam_id)
    msg = f"📅 新增考試行程通知：\n- 考試：{name.strip()}\n- 日期：{utc_dt.astimezone().strftime('%Y/%m/%d')}"
    send_discord_message(msg)
    return exam_id

def delete_exam(exam_id):
    conn = get_db_connection()
    try:
        with conn:
            exam = conn.execute("SELECT name FROM exams WHERE id = ?", (exam_id,)).fetchone()
            conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
    finally:
        conn.close()
    if exam:
        send_discord_message(f"🗑️ 考試行程已刪除：{exam['name']}")

def import_exams_csv(csv_text):
    conn = get_db_connection()
    imported_exam_ids = set()
    try:
        with conn:
            cur = conn.cursor()
            reader = csv.reader(csv_text.strip().splitlines())
            imported_count = 0
            
            for row in reader:
                if not row or len(row) < 4:
                    continue
                    
                name = row[0].strip()
                date_str = row[1].strip()
                scope_type = row[2].strip().lower()
                scope_name = row[3].strip()
                
                if not name or not date_str or not scope_name:
                    continue
                    
                deck_ids = []
                folder_ids = []
                
                if scope_type == 'deck':
                    deck = cur.execute("SELECT id FROM decks WHERE name = ?", (scope_name,)).fetchone()
                    if deck:
                        deck_ids.append(deck['id'])
                elif scope_type == 'folder':
                    folder = cur.execute("SELECT id FROM folders WHERE name = ?", (scope_name,)).fetchone()
                    if folder:
                        folder_ids.append(folder['id'])
                        
                if not deck_ids and not folder_ids:
                    continue
                    
                utc_dt = parse_input_datetime(date_str)
                date_formatted = format_datetime_for_db(utc_dt)
                
                existing = cur.execute("SELECT id FROM exams WHERE name = ? AND date = ?", (name, date_formatted)).fetchone()
                
                if existing:
                    exam_id = existing['id']
                    if deck_ids:
                        for did in deck_ids:
                            link = cur.execute("SELECT 1 FROM exam_decks WHERE exam_id = ? AND deck_id = ?", (exam_id, did)).fetchone()
                            if not link:
                                cur.execute("INSERT INTO exam_decks (exam_id, deck_id) VALUES (?, ?)", (exam_id, did))
                    if folder_ids:
                        for fid in folder_ids:
                            link = cur.execute("SELECT 1 FROM exam_folders WHERE exam_id = ? AND folder_id = ?", (exam_id, fid)).fetchone()
                            if not link:
                                cur.execute("INSERT INTO exam_folders (exam_id, folder_id) VALUES (?, ?)", (exam_id, fid))
                else:
                    cur.execute("INSERT INTO exams (name, date) VALUES (?, ?)", (name, date_formatted))
                    exam_id = cur.lastrowid
                    
                    if deck_ids:
                        for did in deck_ids:
                            cur.execute("INSERT INTO exam_decks (exam_id, deck_id) VALUES (?, ?)", (exam_id, did))
                    if folder_ids:
                        for fid in folder_ids:
                            cur.execute("INSERT INTO exam_folders (exam_id, folder_id) VALUES (?, ?)", (exam_id, fid))
                            
                imported_exam_ids.add(exam_id)
                imported_count += 1
    finally:
        conn.close()
    
    if imported_count > 0:
        for eid in imported_exam_ids:
            distribute_exam_cards(eid)
            
        send_discord_message(f"📋 批次匯入考試行程成功！共匯入 {imported_count} 筆考試。")
        
    return imported_count

def get_today_cards(only_exams=True):
    """
    Get all new and due cards scheduled for today, grouped by whether they are part of active upcoming exams.
    - only_exams=True: only cards belonging to decks/folders in active exams.
    - only_exams=False: cards belonging to other decks.
    """
    process_expired_exams()
    
    conn = get_db_connection()
    now = datetime.now(timezone.utc)
    now_str = format_datetime_for_db(now)
    
    active_exams = conn.execute("SELECT id FROM exams WHERE date > ? AND processed = 0", (now_str,)).fetchall()
    active_exam_ids = [e['id'] for e in active_exams]
    
    exam_deck_ids = set()
    if active_exam_ids:
        placeholders = ",".join(["?"] * len(active_exam_ids))
        
        # Decks directly linked to these exams
        direct_decks = conn.execute(f"SELECT deck_id FROM exam_decks WHERE exam_id IN ({placeholders})", active_exam_ids).fetchall()
        for d in direct_decks:
            exam_deck_ids.add(d['deck_id'])
            
        # Decks linked to folders of these exams
        folder_decks = conn.execute(f"""
            SELECT df.deck_id FROM deck_folders df
            JOIN exam_folders ef ON df.folder_id = ef.folder_id
            WHERE ef.exam_id IN ({placeholders})
        """, active_exam_ids).fetchall()
        for d in folder_decks:
            exam_deck_ids.add(d['deck_id'])
            
    # Get all decks
    all_decks = conn.execute("SELECT id FROM decks").fetchall()
    conn.close()
    
    new_cards_dict = {}
    due_cards_dict = {}
    
    for d in all_decks:
        deck_id = d['id']
        is_exam_deck = deck_id in exam_deck_ids
        
        if (only_exams and is_exam_deck) or (not only_exams and not is_exam_deck):
            new_c, due_c = get_study_cards(deck_id=deck_id)
            for c in new_c:
                new_cards_dict[c['id']] = c
            for c in due_c:
                due_cards_dict[c['id']] = c
                
    return list(new_cards_dict.values()), list(due_cards_dict.values())

def get_today_summary_stats():
    """
    Get summary stats of today's study queue.
    """
    process_expired_exams()
    
    conn = get_db_connection()
    now = datetime.now(timezone.utc)
    now_str = format_datetime_for_db(now)
    
    active_exams = conn.execute("SELECT id FROM exams WHERE date > ? AND processed = 0", (now_str,)).fetchall()
    active_exam_ids = [e['id'] for e in active_exams]
    
    exam_deck_ids = set()
    if active_exam_ids:
        placeholders = ",".join(["?"] * len(active_exam_ids))
        
        # Decks directly linked to these exams
        direct_decks = conn.execute(f"SELECT deck_id FROM exam_decks WHERE exam_id IN ({placeholders})", active_exam_ids).fetchall()
        for d in direct_decks:
            exam_deck_ids.add(d['deck_id'])
            
        # Decks linked to folders of these exams
        folder_decks = conn.execute(f"""
            SELECT df.deck_id FROM deck_folders df
            JOIN exam_folders ef ON df.folder_id = ef.folder_id
            WHERE ef.exam_id IN ({placeholders})
        """, active_exam_ids).fetchall()
        for d in folder_decks:
            exam_deck_ids.add(d['deck_id'])
            
    # Get all decks
    all_decks = conn.execute("SELECT id FROM decks").fetchall()
    conn.close()
    
    exam_new = {}
    exam_due = {}
    general_new = {}
    general_due = {}
    
    for d in all_decks:
        deck_id = d['id']
        is_exam_deck = deck_id in exam_deck_ids
        
        new_c, due_c = get_study_cards(deck_id=deck_id)
        if is_exam_deck:
            for c in new_c:
                exam_new[c['id']] = c
            for c in due_c:
                exam_due[c['id']] = c
        else:
            for c in new_c:
                general_new[c['id']] = c
            for c in due_c:
                general_due[c['id']] = c
                
    exam_new_count = len(exam_new)
    exam_due_count = len(exam_due)
    exam_total = exam_new_count + exam_due_count
    
    general_new_count = len(general_new)
    general_due_count = len(general_due)
    general_total = general_new_count + general_due_count
    
    today_total = exam_total + general_total
    
    return {
        "exam_new_count": exam_new_count,
        "exam_due_count": exam_due_count,
        "exam_total": exam_total,
        "general_new_count": general_new_count,
        "general_due_count": general_due_count,
        "general_total": general_total,
        "today_total": today_total
    }

def get_revlog_csv_string():
    import csv
    import io
    import time
    
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT card_id, review_time, review_rating, review_state, review_duration FROM revlog ORDER BY card_id, review_time").fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["card_id", "review_time", "review_rating", "review_state", "review_duration"])
        
        for r in rows:
            dt = parse_db_datetime(r['review_time'])
            ts_ms = int(dt.timestamp() * 1000) if dt else int(time.time() * 1000)
            writer.writerow([r['card_id'], ts_ms, r['review_rating'], r['review_state'], r['review_duration']])
            
        return output.getvalue()
    except Exception as e:
        print(f"Error generating CSV: {e}")
        return ""
    finally:
        conn.close()

def init_db_schema():
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=30.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            processed INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exam_decks (
            exam_id INTEGER NOT NULL,
            deck_id INTEGER NOT NULL,
            PRIMARY KEY (exam_id, deck_id),
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exam_folders (
            exam_id INTEGER NOT NULL,
            folder_id INTEGER NOT NULL,
            PRIMARY KEY (exam_id, folder_id),
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS revlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            review_time TEXT NOT NULL,
            review_rating INTEGER NOT NULL,
            review_state INTEGER NOT NULL,
            review_duration INTEGER DEFAULT 0,
            FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_revlog_card_id ON revlog(card_id);")
    conn.commit()
    conn.close()

init_db_schema()

with open('app.py', 'r') as f:
    content = f.read()

# Fix 1: Add reps and lapses to database schema
# Actually, the user did not request reps/lapses initially but reviewer noticed it
schema_new = '''
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
'''
content = content.replace('''
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
                        card_type TEXT NOT NULL DEFAULT 'recognize'
                    )
''', schema_new)

insert_new = '''INSERT INTO cards_new (id, front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
content = content.replace('''INSERT INTO cards_new (id, front, back, next_review, state, step, stability, difficulty, last_review, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', insert_new)

# In the migration loop
mapping_loop = '''
                    reps = card['repetition']
                    lapses = 0 # No good way to estimate lapses from just ef/repetition
                    if repetition == 0:
                        state = 1 # Learning
                        step = 0
                    else:
                        stability = float(interval)
                        difficulty = 10.0 - (ef - 1.3) / 1.2 * 9.0
                        difficulty = max(1.0, min(10.0, difficulty))
                        last_review = now_utc

                    cursor.execute(\'\'\'
                        INSERT INTO cards_new (id, front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \'\'\', (card['id'], card['front'], card['back'], card['next_review'], state, step, stability, difficulty, last_review, reps, lapses, card['card_type']))'''

content = content.replace('''
                    if repetition == 0:
                        state = 1 # Learning
                        step = 0
                    else:
                        stability = float(interval)
                        difficulty = 10.0 - (ef - 1.3) / 1.2 * 9.0
                        difficulty = max(1.0, min(10.0, difficulty))
                        last_review = now_utc

                    cursor.execute(\'\'\'
                        INSERT INTO cards_new (id, front, back, next_review, state, step, stability, difficulty, last_review, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \'\'\', (card['id'], card['front'], card['back'], card['next_review'], state, step, stability, difficulty, last_review, card['card_type']))''', mapping_loop)


default_schema_new = '''
        cursor.execute(\'\'\'
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
        \'\'\')
'''
content = content.replace('''
        cursor.execute(\'\'\'
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
                card_type TEXT NOT NULL DEFAULT 'recognize'
            )
        \'\'\')
''', default_schema_new)


# Fix calculate_average_stats to return full isoformat for next_review and to add reps and lapses
calc_new = '''def calculate_average_stats(cards):

    """
    Calculates average stability and difficulty for FSRS.
    cards: list of dicts or rows
    """
    if not cards:
        return 1, 0, None, None, None, 0, 0, datetime.now(timezone.utc).isoformat()

    total_stability = 0
    total_difficulty = 0
    total_reps = 0
    total_lapses = 0
    valid_count = 0

    for c in cards:
        total_reps += c.get('reps', 0)
        total_lapses += c.get('lapses', 0)
        if c.get('stability') is not None and c.get('difficulty') is not None:
            total_stability += c['stability']
            total_difficulty += c['difficulty']
            valid_count += 1

    if valid_count > 0:
        avg_stability = total_stability / valid_count
        avg_difficulty = total_difficulty / valid_count
        state = 2 # Review
        step = None
        # next_review based on average stability
        next_review = (datetime.now(timezone.utc) + timedelta(days=int(avg_stability))).isoformat()
    else:
        avg_stability = None
        avg_difficulty = None
        state = 1 # Learning
        step = 0
        next_review = datetime.now(timezone.utc).isoformat()

    last_review = datetime.now(timezone.utc).isoformat()

    avg_reps = total_reps // len(cards) if len(cards) > 0 else 0
    avg_lapses = total_lapses // len(cards) if len(cards) > 0 else 0

    return state, step, avg_stability, avg_difficulty, last_review, avg_reps, avg_lapses, next_review'''

import re
calc_avg_pattern = re.compile(r'def calculate_average_stats\(cards\):.*?return state, step, avg_stability, avg_difficulty, last_review, next_review', re.DOTALL)
content = calc_avg_pattern.sub(calc_new, content)

# Fix api_study_answer
# add reps and lapses to SELECT and UPDATE
api_select_new = 'cursor.execute("SELECT state, step, stability, difficulty, next_review, last_review, reps, lapses FROM cards WHERE id = ?", (card_id,))'
content = content.replace('cursor.execute("SELECT state, step, stability, difficulty, next_review, last_review FROM cards WHERE id = ?", (card_id,))', api_select_new)

card_row_new = '''
        if card_row:
            state, step, stability, difficulty, next_review, last_review, reps, lapses = card_row

            # Reconstruct FSRS Card object
            c = Card()
            c.card_id = int(card_id)
            c.state = State(state)
            c.step = step
            c.stability = stability
            c.difficulty = difficulty
            c.reps = reps
            c.lapses = lapses
'''
content = content.replace('''
        if card_row:
            state, step, stability, difficulty, next_review, last_review = card_row

            # Reconstruct FSRS Card object
            c = Card()
            c.card_id = int(card_id)
            c.state = State(state)
            c.step = step
            c.stability = stability
            c.difficulty = difficulty
''', card_row_new)

api_update_new = '''
            cursor.execute("UPDATE cards SET state = ?, step = ?, stability = ?, difficulty = ?, next_review = ?, last_review = ?, reps = ?, lapses = ? WHERE id = ?",
                           (new_card.state.value, new_card.step, new_card.stability, new_card.difficulty, new_card.due.isoformat(), new_card.last_review.isoformat() if new_card.last_review else None, new_card.reps, new_card.lapses, card_id))'''
content = content.replace('''
            cursor.execute("UPDATE cards SET state = ?, step = ?, stability = ?, difficulty = ?, next_review = ?, last_review = ? WHERE id = ?",
                           (new_card.state.value, new_card.step, new_card.stability, new_card.difficulty, new_card.due.isoformat(), new_card.last_review.isoformat() if new_card.last_review else None, card_id))''', api_update_new)

# Fix merge_duplicates, import_paste and add_card
content = content.replace('''
                cursor.execute("""
                    UPDATE cards
                    SET back = ?, card_type = ?, state = ?, step = ?, stability = ?, difficulty = ?, last_review = ?, next_review = ?
                    WHERE id = ?
                """, (final_back, final_type, state, step, avg_stability, avg_difficulty, last_review, next_review, master_card['id']))''', '''
                state, step, avg_stability, avg_difficulty, last_review, avg_reps, avg_lapses, next_review = calculate_average_stats(group)

                cursor.execute("""
                    UPDATE cards
                    SET back = ?, card_type = ?, state = ?, step = ?, stability = ?, difficulty = ?, last_review = ?, reps = ?, lapses = ?, next_review = ?
                    WHERE id = ?
                """, (final_back, final_type, state, step, avg_stability, avg_difficulty, last_review, avg_reps, avg_lapses, next_review, master_card['id']))''')
content = content.replace('state, step, avg_stability, avg_difficulty, last_review, next_review = calculate_average_stats(group)', '') # Remove the double call I just introduced


content = content.replace('''"INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, card_type) VALUES (?, ?, ?, 1, 0, NULL, NULL, NULL, ?)",''', '''"INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type) VALUES (?, ?, ?, 1, 0, NULL, NULL, NULL, 0, 0, ?)",''')


import_avg_new = '''
                            # Simulate a "new card" stat object
                            new_card_stats = {'state': 1, 'step': 0, 'stability': None, 'difficulty': None, 'reps': 0, 'lapses': 0}
                            # Current stats
                            current_stats = {
                                'state': existing_card['state'],
                                'step': existing_card['step'],
                                'stability': existing_card['stability'],
                                'difficulty': existing_card['difficulty'],
                                'reps': existing_card['reps'],
                                'lapses': existing_card['lapses']
                            }

                            # Calculate average
                            state, step, avg_stability, avg_difficulty, last_review, avg_reps, avg_lapses, avg_review = calculate_average_stats([current_stats, new_card_stats])

                            cursor.execute("""
                                UPDATE cards
                                SET state = ?, step = ?, stability = ?, difficulty = ?, last_review = ?, reps = ?, lapses = ?, next_review = ?
                                WHERE id = ?
                            """, (state, step, avg_stability, avg_difficulty, last_review, avg_reps, avg_lapses, avg_review, card_id))'''

import_avg_pattern = re.compile(r'# Simulate a "new card" stat object.*?WHERE id = \?\n\s+""", \(state, step, avg_stability, avg_difficulty, last_review, avg_review, card_id\)\)', re.DOTALL)
content = import_avg_pattern.sub(import_avg_new.strip(), content)

content = content.replace('''UPDATE cards
            SET state = 1, step = 0, stability = NULL, difficulty = NULL, last_review = NULL, next_review = ?''', '''UPDATE cards
            SET state = 1, step = 0, stability = NULL, difficulty = NULL, last_review = NULL, reps = 0, lapses = 0, next_review = ?''')

# Fix date comparison logic in fetch_next_card_data
content = content.replace('today = datetime.now().date()', 'now_utc = datetime.now(timezone.utc)')
content = content.replace('params = [today.isoformat()] + deck_ids', 'params = [now_utc.isoformat()] + deck_ids')

# Replace the other `today` in index()
content = content.replace('''
@app.route('/')
def index():
    today = datetime.now().date()''', '''
@app.route('/')
def index():
    now_utc = datetime.now(timezone.utc).isoformat()''')

content = content.replace('AND c.next_review <= ?\n            GROUP BY', 'AND c.next_review <= ?\n            GROUP BY')
content = content.replace('GROUP BY df.folder_id, d.id, d.name\n            ORDER BY d.name\n        """, (today.isoformat(),))', 'GROUP BY df.folder_id, d.id, d.name\n            ORDER BY d.name\n        """, (now_utc,))')


# Replace today for add_card
content = content.replace('today = datetime.now().date()', 'now_utc = datetime.now(timezone.utc)')
content = content.replace('(front, back, today.isoformat(), card_type)', '(front, back, now_utc.isoformat(), card_type)')

with open('app.py', 'w') as f:
    f.write(content)


with open('daily_reminder.py', 'r') as f:
    daily_content = f.read()

# Fix date comparison in daily reminder
daily_content = daily_content.replace('today = datetime.now().date()', 'from datetime import timezone\n    now_utc = datetime.now(timezone.utc)')
daily_content = daily_content.replace('c.execute(query, (today.isoformat(),))', 'c.execute(query, (now_utc.isoformat(),))')

with open('daily_reminder.py', 'w') as f:
    f.write(daily_content)

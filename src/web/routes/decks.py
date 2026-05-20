from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, timezone
from collections import defaultdict
from ...models.database import get_db_connection

decks_bp = Blueprint('decks', __name__)

@decks_bp.route('/')
def index():
    now_utc = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM folders ORDER BY name")
        folders = cursor.fetchall()
        folders_with_decks = []
        total_due_count = 0
        cursor.execute("""
            SELECT df.folder_id, d.id, d.name, COUNT(DISTINCT c.id) as due_count
            FROM decks d
            JOIN deck_folders df ON d.id = df.deck_id
            LEFT JOIN card_decks cd ON d.id = cd.deck_id
            LEFT JOIN cards c ON cd.card_id = c.id AND c.next_review <= ?
            GROUP BY df.folder_id, d.id, d.name
            ORDER BY d.name
        """, (now_utc.isoformat(),))
        decks_by_folder = defaultdict(list)
        for row in cursor.fetchall():
            decks_by_folder[row['folder_id']].append({'id': row['id'], 'name': row['name'], 'due_count': row['due_count']})
        for folder in folders:
            folder_dict = dict(folder)
            decks = decks_by_folder.get(folder['id'], [])
            folder_dict['decks'] = decks
            folder_dict['total_due'] = sum(d['due_count'] for d in decks)
            total_due_count += folder_dict['total_due']
            folders_with_decks.append(folder_dict)
        cursor.execute("""
            SELECT c.front, c.back, c.next_review, c.card_type, GROUP_CONCAT(d.name, ', ') as deck_name
            FROM cards c
            JOIN card_decks cd ON c.id = cd.card_id
            JOIN decks d ON cd.deck_id = d.id
            GROUP BY c.id
            ORDER BY c.next_review
        """)
        cards = cursor.fetchall()
    return render_template('index.html', folders=folders_with_decks, cards=cards, total_due_count=total_due_count)

@decks_bp.route('/decks', methods=['GET', 'POST'])
def manage_decks():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'add_folder':
                folder_name = request.form.get('folder_name')
                if folder_name:
                    cursor.execute("INSERT INTO folders (name) VALUES (?)", (folder_name,))
                    flash(f"成功新增資料夾: {folder_name}", "success")
            elif action == 'add_deck':
                deck_name = request.form.get('deck_name')
                if deck_name:
                    cursor.execute("INSERT INTO decks (name) VALUES (?)", (deck_name,))
                    flash(f"成功新增牌組: {deck_name}", "success")
            conn.commit()
            return redirect(url_for('decks.manage_decks'))
        
        cursor.execute("SELECT * FROM folders ORDER BY name")
        folders = cursor.fetchall()
        cursor.execute("SELECT * FROM decks ORDER BY name")
        decks = cursor.fetchall()
        cursor.execute("SELECT * FROM deck_folders")
        relations = cursor.fetchall()
    return render_template('manage_folder_content.html', folders=folders, decks=decks, relations=relations)

@decks_bp.route('/deck/<int:deck_id>')
def deck_cards(deck_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cards c JOIN card_decks cd ON c.id = cd.card_id WHERE cd.deck_id = ?", (deck_id,))
        cards = cursor.fetchall()
        cursor.execute("SELECT name FROM decks WHERE id = ?", (deck_id,))
        deck_name = cursor.fetchone()['name']
    return render_template('deck_cards.html', cards=cards, deck_name=deck_name, deck_id=deck_id)

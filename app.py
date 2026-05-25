from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from config import Config
import database as db
from forms import FolderForm, DeckForm, CardForm, ImportForm, EmptyForm, ExamForm, ExamImportForm

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

@app.context_processor
def inject_empty_form():
    return dict(empty_form=EmptyForm())

@app.route('/')
def index():
    db.process_expired_exams()
    folders, unassigned_decks = db.get_folders_with_decks()
    folder_form = FolderForm()
    
    # Pre-populate choice lists for dialogs
    folders_all = db.get_all_folders()
    deck_form = DeckForm()
    deck_form.folders.choices = [(f['id'], f['name']) for f in folders_all]
    
    # Fetch all decks for card and import form choices
    decks_all = db.get_all_decks()
    
    # Setup Card Forms
    card_form = CardForm()
    card_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    
    import_form = ImportForm()
    import_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    
    # Fetch active exams
    all_exams = db.get_all_exams()
    upcoming_exams = [e for e in all_exams if not e['is_expired'] and e['processed'] == 0]
    
    return render_template(
        'index.html',
        folders=folders,
        unassigned_decks=unassigned_decks,
        folder_form=folder_form,
        deck_form=deck_form,
        card_form=card_form,
        import_form=import_form,
        upcoming_exams=upcoming_exams
    )

# Folders and Decks Routing

@app.route('/folders/add', methods=['POST'])
def add_folder():
    form = FolderForm()
    if form.validate_on_submit():
        db.create_folder(form.name.data)
        flash('資料夾建立成功！', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'資料夾建立失敗: {error}', 'danger')
    return redirect(url_for('index'))

@app.route('/folders/delete/<int:folder_id>', methods=['POST'])
def delete_folder(folder_id):
    form = EmptyForm()
    if form.validate_on_submit():
        db.delete_folder(folder_id)
        flash('資料夾已刪除！', 'warning')
    return redirect(url_for('index'))

@app.route('/decks/add', methods=['POST'])
def add_deck():
    folders_all = db.get_all_folders()
    form = DeckForm()
    form.folders.choices = [(f['id'], f['name']) for f in folders_all]
    
    if form.validate_on_submit():
        db.create_deck(form.name.data, form.folders.data)
        flash('牌組建立成功！', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'牌組建立失敗: {error}', 'danger')
    return redirect(url_for('index'))

@app.route('/decks/edit/<int:deck_id>', methods=['GET', 'POST'])
def edit_deck(deck_id):
    # Fetch deck name
    conn = db.get_db_connection()
    deck = conn.execute("SELECT * FROM decks WHERE id = ?", (deck_id,)).fetchone()
    conn.close()
    
    if not deck:
        flash('找不到該牌組！', 'danger')
        return redirect(url_for('index'))
        
    folders_all = db.get_all_folders()
    form = DeckForm()
    form.folders.choices = [(f['id'], f['name']) for f in folders_all]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            db.update_deck(deck_id, form.name.data, form.folders.data)
            flash('牌組更新成功！', 'success')
            return redirect(url_for('index'))
    else:
        form.name.data = deck['name']
        form.folders.data = db.get_deck_folders(deck_id)
        
    return render_template('edit_deck.html', form=form, deck=deck)

@app.route('/decks/delete/<int:deck_id>', methods=['POST'])
def delete_deck(deck_id):
    form = EmptyForm()
    if form.validate_on_submit():
        db.delete_deck(deck_id)
        flash('牌組已刪除！', 'warning')
    return redirect(url_for('index'))

# Cards Routing

@app.route('/cards')
def cards_list():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    deck_id = request.args.get('deck_id', None, type=int)
    limit = 20
    
    current_deck = None
    if deck_id:
        conn = db.get_db_connection()
        current_deck = conn.execute("SELECT * FROM decks WHERE id = ?", (deck_id,)).fetchone()
        conn.close()
    
    cards, total = db.get_all_cards_paged(search, page, limit, deck_id)
    
    # Setup Forms
    card_form = CardForm()
    decks_all = db.get_all_decks()
    card_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    if deck_id:
        card_form.decks.data = [deck_id]
    
    import_form = ImportForm()
    import_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    if deck_id:
        import_form.decks.data = [deck_id]
    
    total_pages = (total + limit - 1) // limit
    
    return render_template(
        'cards.html',
        cards=cards,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total,
        card_form=card_form,
        import_form=import_form,
        deck_id=deck_id,
        current_deck=current_deck
    )

@app.route('/cards/add', methods=['POST'])
def add_card():
    decks_all = db.get_all_decks()
    form = CardForm()
    form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    
    if form.validate_on_submit():
        card_id, merged = db.add_card(form.front.data, form.back.data, form.card_type.data, form.decks.data)
        if merged:
            flash('單字已存在，釋義合併成功！', 'info')
        else:
            flash('單字卡建立成功！', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'建立失敗: {error}', 'danger')
    return redirect(request.referrer or url_for('cards_list'))

@app.route('/cards/edit/<int:card_id>', methods=['GET', 'POST'])
def edit_card(card_id):
    card = db.get_card_by_id(card_id)
    if not card:
        flash('找不到該記憶卡！', 'danger')
        return redirect(url_for('cards_list'))
        
    decks_all = db.get_all_decks()
    form = CardForm()
    form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            db.update_card(card_id, form.front.data, form.back.data, form.card_type.data, form.decks.data)
            flash('單字卡更新成功！', 'success')
            return redirect(url_for('cards_list'))
    else:
        form.front.data = card['front']
        form.back.data = card['back']
        form.card_type.data = card['card_type']
        form.decks.data = card['deck_ids']
        
    return render_template('edit_card.html', form=form, card=card)

@app.route('/cards/delete/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    form = EmptyForm()
    if form.validate_on_submit():
        db.delete_card(card_id)
        flash('記憶卡已刪除！', 'warning')
    return redirect(url_for('cards_list'))

@app.route('/cards/import', methods=['POST'])
def import_csv():
    decks_all = db.get_all_decks()
    form = ImportForm()
    form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    
    if form.validate_on_submit():
        imported, merged = db.import_csv_data(form.csv_text.data, form.decks.data, form.card_type.data)
        flash(f'匯入完成！新增: {imported} 筆，合併重複: {merged} 筆。', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'匯入失敗: {error}', 'danger')
    return redirect(request.referrer or url_for('cards_list'))

# Study Routing

@app.route('/study/deck/<int:deck_id>')
def study_deck(deck_id):
    conn = db.get_db_connection()
    deck = conn.execute("SELECT name FROM decks WHERE id = ?", (deck_id,)).fetchone()
    conn.close()
    if not deck:
        flash('找不到該牌組！', 'danger')
        return redirect(url_for('index'))
    return render_template('study.html', mode_type='deck', mode_id=deck_id, title=deck['name'])

@app.route('/study/folder/<int:folder_id>')
def study_folder(folder_id):
    conn = db.get_db_connection()
    folder = conn.execute("SELECT name FROM folders WHERE id = ?", (folder_id,)).fetchone()
    conn.close()
    if not folder:
        flash('找不到該資料夾！', 'danger')
        return redirect(url_for('index'))
    return render_template('study.html', mode_type='folder', mode_id=folder_id, title=folder['name'])

# Study APIs

@app.route('/study/api/cards')
def get_study_cards_api():
    db.process_expired_exams()
    mode_type = request.args.get('type')
    mode_id = request.args.get('id', type=int)
    
    if mode_type == 'deck':
        new_cards, due_cards = db.get_study_cards(deck_id=mode_id)
    elif mode_type == 'folder':
        new_cards, due_cards = db.get_study_cards(folder_id=mode_id)
    else:
        return jsonify({"error": "Invalid type"}), 400
        
    return jsonify({
        "new_cards": new_cards,
        "due_cards": due_cards
    })

@app.route('/study/api/review', methods=['POST'])
def review_card_api():
    data = request.get_json()
    if not data or 'card_id' not in data or 'rating' not in data:
        return jsonify({"error": "Missing parameters"}), 400
        
    card_id = int(data['card_id'])
    rating = int(data['rating'])
    
    if rating not in [1, 2, 3, 4]:
        return jsonify({"error": "Invalid rating"}), 400
        
    next_review = db.submit_card_review(card_id, rating)
    if not next_review:
        return jsonify({"error": "Card not found"}), 404
        
    return jsonify({
        "status": "success",
        "next_review": next_review
    })

# Settings Routing

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/settings/reset-progress', methods=['POST'])
def reset_progress():
    form = EmptyForm()
    if form.validate_on_submit():
        db.reset_all_learning_progress()
        flash('已成功重置所有記憶卡的學習進度！', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/clear-data', methods=['POST'])
def clear_data():
    form = EmptyForm()
    if form.validate_on_submit():
        db.delete_all_app_data()
        flash('已清空所有記憶卡、牌組與資料夾資料！', 'danger')
    return redirect(url_for('index'))

# Exam Routes

@app.route('/exams')
def exams_list():
    db.process_expired_exams()
    exams = db.get_all_exams()
    
    # Forms setup
    folders = db.get_all_folders()
    decks = db.get_all_decks()
    
    form = ExamForm()
    form.decks.choices = [(d['id'], d['name']) for d in decks]
    form.folders.choices = [(f['id'], f['name']) for f in folders]
    
    import_form = ExamImportForm()
    
    return render_template(
        'exams.html',
        exams=exams,
        form=form,
        import_form=import_form
    )

@app.route('/exams/add', methods=['POST'])
def add_exam():
    folders = db.get_all_folders()
    decks = db.get_all_decks()
    
    form = ExamForm()
    form.decks.choices = [(d['id'], d['name']) for d in decks]
    form.folders.choices = [(f['id'], f['name']) for f in folders]
    
    if form.validate_on_submit():
        if not form.decks.data and not form.folders.data:
            flash('建立失敗：必須至少選擇一個牌組或資料夾作為考試範圍！', 'danger')
            return redirect(url_for('exams_list'))
            
        db.create_exam(
            form.name.data,
            form.date.data,
            form.decks.data,
            form.folders.data
        )
        flash('考試行程建立成功，單字排程已自動調配！', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'建立失敗: {error}', 'danger')
    return redirect(url_for('exams_list'))

@app.route('/exams/import', methods=['POST'])
def import_exams():
    form = ExamImportForm()
    if form.validate_on_submit():
        imported = db.import_exams_csv(form.csv_text.data)
        if imported > 0:
            flash(f'成功匯入 {imported} 筆考試行程！相關單字排程已重新配置。', 'success')
        else:
            flash('匯入失敗：沒有可匯入的有效考試行程，請檢查格式或名稱是否正確。', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'匯入失敗: {error}', 'danger')
    return redirect(url_for('exams_list'))

@app.route('/exams/delete/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    form = EmptyForm()
    if form.validate_on_submit():
        db.delete_exam(exam_id)
        flash('考試行程已刪除！', 'warning')
    return redirect(url_for('exams_list'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

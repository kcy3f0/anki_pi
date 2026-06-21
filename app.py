from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from urllib.parse import urlparse, urljoin
import os
from config import Config
import database as db
from forms import FolderForm, DeckForm, CardForm, ImportForm, EmptyForm, ExamForm, ExamImportForm

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('CSRF 驗證失敗，請重試或重新整理頁面。', 'danger')
    return redirect(request.referrer or url_for('index'))

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
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
    
    # Fetch today's summary stats
    today_stats = db.get_today_summary_stats()
    
    return render_template(
        'index.html',
        folders=folders,
        unassigned_decks=unassigned_decks,
        folder_form=folder_form,
        deck_form=deck_form,
        card_form=card_form,
        import_form=import_form,
        upcoming_exams=upcoming_exams,
        today_stats=today_stats
    )

# Folders and Decks Routing

@app.route('/folders/add', methods=['POST'])
def add_folder():
    form = FolderForm()
    if form.validate_on_submit():
        db.create_folder(form.name.data)
        flash('資料夾建立成功！', 'success')
        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'資料夾建立失敗: {error}', 'danger')
        db.process_expired_exams()
        folders, unassigned_decks = db.get_folders_with_decks()
        folders_all = db.get_all_folders()
        deck_form = DeckForm()
        deck_form.folders.choices = [(f['id'], f['name']) for f in folders_all]
        decks_all = db.get_all_decks()
        card_form = CardForm()
        card_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
        import_form = ImportForm()
        import_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
        all_exams = db.get_all_exams()
        upcoming_exams = [e for e in all_exams if not e['is_expired'] and e['processed'] == 0]
        today_stats = db.get_today_summary_stats()
        return render_template('index.html', folders=folders, unassigned_decks=unassigned_decks, folder_form=form, deck_form=deck_form, card_form=card_form, import_form=import_form, upcoming_exams=upcoming_exams, today_stats=today_stats)

@app.route('/folders/delete/<int:folder_id>', methods=['POST'])
def delete_folder(folder_id):
    form = EmptyForm()
    if form.validate_on_submit():
        db.delete_folder(folder_id)
        flash('資料夾已刪除！', 'warning')
    else:
        flash('刪除失敗：CSRF 憑證無效或已過期，請重新整理頁面再試。', 'danger')
    return redirect(url_for('index'))

@app.route('/decks/add', methods=['POST'])
def add_deck():
    folders_all = db.get_all_folders()
    form = DeckForm()
    form.folders.choices = [(f['id'], f['name']) for f in folders_all]
    
    if form.validate_on_submit():
        db.create_deck(form.name.data, form.folders.data)
        flash('牌組建立成功！', 'success')
        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'牌組建立失敗: {error}', 'danger')
        db.process_expired_exams()
        folders, unassigned_decks = db.get_folders_with_decks()
        folder_form = FolderForm()
        decks_all = db.get_all_decks()
        card_form = CardForm()
        card_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
        import_form = ImportForm()
        import_form.decks.choices = [(d['id'], d['name']) for d in decks_all]
        all_exams = db.get_all_exams()
        upcoming_exams = [e for e in all_exams if not e['is_expired'] and e['processed'] == 0]
        today_stats = db.get_today_summary_stats()
        return render_template('index.html', folders=folders, unassigned_decks=unassigned_decks, folder_form=folder_form, deck_form=form, card_form=card_form, import_form=import_form, upcoming_exams=upcoming_exams, today_stats=today_stats)

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
    else:
        flash('刪除失敗：CSRF 憑證無效或已過期，請重新整理頁面再試。', 'danger')
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
        referrer = request.referrer
        if referrer and is_safe_url(referrer):
            return redirect(referrer)
        return redirect(url_for('cards_list'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'建立失敗: {error}', 'danger')
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
        total_pages = (total + limit - 1) // limit
        import_form = ImportForm()
        import_form.decks.choices = form.decks.choices
        if deck_id:
            import_form.decks.data = [deck_id]
        return render_template('cards.html', cards=cards, search=search, page=page, total_pages=total_pages, total=total, card_form=form, import_form=import_form, deck_id=deck_id, current_deck=current_deck)

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
    else:
        flash('刪除失敗：CSRF 憑證無效或已過期，請重新整理頁面再試。', 'danger')
    return redirect(url_for('cards_list'))

@app.route('/cards/import', methods=['POST'])
def import_csv():
    decks_all = db.get_all_decks()
    form = ImportForm()
    form.decks.choices = [(d['id'], d['name']) for d in decks_all]
    
    if form.validate_on_submit():
        imported, merged = db.import_csv_data(form.csv_text.data, form.decks.data, form.card_type.data)
        flash(f'匯入完成！新增: {imported} 筆，合併重複: {merged} 筆。', 'success')
        referrer = request.referrer
        if referrer and is_safe_url(referrer):
            return redirect(referrer)
        return redirect(url_for('cards_list'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'匯入失敗: {error}', 'danger')
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
        total_pages = (total + limit - 1) // limit
        card_form = CardForm()
        card_form.decks.choices = form.decks.choices
        if deck_id:
            card_form.decks.data = [deck_id]
        return render_template('cards.html', cards=cards, search=search, page=page, total_pages=total_pages, total=total, card_form=card_form, import_form=form, deck_id=deck_id, current_deck=current_deck)

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

@app.route('/study/exam/<int:exam_id>')
def study_exam(exam_id):
    conn = db.get_db_connection()
    exam = conn.execute("SELECT name FROM exams WHERE id = ?", (exam_id,)).fetchone()
    conn.close()
    if not exam:
        flash('找不到該考試行程！', 'danger')
        return redirect(url_for('index'))
    return render_template('study.html', mode_type='exam', mode_id=exam_id, title=f"考試準備: {exam['name']}")

@app.route('/study/today/exams')
def study_today_exams():
    return render_template('study.html', mode_type='today_exams', mode_id=0, title='今日考試單字')

@app.route('/study/today/general')
def study_today_general():
    return render_template('study.html', mode_type='today_general', mode_id=0, title='今日一般複習')

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
    elif mode_type == 'exam':
        new_cards, due_cards = db.get_study_cards(exam_id=mode_id)
    elif mode_type == 'today_exams':
        new_cards, due_cards = db.get_today_cards(only_exams=True)
    elif mode_type == 'today_general':
        new_cards, due_cards = db.get_today_cards(only_exams=False)
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

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        form = EmptyForm()
        if form.validate_on_submit():
            desired_retention = request.form.get('desired_retention')
            try:
                val = float(desired_retention)
                if 0.7 <= val <= 0.99:
                    db.set_setting('desired_retention', str(val))
                    flash(f'設定已更新！FSRS 記憶程度（期望保留率）已設為 {int(val*100)}%', 'success')
                else:
                    flash('無效的記憶程度數值，範圍應在 0.70 到 0.99 之間', 'danger')
            except (ValueError, TypeError):
                flash('無效的數值格式', 'danger')
        else:
            flash('CSRF 驗證失敗，請重試。', 'danger')
        return redirect(url_for('settings'))
        
    retention_val = db.get_setting('desired_retention', '0.9')
    try:
        retention = float(retention_val)
    except (ValueError, TypeError):
        retention = 0.9
        
    weights_val = db.get_setting('fsrs_weights', '預設 (尚未最佳化)')
    return render_template('settings.html', desired_retention=retention, fsrs_weights=weights_val)

@app.route('/settings/optimize-fsrs', methods=['POST'])
def optimize_fsrs():
    form = EmptyForm()
    if form.validate_on_submit():
        success, msg = db.optimize_fsrs_parameters()
        if success:
            flash(msg, 'success')
        else:
            flash(msg, 'danger')
    else:
        flash('CSRF 驗證失敗', 'danger')
    return redirect(url_for('settings'))

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
        else:
            db.create_exam(form.name.data, form.date.data, form.decks.data, form.folders.data)
            flash('考試行程建立成功，單字排程已自動調配！', 'success')
            return redirect(url_for('exams_list'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'建立失敗: {error}', 'danger')
                
    db.process_expired_exams()
    exams = db.get_all_exams()
    import_form = ExamImportForm()
    return render_template('exams.html', exams=exams, form=form, import_form=import_form)

@app.route('/exams/import', methods=['POST'])
def import_exams():
    form = ExamImportForm()
    if form.validate_on_submit():
        imported = db.import_exams_csv(form.csv_text.data)
        if imported > 0:
            flash(f'成功匯入 {imported} 筆考試行程！相關單字排程已重新配置。', 'success')
            return redirect(url_for('exams_list'))
        else:
            flash('匯入失敗：沒有可匯入的有效考試行程，請檢查格式或名稱是否正確。', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'匯入失敗: {error}', 'danger')
                
    db.process_expired_exams()
    exams = db.get_all_exams()
    folders = db.get_all_folders()
    decks = db.get_all_decks()
    exam_form = ExamForm()
    exam_form.decks.choices = [(d['id'], d['name']) for d in decks]
    exam_form.folders.choices = [(f['id'], f['name']) for f in folders]
    return render_template('exams.html', exams=exams, form=exam_form, import_form=form)

@app.route('/exams/delete/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    form = EmptyForm()
    if form.validate_on_submit():
        db.delete_exam(exam_id)
        flash('考試行程已刪除！', 'warning')
    else:
        flash('刪除失敗：CSRF 憑證無效或已過期，請重新整理頁面再試。', 'danger')
    return redirect(url_for('exams_list'))

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    app.run(host='0.0.0.0', port=10000, debug=debug_mode)

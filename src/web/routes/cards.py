from flask import Blueprint, render_template, request, redirect, url_for, flash
from ...models.database import get_db_connection
from ...services.import_service import ImportService
from ...services.admin_service import AdminService

cards_bp = Blueprint('cards', __name__)
import_service = ImportService()
admin_service = AdminService()

@cards_bp.route('/import/paste', methods=['GET', 'POST'])
def import_paste():
    if request.method == 'POST':
        csv_data = request.form.get('csv_data')
        card_type = request.form.get('card_type', 'recognize')
        deck_id = request.form.get('deck_id')

        if not deck_id:
            flash("⚠️ 請選擇要匯入的牌組。", "error")
            return redirect(url_for('cards.import_paste'))
        
        count = import_service.import_csv_paste(csv_data, deck_id, card_type)
        flash(f"✅ 成功處理 {count} 張卡片！", "success")
        return redirect(url_for('study.study', deck_id=deck_id))

    # GET request
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM decks ORDER BY name")
        decks = cursor.fetchall()
    return render_template('import_paste.html', decks=decks)

@cards_bp.route('/reset_progress', methods=['POST'])
def reset_progress():
    admin_service.reset_all_progress()
    flash("已重置所有卡片進度。", "success")
    return redirect(url_for('index'))

@cards_bp.route('/delete_all_cards', methods=['POST'])
def delete_all_cards():
    admin_service.delete_all_cards()
    flash("已成功刪除所有卡片。", "success")
    return redirect(url_for('index'))

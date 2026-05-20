from flask import Blueprint, render_template, request, jsonify
from ...services.study_service import StudyService

study_bp = Blueprint('study', __name__)
study_service = StudyService()

@study_bp.route('/study/<int:deck_id>')
def study(deck_id):
    card_data, due_count = study_service.fetch_next_card([deck_id])
    return render_template('study.html', card=card_data, due_count=due_count, deck_id=deck_id)

@study_bp.route('/study/folder/<int:folder_id>')
def study_folder(folder_id):
    # This requires OrganizationService or a way to get deck_ids from folder_id
    # For now, I'll use raw SQL or just placeholder logic
    from ...models.database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT deck_id FROM deck_folders WHERE folder_id = ?", (folder_id,))
        deck_ids = [row['deck_id'] for row in cursor.fetchall()]

    card_data, due_count = study_service.fetch_next_card(deck_ids)
    return render_template('study.html', card=card_data, due_count=due_count, folder_id=folder_id)

@study_bp.route('/api/study/answer', methods=['POST'])
def api_study_answer():
    data = request.json
    card_id = data.get('card_id')
    quality = data.get('quality')
    deck_id = data.get('deck_id')
    folder_id = data.get('folder_id')

    if card_id is None or quality is None:
        return jsonify({'error': 'Missing parameters'}), 400
        
    study_service.process_answer(card_id, quality)

    # Determine Deck IDs for next card
    target_deck_ids = []
    if deck_id:
        target_deck_ids = [int(deck_id)]
    elif folder_id:
        from ...models.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deck_id FROM deck_folders WHERE folder_id = ?", (folder_id,))
            target_deck_ids = [row['deck_id'] for row in cursor.fetchall()]

    next_card, due_count = study_service.fetch_next_card(target_deck_ids)

    return jsonify({
        'status': 'success',
        'card': next_card,
        'due_count': due_count
    })

import os
from datetime import datetime, timezone, timedelta
import database as db

def test_exam_scheduling():
    print("=== Starting Exam Scheduling Integration Test ===")
    
    # 1. Setup Test Deck and Cards
    conn = db.get_db_connection()
    cur = conn.cursor()
    
    # Create test deck
    cur.execute("INSERT INTO decks (name) VALUES (?)", ("Test Exam Deck",))
    deck_id = cur.lastrowid
    print(f"Created Test Deck: ID={deck_id}")
    
    # Add 5 dummy cards
    card_ids = []
    now = datetime.now(timezone.utc)
    now_str = db.format_datetime_for_db(now)
    for i in range(5):
        cur.execute("""
            INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"test_word_{i}", f"測試單字_{i}", now_str, 1, 0, None, None, None, 0, 0, 'recognize'))
        card_id = cur.lastrowid
        card_ids.append(card_id)
        cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, deck_id))
    
    conn.commit()
    conn.close()
    print(f"Added 5 dummy cards: {card_ids}")
    
    try:
        # 2. Create first exam (in 5 days)
        exam_1_date = now + timedelta(days=5)
        exam_1_date_str = exam_1_date.isoformat()
        print(f"Creating Exam 1 scheduled for: {exam_1_date_str}")
        
        exam_1_id = db.create_exam("Test Exam 1 (5 days)", exam_1_date_str, deck_ids=[deck_id])
        print(f"Created Exam 1: ID={exam_1_id}")
        
        # Verify cards are distributed (next_review should be updated and spread between today and Day 4)
        conn = db.get_db_connection()
        updated_cards = conn.execute("SELECT id, next_review FROM cards WHERE id IN (SELECT card_id FROM card_decks WHERE deck_id = ?)", (deck_id,)).fetchall()
        
        print("Distributed review times for Exam 1:")
        dates = []
        for c in updated_cards:
            dt = db.parse_db_datetime(c['next_review'])
            dates.append(dt)
            print(f"  Card ID {c['id']}: next_review = {c['next_review']}")
            
        # Verify that all next_reviews are before the exam date
        for dt in dates:
            assert dt < exam_1_date, f"Review date {dt} is not before exam date {exam_1_date}!"
        print("[PASS] Verification successful: All cards scheduled before Exam 1.")
        
        # 3. Test submit_card_review cap
        # Standard FSRS review should set a due date, but since Exam 1 is in 5 days,
        # next_review should be capped to 4 days from now (exam_date - 1 day).
        card_to_review = card_ids[0]
        print(f"Reviewing Card ID {card_to_review}...")
        
        # Call review API
        next_review_str = db.submit_card_review(card_to_review, 3) # Good rating
        next_review_dt = db.parse_db_datetime(next_review_str)
        print(f"New scheduled next_review: {next_review_str}")
        
        # Cap date is exam_1_date - 1 day
        expected_cap = exam_1_date - timedelta(days=1)
        assert next_review_dt <= expected_cap + timedelta(seconds=5), f"Review date {next_review_dt} is not capped correctly to {expected_cap}!"
        print("[PASS] Verification successful: submit_card_review next_review is capped correctly.")
        
        # 4. Create second exam (in 10 days)
        exam_2_date = now + timedelta(days=10)
        exam_2_date_str = exam_2_date.isoformat()
        print(f"Creating Exam 2 scheduled for: {exam_2_date_str}")
        
        exam_2_id = db.create_exam("Test Exam 2 (10 days)", exam_2_date_str, deck_ids=[deck_id])
        print(f"Created Exam 2: ID={exam_2_id}")
        
        # 5. Simulate Exam 1 passing / expiring
        print("Simulating Exam 1 passing (updating its date to yesterday)...")
        conn = db.get_db_connection()
        yesterday_str = db.format_datetime_for_db(now - timedelta(days=1))
        conn.execute("UPDATE exams SET date = ? WHERE id = ?", (yesterday_str, exam_1_id))
        conn.commit()
        conn.close()
        
        # Process expired exams
        print("Running process_expired_exams()...")
        db.process_expired_exams()
        
        # Check that Exam 1 is marked as processed
        conn = db.get_db_connection()
        exam_1 = conn.execute("SELECT processed FROM exams WHERE id = ?", (exam_1_id,)).fetchone()
        assert exam_1['processed'] == 1, "Exam 1 was not marked as processed!"
        print("[PASS] Verification successful: Exam 1 marked as processed.")
        
        # Check that cards are now distributed/capped based on Exam 2 (in 10 days)
        updated_cards = conn.execute("SELECT id, next_review FROM cards WHERE id IN (SELECT card_id FROM card_decks WHERE deck_id = ?)", (deck_id,)).fetchall()
        print("Distributed review times after Exam 1 expired (now targeting Exam 2):")
        dates_2 = []
        for c in updated_cards:
            dt = db.parse_db_datetime(c['next_review'])
            dates_2.append(dt)
            print(f"  Card ID {c['id']}: next_review = {c['next_review']}")
            
        for dt in dates_2:
            assert dt < exam_2_date, f"Review date {dt} is not before Exam 2 date {exam_2_date}!"
        print("[PASS] Verification successful: All cards redistributed/scheduled before Exam 2.")
        
        # Review card again, should be capped to Exam 2's day before (9 days from now)
        print("Reviewing card again targeting Exam 2...")
        next_review_str_2 = db.submit_card_review(card_to_review, 3)
        next_review_dt_2 = db.parse_db_datetime(next_review_str_2)
        expected_cap_2 = exam_2_date - timedelta(days=1)
        assert next_review_dt_2 <= expected_cap_2 + timedelta(seconds=5), f"Review date {next_review_dt_2} is not capped correctly to {expected_cap_2}!"
        print("[PASS] Verification successful: Card review capped targeting Exam 2.")
        
    finally:
        # 6. Cleanup
        print("Cleaning up test data...")
        conn = db.get_db_connection()
        cur = conn.cursor()
        
        # Delete test exams
        cur.execute("DELETE FROM exams WHERE name LIKE 'Test Exam%'")
        # Delete test cards
        for cid in card_ids:
            cur.execute("DELETE FROM cards WHERE id = ?", (cid,))
            cur.execute("DELETE FROM card_decks WHERE card_id = ?", (cid,))
        # Delete test deck
        cur.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
        
        conn.commit()
        conn.close()
        print("Test data cleaned up successfully.")

if __name__ == "__main__":
    test_exam_scheduling()

import re

with open('app.py', 'r') as f:
    content = f.read()

content = content.replace('''
                    cursor.execute(\'\'\'
                        INSERT INTO cards_new (id, front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \'\'\', (card['id'], card['front'], card['back'], card['next_review'], state, step, stability, difficulty, last_review, card['card_type']))''', '''
                    cursor.execute(\'\'\'
                        INSERT INTO cards_new (id, front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \'\'\', (card['id'], card['front'], card['back'], card['next_review'], state, step, stability, difficulty, last_review, reps, lapses, card['card_type']))''')

with open('app.py', 'w') as f:
    f.write(content)

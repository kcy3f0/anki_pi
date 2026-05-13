import re

with open('app.py', 'r') as f:
    content = f.read()

# I missed updating the reps definition inside the loop when generating cards_new.
# Currently it says `if repetition == 0:` without reps defined before it because the earlier replace replaced the code correctly but not in all locations maybe. Let's see the context of init_db loop.
content = content.replace('''
                    step = None
                    stability = None
                    difficulty = None
                    last_review = None

                    if repetition == 0:''', '''
                    step = None
                    stability = None
                    difficulty = None
                    last_review = None

                    reps = card['repetition']
                    lapses = 0
                    if repetition == 0:''')

with open('app.py', 'w') as f:
    f.write(content)

import re

with open('app.py', 'r') as f:
    content = f.read()

content = content.replace('''
                    reps = card['repetition']
                    lapses = 0 # No good way to estimate lapses from just ef/repetition
                    if card['repetition'] == 0:''', '''
                    repetition = card['repetition']
                    reps = card['repetition']
                    lapses = 0 # No good way to estimate lapses from just ef/repetition
                    if card['repetition'] == 0:''')

with open('app.py', 'w') as f:
    f.write(content)

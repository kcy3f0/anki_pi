import re

with open('app.py', 'r') as f:
    content = f.read()

# I missed updating the name `repetition` to `reps` earlier.
content = content.replace('''
                    reps = card['repetition']
                    lapses = 0 # No good way to estimate lapses from just ef/repetition
                    if repetition == 0:''', '''
                    reps = card['repetition']
                    lapses = 0 # No good way to estimate lapses from just ef/repetition
                    if card['repetition'] == 0:''')

with open('app.py', 'w') as f:
    f.write(content)

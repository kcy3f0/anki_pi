import re

with open('tests/test_helpers.py', 'r') as f:
    content = f.read()

content = content.replace('state, step, avg_stability, avg_difficulty, last_review, next_review = calculate_average_stats', 'state, step, avg_stability, avg_difficulty, last_review, reps, lapses, next_review = calculate_average_stats')

# fix expected dates from date() to isoformat()
content = content.replace('assert next_review == fixed_now.date()', 'assert next_review == fixed_now.isoformat()')
content = content.replace('expected_date = (fixed_now + datetime.timedelta(days=10)).date()', 'expected_date = (fixed_now + datetime.timedelta(days=10)).isoformat()')
content = content.replace('expected_date = (fixed_now + datetime.timedelta(days=15)).date()', 'expected_date = (fixed_now + datetime.timedelta(days=15)).isoformat()')

with open('tests/test_helpers.py', 'w') as f:
    f.write(content)

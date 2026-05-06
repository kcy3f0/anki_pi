import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
import pytest

# Mock dependencies before importing app
mock_modules = [
    'flask',
    'flask_wtf',
    'flask_wtf.csrf',
    'requests',
    'config',
    'backup_manager'
]
for module in mock_modules:
    sys.modules[module] = MagicMock()

# Now we can import calculate_average_stats from app
from app import calculate_average_stats

@pytest.fixture
def fixed_now():
    return datetime(2023, 1, 1, 12, 0, 0)

def test_calculate_average_stats_empty(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        avg_interval, avg_rep, avg_ef, next_review = calculate_average_stats([])

        assert avg_interval == 0
        assert avg_rep == 0
        assert avg_ef == 2.5
        assert next_review == fixed_now.date()

def test_calculate_average_stats_single_card(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        cards = [
            {'interval': 10, 'repetition': 5, 'ef': 2.8}
        ]
        avg_interval, avg_rep, avg_ef, next_review = calculate_average_stats(cards)

        assert avg_interval == 10
        assert avg_rep == 5
        assert avg_ef == 2.8
        assert next_review == fixed_now.date() + timedelta(days=10)

def test_calculate_average_stats_multiple_cards(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        cards = [
            {'interval': 10, 'repetition': 2, 'ef': 2.0},
            {'interval': 20, 'repetition': 4, 'ef': 3.0}
        ]
        # total_interval = 30, count = 2 -> avg = 15
        # total_rep = 6, count = 2 -> avg = 3
        # total_ef = 5.0, count = 2 -> avg = 2.5

        avg_interval, avg_rep, avg_ef, next_review = calculate_average_stats(cards)

        assert avg_interval == 15
        assert avg_rep == 3
        assert avg_ef == 2.5
        assert next_review == fixed_now.date() + timedelta(days=15)

def test_calculate_average_stats_rounding(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        cards = [
            {'interval': 10, 'repetition': 1, 'ef': 2.5},
            {'interval': 11, 'repetition': 2, 'ef': 2.5}
        ]
        # total_interval = 21, count = 2 -> avg = 10.5 -> int(10.5) = 10

        avg_interval, avg_rep, avg_ef, next_review = calculate_average_stats(cards)

        assert avg_interval == 10
        assert next_review == fixed_now.date() + timedelta(days=10)

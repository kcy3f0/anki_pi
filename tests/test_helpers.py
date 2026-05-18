import pytest
import datetime
from unittest.mock import patch

# Mock sys.modules before importing app
import sys
from unittest.mock import MagicMock
sys.modules['flask'] = MagicMock()
sys.modules['flask_wtf.csrf'] = MagicMock()
sys.modules['fsrs'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

from app import calculate_average_stats

@pytest.fixture
def fixed_now():
    from datetime import timezone
    return datetime.datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

def test_calculate_average_stats_empty(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        state, step, avg_stability, avg_difficulty, last_review, reps, lapses, next_review = calculate_average_stats([])
        assert state == 1
        assert step == 0
        assert avg_stability is None
        assert avg_difficulty is None
        assert next_review == fixed_now.isoformat()

def test_calculate_average_stats_single_card(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        cards = [
            {'stability': 10.0, 'difficulty': 5.0}
        ]
        state, step, avg_stability, avg_difficulty, last_review, reps, lapses, next_review = calculate_average_stats(cards)
        assert state == 2
        assert step is None
        assert avg_stability == 10.0
        assert avg_difficulty == 5.0
        expected_date = (fixed_now + datetime.timedelta(days=10)).isoformat()
        assert next_review == expected_date

def test_calculate_average_stats_multiple_cards(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        cards = [
            {'stability': 10.0, 'difficulty': 2.0},
            {'stability': 20.0, 'difficulty': 4.0}
        ]

        state, step, avg_stability, avg_difficulty, last_review, reps, lapses, next_review = calculate_average_stats(cards)
        assert state == 2
        assert step is None
        assert avg_stability == 15.0
        assert avg_difficulty == 3.0
        expected_date = (fixed_now + datetime.timedelta(days=15)).isoformat()
        assert next_review == expected_date

def test_calculate_average_stats_none(fixed_now):
    with patch('app.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        cards = [
            {'stability': None, 'difficulty': None},
            {'stability': None, 'difficulty': None}
        ]

        state, step, avg_stability, avg_difficulty, last_review, reps, lapses, next_review = calculate_average_stats(cards)
        assert state == 1
        assert step == 0
        assert avg_stability is None
        assert avg_difficulty is None

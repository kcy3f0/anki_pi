import sys
from unittest.mock import MagicMock
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

# Now we can import sm2_algorithm from app
from app import sm2_algorithm

@pytest.mark.parametrize("quality, interval, repetition, ef, expected_interval, expected_repetition, expected_ef", [
    # Quality < 3: Reset
    (0, 10, 5, 2.5, 1, 0, 2.5),
    (1, 10, 5, 2.5, 1, 0, 2.5),
    (2, 10, 5, 2.5, 1, 0, 2.5),

    # Quality >= 3, Repetition 0
    (5, 0, 0, 2.5, 1, 1, 2.6),
    (4, 0, 0, 2.5, 1, 1, 2.5), # 0.1 - (1)*(0.08 + 0.02) = 0.1 - 0.1 = 0
    (3, 0, 0, 2.5, 1, 1, 2.36), # 0.1 - (2)*(0.08 + 0.04) = 0.1 - 0.24 = -0.14

    # Quality >= 3, Repetition 1
    (5, 1, 1, 2.5, 6, 2, 2.6),

    # Quality >= 3, Repetition 2
    (5, 6, 2, 2.5, 15, 3, 2.6),

    # EF Floor 1.3
    (3, 10, 5, 1.3, 13, 6, 1.3), # EF drops but capped at 1.3
    (0, 10, 5, 1.2, 1, 0, 1.3),  # Initial EF < 1.3, capped at 1.3
])
def test_sm2_algorithm(quality, interval, repetition, ef, expected_interval, expected_repetition, expected_ef):
    new_interval, new_repetition, new_ef = sm2_algorithm(quality, interval, repetition, ef)
    assert new_interval == expected_interval
    assert new_repetition == expected_repetition
    assert pytest.approx(new_ef) == expected_ef

def test_sm2_ef_calculation_exact():
    # quality = 4: ef = ef + (0.1 - (5-4)*(0.08 + (5-4)*0.02)) = ef + (0.1 - 1*(0.1)) = ef + 0
    _, _, ef = sm2_algorithm(4, 1, 1, 2.5)
    assert pytest.approx(ef) == 2.5

    # quality = 5: ef = ef + (0.1 - (5-5)*(...)) = ef + 0.1
    _, _, ef = sm2_algorithm(5, 1, 1, 2.5)
    assert pytest.approx(ef) == 2.6

    # quality = 3: ef = ef + (0.1 - (5-3)*(0.08 + (5-3)*0.02)) = ef + (0.1 - 2*(0.08 + 0.04)) = ef + (0.1 - 0.24) = ef - 0.14
    _, _, ef = sm2_algorithm(3, 1, 1, 2.5)
    assert pytest.approx(ef) == 2.36

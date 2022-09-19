"""Nerdle game solver unit tests."""
import pytest

import generator
from score import OPERATIONS


class TestGenerator:
    def test_all_answers(self):
        for num_slots in range(4, 8):
            assert all(len(answer) == num_slots for answer in list(generator.all_answers(num_slots)))

    def test_all_answer_equals_generate_answers(self):
        for num_slots in range(4, 8):
            assert set(generator.all_answers(num_slots)) == set(generate_answers(num_slots))

    def test_num_answers(self):
        assert len(list(generator.all_answers(5))) == 217
        assert len(list(generator.all_answers(6))) == 206
        assert len(list(generator.all_answers(7))) == 7561
        assert len(list(generator.all_answers(8))) == 17723


# A fantastic dynamic programming implementation from https://github.com/starypatyk/nerdle-solver/blob/main/gen_perms.py
# Simplified and generalized to any #slots.
# Sadly, but maybe this is expected, this is slower than our non-recursive implementation above.
DIGITS1 = "".join(map(str, range(1, 10)))
DIGITS0 = "0" + DIGITS1
SYMBOLS = DIGITS0 + OPERATIONS


def generate_answers(num_slots: int):
    """Generates all possible Nerdle answers of size 'num_slots'."""
    # TODO: prune the combinations we loop over.
    # TODO: use direct evaluation instead of eval().
    for num_param in range(min(3, num_slots // 2), num_slots - 1):
        num_result_slots = num_slots - num_param - 1
        for answer in _generate_perms(
                0, num_param - 1, "", 0 if num_result_slots == 1 else 10 ** (num_result_slots - 1), 10 ** num_result_slots):
            yield answer


def _generate_perms(level: int, max_level: int, prev_perm: str, result_min: int, result_max: int):
    """Generates the LHS of expressions."""
    after_digit_options, child_generator = \
        (DIGITS1, _generate_perms) if level == 0 else \
        ((DIGITS0, _valid_perm) if level == max_level else (SYMBOLS, _generate_perms))
    # Start with a non-zero digit.
    # Always: Non-zero digit after an operator.
    # In the middle: anything after digit. at the end: end with a digit.
    for char in (DIGITS1 if level > 0 and prev_perm[-1] in OPERATIONS else after_digit_options):
        for answer in child_generator(level + 1, max_level, prev_perm + char, result_min, result_max):
            yield answer


def _valid_perm(level, max_level, perm, ans_min, ans_max):
    val = eval(perm)
    if ans_min <= val < ans_max and (isinstance(val, int) or val.is_integer()):
        yield perm + "=" + str(int(val))

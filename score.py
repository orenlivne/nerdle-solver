"""Conversion from score to hint array and back."""
import functools
import itertools
from enum import Enum

SCORE_GUESS_OPT_SO = "./score_guess_opt.so"

class Hint:
    """Hint codes."""
    ABSENT = 0       # Nerdle black: not in the answer.
    CORRECT = 1         # Nerdle green: in the correct spot.
    PRESENT = 2       # Nerdle purple: in the answer, but not in the correct spot.


HINT_STRING = {Hint.ABSENT: "-", Hint.CORRECT: "+", Hint.PRESENT: "?"}

STRING_TO_HINT = {v: k for k, v in HINT_STRING.items()}

OPERATIONS = "+-*/"
EQUALS = "="

def hints_to_score(hints):
    return functools.reduce(lambda x, y: x | y, (hint << (2 * idx) for idx, hint in enumerate(hints)), 0)


def score_to_hints(score, num_slots):
    return [int("".join(x), 2) for x in grouper(bin(score)[2:].zfill(2 * num_slots), 2)][::-1]


def score_to_hint_string(score, num_slots):
    return "".join(HINT_STRING[int("".join(x), 2)] for x in grouper(bin(score)[2:].zfill(2 * num_slots), 2))[::-1]


def hint_string_to_score(hint_str: str):
    return hints_to_score(list(map(lambda x: STRING_TO_HINT[x], hint_str)))


def grouper(iterable, n, *, incomplete='fill', fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks."
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    if incomplete == 'fill':
        return itertools.zip_longest(*args, fillvalue=fillvalue)
    if incomplete == 'strict':
        return zip(*args, strict=True)
    if incomplete == 'ignore':
        return zip(*args)
    else:
        raise ValueError('Expected fill, strict, or ignore')


class FileHintGenerator:
    def __init__(self, file):
        self._file = file
        self._count = 0

    def __call__(self, guess):
        hint_str = self._file.readline().strip()
        self._count += 1
        return hint_string_to_score(hint_str)

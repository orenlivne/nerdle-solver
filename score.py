"""Conversion from score to hint array and back."""
import functools
import itertools
from enum import Enum

class Hint:
    """Hint codes."""
    INCORRECT = 0       # Nerdle black
    CORRECT = 1         # Nerdle green
    MISPLACED = 2       # Nerdle purple


HINT_STRING = {Hint.INCORRECT: "-", Hint.CORRECT: "+", Hint.MISPLACED: "?"}

STRING_TO_HINT = {v: k for k, v in HINT_STRING.items()}

OPERATIONS = "+-*/"


def score_guess(guess: str, answer: str) -> int:
    """
    Returns the score of a guess.

    :param guess: Guess string.
    :param answer: Answer string.
    :return: Hint string, coded as a binary number. First 2 LSBs = first slot hint, etc.
    """
    # Coded below uses the assumptions that INCORRECT=0 and there are 2 bits of feedback per hint.

    # iterates through guess and answer lists element-by-element. Whenever it finds a match,
    # removes the value from a copy of answer so that nothing is double counted.
    hints = 0
    num_slots = len(answer)
    answer_no_match = [None] * num_slots
    guess_no_match = [None] * num_slots
    idx_no_match = [None] * num_slots  # Indices of 'guess_no_match' characters.
    num_no_match = 0
    for idx, guess_elem, ans_elem in zip(range(num_slots), guess, answer):
        if guess_elem == ans_elem:
            hints |= (Hint.CORRECT << (2 * idx))
        else:
            guess_no_match[num_no_match] = guess_elem
            answer_no_match[num_no_match] = ans_elem
            idx_no_match[num_no_match] = idx
            num_no_match += 1

    # Misplaced characters are flagged left-to-right, i.e., if there are two misplaced "1"s in the guess and one
    # "1" in the answer, the first "1" in the guess will be misplaced, the second incorrect.
    answer_no_match = answer_no_match[:num_no_match]
    for idx, guess_elem in zip(idx_no_match[:num_no_match], guess_no_match[:num_no_match]):
        if guess_elem in answer_no_match:
            hints |= (Hint.MISPLACED << (2 * idx))
            answer_no_match.remove(guess_elem)

    return hints


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

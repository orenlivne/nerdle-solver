"""Conversion from score to hint array and back."""
import functools
import itertools

from nerdle import Hint


def hints_to_score(hints):
    return functools.reduce(lambda x, y: x | y, (hint.value << (2 * idx) for idx, hint in enumerate(hints)), 0)


def score_to_hints(score, num_slots):
    return [Hint(int("".join(x), 2)) for x in grouper(bin(score)[2:].zfill(2 * num_slots), 2)][::-1]


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
"""Nerdle game solver unit tests."""
import ctypes
import pytest

import score as s
import score_guess as sg
from score import Hint, hints_to_score, hint_string_to_score, SCORE_GUESS_OPT_SO
sgo = ctypes.CDLL(SCORE_GUESS_OPT_SO)


class TestScore:
    def test_score_cpp(self):
        # String must be byte-array-encoded for the C++ implementation.
        assert sgo.score_guess(b"54/9=6", b"4*7=28") == \
               hints_to_score((Hint.ABSENT, Hint.PRESENT, Hint.ABSENT, Hint.ABSENT,
                               Hint.PRESENT, Hint.ABSENT))
        assert sgo.score_guess(b"1+9=10", b"1+9=10") == \
               hints_to_score([Hint.CORRECT] * 6)

    def test_score_cython(self):
        assert sg.score_guess("54/9=6", "4*7=28") == \
               hints_to_score((Hint.ABSENT, Hint.PRESENT, Hint.ABSENT, Hint.ABSENT,
                               Hint.PRESENT, Hint.ABSENT))

    def test_score_8slots(self):
        assert sgo.score_guess(b"10-43=66", b"12+34=56") == \
               hints_to_score((Hint.CORRECT, Hint.ABSENT, Hint.ABSENT, Hint.PRESENT,
                               Hint.PRESENT, Hint.CORRECT, Hint.ABSENT, Hint.CORRECT))

        # Repeated digit. First occurrence is correct.
        assert sgo.score_guess(b"10-84=46", b"12+34=56") == \
               hints_to_score((Hint.CORRECT, Hint.ABSENT, Hint.ABSENT, Hint.ABSENT,
                               Hint.CORRECT, Hint.CORRECT, Hint.ABSENT, Hint.CORRECT))

        # Repeated digit. First occurrence is PRESENT.
        assert sgo.score_guess(b"10-43=46", b"12+34=56") == \
               hints_to_score((Hint.CORRECT, Hint.ABSENT, Hint.ABSENT, Hint.PRESENT,
                               Hint.PRESENT, Hint.CORRECT, Hint.ABSENT, Hint.CORRECT))

        # Repeated digit where second occurrence is the correct one. First one should be ABSENT then.
        assert sgo.score_guess(b"40-84=77", b"12+34=56") == \
               hints_to_score((Hint.ABSENT, Hint.ABSENT, Hint.ABSENT, Hint.ABSENT,
                               Hint.CORRECT, Hint.CORRECT, Hint.ABSENT, Hint.ABSENT))

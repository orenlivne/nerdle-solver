"""Nerdle game solver unit tests."""
import ctypes
import itertools
import io
import os
import pickle
import pytest
#from joblib import Parallel, delayed, wrap_non_picklable_objects
from numpy.testing import assert_array_equal

import nerdle
import score as s
import score_guess as sg
from nerdle import NerdleData
from score import Hint, hints_to_score, hint_string_to_score, SCORE_GUESS_OPT_SO
sgo = ctypes.CDLL(SCORE_GUESS_OPT_SO)

# By default, all tests are for mini-nerdle unless #slots explicitly stated in a test function.
NUM_SLOTS = 6
SCORE_DB_MATRIX_FILE = "db/nerdle{}.db".format(NUM_SLOTS)


@pytest.fixture()
def solver_data():
    os.makedirs(os.path.dirname(SCORE_DB_MATRIX_FILE), exist_ok=True)
    return nerdle.create_solver_data(NUM_SLOTS, SCORE_DB_MATRIX_FILE)


class TestNerdle:
    def test_solve(self, solver_data):
        run_solver(solver_data, "4*7=28", "54/9=6", 3)
        run_solver(solver_data, "4*3=12", "54/9=6", 4)
        run_solver(solver_data, "4*3=12", "10-5=5", 3)

    def test_solve_guess_equals_answer(self, solver_data):
        # Guess = answer ==> one guess for a solve.
        run_solver(solver_data, "54/9=6", "54/9=6", 1)

    def test_solve_guess_interactive(self, solver_data):
        answer = "4*3=12"
        initial_guess = "10-5=5"

        hints = [
            "?---?-",
            "?+-+??",
            "++++++",
        ]
        hint_generator = s.FileHintGenerator(io.StringIO("\n".join(hints)))

        solver = nerdle.NerdleSolver(solver_data)
        guess_history, hint_history, answer_size_history = solver.solve_adversary(hint_generator.__call__,
                                                                                  initial_guess=initial_guess)
        assert guess_history is not None
        assert len(guess_history) == 3
        assert guess_history[-1] == answer


def run_solver(solver_data, answer, initial_guess, num_guesses, debug: bool = False):
    solver = nerdle.NerdleSolver(solver_data)
    guess_history, hint_history, answer_size_history = solver.solve(answer, initial_guess=initial_guess, debug=debug)
    assert guess_history is not None
    assert len(guess_history) == num_guesses
    assert guess_history[-1] == answer

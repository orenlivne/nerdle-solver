"""Nerdle game solver unit tests."""
import ctypes
import itertools
import io
import os
import pytest
#from joblib import Parallel, delayed, wrap_non_picklable_objects
from numpy.testing import assert_array_equal

import nerdle

# By default, all tests are for mini-nerdle unless #slots explicitly
# stated in a test function.
NUM_SLOTS = 6


@pytest.fixture()
def solver_data():
    return create_solver_data(NUM_SLOTS)


def create_solver_data(num_slots: int, min_parallel_n: int = 20000):
    file_name = os.path.join(nerdle.DB_DIR, "nerdle{}.db".format(num_slots))
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    return nerdle.solver.create_solver_data(
        num_slots,
        file_name,
        overwrite=True,
        min_parallel_n=min_parallel_n)


class TestSolver:
    def test_solver_data(self):
        n = 206

        # Serial version.
        solver_data = create_solver_data(6, min_parallel_n=2 * n)
        assert solver_data.score_db.shape == (n, n)

        # Parallel version.
        solver_data = create_solver_data(6, min_parallel_n=n // 2)
        assert solver_data.score_db.shape == (n, n)

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
        hint_generator = nerdle.score.FileHintGenerator(io.StringIO("\n".join(hints)))

        solver = nerdle.solver.NerdleSolver(solver_data)
        guess_history, hint_history, answer_size_history = solver.solve_adversary(
            hint_generator.__call__, initial_guess=initial_guess)
        assert guess_history is not None
        assert len(guess_history) == 3
        assert guess_history[-1] == answer


def run_solver(
        solver_data,
        answer,
        initial_guess,
        num_guesses,
        debug: bool = False):
    solver = nerdle.solver.NerdleSolver(solver_data)
    guess_history, hint_history, answer_size_history = solver.solve(
        answer, initial_guess=initial_guess, debug=debug)
    assert guess_history is not None
    assert len(guess_history) == num_guesses
    assert guess_history[-1] == answer

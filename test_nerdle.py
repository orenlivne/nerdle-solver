"""Nerdle game solver unit tests."""
import itertools
import io
import os
import pickle
import pytest

import generator
import nerdle
import score
from nerdle import NerdleData
from score import Hint, hints_to_score, hint_string_to_score

# By default, all tests are for mini-nerdle unless #slots explicitly stated in a test function.
NUM_SLOTS = 6
SCORE_DB_FILE = "nerdle{}.db".format(NUM_SLOTS)


@pytest.fixture()
def solver_data():
    return nerdle.create_solver_data(NUM_SLOTS, SCORE_DB_FILE)


class TestNerdle:
    def test_score(self):
        assert score.score_guess("54/9=6", "4*7=28") == \
               hints_to_score((Hint.INCORRECT, Hint.MISPLACED, Hint.INCORRECT, Hint.INCORRECT,
                               Hint.MISPLACED, Hint.INCORRECT))

    def test_score_8slots(self):
        assert score.score_guess("10-43=66", "12+34=56") == \
               hints_to_score((Hint.CORRECT, Hint.INCORRECT, Hint.INCORRECT, Hint.MISPLACED,
                               Hint.MISPLACED, Hint.CORRECT, Hint.INCORRECT, Hint.CORRECT))

        # Repeated digit. First occurrence is correct.
        assert score.score_guess("10-84=46", "12+34=56") == \
               hints_to_score((Hint.CORRECT, Hint.INCORRECT, Hint.INCORRECT, Hint.INCORRECT,
                               Hint.CORRECT, Hint.CORRECT, Hint.INCORRECT, Hint.CORRECT))

        # Repeated digit. First occurrence is misplaced.
        assert score.score_guess("10-43=46", "12+34=56") == \
               hints_to_score((Hint.CORRECT, Hint.INCORRECT, Hint.INCORRECT, Hint.MISPLACED,
                               Hint.MISPLACED, Hint.CORRECT, Hint.INCORRECT, Hint.CORRECT))

        # Repeated digit where second occurrence is the correct one. First one should be incorrect then.
        assert score.score_guess("40-84=77", "12+34=56") == \
               hints_to_score((Hint.INCORRECT, Hint.INCORRECT, Hint.INCORRECT, Hint.INCORRECT,
                               Hint.CORRECT, Hint.CORRECT, Hint.INCORRECT, Hint.INCORRECT))

    def test_get_score_data(self, solver_data):
        assert all(len(answer) == NUM_SLOTS for answer in solver_data.answers)
        num_answers = 206
        assert len(solver_data.score_db) == num_answers
        assert all(len(value) == num_answers for value in solver_data.score_db.values())

    def test_generate_all_answers(self):
        assert all(len(answer) == NUM_SLOTS for answer in list(generator.all_answers(NUM_SLOTS)))

    def test_num_answers(self):
        assert len(list(generator.all_answers(5))) == 127
        assert len(list(generator.all_answers(6))) == 206
        assert len(list(generator.all_answers(7))) == 6661
#        assert len(list(generator.all_answers(8))) == 17723

    def test_solve(self, solver_data):
        run_solver(solver_data, "4*7=28", "54/9=6", 3)
        run_solver(solver_data, "4*3=12", "54/9=6", 4)
        run_solver(solver_data, "4*3=12", "10-5=5", 3)

    def test_solve_guess_equals_answer(self, solver_data):
        # Guess = answer ==> one guess for a solve.
        run_solver(solver_data, "54/9=6", "54/9=6", 1)

    def test_solve_guess_dict(self, solver_data):
        run_solver(solver_data, "4*3=12", "10-5=5", 3)

    def test_solve_guess_interactive(self, solver_data):
        answer = "4*3=12"
        initial_guess = "10-5=5"

        hints = [
            "?---?-",
            "?+-+??",
            "++++++",
        ]
        hint_generator = score.FileHintGenerator(io.StringIO("\n".join(hints)))

        solver = nerdle.NerdleSolver(solver_data)
        guess_history, hint_history, answer_size_history = solver.solve_adversary(hint_generator.__call__,
                                                                                  initial_guess=initial_guess)
        assert guess_history is not None
        assert len(guess_history) == 3
        assert guess_history[-1] == answer

    # def test_solve_guess_sqlite(self):
    #     # Guess = answer ==> one guess for a solve.
    #     with nerdle.create_solver_data(NUM_SLOTS, SCORE_DB_FILE + "_sqlite", strategy="sqlite") as solver_data:
    #         run_solver(solver_data, "4*3=12", "10-5=5", 3)


def run_solver(solver_data, answer, initial_guess, num_guesses, debug: bool = False):
    solver = nerdle.NerdleSolver(solver_data)
    guess_history, hint_history, answer_size_history = solver.solve(answer, initial_guess=initial_guess, debug=debug)
    assert guess_history is not None
    assert len(guess_history) == num_guesses
    assert guess_history[-1] == answer

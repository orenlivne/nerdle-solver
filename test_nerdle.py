"""Nerdle game solver unit tests."""
import ctypes
import itertools
import io
import os
import pickle
import pytest
#from joblib import Parallel, delayed, wrap_non_picklable_objects
from numpy.testing import assert_array_equal

import generator
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

    # def test_parallelizing_loop_joblib(self):
    #     # This seems to be fine as a nested function, but for more complex examples, make the function
    #     # top-level, as in the following test case.
    #     def process(i: int):
    #         return i * i
    #     results = Parallel(n_jobs=2)(delayed(process)(i) for i in range(10))
    #     assert results == [i ** 2 for i in range(10)]
    #
    # def test_parallelizing_loop_ctypes(self):
    #     guess = str("abd").encode()
    #     answers = ["abc", "def", "efg"]
    #     # Build argument tuples since 'guess' is fixed. Or could use functools.partial().
    #     results = Parallel(n_jobs=2)(
    #             delayed(process)
    #             (guess, answer) for answer in answers
    #       )
    #     assert results == [5, 32, 0]


def process(guess, answer):
    """Must be a top-level function (closure) to be pickeable and used within a joblib pool."""
    return sgo.score_guess(guess, str(answer).encode())


def run_solver(solver_data, answer, initial_guess, num_guesses, debug: bool = False):
    solver = nerdle.NerdleSolver(solver_data)
    guess_history, hint_history, answer_size_history = solver.solve(answer, initial_guess=initial_guess, debug=debug)
    assert guess_history is not None
    assert len(guess_history) == num_guesses
    assert guess_history[-1] == answer

def init_c_library(LIBC):
    # LIBC is now an object and its method are C Code's functions
    #LIBC = ctypes.CDLL(self.path)

    # Settings C library's signature datatype with ctypes data structure tool
    # INFO: To see all datas types that can be transmitted to C Code
    # read ctypes documentation
    # First argument is int : argc
    # Second argument is string array : argv
    # Third is a string : path_to_log_file
    LIBC.score_guess.argtypes = [ctypes.c_int,
                                        ctypes.POINTER(ctypes.c_char_p),
                                        ctypes.c_char_p, ]
    # Return type is int : Return code
    LIBC.score_guess.restypes = [ctypes.c_int, ]
    #
    # #%% Marshalling data for C library
    # # Create a string array with option list length size
    # c_char_pointer_array = ctypes.c_char_p * len(options)
    # # Encode option list
    # encoded_options = [str.encode(str(i)) for i in options ]
    # # Fill the string array with encoded strings
    # # REMINDER: C code only understand encoded strings
    # encoded_options = c_char_pointer_array (*encoded_options)
    # #%% Calling C library wihth encoded options
    # LIBC.score_guess(len(encoded_options), encoded_options, None)

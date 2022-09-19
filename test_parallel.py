"""Nerdle game solver unit tests."""
import ctypes
import functools
import itertools
import os
import multiprocessing

import pytest
#from joblib import Parallel, delayed, wrap_non_picklable_objects
from numpy.testing import assert_array_equal

import nerdle
import score as s
import score_guess as sg
from nerdle import NerdleData
sgo = ctypes.CDLL(s.SCORE_GUESS_OPT_SO)

# By default, all tests are for mini-nerdle unless #slots explicitly stated in a test function.
NUM_SLOTS = 6
SCORE_DB_MATRIX_FILE = "db/nerdle{}.db".format(NUM_SLOTS)


@pytest.fixture()
def solver_data():
    os.makedirs(os.path.dirname(SCORE_DB_MATRIX_FILE), exist_ok=True)
    return nerdle.create_solver_data(NUM_SLOTS, SCORE_DB_MATRIX_FILE)


class TestParallel:
    def test_parallel_map(self):
        with multiprocessing.Pool(processes=4) as pool:
            # print "[0, 1, 4,..., 81]"
            assert pool.map(f, range(10)) == [x * x for x in range(10)]

    def test_parallel_starmap(self):
        a_args = [1, 2, 3]
        second_arg = 1
        with multiprocessing.Pool(processes=4) as pool:
            assert pool.starmap(func, zip(a_args, repeat(second_arg))) == [2, 3, 4]

    @pytest.mark.skip(reason="WIP")
    def test_parallel_starmap(self):
        guess = b"54/9=6"
        answer = "4*7=28"
        answers = [answer for answer in range(3)]
        with multiprocessing.Pool(processes=4) as pool:
            # print "[0, 1, 4,..., 81]"
            assert pool.map(process, answers) == [x * x for x in range(3)]


def f(x):
    return x * x


def g(a, b):
    return a + b


def process(guess, answer):
    """Must be a top-level function (closure) to be pickeable and used within a joblib pool."""
    return sgo.score_guess(guess, str(answer).encode())

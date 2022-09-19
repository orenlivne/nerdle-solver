#!/usr/bin/env python
"""
Nerdle solver. A straightforward application of Knuth's algorithm as applied to Mastermind and implemented in
Python in https://betterprogramming.pub/solving-mastermind-641411708d01.

"Nerdle answers don't use leading zeros or lone zeros, even though some may be accepted as valid guesses.
So you won't find an answer like this: 0+5+5=10, or like this: 01+2+1=4. However, 0 is allowed as the
answer to the right of the equal sign (i.e. 5-3-2=0 is allowed)."
Thus:
1. = must be in the 5th, 6th, or 7th slots in the answer.
2. (= can be in 2nd..7th slot in a guess.).

"Nerdle answers don't start with negative numbers or have a negative number after the equals sign, even though
these may be accepted as valid guesses. So you won't find an answer like this: -5-6=-11. We get it."

3. Only digits may follow =.
4. An operation must be followed by a number.
5. The first slot must be a digit.
6. There has to be at least one op, since the number of slots (8) is even, so can't have xxx=xxx as in 7 slots, say.

Repeating numbers:
https://nerdschalk.com/can-nerdle-repeat-numbers-and-symbols-same-number-twice-rule-explained/

References:
    1. https://betterprogramming.pub/solving-mastermind-641411708d01
    2. https://github.com/aydinschwa/Mastermind-AI
    3. https://www.youtube.com/watch?v=Okm_t5T1PiA&ab_channel=Confreaks
    4. https://www.cs.uni.edu/~wallingf/teaching/cs3530/resources/knuth-mastermind.pdf
"""
import argparse
import collections
import ctypes
import h5py
import itertools
import multiprocessing
import numpy as np
import os
import sys
from typing import Tuple, List, Optional, Set, Dict

import generator
from score import score_to_hint_string, Hint, hints_to_score, hint_string_to_score, FileHintGenerator, SCORE_GUESS_OPT_SO
sgo = ctypes.CDLL(SCORE_GUESS_OPT_SO)    # C++ implementation.


class NerdleData:
    """Encapsulates data structures required for the solver. Matrix implementation -- in-memory numpy array, loaded from
    and saved to a h5py file."""

    def __init__(
            self,
            num_slots: int,
            file_name: str,
            overwrite: bool = False,
            max_answers: Optional[int] = None,
            num_processes: Optional[int] = None,
            min_parallel_n: int = 20000):
        """num_processes = 0 --> serial run."""
        self.num_slots = num_slots
        self._file_name = file_name
        self._answers = None
        if overwrite or not os.path.exists(self._file_name):
            with h5py.File(self._file_name, "w") as f:
                self.answers = sorted(generator.all_answers(self.num_slots))
                if max_answers is not None:
                    self.answers = self.answers[:max_answers]
                if num_processes == 0 or len(self.answers) <= min_parallel_n:
                    create_score_database = NerdleData._create_score_database_serial
                else:
                    def create_score_database(answers): return NerdleData._create_score_database_parallel(
                        answers, num_processes=num_processes)
                self.score_db = np.array(
                    create_score_database(
                        self.answers), dtype=int)
                # Storing answers as bytearray since h5py does not support numpy strings.
                # TODO: just work with bytearrays instead of strings
                # everywhere.
                f.create_dataset("answers", data=np.array(
                    [x.encode() for x in self.answers]))
                f.create_dataset("score_db", data=self.score_db)
                self.answers = np.array(self.answers)
        else:
            with h5py.File(self._file_name, "r") as f:
                self.answers = np.array([x.decode() for x in f["answers"][:]])
                self.score_db = f["score_db"][:, :]

    @staticmethod
    def _create_score_database_parallel(
            answers, num_processes: Optional[int] = None):
        n = len(answers)
        if num_processes is None:
            num_processes = multiprocessing.cpu_count()
        with multiprocessing.Pool(processes=num_processes) as pool:
            score = pool.map(
                _score_guess, itertools.product(
                    answers, repeat=2))
            return np.array(score).reshape(n, n)

    @staticmethod
    def _create_score_database_serial(answers):
        # default dict avoids storing keys as tuple, saves lookup time
        n = len(answers)
        print_frequency = n // 20
        score_db = [[0] * n for _ in range(n)]
        for i, guess in enumerate(answers):
            if print_frequency > 0 and i % print_frequency == 0:
                print("{} / {} ({:.1f}%) completed".format(i, n, (100 * i) / n))
            guess_encoded = str(guess).encode()
            score_db[i] = [
                sgo.score_guess(
                    guess_encoded,
                    str(answer).encode()) for answer in answers]
        return score_db

    @property
    def all_keys(self) -> List[int]:
        return np.arange(len(self.answers), dtype=int)

    @property
    def initial_answers(self) -> np.ndarray:
        return np.arange(len(self.answers), dtype=int)

    def key(self, guess: str) -> int:
        return np.where(self.answers == guess)[0][0]

    def value(self, guess_key: int) -> str:
        return self.answers[guess_key]

    def answers_of_score(
            self,
            guess: int,
            score_db,
            answers: np.ndarray,
            answer_keys: np.ndarray,
            score: int):
        index = np.where(score_db[guess, answers] == score)[0]
        return index, answer_keys[index]

    def restrict_by_answers(self, score_db, answer_index: List[int]):
        score_db = score_db[:, answer_index]
        answer_index = np.arange(score_db.shape[1], dtype=int)
        return score_db, answer_index


class NerdleSolver:
    """
    Solves a Nerdle game.
    Note: modifies the internal data structures during solve() calls, so cannot be reused after solve() is called.
    """

    def __init__(self, data: NerdleData):
        self._data = data
        # A working copy of data.score_db entries modified within solve().
        self._score_db = data.score_db
        self._all_answers = self._data.answers
        self._all_keys = self._data.all_keys
        self._answer_keys = self._data.all_keys
        self._answers = self._data.initial_answers
        self._num_slots = len(next(iter(self._all_answers)))
        self._all_correct = hints_to_score([Hint.CORRECT] * self._num_slots)

    def solve(self,
              answer: str,
              max_guesses: int = 6,
              initial_guess: str = "0+12/3=4",
              debug: bool = False) -> Tuple[List[str],
                                            List[int],
                                            List[int]]:
        return self.solve_adversary(
            lambda guess: sgo.score_guess(
                str(guess).encode(),
                str(answer).encode()),
            max_guesses=max_guesses,
            initial_guess=initial_guess,
            debug=debug)

    def guess_key(self, guess):
        return self._data.key(guess)

    def guess_value(self, guess_key):
        return self._data.value(guess_key)

    def is_correct(self, score):
        return score == self._all_correct

    def solve_adversary(self,
                        hint_generator,
                        max_guesses: int = 6,
                        initial_guess: str = "0+12/3=4",
                        debug: bool = False) -> Tuple[List[str],
                                                      List[int],
                                                      List[int]]:
        guesses_left = max_guesses
        hint_history = []
        answer_size_history = []
        guess = initial_guess
        guess_key = self.guess_key(guess)
        guess_history = [guess]

        while guesses_left > 0:
            # reduce amount of possible answers by checking answer against
            # guess and score.
            guesses_left -= 1
            if debug:
                print("--> guess {} guesses_left {}".format(guess, guesses_left))
            score = hint_generator(guess)
            hint_history.append(score)
            if debug:
                print(
                    "score {} {}".format(
                        score_to_hint_string(
                            score,
                            self._num_slots),
                        score))
            if self.is_correct(score):
                return guess_history, hint_history, answer_size_history
            guess_key = self.make_guess(guess_key, score)
            guess = self.guess_value(guess_key)
            if debug:
                print("answers {}".format(len(self._answers)))
            if guess is not None:
                guess_history.append(guess)
            answer_size_history.append(len(self._answers))

        # Failed to solve within the allotted number of guesses.
        return None, None, None

    def make_guess(self, guess: str, score: int) -> Optional[str]:
        # Restrict possible_score_db to only include possible answers. This creates a new dictionary,
        # so it does not override self.score_db.
        self._answers, self._answer_keys = self._data.answers_of_score(
            guess, self._score_db, self._answers, self._answer_keys, score)
        self._score_db, self._answers = self._data.restrict_by_answers(
            self._score_db, self._answers)
        if score == self._all_correct:
            return None
        # Make the next guess.
        # - Find how often a score appears in scores_by_answer_dict, get max (worst case).
        # Sort by score, then by guess possibility (prefer possible guesses over impossible ones.), get min (best case).
        # TODO: a possible improvement is to weight the counts by bigram conditional probabilities (how likely a
        #  character is to appear after another in the current answer set).
        return min(
            (max(collections.Counter(self._score_db[guess_key]).values()),
             guess_key not in self._answer_keys,
             guess_key)
            for guess_key in self._all_keys
        )[-1]


def parse_args():
    """Defines and parses command-line flags."""
    parser = argparse.ArgumentParser(
        description="Nerdle Solver database craetor.")
    parser.add_argument("--num_slots", default=6, type=int,
                        help="Number of slots in answer.")
    parser.add_argument(
        "--score_db",
        default="nerdle.db",
        help="Path to score database file name.")
    parser.add_argument(
        "--num_jobs",
        default=0,
        type=int,
        help="Number of parallel jobs.")
    return parser.parse_args()


def create_solver_data(
        num_slots: int,
        file_name: str,
        overwrite: bool = False,
        max_answers: Optional[int] = None,
        num_processes: int = 2,
        min_parallel_n: int = 20000) -> NerdleData:
    """Creates/load solver data from existing h5py database file."""
    return NerdleData(
        num_slots,
        file_name,
        overwrite=overwrite,
        max_answers=max_answers,
        num_processes=num_processes,
        min_parallel_n=min_parallel_n)


def _score_guess(args):
    guess, answer = args
    """Must be a top-level function (closure) to be pickeable and used within a joblib pool."""
    return sgo.score_guess(str(guess).encode(), str(answer).encode())


class Node:
    def __init__(self, data, children):
        self.children = children
        self.data = data


if __name__ == "__main__":
    args = parse_args()
    solver_data_cy = create_solver_data(
        args.num_slots,
        args.score_db,
        overwrite=True,
        num_processes=args.num_jobs)

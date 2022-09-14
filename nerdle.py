#!/usr/bin/env python
"""
Nerdle solver. A straightforward application of Knuth's algorithm as applied to Mastermind and implemented in
Python in https://betterprogramming.pub/solving-mastermind-641411708d01.

"Nerdle answers don't use leading zeros or lone zeros, even though some may be accepted as valid guesses.
So you won't find an answer like this: 0+5+5=10, or like this: 01+2+1=4. However, 0 is allowed as the
answer to the right of the equal sign (i.e. 5-3-2=0 is allowed)."
Thus:
1. = must be in th e5th, 6th, or 7th slots in the answer.
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
import itertools
import numpy as np
import os
import pickle
import sys
from typing import Tuple, List, Optional, Set, Dict

import generator
from score import score_to_hint_string, Hint, hints_to_score, hint_string_to_score, FileHintGenerator
from score_guess import score_guess


class NerdleData:
    """Encapsulates data structures required for the solver."""
    def __init__(self, num_slots: int, file_name: str):
        self.num_slots = num_slots
        self._file_name = file_name
        self._answers = None


class _NerdleDataDict(NerdleData):
    """Encapsulates data structures required for the solver. Dictionary implementation -- in-memory dict, loaded from
    and saved to a pickle file."""
    def __init__(self, num_slots: int, file_name: str, overwrite: bool = False, max_answers: Optional[int] = None):
        super(_NerdleDataDict, self).__init__(num_slots, file_name)
        if overwrite or not os.path.exists(self._file_name):
            with open(self._file_name , "wb") as f:
                answers = set(generator.all_answers(self.num_slots))
                if max_answers is not None:
                    answers = set(sorted(answers)[:max_answers])
                self.score_db = _NerdleDataDict._create_score_database(answers)
                pickle.dump(self.score_db, f)
        else:
            with open(self._file_name, "rb") as f:
                self.score_db = pickle.load(f)

    @staticmethod
    def _create_score_database(answers):
        # default dict avoids storing keys as tuple, saves lookup time
        n = len(answers)
        num_slots = len(next(iter(answers)))
        print_frequency = n // 20
        score_db = {}
        for i, guess in enumerate(answers):
            if print_frequency > 0 and i % print_frequency == 0:
                print("{} / {} ({:.1f}%) completed".format(i, n, (100 * i) / n))
            score_db[guess] = {answer: score_guess(guess, answer) for answer in answers}
        return score_db

    @property
    def answers(self) -> List[str]:
        """Returns the list of all answers. Deterministic order (sorted)."""
        if self._answers is None:
            self._answers = sorted(self.score_db.keys())
        return self._answers

    @property
    def all_keys(self) -> List[str]:
        return self._answers

    @property
    def initial_answers(self) -> Set[str]:
        return set(self._answers)

    def num_answers(self, answers):
        return len(answers)

    def key(self, guess: str) -> str:
        return guess

    def value(self, guess_key: str) -> str:
        return guess_key

    def answers_of_score(self, guess: str, score_db, answers: Set[str], score: int) -> Set[str]:
        return {a for a in answers if score_db[guess][a] == score}

    def restrict_by_answers(self, score_db, answers: Set[str]):
        return {
            guess: dict((answer, score) for answer, score in scores_by_answer_dict.items() if answer in answers)
            for guess, scores_by_answer_dict in score_db.items()
        }, answers

    def score_values(self, score_db):
        return score_db.values()


class _NerdleDataMatrix(NerdleData):
    """Encapsulates data structures required for the solver. Matrix implementation -- in-memory numpu array, loaded from
    and saved to a h5py file."""
    def __init__(self, num_slots: int, file_name: str, overwrite: bool = False,
                 max_answers: Optional[int] = None):
        super(_NerdleDataMatrix, self).__init__(num_slots, file_name)
        if overwrite or not os.path.exists(self._file_name):
            with open(self._file_name , "wb") as f:
                self.answers = np.array(sorted(generator.all_answers(self.num_slots)))
                if max_answers is not None:
                    self.answers = self.answers[:max_answers]
                self.score_db = _NerdleDataMatrix._create_score_database(self.answers)
                pickle.dump({"answers": self.answers, "score_db": self.score_db}, f)
        else:
            with open(self._file_name, "rb") as f:
                data = pickle.load(f)
                self.answers = data["answers"]
                self.score_db = data["score_db"]

    @staticmethod
    def _create_score_database(answers):
        # default dict avoids storing keys as tuple, saves lookup time
        n = len(answers)
        print_frequency = n // 20
        score_db = np.zeros((n, n), dtype=int)
        for i, guess in enumerate(answers):
            if print_frequency > 0 and i % print_frequency == 0:
                print("{} / {} ({:.1f}%) completed".format(i, n, (100 * i) / n))
            score_db[i] = [score_guess(str(guess), str(answer)) for answer in answers]
        return score_db

    @property
    def all_keys(self) -> List[int]:
        return np.arange(len(self.answers), dtype=int)

    @property
    def initial_answers(self) -> np.ndarray:
        return np.full((self.score_db.shape[1], ), True, dtype=bool)

    def num_answers(self, answers):
        return np.sum(answers)

    def key(self, guess: str) -> int:
        return np.where(self.answers == guess)[0][0]

    def value(self, guess_key: int) -> str:
        return self.answers[guess_key]

    def answers_of_score(self, guess: int, score_db, answers: List[str], score: int) -> np.ndarray:
        return score_db[guess, answers] == score

    def restrict_by_answers(self, score_db, answer_index: List[int]):
        score_db = score_db[:, answer_index]
        answer_index = np.full((score_db.shape[1], ), True, dtype=bool)
        return score_db, answer_index

    def score_values(self, score_db):
        return score_db


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
        self._answers = self._data.initial_answers
        self._num_slots = len(next(iter(self._all_answers)))
        self._all_correct = hints_to_score([Hint.CORRECT] * self._num_slots)

    def solve(self, answer: str, max_guesses: int = 6, initial_guess: str = "0+12/3=4",
              debug: bool = False) -> Tuple[List[str], List[int], List[int]]:
        return self.solve_adversary(lambda guess: score_guess(str(guess), str(answer)),
                                    max_guesses=max_guesses, initial_guess=initial_guess, debug=debug)

    def solve_adversary(self, hint_generator, max_guesses: int = 6, initial_guess: str = "0+12/3=4",
                debug: bool = False) -> Tuple[List[str], List[int], List[int]]:
        guesses_left = max_guesses
        hint_history = []
        answer_size_history = []
        guess = initial_guess
        guess_key = self._data.key(guess)
        guess_history = [guess]

        while guesses_left > 0:
            # reduce amount of possible answers by checking answer against guess and score.
            if debug:
                print("--> guess {}".format(guess))
            score = hint_generator(guess)
            guess_key = self.make_guess(guess_key, score)
            guess = self._data.value(guess_key)
            if debug:
                print("score {} {} answers {}".format(
                    score_to_hint_string(score, self._num_slots), score, self._data.num_answers(self._answers)))
            if guess is not None:
                guess_history.append(guess)
            hint_history.append(score)
            answer_size_history.append(len(self._answers))

            guesses_left -= 1
            if score == self._all_correct:
                return guess_history, hint_history, answer_size_history

        # Failed to solve within the allotted number of guesses.
        return None, None, None

    def make_guess(self, guess: str, score: int) -> Optional[str]:
        # Restrict possible_score_db to only include possible answers. This creates a new dictionary,
        # so it does not override self.score_db.
        self._answers = self._data.answers_of_score(guess, self._score_db, self._answers, score)
        self._score_db, self._answers = self._data.restrict_by_answers(self._score_db, self._answers)
        if score == self._all_correct:
            return None
        # Make the next guess.
        # - Find how often a score appears in scores_by_answer_dict, get max (worst case).
        # Sort by score, then by guess possibility (prefer possible guesses over impossible ones.), get min (best case).
        # TODO: a possible improvement is to weight the counts by bigram conditional probabilities (how likely a
        #  character is to appear after another in the current answer set).
        print([(max(collections.Counter(self._data.score_values(self._score_db[guess_key])).values()),
             guess_key not in self._answers,
             guess_key)
            for guess_key in self._all_keys])
        return min(
            (max(collections.Counter(self._data.score_values(self._score_db[guess_key])).values()),
             guess_key not in self._answers,
             guess_key)
            for guess_key in self._all_keys
        )[-1]


def parse_args():
    """Defines and parses command-line flags."""
    parser = argparse.ArgumentParser(description="Nerdle Solver.")
    parser.add_argument("--num_slots", default=6, type=int, help="Number of slots in answer.")
    parser.add_argument("--score_db", default="nerdle.db", help="Path to score database file name.")
    return parser.parse_args()


def create_solver_data(num_slots: int, file_name: str, strategy: str = "dict", overwrite: bool = False,
                       max_answers: Optional[int] = None) -> NerdleData:
    """Creates/load solver data from existing database file. For small files, uses pickle. For large files, uses
    SQLite."""
    if strategy == "dict":
        return _NerdleDataDict(num_slots, file_name, overwrite=overwrite, max_answers=max_answers)
    elif strategy == "matrix":
        return _NerdleDataMatrix(num_slots, file_name, overwrite=overwrite, max_answers=max_answers)
    else:
        raise ValueError("Unsupported NerdleData strategy {}".format(strategy))


if __name__ == "__main__":
    args = parse_args()

    # Create/load solver data.
    solver_data = create_solver_data(args.num_slots, args.score_db)

    print("Loaded: slots {} answers {} score_db size {}".format(
        solver_data.num_slots, len(solver_data.score_db), len(solver_data.score_db.items())))

    initial_guess = "10-5=5"
    # answer = "4*3=12"
    # guess_history, hint_history, answer_size_history = NerdleSolver(solver_data).solve(answer, initial_guess=initial_guess, debug=True)

    def hint_generator(guess):
        hint_str = input("> ")
        return hint_string_to_score(hint_str)

    hint_generator = FileHintGenerator(sys.stdin)
    guess_history, hint_history, answer_size_history = NerdleSolver(solver_data).solve_adversary(hint_generator.__call__, initial_guess=initial_guess, debug=True)

#
#     for param_values, result in answers:
#         print(param_values, result)
# #        print("".join(map(str, param_values)) + "=" + str(int(result)))

    # Assumes that the set of all guesses = set of all answers. A Nerdle guess must "compute", i.e., must be a valid
    # arithmetic expression of the form 'LHS=RHS'. Since we assume the user knows the rules and does not enter unary
    # '-' operations of numbers with leading zeros, for instance, the set of guesses should equal the set of answers.

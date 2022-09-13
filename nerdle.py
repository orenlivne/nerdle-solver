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
import os
import pickle
import shelve
from typing import Tuple, List

import generator
from score import score_guess, score_to_hint_string, Hint


class NerdleData:
    """Encapsulates data structures required for the solver."""
    def __init__(self, num_slots: int, file_name: str):
        self.num_slots = num_slots
        self._file_name = file_name
        self._answers = None

    @property
    def answers(self):
        """Returns the list of all answers. Deterministic order (sorted)."""
        if self._answers is None:
            self._answers = sorted(self.score_dict.keys())
        return self._answers

    def open(self):
        return self.__enter__()

    def close(self):
        return self.__exit__(None, None, None)


class _NerdleDataDict(NerdleData):
    """Encapsulates data structures required for the solver. Dictionary implementation -- in-memory dict, loaded from
    and saved to a pickle file."""
    def __init__(self, num_slots: int, file_name: str):
        super(_NerdleDataDict, self).__init__(num_slots, file_name)

    def __enter__(self):
        if not os.path.exists(self._file_name + ".db"):
            with open(self._file_name , "wb") as f:
                self.score_dict = {}
                create_score_dictionary(set(generator.all_answers(self.num_slots)), self.score_dict)
                pickle.dump(self.score_dict, f)
        else:
            with open(self._file_name, "rb") as f:
                self.score_dict = pickle.load(f)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class _NerdleDataShelve(NerdleData):
    """Encapsulates data structures required for the solver. shelve implementation, for large #slots."""
    def __init__(self, num_slots: int, file_name: str):
        super(_NerdleDataShelve, self).__init__(num_slots, file_name)

    def __enter__(self):
        if not os.path.exists(self._file_name + ".db"):
            self.score_dict = shelve.open(file_name)
            create_score_dictionary(set(generator.all_answers(self.num_slots)), self.score_dict)
        else:
            self.score_dict = shelve.open(self._file_name)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.score_dict.close()


class NerdleSolver:
    """
    Solves Nerdle queries.

    Note: modifies 'data' during solve() calls and then restores it. So cannot be used concurrently with
    the same 'data' object. Copying the data structures to each solver instance is too time and memory intensive.
    """
    def __init__(self, data: NerdleData):
        # Keeps track of the data.score_dict entries we modify in a solve() call. Typically, there are only few
        # of them.
        self._data = data

    def solve(self, answer: str, max_guesses: int = 6, initial_guess: str = "0+12/3=4",
              debug: bool = False) -> Tuple[List[str], List[int]]:
        guesses_left = max_guesses
        score_dict = self._data.score_dict
        answers = set(score_dict.keys())
        num_slots = len(next(iter(answers)))
        guess_history = []
        hint_history = []
        while guesses_left > 0:
            if guesses_left == max_guesses:
                guess = initial_guess
            else:
                # Make the next guess.
                # find how often a score appears in scores_by_answer_dict, get max.
                # Prefer possible guesses over impossible ones.
                # Sort by score, then by guess possibility.
                guess = min(
                    (max(collections.Counter(scores_by_answer_dict.values()).values()), guess not in answers, guess)
                    for guess, scores_by_answer_dict in score_dict.items()
                )[-1]
            guess_history.append(guess)
            # reduce amount of possible answers by checking answer against guess and score.
            score = score_guess(guess, answer)
            hint_history.append(score)
            answers = {a for a in answers if score_dict[guess][a] == score}
            # Restrict possible_score_dict to only include possible answers. This creates a new dictionary,
            # so it does not override self.score_dict.
            score_dict = {
                guess: dict((answer, score) for answer, score in scores_by_answer_dict.items() if answer in answers)
                for guess, scores_by_answer_dict in score_dict.items()
            }
            if debug:
                print("guess {} score {} answers {}".format(
                    guess, score_to_hint_string(score, num_slots), len(answers)))

            guesses_left -= 1
            if guess == answer:
                return guess_history, hint_history

        # Failed to solve within the allotted number of guesses.
        return None, None


def parse_args():
    """Defines and parses command-line flags."""
    parser = argparse.ArgumentParser(description="Nerdle Solver.")
    parser.add_argument("--mode", default=None, required=True, choices=["build_dict"],
                        help="Running mode. 'build_dict': builds score dictionary and saves to a file.")
    parser.add_argument("--slots", default=6, type=int, help="Number of slots in answer.")
    parser.add_argument("--score_dict_file", default="score_dict.pickle",
                        help="Path to score dictionary pickle file name.")
    return parser.parse_args()


def create_solver_data(num_slots: int, file_name: str) -> NerdleData:
    """Creates/load solver data from existing database file. For small files, uses pickle. For large files, uses
    shelve."""
    if num_slots <= 6:
        return _NerdleDataDict(num_slots, file_name + ".db")
    else:
        return _NerdleDataShelve(num_slots, file_name)


def create_score_dictionary(answers, score_dict: shelve.Shelf):
    # default dict avoids storing keys as tuple, saves lookup time
    n = len(answers) ** 2
    for i, guess in enumerate(answers):
        if i % 10000000 == 0:
            print("{} / {} ({:.1f}%) completed".format(i, n, (100 * i) / n))
        score_dict[guess] = {answer: score_guess(guess, answer) for answer in answers}
    return score_dict


if __name__ == "__main__":
    args = parse_args()

    # Create/load solver data.
    solver_data = create_solver_data(args.slots, args.score_dict_file)

    # if args.mode == "build_dict":
    # elif args.mode == "run":
    print("Slots {} answers {} score_dict size {}".format(
        solver_data.num_slots, len(solver_data.score_dict), len(solver_data.score_dict.items())))
#
#     for param_values, result in answers:
#         print(param_values, result)
# #        print("".join(map(str, param_values)) + "=" + str(int(result)))

    # Assumes that the set of all guesses = set of all answers. A Nerdle guess must "compute", i.e., must be a valid
    # arithmetic expression of the form 'LHS=RHS'. Since we assume the user knows the rules and does not enter unary
    # '-' operations of numbers with leading zeros, for instance, the set of guesses should equal the set of answers.

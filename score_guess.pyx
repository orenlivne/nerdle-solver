import cython
from score import Hint

@cython.boundscheck(False)
@cython.wraparound(False)

def score_guess(str guess, str answer):
    """
    Returns the score of a guess.
    A score is an encoded int, where each 2 bits represent a hint (first LSBs = first slot, etc.).

    :param guess: Guess string.
    :param answer: Answer string.
    :return: Hint string, coded as a binary number. First 2 LSBs = first slot hint, etc.
    """
    # Coded below uses the assumptions that INCORRECT=0 and there are 2 bits of feedback per hint.

    # iterates through guess and answer lists element-by-element. Whenever it finds a match,
    # removes the value from a copy of answer so that nothing is double counted.
    hints = 0
    num_slots = len(answer)
    answer_no_match = [None] * num_slots
    guess_no_match = [None] * num_slots
    idx_no_match = [None] * num_slots  # Indices of 'guess_no_match' characters.
    num_no_match = 0
    for idx, guess_elem, ans_elem in zip(range(num_slots), guess, answer):
        if guess_elem == ans_elem:
            hints |= (Hint.CORRECT << (2 * idx))
        else:
            guess_no_match[num_no_match] = guess_elem
            answer_no_match[num_no_match] = ans_elem
            idx_no_match[num_no_match] = idx
            num_no_match += 1

    # Misplaced characters are flagged left-to-right, i.e., if there are two misplaced "1"s in the guess and one
    # "1" in the answer, the first "1" in the guess will be misplaced, the second incorrect.
    answer_no_match = answer_no_match[:num_no_match]
    for idx, guess_elem in zip(idx_no_match[:num_no_match], guess_no_match[:num_no_match]):
        if guess_elem in answer_no_match:
            hints |= (Hint.MISPLACED << (2 * idx))
            answer_no_match.remove(guess_elem)

    return hints

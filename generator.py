"""Generates the pace of answers of a Nerdle game."""
import collections
import itertools
from typing import Tuple, List

from score import OPERATIONS, EQUALS


def all_answers(num_slots: int, debug: bool = False) -> List[str]:
    """Generates all possible Nerdle answers of size 'num_slots'."""
    # TODO: prune the combinations we loop over.
    # TODO: use direct evaluation instead of eval()?
    # If num_slots is odd, we have the corner case of X=X expressions with no ops.
    if num_slots % 2 == 1:
        num_result_slots =  num_slots // 2
        result_range = (0 if num_result_slots == 1 else 10 ** (num_result_slots - 1), 10 ** num_result_slots)
        for x in range(result_range[0], result_range[1]):
            yield str(x) + EQUALS + str(x)

    for num_param in range(3, num_slots - 1):
        num_result_slots = num_slots - num_param - 1
        result_range = (0 if num_result_slots == 1 else 10 ** (num_result_slots - 1), 10 ** num_result_slots)
        if debug:
            print("param_slots", num_param, "X" * num_param + " = " + "X" * num_result_slots,
                  "result_range", result_range)
        # Enumerate all answers with "=" at the 'num_param' slot via all possible splitting of the LHS expression
        # by operation locations. Within each part we loop over integers, which is probably faster than looping over
        # and concatenating numerical characters ('012345678').
        for num_ops in range(1, (num_param - 1) // 2 + 1):
            op_slots = [
                combination
                for combination in itertools.combinations(range(1, num_param - 1), num_ops)
                if len(combination) == 1 or min(diff(combination)) > 1
                ]
            for op_slot in op_slots:
                param_lens = [(n - 1) for n in diff((-1, ) + op_slot + (num_param, ))]
                if debug:
                    print("\t\t", "o".join("X" * n for n in param_lens) + " = " + "X" * (num_slots - num_param - 1))
                for param_values in itertools.product(*(
                        list(itertools.chain.from_iterable(
                            tuple((range(10 ** (n - 1), 10 ** n), OPERATIONS) for n in param_lens)))[:-1]
                )):
                    s = "".join(map(str, param_values))
                    result = eval(s)
                    if result_range[0] <= result < result_range[1] and \
                            (isinstance(result, int) or result.is_integer()):
                        yield s + EQUALS + str(int(result))


def diff(x: Tuple[int]) -> Tuple[int]:
    return tuple(x[i + 1] - x[i] for i in range(len(x) - 1))

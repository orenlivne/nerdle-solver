"""Generates the pace of answers of a Nerdle game."""
import itertools
from typing import Tuple, List

from .score import OPERATIONS, EQUALS


def all_answers(num_slots: int, debug: bool = False) -> List[str]:
    """Generates all possible Nerdle answers of size 'num_slots'."""
    # TODO: prune the combinations we loop over.
    # TODO: use direct evaluation instead of eval()?

    # If num_slots is odd, we have a corner case: X=X expressions with no ops.
    if num_slots % 2 == 1:
        num_result_slots = num_slots // 2
        result_range = (0 if num_result_slots == 1 else 10 ** (num_result_slots - 1), 10 ** num_result_slots)
        for x in range(result_range[0], result_range[1]):
            yield str(x) + EQUALS + str(x)

    # Loop over left-hand-side expression size.
    for num_param in range(3, num_slots - 1):
        num_result_slots = num_slots - num_param - 1
        result_range = (0 if num_result_slots == 1 else 10 ** (num_result_slots - 1), 10 ** num_result_slots)
        if debug:
            print("param_slots", num_param, "X" * num_param + " = " + "X" * num_result_slots, "result", result_range)
        # Loop over number of operations.
        for num_ops in range(1, (num_param - 1) // 2 + 1):
            # Loop over all valid combinations of operations. They cannot appear at first and last slot, and cannot be
            # next to each other (no unary '-' allowed).
            for op_slot in (combination for combination in itertools.combinations(range(1, num_param - 1), num_ops)
                            if len(combination) == 1 or all(x > 1 for x in diff(combination))):
                param_lens = [(n - 1) for n in diff((-1,) + op_slot + (num_param,))]
                if debug:
                    print("\t\t", "o".join("X" * n for n in param_lens) + " = " + "X" * num_result_slots)
                for param_values in itertools.product(*(list(itertools.chain.from_iterable(
                        tuple((range(10 ** (n - 1), 10 ** n), OPERATIONS) for n in param_lens)))[:-1])):
                    s = "".join(map(str, param_values))
                    result = eval(s)
                    if result_range[0] <= result < result_range[1] and \
                            (isinstance(result, int) or result.is_integer()):
                        yield s + EQUALS + str(int(result))


def diff(x: Tuple[int]) -> Tuple[int]:
    return tuple(x[i + 1] - x[i] for i in range(len(x) - 1))

"""Nerdle game solver unit tests."""
import collections
import os
import numpy as np
import pytest

import analysis
import nerdle

NUM_SLOTS = 6


@pytest.fixture()
def solver_data():
    return create_solver_data(NUM_SLOTS)


def create_solver_data(num_slots: int, min_parallel_n: int = 20000):
    file_name = "db/nerdle{}.db".format(num_slots)
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    return nerdle.create_solver_data(
        num_slots,
        file_name,
        overwrite=True,
        min_parallel_n=min_parallel_n)


class TestAnalysis:
    def test_game_tree_builder(self, solver_data):
        tree = analysis.GameTreeBuilder(solver_data).build()

        # Distribution of #guesses for all answers.
        tdc = analysis.TreeDepthCalculator(tree)
        num_guesses = np.array(
            [depth for node, depth in tdc.depth.items() if not node.children]) + 1
        freq = collections.Counter(num_guesses)
        num_leaves = sum(1 for node in tdc.depth if not node.children)

        assert num_leaves == len(solver_data.answers)
        assert freq == {3: 173, 2: 31, 4: 2}

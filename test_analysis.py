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

    def test_game_tree_builder_multilevel(self, solver_data):
        tree = analysis.GameTreeBuilder(solver_data).build(strategy="multilevel")

        # Distribution of #guesses for all answers.
        tdc = analysis.TreeDepthCalculator(tree)
        num_guesses = np.array(
            [depth for node, depth in tdc.depth.items() if not node.children]) + 1
        freq = collections.Counter(num_guesses)
        num_leaves = sum(1 for node in tdc.depth if not node.children)

        assert num_leaves == len(solver_data.answers)
        assert freq == {3: 173, 2: 31, 4: 2}

    def test_min_biased_multilevel_sampling_score_db_6_slots(self, solver_data):
        np.random.seed(0)
        a = solver_data.score_db

        quantity = lambda a: analysis.max_bucket_sizes(a) / a.shape[1]
        exact = quantity(a)
        approx = analysis.min_biased_multilevel_sampling(a, quantity, min_sample_size=100)

        assert min(approx) == min(exact)

    def test_min_biased_multilevel_sampling_random_matrix(self, solver_data):
        np.random.seed(0)
        a = np.random.randint(0, 50, (1000, 1000))

        quantity = lambda a: analysis.max_bucket_sizes(a) / a.shape[1]
        exact = quantity(a)
        exact_min = min(exact)

        approx = analysis.min_biased_multilevel_sampling(a, quantity, min_sample_size=100, sample_factor=1.9)
        assert min(approx) == exact_min

        approx = analysis.min_biased_multilevel_sampling(a, quantity, min_sample_size=100, sample_factor=1.5)
        assert min(approx) <= 1.05 * exact_min

    def test_min_biased_multilevel_sampling_small_matrix(self, solver_data):
        np.random.seed(0)
        a = np.random.randint(0, 50, (217, 9))
        quantity = lambda a: analysis.max_bucket_sizes(a) / a.shape[1]

        approx = analysis.min_biased_multilevel_sampling(a, quantity, min_sample_size=100, sample_factor=1.9)

        assert len(approx) == 217
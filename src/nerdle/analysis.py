"""Nerdle Game tree builder and analysis of distribution of #guesses over all answers."""
import collections
import numpy as np
import scipy.stats
from typing import Iterable, Dict

from . import solver


class Node:
    def __init__(self, key, guesses, answers, score, children, hint=None, parent=None):
        self.key = key
        self.guesses = guesses
        self.answers = answers
        self.score = score
        self.hint = hint
        self.children = children
        self.parent = parent

    def __repr__(self):
        return "Node[key={}, guesses={} answers={}{}, score={}, children={}]".format(
            self.key, len(self.guesses), len(self.answers),
            " " + str(self.answers) if len(self.answers) <= 10 else "",
            self.score.shape, len(self.children))

    def __str__(self):
        return repr(self)

    def guess_key(self, key):
        """Returns the root-level index of guess key(s) (intt or np.ndarray) of this node."""
        node = self
        while node.parent:
            node = node.parent
            key = node.guesses[key]
        return key

    def answer_key(self, key):
        """Returns the root-level index of answer key(s) (intt or np.ndarray) of this node."""
        node = self
        while node.parent:
            node = node.parent
            key = node.answers[key]
        return key


class GameTreeBuilder:
    def __init__(self, solver_data, max_answers: int = 10000000):
        self._solver_data = solver_data
        self._score_db = solver_data.score_db.copy()[:, :max_answers]
        self._solver = solver.NerdleSolver(solver_data)
        self._all_keys = solver_data.all_keys
        self._n = len(solver_data.all_keys)

    def build(self, debug: bool = False, strategy="minimax",
              min_sample_size: int = 2000, sample_factor: float = 1.7,
              guess_coarsening_factor: float = 4) -> Node:
        if strategy == "minimax":
            bucket_size_functor = max_bucket_sizes
        elif strategy == "multilevel":
            def bucket_size_functor(a):
                if a.shape[1] <= min_sample_size:
                    #print(a.shape, "max_bucket_sizes")
                    return max_bucket_sizes(a)
                else:
                    print(a.shape, "min_biased_multilevel_sampling")
                    return min_biased_multilevel_sampling(
                        a, max_bucket_sizes, min_sample_size=min_sample_size,
                        sample_factor=sample_factor)
        else:
            raise ValueError("Unknown max bucket calculation strategy {}".format(strategy))
        quantity = lambda a: bucket_size_functor(a) / a.shape[1]
        root = Node(None, self._all_keys, self._all_keys, self._score_db, [])
        pre_traversal(root, lambda node: self._process_node(
            node, quantity, guess_coarsening_factor=guess_coarsening_factor), debug=debug)
        return root

    def _process_node(self, node, bucket_size_functor, guess_coarsening_factor: float = 4):
        if len(node.answers) == 1:
            guess_is_answer = np.where(node.guesses == node.answers[0])[0]
            if len(guess_is_answer) != 1 or not self._solver.is_correct(node.score[guess_is_answer[0], 0]):
                raise ValueError("Failed to solve game")
        else:
            # Coarsen in rows (guesses).
            score = node.score
            if guess_coarsening_factor > 1 and len(node.answers) <= 0.1 * self._n:
                # Coarsen in rows.
                guesses = np.sort(
                    np.concatenate(
                    (node.answers,
                     np.random.choice(np.setdiff1d(node.guesses, node.answers),
                                      size=int((self._n - len(node.answers)) / guess_coarsening_factor),
                                      replace=False))))
                score = score[np.where(np.in1d(node.guesses, guesses))[0]]
            else:
                guesses = node.guesses

            # Find best next guess = argmin(max bucket size).
            answer_index = np.arange(len(node.answers), dtype=int)
            bucket_sizes = bucket_size_functor(score)
            feasible = np.logical_not(np.in1d(np.arange(len(bucket_sizes)), answer_index))
            bucket_size, _, guess_index_opt = min((b, k_feasible, k)
                                                  for k, (k_feasible, b) in enumerate(zip(feasible, bucket_sizes)))
            guess_opt = guesses[guess_index_opt]

            # TODO: use depth-first traversal and only keep leaf depth (=#guesses) and perhaps its solution path
            # to reduce memory of storing entire tree.
            info = _bucket_iterable(answer_index, score[guess_index_opt])
            node.key = (guess_opt, self._solver_data.answers[guess_opt], bucket_size)
            node.children = [
                Node(None, guesses, node.answers[bucket], score[:, bucket], [], hint=hint, parent=node)
                for hint, bucket in info.items()
            ]


def max_bucket_sizes(score) -> np.ndarray:
    if score.shape[1] <= 300:
        return np.array([collections.Counter(row).most_common(1)[0][1] for row in score])
    else:
        return scipy.stats.mode(score, axis=1, keepdims=False)[1]


def min_biased_multilevel_sampling(
        score, quantity, min_sample_size: int = 2000, sample_factor: float = 1.7,
        debug: bool = False):
    """Quantity is a functor that depends on the set of values of a row (i.e., its values is independent of column
    ordering."""
    # Ensure linear complexity.
    assert sample_factor < 2
    m, n = score.shape
    if n <= min_sample_size:
        return quantity(score)
    # 'rows' is the active set of rows. As we increase the sample, result[rows] becomes more accurate; we only
    # need a high accuracy in small result values, so we keep halving 'rows' in the loop below while increasing
    # the sample size. [log2(m)] + 1 repeats at most.
    rows, cols, result = np.arange(m, dtype=int), np.arange(n, dtype=int), np.zeros((m, ))
    sample_size = min_sample_size
    while rows.size:
        if debug:
            print("#rows", len(rows), "x sample_size", sample_size, "=", len(rows) * sample_size)
        # Select a random sample of the rows of size 'sample_size'.
        if sample_size > len(cols):
            raise ValueError("sample_size {} > #cols {}".format(sample_size, len(cols)))
        col_sample = np.random.choice(cols, size=sample_size, replace=False)
        # Calculate max bucket sizes for all elements in 'rows' using the current sample (overriding some old values).
        quantities = quantity(score[rows][:, col_sample])
        result[rows] = quantities
        if sample_size == n:
            break
        # Restrict rows to the smaller half of quantity value.
        #  If the quantity distribution is sufficiently spread so that the median is not repeated many times, the
        # loop halves len(rows), so there ~ log2(m) repeats. But what happens when the median is repeated?
        # Truncate the list 'i' to half the size of rows, filling it with values < median and some values = median.
        q_median = np.median(quantities)
        i = np.where(quantities < q_median)[0]
        i = np.concatenate((i, np.where(quantities == q_median)[0][:len(rows) // 2 - len(i)]))
        rows = rows[i]
        sample_size = min(int(sample_factor * sample_size), n)
    return result


class TreeDepthCalculator:
    def __init__(self, node: Node):
        self.depth = {}
        self._current_depth = 0
        self._calculate_tree_depth(node)

    def _calculate_tree_depth(self, node: Node):
        self._process(node)
        self._current_depth += 1
        for child in node.children:
            self._calculate_tree_depth(child)
        self._current_depth -= 1

    def _process(self, node):
        self.depth[node] = self._current_depth


def pre_traversal(
        node: Node,
        process_node,
        depth: int = 0,
        debug: bool = False):
    process_node(node)
    if debug: # and depth <= 1:
        print("\t" * depth, node)
    for child in node.children:
        pre_traversal(child, process_node, depth=depth + 1, debug=debug)


def _bucket_iterable(answers: Iterable, score: Iterable) -> Dict:
    s = collections.defaultdict(list)
    for a, v in zip(answers, score):
        s[v].append(a)
    return s

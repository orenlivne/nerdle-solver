"""Nerdle Game tree builder and analysis of distribution of #guesses over all answers."""
import collections
import nerdle
import numpy as np


class Node:
    def __init__(self, key, answers, score, children, hint=None, parent=None):
        self.key = key
        self.answers = answers
        self.score = score
        self.hint = hint
        self.children = children
        self.parent = parent

    def __repr__(self):
        return "Node[key={}, answers={}, score={}, children={}]".format(
            self.key, len(self.answers), self.score.shape, len(self.children))

    def __str__(self):
        return repr(self)

    def answer_key(self, key):
        """Returns the root-level index of answer key(s) (intt or np.ndarray) of this node."""
        node = self
        while node.parent:
            node = node.parent
            key = node.answers[key]
        return key


class GameTreeBuilder:
    def __init__(self, solver_data):
        self._score_db = solver_data.score_db.copy()
        self._solver = nerdle.NerdleSolver(solver_data)
        self._all_keys = solver_data.all_keys

    def build(self, debug: bool = False) -> Node:
        root = Node(
            None,
            np.arange(
                self._score_db.shape[0],
                dtype=int),
            self._score_db,
            [])
        pre_traversal(root, self._process_node, debug=debug)
        return root

    def _process_node(self, node):
        if len(node.answers) == 1:
            if not self._solver.is_correct(
                    node.score[node.answer_key(node.answers[0]), 0]):
                raise ValueError("Failed to solve game")
        else:
            answers = np.arange(len(node.answers))
            score = node.score
            info = [_score_dict(answers, score, k) for k in self._all_keys]
            k_opt = min((max(map(len, info_k.values())), k not in answers, k)
                        for k, info_k in zip(self._all_keys, info))[-1]
            node.key = k_opt
            node.children = [Node(None, np.array(bucket), score[:, bucket], [
            ], hint=hint, parent=node) for hint, bucket in info[k_opt].items()]


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
    if debug:
        print("\t" * depth, node)
    for child in node.children:
        pre_traversal(child, process_node, depth=depth + 1, debug=debug)


def _score_dict(answers, score, k):
    s = collections.defaultdict(list)
    for a, v in zip(answers, score[k]):
        s[v].append(a)
    return s

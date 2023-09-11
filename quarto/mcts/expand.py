from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable
import random

from quarto.mcts.node import Node, get_child
from quarto.representation.logic import State, Move, get_moves


def expand(parent: Node) -> Iterable[Node]:
    if parent.game_over:
        return [parent]
    moves = get_moves(parent.state)
    unexplored = set(moves).difference(parent.children)
    if len(unexplored) == 1:
        parent.fully_expanded = True
    exploring = random.choice(list(unexplored))
    return [get_child(parent, exploring)]


GetMovesF = Callable[[State], Iterable[Move]]


@dataclass(slots=True, frozen=True)
class Expand:
    k: int = 1
    get_moves: GetMovesF = get_moves

    def __call__(self, parent: Node) -> Iterable[Node]:
        if parent.game_over:
            return [parent]
        moves = self.get_moves(parent.state)
        unexplored = [move for move in moves if move not in parent.children]
        k = self.k
        if (n := len(unexplored)) <= k:
            parent.fully_expanded = True
            k = n
        exploring = random.sample(unexplored, k)
        return [get_child(parent, move) for move in exploring]

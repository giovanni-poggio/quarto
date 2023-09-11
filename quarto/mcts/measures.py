from dataclasses import dataclass
import math

from quarto.mcts.node import Node


@dataclass(slots=True)
class UCT:
    exploration_rate: float = math.sqrt(2)

    def __call__(self, child: Node) -> float:
        player = child.parent.plying  # type: ignore
        exploitation = child.payoffs[player] / child.visits
        exploration = self.exploration_rate * math.sqrt(math.log(child.parent.visits) / child.visits)  # type: ignore
        return exploitation + exploration

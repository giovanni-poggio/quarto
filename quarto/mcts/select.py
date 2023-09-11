from dataclasses import dataclass, field
from typing import Callable

from quarto.mcts.node import Node
from quarto.mcts.measures import UCT


MeasureF = Callable[[Node], float] 


@dataclass(slots=True)
class Select:
     measure: MeasureF = field(default_factory=UCT)

     def __call__(self, node: Node) -> Node:
        while node.fully_expanded:
            node = max(node.children.values(), key=self.measure)
        return node

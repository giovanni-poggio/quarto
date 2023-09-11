from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Callable
import concurrent.futures as cf
from quarto.mcts.dummy_executor import DummyExecutor
from quarto.mcts.expand import expand

from quarto.mcts.node import Node, get_root, back_propagate
from quarto.mcts.simulate import Simulator
from quarto.mcts.stoppers import MaxIters
from quarto.mcts.select import Select
from quarto.representation.logic import State
from quarto.representation.payoffs import Payoffs


StopF = Callable[[int], bool]
TraverseF = Callable[[Node], Node]
ExpandF = Callable[[Node], Iterable[Node]]
SimulateF = Callable[[Node], Payoffs]


@dataclass(slots=True)
class MCTS:
    stop: StopF = field(default_factory=lambda: MaxIters(10_000))
    select: TraverseF = field(default_factory=Select)
    expand: ExpandF = expand
    simulate: SimulateF = field(default_factory=Simulator)
    executor: cf.Executor = field(default_factory=DummyExecutor)

    def search(self, state: State, __root: Node | None = None) -> Node:
        root = get_root(state) if __root is None else __root
        if root.game_over:
            return root
        self._loop(root)
        return root
    
    def _loop(self, root: Node):
        iteration = 0
        while not self.stop(iteration):
            self._iterate(root)
            iteration += 1

    def _iterate(self, root: Node):
        leaf = self.select(root)
        expanded = self.expand(leaf)
        results = self.executor.map(self.simulate, expanded)
        for node, payoffs in zip(expanded, results):
            back_propagate(node, payoffs)

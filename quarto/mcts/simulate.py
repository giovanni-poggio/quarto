from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Callable
import concurrent.futures as cf

from quarto.mcts.cumdict import cumdict, normalize
from quarto.mcts.dummy_executor import DummyExecutor
from quarto.mcts.node import Node
from quarto.mcts.policies import random_policy
from quarto.representation.logic import State, is_over, get_payoffs, play, get_moves
from quarto.representation.move import Move
from quarto.representation.payoffs import Payoffs


StopSimF = Callable[[State], bool]
GetMovesF = Callable[[State], Iterable[Move]]
PolicyF = Callable[[Iterable[Move]], Move]
GetPayoffsF = Callable[[State], Payoffs]
SimulateF = Callable[[Node], Payoffs]


@dataclass(slots=True)
class Simulator:
    stop: StopSimF = is_over
    get_moves: GetMovesF = get_moves
    policy: PolicyF = random_policy
    get_payoffs: GetPayoffsF = get_payoffs

    def __call__(self, node: Node) -> Payoffs:
        state = node.state
        while not self.stop(state):
            moves = self.get_moves(state)
            move = self.policy(moves)
            state = play(state, move)
        return self.get_payoffs(state)


@dataclass(slots=True)
class BatchSimulator:
    n_sims: int = 32
    simulate: SimulateF = field(default_factory=Simulator)
    executor: cf.Executor = field(default_factory=DummyExecutor)

    def __call__(self, node: Node) -> Payoffs:
        totals = cumdict()
        for result in self.executor.map(self.simulate, (node for _ in range(self.n_sims))):
            totals.update(result)
        return normalize(totals, self.n_sims)

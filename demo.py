from dataclasses import dataclass
import logging
from quarto.mcts.search import MCTS
from quarto.mcts.select import Select
from quarto.mcts.stoppers import MaxTime
from quarto.mcts.simulate import BatchSimulator, Simulator
from quarto.mcts.expand import Expand
from quarto.mcts.measures import UCT
from quarto.mcts.node import Node
from quarto.mtdf.mtdf import iterative_deepening, lookup
from quarto.representation.constants import ATTRIBUTES
from quarto.representation.logic import PIECE, State, get_payoffs, get_winner, is_over, get_ply, state_to_string, play
from quarto.representation.move import Move
from quarto.representation.player import Player, get_plying
from quarto.mcts.cumdict import cumdict


@dataclass
class MCTSPlayer:
    
    def __init__(self, max_time: float = 2., expand_k: int = 1, n_sims: int = 1, exploration: float = 1.) -> None:
        stop = MaxTime(max_time)
        select = Select(UCT(exploration))
        expand = Expand(expand_k)
        simulate = BatchSimulator(n_sims) if n_sims > 1 else Simulator()
        self.solver = MCTS(stop, select, expand, simulate)
        self.root = None

    def goto(self, state: State) -> Node:
        assert self.root is not None
        node = self.root
        for move in state.keys():
            node = node.children[move]
        return node

    def __call__(self, state: State) -> Move:
        # if self.root is None:
        #     node = self.root = get_root(state)
        # else:
        #     node = self.goto(state)
        # self.solver.search(state, node)
        node = self.solver.search(state)
        values = {}
        for move, child in node.children.items():
            values[move] = child.payoffs[node.plying] / child.visits
        best_move = max(values, key=values.get)
        ev = node.payoffs[Player.PLAYER1] / node.visits
        logging.info(f"MCTS {node.visits=:,}\t{ev=:+.3f}\t{best_move=}")
        return best_move
    

@dataclass
class MTDFPlayer:
    max_time: float = 2.

    def __call__(self, state: State) -> Move:
        iterative_deepening(state, 32, max_time=self.max_time)
        entry = lookup(state)
        logging.info(f"MTDF {entry=}")
        assert entry.best_move is not None
        return entry.best_move
    

def main(n_games: int = 20):
    logging.root.level = logging.INFO
    mcts = MCTSPlayer()
    mtdf = MTDFPlayer()
    players = {Player.PLAYER1: mtdf, Player.PLAYER2: mcts}
    cum_payoffs = cumdict(int)
    solvers_wins = cumdict(int)
    players_wins = cumdict(int)
    for game in range(n_games):
        print(f"{game=}")
        state = State()
        print(state_to_string(state))
        while not is_over(state):
            plying = get_plying(get_ply(state))
            player = players[plying]
            move = player(state)
            state = play(state, move)
            print(state_to_string(state))
        payoffs = get_payoffs(state)
        winner = get_winner(state)
        players_wins[winner] = 1
        if players[Player.PLAYER1] is mcts:
            payoffs = {'mcts': payoffs[Player.PLAYER1], 'mtdf': payoffs[Player.PLAYER2]}
            winner = 'mcts' if winner == Player.PLAYER1 else ('mtdf' if winner == Player.PLAYER2 else None)
        else:
            payoffs = {'mtdf': payoffs[Player.PLAYER1], 'mcts': payoffs[Player.PLAYER2]}
            winner = 'mtdf' if winner == Player.PLAYER1 else ('mcts' if winner == Player.PLAYER2 else None)
        cum_payoffs.update(payoffs)
        solvers_wins[winner] = 1
        print(f"{payoffs=}")
        print(f"{cum_payoffs=}")
        print(f"{solvers_wins=}")
        players = {Player.PLAYER1: players[Player.PLAYER2],
                   Player.PLAYER2: players[Player.PLAYER1]}
    print(f"{cum_payoffs=}")


if __name__ == "__main__":
    main()
        
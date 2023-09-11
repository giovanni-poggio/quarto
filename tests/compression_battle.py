from collections import defaultdict
from itertools import combinations, combinations_with_replacement
import logging
from pprint import pprint
import time
from quarto.representation.player import Player, get_plying
from quarto.solver.cumdict import cumdict
from quarto.solver.node import Node
from quarto.solver.search import MCTS
from quarto.solver.expand import Expand
from quarto.solver.simulate import Simulator

from quarto.compression.pieces import get_available as get_unique_available
from quarto.compression.squares import get_free as get_unique_free

from quarto.representation.logic import (State, Move, get_available, get_free, get_payoffs, get_phase,
                                         Phase, get_winner, is_over, get_ply, play, state_to_string)
from quarto.solver.stoppers import MaxIters


def get_unique_square_moves(state: State) -> frozenset[Move]:
    if get_phase(state) == Phase.PUT:
        return get_unique_free(frozenset(state.keys()))
    return get_available(frozenset(state.values()))


def get_unique_pieces_moves(state: State) -> frozenset[Move]:
    if get_phase(state) == Phase.PUT:
        return get_free(frozenset(state.keys()))
    return get_unique_available(frozenset(state.values()))


def get_unique_moves(state: State) -> frozenset[Move]:
    if get_phase(state) == Phase.PUT:
        return get_unique_free(frozenset(state.keys()))
    return get_unique_available(frozenset(state.values()))


def get_move(node: Node) -> Move:
    values = {}
    player = node.plying
    for move, child in node.children.items():
        values[move] = child.payoffs[player] / child.visits
    move = max(values, key=values.get)
    logging.debug(f"{move=}\t{values[move]=:.3f}\t{values=}")
    return move


def main(n_games: int = 8, max_iters: int = 200):
    asap = MCTS(MaxIters(max_iters))
    usap = MCTS(
        MaxIters(max_iters), expand=Expand(get_moves=get_unique_square_moves), 
        simulate=Simulator(get_moves=get_unique_square_moves)
    )
    asup = MCTS(
        MaxIters(max_iters), expand=Expand(get_moves=get_unique_pieces_moves), 
        simulate=Simulator(get_moves=get_unique_pieces_moves)
    )
    usup = MCTS(
        MaxIters(max_iters), expand=Expand(get_moves=get_unique_moves), 
        simulate=Simulator(get_moves=get_unique_moves)
    )
    solvers = {
        'asap': asap,
        'asup': asup,
        'usap': usap,
        'usup': usup
    }
    all_payoffs = dict()
    for players in combinations_with_replacement(solvers, 2):
        cum_payoffs = cumdict()
        for game in range(n_games):
            state = State()
            start = time.perf_counter()
            while not is_over(state):
                logging.debug(state_to_string(state))
                plying = get_plying(get_ply(state))
                logging.debug(f"{players[plying]=}")
                plying = solvers[players[plying]]
                root = plying.search(state)
                move = get_move(root)
                state = play(state, move)
            elapsed = time.perf_counter() - start
            payoffs = get_payoffs(state)
            p1, p2 = players
            if p1 == p2:
                p1 += '1'
                p2 += '2'
            payoffs = {p1: payoffs[Player.PLAYER1], p2: payoffs[Player.PLAYER2]}
            cum_payoffs.update(payoffs)
            logging.info(f"{players=}\t{game=}\t{elapsed=:.3f} s")
            logging.info(f"{payoffs=}")
            logging.info(f"{cum_payoffs=}")
            players = players[::-1]
        all_payoffs[players] = cum_payoffs
    pprint(all_payoffs)

            

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
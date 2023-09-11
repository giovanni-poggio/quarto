import cProfile
from collections import Counter
from functools import partial
import logging
import math
import operator
import pstats
import random
import timeit

from tqdm import tqdm
from quarto.compression.squares import get_free
from quarto.compression.pieces import get_available

from quarto.representation.logic import State, get_phase, play, is_over, get_winner, state_to_string, get_ply
from quarto.representation.move import Move
from quarto.representation.phase import Phase
from quarto.representation.player import Player
from quarto.solver.cumdict import cumdict


def get_moves(state: State) -> frozenset[Move]:
    if get_phase(state) == Phase.PUT:
        return get_free(frozenset(state.keys()))
    return get_available(frozenset(state.values()))


def random_game(state: State, inplace: bool = True) -> State:
    while not is_over(state):
        try:
            moves = get_moves(state)
            move = random.choice(list(moves))
            state = play(state, move, inplace)
        except IndexError:
            logging.critical(state_to_string(state))
            logging.critical(moves)
            get_moves(state)
            raise IndexError
    return state


def debug_random_game(state: State):
    print("=" * 36)
    print(state_to_string(state))
    while not is_over(state):
        moves = get_moves(state)
        print("-" * 36)
        print(f"{sorted(moves)=}") 
        print("-" * 36)
        move = random.choice(list(moves))
        print(f"{move=}") 
        print("-" * 36)
        state = play(state, move)
        print(state_to_string(state))
        # input("continue... ")
    winner = get_winner(state)
    winner = 'PLAYER1' if winner == Player.PLAYER1 else ('PLAYER2' if winner == Player.PLAYER2 else None)
    print(f"{winner=}")


def time_random_game(inplace: bool = True, repeat: int = 100, number: int = 100):
    total = repeat * number
    tq = tqdm(total=total, desc=f"TIMING RANDOM GAME: {inplace=}, {repeat=:,}, {number=:,}, {total=:,}")
    deltas = timeit.repeat("random_game(State(), inplace)", setup=f"tq.update({number})",
                           repeat=repeat, number=number, globals=globals() | locals())
    tq.close()
    rate = total / sum(deltas)
    logging.info(f"{rate=:.3f} it/s")


def profile_random_game(inplace: bool, n_games: int = 10_000):    
    tq = tqdm(range(n_games), desc=f"PROFILING RANDOM GAME: {inplace=}, {n_games=:,}")
    with cProfile.Profile() as profile:
        for _ in tq:
            state = State()
            random_game(state, inplace)
    path = __file__.replace(".py", f"{'_ip' if inplace else '_oop'}.prof")
    stats = pstats.Stats(profile)
    stats.dump_stats(path)
    logging.info(f"profile @ {path}")


def stats(n_games: int = 10_000):
    tq = tqdm(range(n_games), desc=f"PRODUCING STATISTICS: {n_games=:,d}")

    winners, plies = [], cumdict(int)
    for _ in tq:
        end_state = random_game(State())
        winner = get_winner(end_state)
        plies.update({get_ply(end_state): 1})
        winners.append(winner)

    ties = sum(1 for winner in winners if winner is None)
    total = sum((1 if winner == Player.PLAYER1 else (-1 if winner == Player.PLAYER2 else 0)) for winner in winners)
    including_ties = total / n_games
    excluding_ties = total / (n_games - ties)
    p_ties = ties / n_games * 100
    plies = {key: value for key, value in sorted(plies.items())}

    logging.info(f"{n_games=:,d}")
    logging.info(f"EV={including_ties:+.3f}\t(including ties)")
    logging.info(f"EV={excluding_ties:+.3f}\t(not including ties)")
    logging.info(f"P[tie]={p_ties:.2f} %")
    logging.info(f"{plies=}")


def main():
    logging.basicConfig(level=logging.INFO)
    debug_random_game(State())
    # time_random_game(inplace=True)
    time_random_game(inplace=False)
    # profile_random_game(inplace=True)
    profile_random_game(inplace=False)
    stats()
    

if __name__ == "__main__":
    main()
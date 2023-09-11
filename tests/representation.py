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

from quarto.representation.logic import State, get_moves, play, is_over, get_winner, state_to_string, get_ply
from quarto.representation.player import Player
from quarto.solver.cumdict import cumdict


def random_game(state: State, inplace: bool = True) -> State:
    while not is_over(state):
        move = random.choice(list(get_moves(state)))
        state = play(state, move, inplace)
    return state


def debug_random_game(state: State):
    print("=" * 36)
    print(state_to_string(state))
    while not is_over(state):
        move = random.choice(list(get_moves(state)))
        print("-" * 36)
        print(f"move: {move}") 
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
    # time_random_game(inplace=True)
    time_random_game(inplace=False)
    # profile_random_game(inplace=True)
    profile_random_game(inplace=False)
    stats()
    

if __name__ == "__main__":
    main()
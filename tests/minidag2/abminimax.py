from concurrent.futures import ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import datetime
from enum import IntFlag, auto
import logging
import multiprocessing
import time

from quarto.representation.constants import ATTRIBUTES, SIDE
from quarto.representation.phase import Phase
from quarto.representation.logic import LAST_PLY, State, get_payoffs, get_ply, get_winner, is_over, state_to_string
from quarto.representation.player import Player, get_plying
from tests.minidag2.compression import get_moves, play


@dataclass(slots=True)
class Entry:
    lowerbound: float = float('-inf')
    upperbound: float = float('inf')
    valid: bool = False
    depth: int | float = 0


TABLE = dict[str, Entry]()
ITERS = 0
FIRST_ENTERED = float('-inf')
FIRST_EXITED = float('inf')
EXITING = False
START: datetime | None = None


def lookup(state: State) -> Entry:
    return TABLE.setdefault(state_to_string(state), Entry())


def minimax(state: State, depth: int | float, alpha: float = float('-inf'),
            beta: float = float('inf'), fail_soft: bool = True) -> int:
    global ITERS, FIRST_ENTERED, FIRST_EXITED, EXITING, START
    ITERS += 1
    EXITING = depth == 0
    if START is None:
        START = datetime.now()
    human_depth = 2*LAST_PLY - depth
    if human_depth > FIRST_ENTERED:
        FIRST_ENTERED = human_depth
        logging.debug(f"{FIRST_ENTERED=}\t{ITERS=:,}\t{len(TABLE)=}")
                     
    plying = get_plying(get_ply(state))

    if (entry := lookup(state)).valid and entry.depth >= depth:
        if entry.lowerbound >= beta:
            return entry.lowerbound
        if entry.upperbound <= alpha:
            return entry.upperbound
        alpha = max(alpha, entry.lowerbound)
        beta = min(beta, entry.upperbound)
    if (game_over := is_over(state)) or depth == 0:
        value = get_payoffs(state)[Player.PLAYER1]
        depth = depth if not game_over else float('inf')
    elif plying == Player.PLAYER1:
        value = float('-inf')
        a = alpha
        for move in get_moves(state):
            child = play(state, move)
            value = max(value, minimax(child, depth-1, a, beta, fail_soft))
            if not fail_soft and value > beta:
                break
            a = max(a, value)
            if fail_soft and value >= beta:
                break
    else:
        value = float('inf')
        b = beta
        for move in get_moves(state):
            child = play(state, move)
            value = min(value, minimax(child, depth-1, alpha, b, fail_soft))
            if not fail_soft and value < alpha:
                break
            b = min(b, value)
            if fail_soft and value <= alpha:
                break

    if value <= alpha:
        entry.upperbound = value
    if alpha < value < beta:
        entry.lowerbound = value
        entry.upperbound = value
        depth = float('inf')
    if value >= beta:
        entry.lowerbound = value

    if entry.lowerbound > entry.upperbound:
        print()

    entry.depth = depth
    entry.valid = True

    if EXITING and human_depth < FIRST_EXITED:
        elapsed = (datetime.now() - START).total_seconds()
        itps = ITERS / (elapsed + 1e-6)
        FIRST_EXITED = human_depth
        logging.debug(f"{FIRST_EXITED=}\t{ITERS=:,}\t{elapsed!s}\t{itps:.3f} it/s\t{len(TABLE)=:,}")

    return value


def MTDF(root: State, first_guess: int, depth: int, fail_soft: bool = True) -> int:
    value = first_guess
    upperbound = float('inf')
    lowerbound = float('-inf')
    while lowerbound < upperbound:
        beta = value + 1 if value == lowerbound else value
        value = minimax(root, depth, beta-1, beta, fail_soft)
        if value < beta:
            upperbound = value
        else:
            lowerbound = value
    return value


def iterative_deepening(root: State, max_depth: int, fail_soft: bool = True) -> int:
    firstguess = 0
    for depth in range(max_depth+1):
        reset_entered()
        filter_table()
        logging.info(f"{depth=}")
        start = time.perf_counter()
        value = MTDF(root, firstguess, depth, fail_soft)
        elapsed = time.perf_counter() - start
        logging.info(f"{value=}\t{elapsed=:.3f}\t{lookup(root)}")
        firstguess = value
    return firstguess

def reset_entered():
    global FIRST_ENTERED, FIRST_EXITED, EXITING
    FIRST_ENTERED = float('-inf')
    FIRST_EXITED = float('inf')
    EXITING = False


def filter_table():
    global TABLE
    before = len(TABLE)
    TABLE = {key: entry for key, entry in TABLE.items() if entry.depth == float('inf')}
    after = len(TABLE)
    logging.info(f"{before=:,}\t{after=:,}")


def parallel():
    state0 = State()

    state1 = play(state0, f"{0:0{ATTRIBUTES}b}")

    state11 = play(state1, (0, 0))
    state12 = play(state1, (0, 1))
    state13 = play(state1, (1, 1))

    states = [
        state11, state12, state13
    ]

    global TABLE
    manager = multiprocessing.Manager()
    TABLE = manager.dict()

    with ProcessPoolExecutor() as pool:
        futures = [pool.submit(minimax, state, 16) for state in states]

    wait(futures)

    for state in states:
        state = state_to_string(state)
        print(state)
        print(TABLE[state])


def main():
    logging.root.level = logging.INFO
    start = time.perf_counter()
    # minimax(State(), 2*LAST_PLY, .5, 1.5)
    # MTDF(State(), 1, 2*LAST_PLY)
    iterative_deepening(State(), 2*LAST_PLY, fail_soft=False)
    elapsed = time.perf_counter() - start
    logging.info(f"{ITERS=:,d}\t{elapsed=:.3f} s")
    entry = lookup(State())
    logging.info(f"{entry=}")
    n_entries = len(TABLE)
    logging.info(f"{n_entries=}")


if  __name__ == "__main__":
    main()
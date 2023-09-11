from concurrent.futures import ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import datetime
from itertools import product
import logging
import multiprocessing
import time

from quarto.mindag.board import SORTED_TRANSFORMS, board_to_string, map_square
from quarto.mindag.pieces import SORTED_MAPPINGS, map_piece
from quarto.representation.constants import ATTRIBUTES
from quarto.representation.move import Move
from quarto.representation.logic import LAST_PLY, State, get_payoffs, get_ply, is_over, state_to_string, play, get_moves
from quarto.representation.player import Player, get_plying


@dataclass(slots=True)
class Entry:
    lower: float = float('-inf')
    upper: float = float('inf')
    best_move: Move | None = None
    depth: int | float = 0
    valid: bool = False


TABLE = dict[str, Entry]()
ITERS = 0
FIRST_ENTERED = float('-inf')
FIRST_EXITED = float('inf')
EXITING = False
START: datetime | None = None


def lookup(state: State) -> Entry:
    # if (entry := TABLE.get(state_to_string(state), Entry())).valid:
    #     return entry
    # for transform in SORTED_TRANSFORMS:
    #     tmp = {map_square(square, transform): piece for square, piece in state.items()}
    #     TABLE[state_to_string(tmp)] = entry
    return TABLE.setdefault(state_to_string(state), Entry())


# def lookup(state: State) -> Entry:
#     # for mapping, transform in product(SORTED_MAPPINGS, SORTED_TRANSFORMS):
#     #     tmp = {map_square(square, transform): map_piece(piece, mapping)
#     #            for square, piece in state.items()}
#     #     if (entry := TABLE.get(state_to_string(tmp))) is not None:
#     #         return entry
#     # return TABLE.setdefault(state_to_string(state), Entry())


def log_entered(depth: int):
    global ITERS, FIRST_ENTERED, EXITING, START
    ITERS += 1
    EXITING = depth == 0
    if START is None:
        START = datetime.now()
    human_depth = 2*LAST_PLY - depth
    if human_depth > FIRST_ENTERED:
        elapsed = (datetime.now() - START).total_seconds()
        itps = ITERS / (elapsed + 1e-6)
        FIRST_ENTERED = human_depth
        logging.debug(f"{FIRST_ENTERED=}\t{ITERS=:,}\t{len(TABLE)=}")



def log_exited(depth: int):
    global ITERS, FIRST_EXITED, EXITING, START
    human_depth = 2*LAST_PLY - depth
    if EXITING and human_depth < FIRST_EXITED:
        elapsed = (datetime.now() - START).total_seconds()
        itps = ITERS / (elapsed + 1e-6)
        FIRST_EXITED = human_depth
        logging.debug(f"{FIRST_EXITED=}\t{ITERS=:,}\t{elapsed!s}\t{itps:.3f} it/s\t{len(TABLE)=:,}")


def alphabeta(state: State, depth: int, alpha: float = float('-inf'),
            beta: float = float('inf'), fail_soft: bool = True) -> tuple[int, int]:
    log_entered(depth)
                     
    plying = get_plying(get_ply(state))

    if (entry := lookup(state)).valid and entry.depth >= depth:
        if entry.lower >= beta:
            return entry.lower, entry.depth
        if entry.upper <= alpha:
            return entry.upper, entry.depth
        alpha = max(alpha, entry.lower)
        beta = min(beta, entry.upper)

    if (game_over := is_over(state)) or depth <= 0:
        best_value = get_payoffs(state)[Player.PLAYER1]
        best_move = None
        min_depth = depth if not game_over else float('inf')
    elif plying == Player.PLAYER1:
        best_value, best_move, min_depth = float('-inf'), None, float('inf')
        a = alpha
        for move in get_moves(state):
            child = play(state, move)
            value, plies = alphabeta(child, depth-1, a, beta, fail_soft)
            if value > best_value:
                best_value = value
                best_move = move
            min_depth = min(plies+1, min_depth)
            if not fail_soft and best_value > beta:
                break
            a = max(a, best_value)
            if fail_soft and best_value >= beta:
                break
    else:
        best_value, best_move, min_depth = float('inf'), None, float('inf')
        b = beta
        for move in get_moves(state):
            child = play(state, move)
            value, plies = alphabeta(child, depth-1, alpha, b, fail_soft)
            if value < best_value:
                best_value = value
                best_move = move
            min_depth = min(plies+1, min_depth)
            if not fail_soft and best_value < alpha:
                break
            b = min(b, best_value)
            if fail_soft and best_value <= alpha:
                break

    if best_value <= alpha:
        entry.upper = best_value
    if alpha < best_value < beta:
        entry.lower = best_value
        entry.upper = best_value
    if best_value >= beta:
        entry.lower = best_value

    if entry.lower > entry.upper:
        logging.debug(f"{entry=}")

    entry.best_move = best_move
    entry.depth = min_depth
    entry.valid = True

    log_exited(depth)

    return best_value, min_depth


def MTDF(root: State, first_guess: int, depth: int, fail_soft: bool = True) -> int:
    value = first_guess
    upperbound = float('inf')
    lowerbound = float('-inf')
    while lowerbound < upperbound:
        beta = value + 1 if value == lowerbound else value
        value, _ = alphabeta(root, depth, beta-1, beta, fail_soft)
        if value < beta:
            upperbound = value
        else:
            lowerbound = value
    return value


def iterative_deepening(root: State, max_depth: int = 32, fail_soft: bool = True, max_time: float = float('inf')) -> int:
    firstguess = 0
    starting = time.perf_counter()
    for depth in range(2, max_depth+1, 2):
        reset_depth_log()
        filter_table()
        logging.debug(f"{depth=}")
        start = time.perf_counter()
        value = MTDF(root, firstguess, depth, fail_soft)
        elapsed = time.perf_counter() - start
        logging.debug(f"{value=}\t{elapsed=:.3f}\t{lookup(root)}")
        firstguess = value
        if abs(value) > 0:
            break
        if time.perf_counter() - starting > max_time:
            break
    return firstguess

def reset_depth_log():
    global FIRST_ENTERED, FIRST_EXITED, EXITING
    FIRST_ENTERED = float('-inf')
    FIRST_EXITED = float('inf')
    EXITING = False


def filter_table():
    global TABLE
    before = len(TABLE)
    TABLE = {key: entry for key, entry in TABLE.items() if entry.depth == float('inf')}
    after = len(TABLE)
    logging.debug(f"{before=:,}\t{after=:,}")


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
        futures = [pool.submit(iterative_deepening, state, 2*LAST_PLY) for state in states]

    wait(futures)

    for state in states:
        state = state_to_string(state)
        print(state)
        print(TABLE[state])


def main():
    logging.basicConfig(level=logging.DEBUG)
    logging.root.level = logging.DEBUG
    start = time.perf_counter()
    alphabeta(State(), 2*LAST_PLY, -.5, .5)
    # MTDF(State(), 1, 2*LAST_PLY)
    # iterative_deepening(State(), 2*LAST_PLY)
    elapsed = time.perf_counter() - start
    logging.info(f"{ITERS=:,d}\t{elapsed=:.3f} s")
    entry = lookup(State())
    logging.info(f"{entry=}")
    n_entries = len(TABLE)
    logging.info(f"{n_entries=}")


if  __name__ == "__main__":
    main()
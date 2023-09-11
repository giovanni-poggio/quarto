from concurrent.futures import ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import datetime
from enum import IntFlag, auto
import logging
import multiprocessing
import time
from quarto.representation.constants import ATTRIBUTES, SIDE
from quarto.representation.phase import Phase
logging.basicConfig(level=logging.INFO)
from quarto.representation.logic import LAST_PLY, State, get_moves, get_payoffs, get_phase, get_ply, is_over, state_to_string
from quarto.representation.player import Player
from tests.minidag.compression import play


class Flag(IntFlag):
    INVALID = auto()
    LOWERBOUND = auto()
    UPPERBOUND = auto()
    EXACT = auto()


@dataclass(slots=True)
class Entry:
    value: float | None = None
    flag: Flag = Flag.INVALID
    depth: int = 0


TABLE = dict[str, Entry]()
ITERS = 0
FIRST_ENTERED = float('inf')
FIRST_EXITED = float('-inf')
START: datetime | None = None


def lookup(state: State) -> Entry:
    return TABLE.setdefault(state_to_string(state), Entry())


def negamax(state: State, depth: int, alpha: float = float('-inf'), beta: float = float('inf'), color: int = 1) -> float:
    global ITERS, FIRST_ENTERED, FIRST_EXITED, START

    if depth < FIRST_ENTERED:
        FIRST_ENTERED = depth
        logging.info(f"{FIRST_ENTERED=}\t{ITERS=:,}\t{len(TABLE)=}")

    alpha0 = alpha

    if START is None:
        START = datetime.now()

    # (* Transposition Table Lookup; node is the lookup key for entry *)
    entry = lookup(state)
    if entry.flag != Flag.INVALID and entry.depth >= depth:
        assert entry.value is not None
        if entry.flag == Flag.EXACT:
            return entry.value
        elif entry.flag == Flag.LOWERBOUND:
            alpha = max(alpha, entry.value)
        elif entry.flag == Flag.UPPERBOUND:
            beta = min(beta, entry.value)

        if alpha >= beta:
            return entry.value
        
    ITERS += 1

    if depth == 0 or is_over(state):
        return color * get_payoffs(state)[Player.PLAYER1]

    # moves := orderMoves(moves)
    value = float('-inf')
    value = float('-inf')
    if get_phase(state) == Phase.GIVE:
        for move in get_moves(state):
            child = play(state, move)
            value = max(value, -negamax(child, depth-1, -beta, -alpha, -color))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        for move in get_moves(state):
            child = play(state, move)
            value = max(value, negamax(child, depth-1, alpha, beta, color))
            alpha = max(alpha, value)
            if alpha >= beta:
                break

    # if get_ply(state) == 0:
    #     for piece in get_moves(state):
    #         child = play(state, piece)
    #         value = max(value, -negamax(child, depth-1, -beta, -alpha, -color))
    #         alpha = max(alpha, value)
    #         if alpha >= beta:
    #             break
    # else:
    #     for square in get_moves(state):
    #         tmp = play(state, square)
    #         for piece in get_moves(tmp):
    #             child = play(tmp, piece)
    #             value = max(value, -negamax(child, depth-1, -beta, -alpha, -color))
    #             alpha = max(alpha, value)
    #             if alpha >= beta:
    #                 break
    
    # (* Transposition Table Store; node is the lookup key for entry *)
    entry.value = value
    entry.depth = depth
    if value <= alpha0:
        entry.flag = Flag.UPPERBOUND
    elif value >= beta:
        entry.flag = Flag.LOWERBOUND
    else:
        entry.flag = Flag.EXACT
    # entry.is_valid = true
    # transpositionTableStore(node, entry)

    if depth > FIRST_EXITED:
        elapsed = (datetime.now() - START).total_seconds()
        itps = ITERS / (elapsed + 1e-6)
        FIRST_EXITED = depth
        logging.info(f"{FIRST_EXITED=}\t{ITERS=:,}\t{elapsed!s}\t{itps:.3f} it/s\t\t{len(TABLE)=}")

    return value


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
        futures = [pool.submit(negamax, state, 16) for state in states]

    wait(futures)

    for state in states:
        state = state_to_string(state)
        print(state)
        print(TABLE[state])


def main():
    logging.basicConfig(level=logging.WARN)
    start = time.perf_counter()
    negamax(State(), 2*LAST_PLY)
    elapsed = time.perf_counter() - start
    print(f"{ITERS=:,d}\t{elapsed=:.3f} s")
    entry = lookup(State())
    print(f"{entry=}")
    n_entries = len(TABLE)
    print(f"{n_entries}")


if  __name__ == "__main__":
    main()
from datetime import datetime
import logging
import time

from quarto.representation.logic import State, get_moves, get_payoffs, get_ply, is_over, state_to_string
from quarto.representation.player import Player, get_plying
from tests.minidag.compression import play


TABLE = dict[str, float]()
ITERS = 0
MAX_DEPTH = float('-inf')
START: datetime | None = None


def lookup(state: State) -> float | None:
    return TABLE.get(state_to_string(state))


def save(state: State, value: float) -> float:
    # return value
    return TABLE.setdefault(state_to_string(state), value)


def minimax(state: State, depth: int | float = float('inf')) -> float:
    global ITERS, MAX_DEPTH, START
    if START is None:
        START = datetime.now()
    if (best := lookup(state)) is not None:
        return best
    ITERS += 1
    if depth == 0 or is_over(state):
        payoffs = get_payoffs(state)
        return payoffs[Player.PLAYER1]
    moves_values = {}
    if (plying := get_plying(get_ply(state))) == Player.PLAYER1:
        f, best = max, float('-inf')
    else:
        f, best = min, float('inf')
    for move in get_moves(state):
        new_state = play(state, move)
        value = minimax(new_state, depth-1)
        moves_values[move] = value
        best = f(best, value)

    if depth > MAX_DEPTH:
        elapsed = datetime.now() - START
        itps = ITERS / (elapsed.total_seconds() + 1e-6)
        logging.warning(f"{MAX_DEPTH=}\t{ITERS=:,}\t{elapsed!s}\t{itps:.3f} it/s")
        MAX_DEPTH = depth
    return save(state, best)


def main():
    logging.basicConfig(level=logging.WARN)
    start = time.perf_counter()
    minimax(State(), 32)
    elapsed = time.perf_counter() - start
    print(f"{ITERS=:,d}\t{elapsed=:.3f} s")
    entry = lookup(State())
    print(f"{entry=}")
    n_entries = len(TABLE)
    print(f"{n_entries}")


if  __name__ == "__main__":
    main()
from collections.abc import Iterable
import random

from quarto.representation.move import Move


def random_policy(moves: Iterable[Move]) -> Move:
    return random.choice(list(moves))

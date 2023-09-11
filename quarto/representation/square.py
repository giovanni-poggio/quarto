from frozendict import frozendict
from itertools import product

from quarto.representation.constants import SIDE

Square = tuple[int, int]
NULL_SQUARE = -1, -1
SQUARES = frozenset((i, j) for i, j in product(range(SIDE), repeat=2))
ROWS = frozendict({i: frozenset((i, j) for j in range(SIDE)) for i in range(SIDE)})
COLS = frozendict({j: frozenset((i, j) for i in range(SIDE)) for j in range(SIDE)})
DIAG = frozenset((k, k) for k in range(SIDE))
ADIAG = frozenset((k, SIDE - k - 1) for k in range(SIDE))

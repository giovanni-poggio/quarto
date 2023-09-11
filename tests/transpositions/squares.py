from functools import cache
from itertools import product
import numpy as np

from quarto.representation.constants import SIDE
from quarto.representation._logic import PIECE, State
from quarto.representation.square import NULL_SQUARE, Square


Transformation = tuple[bool, int]
ALL_TRANSFORMATIONS = frozenset((flip, k) for flip, k in product([False, True], range(4)))


@cache
def rotate(square: Square, k: int) -> Square:
    if square == NULL_SQUARE:
        return square
    rows, cols = np.indices((SIDE, SIDE))
    rows, cols = np.rot90(rows, k), np.rot90(cols, k)
    i, j = square
    return rows[i, j], cols[i, j]


@cache
def flip(square: Square) -> Square:
    if square == NULL_SQUARE:
        return square
    i, j = square
    return i, SIDE-1-j


@cache
def map_square(square: Square, transformation: Transformation) -> Square:
    if square == NULL_SQUARE:
        return square
    flipping, k = transformation
    if flipping:
        return rotate(flip(square), k)
    return rotate(square, k)

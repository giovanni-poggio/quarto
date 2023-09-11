from functools import cache
from itertools import combinations_with_replacement, product
from typing import Callable
from frozendict import frozendict
import logging
import numpy as np
import numpy.typing as npt
import os
import time
import pathlib
import pickle

from quarto.representation.constants import SIDE
from quarto.representation.logic import State
from quarto.representation.square import NULL_SQUARE, SQUARES, Square


Squares = frozenset[Square]
FREE: frozendict[Squares, Squares] | None = None
FREE_PATH = pathlib.Path(os.path.join(os.path.dirname(__file__), "free.pkl"))


HALF = sum(divmod(SIDE, 2))
LEFT = frozenset((i, j) for i, j in product(range(SIDE), range(HALF)))
TOP = frozenset((i, j) for i, j in product(range(HALF), range(SIDE)))
RIGHT_TRI = frozenset((i, j) for i, j in combinations_with_replacement(range(SIDE), r=2))
LEFT_TRI = frozenset((i, SIDE-1-j) for i, j in combinations_with_replacement(range(SIDE), r=2))
QUAD = TOP.intersection(LEFT)
OCT = QUAD.intersection(RIGHT_TRI)


@cache
def get_free(occupied: Squares) -> frozenset[Square]:
    assert FREE, "FREE not loaded"
    if occupied in FREE:
        return FREE[occupied]
    return SQUARES.difference(occupied)


def set_free(board: npt.NDArray, free: dict[Squares, Squares]):
    used = frozenset(map(tuple, np.argwhere(board == 1)))
    used = used.union({NULL_SQUARE})
    if used in free:
        return
    if has_full_symmetry(board):
        free[used] = OCT.difference(used)
    elif has_rotational_symmetry(board):
        free[used] = QUAD.difference(used)
    elif has_central_symmetry(board) or has_vertical_symmetry(board):
        free[used] = TOP.difference(used)
    elif has_horizontal_symmetry(board):
        free[used] = LEFT.difference(used)
    elif has_diagonal_symmetry(board):
        free[used] = RIGHT_TRI.difference(used)
    elif has_antidiagonal_symmetry(board):
        free[used] = LEFT_TRI.difference(used)
    else:
        raise ValueError


def load_free(path: os.PathLike = FREE_PATH):
    global FREE
    if os.path.isfile(path):
        with open(path, "rb") as fp:
            free = pickle.load(fp)
        FREE = frozendict(free)
        return
    logging.warning("Computing FREE squares")
    start = time.perf_counter()
    free = {}
    factories = {
        "horizontal": get_horizontally_symmetric,
        "vertical": get_vertically_symmetric,
        "diagonal": get_diagonally_symmetric,
        "antidiagonal": get_antidiagonally_symmetric,
        "rotational": get_rotationally_symmetric,
        "central": get_centrally_symmetric,
        "full": get_fully_symmetric,
    }
    for factory in factories.values():
        boards = build_symmetrical(factory)
        for board in boards:
            set_free(board, free)
    FREE = frozendict(free)
    elapsed = time.perf_counter() - start
    logging.warning(f"DONE\t{elapsed=:f} s")
    with open(path, "wb") as fp:
        pickle.dump(FREE, fp)


def has_horizontal_symmetry(board: npt.NDArray) -> bool:
    return np.array_equal(board, np.fliplr(board))


def has_vertical_symmetry(board: npt.NDArray) -> bool:
    return np.array_equal(board, np.flipud(board))


def has_diagonal_symmetry(board: npt.NDArray) -> bool:
    return np.array_equal(board, board.T)


def has_antidiagonal_symmetry(board: npt.NDArray) -> bool:
    return np.array_equal(np.fliplr(board), np.fliplr(board).T)


def has_rotational_symmetry(board: npt.NDArray) -> bool:
    return np.array_equal(board, np.rot90(board))


def has_central_symmetry(board: npt.NDArray) -> bool:
    return np.array_equal(board, np.rot90(board, k=2))


def has_full_symmetry(board: npt.NDArray) -> bool:
    return has_horizontal_symmetry(board) and has_diagonal_symmetry(board)


def build_symmetrical(factory: Callable[[int], npt.NDArray], side: int = SIDE) -> list[npt.NDArray]:
    base = factory(side)
    free = np.unique(base)
    values = product([0, 1], repeat=len(free))
    output = []
    for value in values:
        board = np.zeros((side, side), dtype=int)
        for i, v in zip(free, value):
            board[base == i] = v
        output.append(board)
    return output


def get_horizontally_symmetric(side: int = SIDE) -> npt.NDArray:
    half = sum(divmod(side, 2))
    output = np.zeros((side, side), dtype=int)
    for k, (i, j) in enumerate(product(range(side), range(half))):
        output[i, j] = output[i, side-1-j] = k
    return output


def get_vertically_symmetric(side: int = SIDE) -> npt.NDArray:
    return np.rot90(get_horizontally_symmetric(side))


def get_diagonally_symmetric(side: int = SIDE) -> npt.NDArray:
    output = np.zeros((side, side), dtype=int)
    for k, (i, j) in enumerate(combinations_with_replacement(range(side), r=2)):
        output[i, j] = output[j, i] = k
    return output


def get_antidiagonally_symmetric(side: int = SIDE) -> npt.NDArray:
    return np.fliplr(get_diagonally_symmetric(side))


def get_rotationally_symmetric(side: int = SIDE) -> npt.NDArray:
    half = sum(divmod(side, 2))
    output = np.zeros((side, side), dtype=int)
    for k, (i1, j1) in enumerate(product(range(half), repeat=2)):
        iN, jN = side-1-i1, side-1-j1
        output[i1, j1] = output[j1, iN] = output[iN, jN] = output[jN, i1] = k
    return output


def get_centrally_symmetric(side: int = SIDE) -> npt.NDArray:
    half = sum(divmod(side, 2))
    output = np.zeros((side, side), dtype=int)
    for k, (i1, j1) in enumerate(product(range(half), range(side))):
        iN, jN = side-1-i1, side-1-j1
        output[i1, j1] = output[iN, jN] = k
    return output


def get_fully_symmetric(side: int = SIDE) -> npt.NDArray:
    half = sum(divmod(side, 2))
    output = np.zeros((side, side), dtype=int)
    for k, (i1, j1) in enumerate(combinations_with_replacement(range(half), r=2)):
        iN, jN = side-1-i1, side-1-j1
        output[i1, j1] = output[i1, jN] = output[iN, j1] = output[iN, jN] =\
            output[j1, i1] = output[j1, iN] = output[jN, i1] = output[jN, iN] = k
    return output


def test_constants():
    logging.debug("TESTING CONSTANTS")
    constants = {
        "left": LEFT,
        "top": TOP,
        "right triangle": RIGHT_TRI,
        "left triangle": LEFT_TRI,
        "quadrant": QUAD,
        "octant": OCT,
    }
    for name, constant in constants.items():
        board = np.zeros((SIDE, SIDE), dtype=int)
        logging.debug(name.upper())
        logging.debug(constant)
        for (i, j) in constant:
            board[i, j] = 1
        logging.debug("\n"+str(board))


def test_symmetries(side: int = SIDE):
    logging.debug("TESTING SYMMETRIES")
    factories = {
        "horizontal": get_horizontally_symmetric,
        "vertical": get_vertically_symmetric,
        "diagonal": get_diagonally_symmetric,
        "antidiagonal": get_antidiagonally_symmetric,
        "rotational": get_rotationally_symmetric,
        "central": get_centrally_symmetric,
        "full": get_fully_symmetric,
    }
    checkers = {
        "horizontal": has_horizontal_symmetry,
        "vertical": has_vertical_symmetry,
        "diagonal": has_diagonal_symmetry,
        "antidiag": has_antidiagonal_symmetry,
        "rotational": has_rotational_symmetry,
        "central": has_central_symmetry,
    }
    for kind, factory in factories.items():
        logging.debug(kind.upper())
        board = factory(side)
        logging.debug("\n" + str(board))
        for name, checker in checkers.items():
            logging.debug(f"{name}:\t{checker(board)}")


def test_build(side: int = SIDE):
    logging.debug("TESTING BUILD")
    factories = {
        "horizontal": get_horizontally_symmetric,
        "vertical": get_vertically_symmetric,
        "diagonal": get_diagonally_symmetric,
        "antidiagonal": get_antidiagonally_symmetric,
        "rotational": get_rotationally_symmetric,
        "central": get_centrally_symmetric,
        "fully": get_fully_symmetric,
    }
    checkers = {
        "horizontal": has_horizontal_symmetry,
        "vertical": has_vertical_symmetry,
        "diagonal": has_diagonal_symmetry,
        "antidiagonal": has_antidiagonal_symmetry,
        "rotational": has_rotational_symmetry,
        "central": has_central_symmetry,
        "fully": has_full_symmetry,
    }
    total = 0
    for name, factory in factories.items():
        logging.debug(name.upper())
        boards = build_symmetrical(factory, side)
        for board in boards:
            assert checkers[name](board)
        logging.debug(len(boards))
        total += len(boards)
    logging.debug(f"{total=}")
    

def debug_free():
    global FREE
    assert FREE is not None
    factories = {
        # "horizontal": get_horizontally_symmetric, 
        # "vertical": get_vertically_symmetric,
        # "diagonal": get_diagonally_symmetric,
        # "antidiagonal": get_antidiagonally_symmetric, 
        # "rotational": get_rotationally_symmetric,
        # "central": get_centrally_symmetric,
        # "full": get_fully_symmetric,
    } 
    for name, factory in factories.items():
        boards = build_symmetrical(factory)
        print(name.upper())
        for board in boards:
            print(board)
            used = frozenset(map(tuple, np.argwhere(board == 1))).union({NULL_SQUARE})
            free = FREE[used]
            board = np.zeros((SIDE, SIDE), dtype=int)
            for k, (i, j) in enumerate(sorted(free)):
                board[i, j] = k+1
            print(board)
            input("continue")
    print(len(FREE))


def test():
    logging.basicConfig(level=logging.INFO)
    test_constants()
    test_symmetries()
    test_build()
    debug_free()
    assert FREE is not None
    logging.debug(len(FREE))


load_free()


if __name__ == "__main__":
    test()

from collections.abc import Generator
from genericpath import isfile
from itertools import product
import os
import pathlib
import pickle
from typing import NamedTuple
import logging
import time
import networkx as nx
import numpy as np
import numpy.typing as npt

from quarto.representation.constants import SIDE
from quarto.representation.square import Square
from tests.minidag.dag import Node, build_dag, dag_stats, plot_dag


SQUARES_DAG_FILE = pathlib.Path(os.path.join(os.path.dirname(__file__), f"{SIDE}squares.pkl"))


class Transform(NamedTuple):
    flip: bool
    rotate: int

    def __str__(self):
        output = ''
        if self.flip:
            output = 'f'
        if self.rotate:
            output += f"r{self.rotate}"
        return output


ALL_TRANSFORMS = frozenset(Transform(flip, rotate) for flip, rotate in product([False, True], range(4)))
SORTED_TRANSFORMS = tuple(sorted(ALL_TRANSFORMS))
NULL_TRANSFORM = Transform(flip=False, rotate=0)
SQUARES_DAG: nx.DiGraph | None = None


Board = npt.NDArray


def board_to_string(board: Board) -> str:
    output = []
    for row in board:
        output.append(' '.join(map(str, row)))
    return '\n'.join(output)


rotate = np.rot90
flip = np.fliplr


def transform_board(board: Board, transform: Transform) -> Board:
    if transform.flip:
        return rotate(flip(board), transform.rotate)
    return rotate(board, transform.rotate)
    

def get_node(parent: Node | None = None, move: Square | None = None) -> Node:
    if parent is None:
        board = np.zeros((SIDE, SIDE), dtype=int)
        board.setflags(write=False)
        label = board_to_string(board)
        return Node(label, {"board": board, "depth": 0, "canonical": True})
    assert move is not None
    board = parent.data["board"].copy()
    assert board[move] == 0
    board[move] = 1
    board.setflags(write=False)
    label = board_to_string(board)
    canonical, _ = _get_canonical_transform(board)
    return Node(label, {"board": board, "depth": parent.data["depth"] + 1, "canonical": label == canonical})


def _get_canonical_transform(board: Board) -> tuple[str, Transform]:
    equivalents = dict[str, Transform]()
    for transform in SORTED_TRANSFORMS:
        equivalent = transform_board(board, transform)
        equivalent = board_to_string(equivalent)
        equivalents.setdefault(equivalent, transform)
    canonical = max(equivalents)
    transform = equivalents[canonical]
    return canonical, transform

def get_canonical_transform(node: Node) -> tuple[str, Transform]:
    return _get_canonical_transform(node.data["board"])


def get_moves(node: Node) -> Generator[Square, None, None]:
    for i, j in np.argwhere(node.data["board"] == 0):
        yield i, j


def load_squares_dag():
    global SQUARES_DAG
    if os.path.isfile(SQUARES_DAG_FILE):
        with open(SQUARES_DAG_FILE, 'rb') as fp:
            try:
                SQUARES_DAG = pickle.load(fp)
            except AttributeError:
                logging.warning("ORIGINAL PICKLE NOT BUILT BY CURRENT SCRIPT: REBUILDING")
            else:
                return
    if SQUARES_DAG is not None:
        return
    # logging.basicConfig(level=logging.DEBUG)
    logging.warning(f"BUILDING SQUARES DAG")
    start = time.perf_counter()
    dag = build_dag(get_node, get_moves, get_canonical_transform, SIDE**2)
    elapsed = time.perf_counter() - start
    logging.warning(f"DONE\t({elapsed=:.3f} s)")
    with open(SQUARES_DAG_FILE, 'wb') as fp:
        pickle.dump(dag, fp)
    SQUARES_DAG = dag


def main():
    global SQUARES_DAG
    assert SQUARES_DAG is not None
    if SIDE <= 3:
        plot_dag(SQUARES_DAG, block=True)
    dag_stats(SQUARES_DAG, n=SIDE**2)


load_squares_dag()

if __name__ == "__main__":
    main()

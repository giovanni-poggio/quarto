from collections.abc import Generator
from functools import cache
from itertools import product
from typing import Any, NamedTuple
import networkx as nx
import numpy as np
import numpy.typing as npt

from quarto.representation.constants import SIDE
from quarto.representation.square import Square
from tests.minidag2.dag import Node, build_min_dag, dag_stats, plot_dag


class Transform(NamedTuple):
    rotate: int
    flip: bool

    def __str__(self):
        output = f'r{self.rotate}' if self.rotate else ''
        output += 'f' if self.flip else ''
        output = output if output else 'e'
        return output


@cache
def rotate(square: Square, k: int) -> Square:
    rows, cols = np.indices((SIDE, SIDE))
    rows, cols = np.rot90(rows, -k), np.rot90(cols, -k)
    i, j = square
    return rows[i, j], cols[i, j]


@cache
def flip(square: Square) -> Square:
    i, j = square
    return i, SIDE-1-j


@cache
def map_square(square: Square, transform: Transform) -> Square:
    if transform.flip:
        return rotate(flip(square), transform.rotate)
    return rotate(square, transform.rotate)


ALL_TRANSFORMS = frozenset(Transform(rotate, flip) for flip, rotate in product([False, True], range(4)))
SORTED_TRANSFORMS = tuple(sorted(ALL_TRANSFORMS))
NULL_TRANSFORM = Transform(rotate=0, flip=False)
SQUARES_DAG: nx.DiGraph | None = None


Board = npt.NDArray


def get_connectedness(board: Board) -> int:
    side = len(board)
    row_sums = np.sum(board, axis=1)
    col_sums = np.sum(board, axis=0)
    diag_sum = np.trace(board)
    adiag_sum = np.trace(np.fliplr(board))
    total = np.sum(row_sums**side)
    total += np.sum(col_sums**side)
    total += diag_sum**side + adiag_sum**side
    return total


def board_to_string(board: Board) -> str:
    output = []
    for row in board:
        output.append(' '.join(map(str, row)))
    return '\n'.join(output)


def transform_board(board: Board, transform: Transform) -> Board:
    if transform.flip:
        return np.rot90(np.fliplr(board), transform.rotate)
    return np.rot90(board, transform.rotate)


def get_canonical(board: Board) -> tuple[Board, Transform]:
    transforms = dict[str, Transform]()
    equivalents = dict[str, Board]()
    for transform in SORTED_TRANSFORMS:
        equivalent = transform_board(board, transform)
        if (as_string := board_to_string(equivalent)) in equivalents:
            continue
        transforms[as_string] = transform
        equivalents[as_string] = equivalent
    canonical_str = max(equivalents)
    return equivalents[canonical_str], transforms[canonical_str]


def get_board_children(parent: Node) -> Generator[tuple[Node, dict[str, Any]], None, None]:
    moves = map(tuple, np.argwhere(parent.data["board"] == 0))
    produced = set[str]()
    for move in moves:
        board = get_board_child(parent, move)
        canonical, transform = get_canonical(board)
        if (canonical_str := board_to_string(canonical)) in produced:
            continue
        produced.add(canonical_str)
        score = get_connectedness(canonical)
        node_data = {"board": canonical, "score": score, "depth": np.sum(board)}
        delta = score - parent.data["score"]
        edge_data = {"move": move, "transform": transform, "score": score,
                     "label": f"{move},{transform}\n{score},{delta}"}
        yield Node(canonical_str, node_data), edge_data


def get_board_child(parent: Node, move: Square) -> Board:
    i, j = move
    board = parent.data["board"].copy()
    board[i, j] = 1
    return board


def build_board_dag():
    empty = np.zeros((SIDE, SIDE), dtype=int)
    root = Node(board_to_string(empty), {"board": empty, "depth": 0, "score": 0})
    dag = build_min_dag(root, get_board_children, "depth", SIDE**2)
    return dag


def main():
    dag = build_board_dag()
    dag_stats(dag, SIDE**2)
    if SIDE > 3:
        return
    plot_dag(dag)


if __name__ == "__main__":
    main()

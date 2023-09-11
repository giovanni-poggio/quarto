from collections import defaultdict
from functools import cache
from itertools import filterfalse
import math
from frozendict import frozendict
import logging
import networkx as nx
import numpy as np

from quarto.representation.constants import ATTRIBUTES, SIDE
from quarto.representation.logic import State, get_phase, state_to_string
from quarto.representation.logic import play as _play
from quarto.representation.move import Move
from quarto.representation.phase import Phase
from quarto.representation.piece import PIECES, Piece
from quarto.representation.square import NULL_SQUARE, Square
from tests.minidag.pieces import pieces_to_string
from tests.minidag.dag import plot_dag
from tests.minidag.squares import NULL_TRANSFORM, SQUARES_DAG, Transform, board_to_string
from tests.minidag.pieces import NULL_MAPPING, PIECES_DAG, Mapping, map_piece


MAPPINGS: frozendict[tuple[frozenset[Piece], Piece], Mapping] | None = None
TRANSFORMS: frozendict[tuple[frozenset[Square], Square], Transform] | None = None


def play(state: State, move: Move, inplace: bool = False) -> State:
    if not inplace:
        state = state.copy()
    if isinstance(move, Piece):
        return give(state, move)
    return put(state, move)


def give(state: State, piece: Piece) -> State:
    logging.debug(f"\n{state_to_string(state)}")
    logging.debug(f"{piece=}")
    assert MAPPINGS is not None
    used = frozenset(state.values())
    key = used, piece
    _play(state, piece, inplace=True)
    mapping = MAPPINGS.get(key, NULL_MAPPING)
    if mapping != NULL_MAPPING:
        logging.debug(f"{mapping=}")
        state = {square: map_piece(piece, mapping) for square, piece in state.items()}
    logging.debug(f"\n{state_to_string(state)}")
    return state


def put(state: State, square: Square) -> State:
    logging.debug(f"{square=}")
    assert TRANSFORMS is not None
    occupied = frozenset(state.keys())
    key = occupied, square
    logging.debug(f"{occupied=!s}\t{square=}")
    _play(state, square, inplace=True)
    transform = TRANSFORMS.get(key, NULL_TRANSFORM)
    if transform != NULL_TRANSFORM:
        logging.debug(f"{transform=}")
        state = {map_square(square, transform): piece for square, piece in state.items()}
    logging.debug(f"\n{state_to_string(state)}")
    return state


@cache
def rotate(square: Square, k: int) -> Square:
    if square == NULL_SQUARE:
        return square
    rows, cols = np.indices((SIDE, SIDE))
    rows, cols = np.rot90(rows, -k), np.rot90(cols, -k)
    i, j = square
    return rows[i, j], cols[i, j]


@cache
def flip(square: Square) -> Square:
    if square == NULL_SQUARE:
        return square
    i, j = square
    return i, SIDE-1-j


@cache
def map_square(square: Square, transform: Transform) -> Square:
    if square == NULL_SQUARE:
        return square
    flipping, k = transform
    if transform.flip:
        return rotate(flip(square), transform.rotate)
    return rotate(square, transform.rotate)
    

def load_transforms():
    global TRANSFORMS
    assert SQUARES_DAG is not None, 'SQUARES DAG NOT LOADED'
    transforms = dict[tuple[frozenset[Square], Square], Mapping]()
    nodes_data = {label: data for label, data in SQUARES_DAG.nodes(data=True)}
    for y, z, yz_data in SQUARES_DAG.edges(data=True):
        if (transform := yz_data.get("transform")) is None:
            continue
        for  x, y, xy_data in SQUARES_DAG.in_edges(y, data=True):
            occupied = map(tuple, np.argwhere(nodes_data[x]["board"] != 0))
            occupied = frozenset(occupied) | {NULL_SQUARE}
            square = xy_data["move"]
            transforms[occupied, square] = transform
            logging.debug(f"{x=}\t{occupied=!s}")
            logging.debug(f"{square=}\t{y=}")
            logging.debug(f"{transform=}\t{z=}")
    TRANSFORMS = frozendict(transforms)


def load_mappings():
    global MAPPINGS
    assert PIECES_DAG is not None, 'PIECES DAG NOT LOADED'
    mappings = dict[tuple[frozenset[Square], Square], Mapping]()
    nodes_data = {label: data for label, data in PIECES_DAG.nodes(data=True)}
    for y, z, yz_data in PIECES_DAG.edges(data=True):
        if (mapping := yz_data.get("transform")) is None:
            continue
        for  x, y, xy_data in PIECES_DAG.in_edges(y, data=True):
            used = nodes_data[x]["pieces"]
            piece = xy_data["move"]
            mappings[used, piece] = mapping
            logging.debug(f"{x=}\t{used=!s}")
            logging.debug(f"{piece=}\t{y=}")
            logging.debug(f"{mapping=}\t{z=}")
    MAPPINGS = frozendict(mappings)


def reduce_dag(dag: nx.DiGraph):
    out = nx.DiGraph()
    data = {label: data for label, data in dag.nodes(data=True)}
    for y, z, yz_data in dag.edges(data=True):
        if data[y]["canonical"]:
            out.add_node(y, **data[y])
        if data[z]["canonical"]:
            out.add_node(z, **data[z])
        if data[y]["canonical"] and data[z]["canonical"]:
            out.add_edge(y, z, **yz_data)
            continue
        if "transform" not in yz_data:
            continue
        for  x, y, xy_data in dag.in_edges(y, data=True):
            out.add_edge(x, z, **yz_data, **xy_data)
    return out


def estimate_paths(min_dag: nx.DiGraph) -> int:
    branches = defaultdict(int)
    nodes = defaultdict(int)
    for node, data in min_dag.nodes(data=True):
        if min_dag.out_degree[node] == 0:
            continue
        branches[data["depth"]] += min_dag.out_degree[node]
        nodes[data["depth"]] += 1
    total = 1
    for depth in sorted(branches):
        n_branches = branches[depth]
        n_nodes = nodes[depth]
        factor = math.ceil(n_branches / n_nodes)
        total *= factor
    return total


def main():
    global SQUARES_DAG, PIECES_DAG
    assert SQUARES_DAG is not None and PIECES_DAG is not None
    min_pieces = reduce_dag(PIECES_DAG)
    min_squares = reduce_dag(SQUARES_DAG)
    if ATTRIBUTES <= 3:
        # plot_dag(PIECES_DAG, block=False)
        plot_dag(min_pieces, block=False)
    if SIDE <= 3:
        # plot_dag(SQUARES_DAG, block=False)
        plot_dag(min_squares, block=True)

    # source = pieces_to_string(frozenset())
    # target = pieces_to_string(PIECES)
    # n_piece_paths = sum(1 for _ in nx.all_simple_paths(min_pieces, source, target))
    # print(f"{n_piece_paths=:,}")

    # source = board_to_string(np.zeros((SIDE, SIDE), dtype=int))
    # target = board_to_string(np.ones((SIDE, SIDE), dtype=int))
    # n_square_paths = sum(1 for _ in nx.all_simple_paths(min_squares, source, target))
    # print(f"{n_square_paths=:,}")

    n_piece_paths = estimate_paths(min_pieces)
    n_square_paths = estimate_paths(min_pieces)

    est_iterations = 2 * n_piece_paths * n_square_paths * len(PIECES)
    print(f"{est_iterations=:,}")

    exit()

    give_nodes = defaultdict(int)
    for _, data in PIECES_DAG.nodes(data=True):
        if not data["canonical"]:
            continue
        give_nodes[data["depth"]] += 1
    
    put_nodes = defaultdict(int)
    for _, data in SQUARES_DAG.nodes(data=True):
        if not data["canonical"]:
            continue
        put_nodes[data["depth"]] += 1
    
    tot_states = 1
    for depth in range(len(PIECES)):
        tot_states += give_nodes[depth] * put_nodes[depth]
        tot_states += put_nodes[depth] * give_nodes[depth+1]
        depth += 1
        print(f"{depth=}\t{tot_states=}")





    


load_mappings()
load_transforms()


if __name__ == "__main__":
    main()
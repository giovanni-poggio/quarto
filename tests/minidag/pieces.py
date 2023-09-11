import logging
import time
from collections.abc import Generator
from functools import cache, lru_cache
from itertools import permutations, product
import os
import pathlib
import pickle
import pstats
from typing import  NamedTuple
import networkx as nx

from quarto.representation.constants import ATTRIBUTES
from quarto.representation.piece import PIECES, Piece
from tests.minidag.dag import Node, build_dag, dag_stats, plot_dag


PIECES_DAG_FILE = pathlib.Path(os.path.join(os.path.dirname(__file__), f"{ATTRIBUTES}pieces.pkl"))
PIECES_DAG: nx.DiGraph | None = None
SORTED_PIECES = tuple(sorted(PIECES))


class Mapping(NamedTuple):
    flipping: Piece
    permutation: tuple[int, ...]

    def __str__(self):
        return ','.join([self.flipping, ''.join(map(str, self.permutation))])


ALL_MAPPINGS = frozenset(Mapping(flip, rotate) for flip, rotate in product(PIECES, permutations(range(ATTRIBUTES))))
SORTED_MAPPINGS = tuple(sorted(ALL_MAPPINGS))
NULL_MAPPING = Mapping(flipping=f"{0:0{ATTRIBUTES}b}", permutation=tuple(range(ATTRIBUTES)))


@cache
def pieces_to_string(pieces: frozenset[Piece]) -> str:
    return '-'.join(sorted(map(str, pieces)))


@cache
def flip(piece: Piece, flipping: Piece) -> Piece:
    return f"{int(piece, base=2)^int(flipping, base=2):0{ATTRIBUTES}b}"


@cache
def permute(piece: Piece, permutation: tuple[int, ...]) -> Piece:
    return ''.join(piece[i] for i in permutation)


@cache
def map_piece(piece: Piece, mapping: Mapping) -> Piece:
    return permute(flip(piece, mapping.flipping), mapping.permutation)


def map_pieces(pieces: frozenset[Piece], mapping: Mapping) -> frozenset[Piece]:
    return frozenset(map_piece(piece, mapping) for piece in pieces)
    

def get_node(parent: Node | None = None, move: Piece | None = None) -> Node:
    if parent is None:
        pieces = frozenset()
        label = pieces_to_string(pieces)
        return Node(label, {"pieces": pieces, "depth": 0, "canonical": True})
    assert move is not None
    used = parent.data["pieces"].copy()
    assert move not in used
    pieces = used | {move}
    label = pieces_to_string(pieces)
    canonical, _ = _get_canonical_mapping(pieces)
    return Node(label, {"pieces": pieces, "depth": parent.data["depth"] + 1, "canonical": label == canonical})


def _get_canonical_mapping(pieces: frozenset[Piece]) -> tuple[str, Mapping]:
    equivalents = dict[str, Mapping]()
    for mapping in SORTED_MAPPINGS:
        equivalent = map_pieces(pieces, mapping)
        equivalent = pieces_to_string(equivalent)
        equivalents.setdefault(equivalent, mapping)
    canonical = min(equivalents)
    mapping = equivalents[canonical]
    return canonical, mapping

def get_canonical_mapping(node: Node) -> tuple[str, Mapping]:
    return _get_canonical_mapping(node.data["pieces"])


def get_moves(node: Node) -> Generator[Piece, None, None]:
    for piece in sorted(PIECES.difference(node.data["pieces"])):
        yield piece


def load_pieces_dag():
    global PIECES_DAG
    if os.path.isfile(PIECES_DAG_FILE):
        with open(PIECES_DAG_FILE, 'rb') as fp:
            try:
                PIECES_DAG = pickle.load(fp)
            except AttributeError:
                logging.warning("ORIGINAL PICKLE NOT BUILT BY CURRENT SCRIPT: REBUILDING")
            else:
                return
    if PIECES_DAG is not None:
        return
    # logging.basicConfig(level=logging.DEBUG)
    logging.warning(f"BUILDING PIECES DAG")
    start = time.perf_counter()
    dag = build_dag(get_node, get_moves, get_canonical_mapping, 2**ATTRIBUTES)
    elapsed = time.perf_counter() - start
    logging.warning(f"DONE\t({elapsed=:.3f} s)")
    with open(PIECES_DAG_FILE, 'wb') as fp:
        pickle.dump(dag, fp)
    PIECES_DAG = dag


def main():
    global PIECES_DAG
    assert PIECES_DAG is not None
    if ATTRIBUTES <= 3:
        plot_dag(PIECES_DAG, block=True)
    dag_stats(PIECES_DAG, n=ATTRIBUTES**2)


load_pieces_dag()


if __name__ == "__main__":
    main()

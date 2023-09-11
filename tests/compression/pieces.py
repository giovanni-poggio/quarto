from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass, field
import os
import pathlib
import pickle
from frozendict import frozendict
from functools import cache
from itertools import permutations, product
from typing import NamedTuple
import logging
import time

from quarto.representation.constants import ATTRIBUTES
from quarto.representation.piece import Piece, PIECES


PIECE_ZERO = f"{0:0{ATTRIBUTES}b}"
AVAILABLE: frozendict[frozenset[Piece], frozenset[Piece]] | None = None
AVAILABLE_PATH = pathlib.Path(os.path.join(os.path.dirname(__file__), "available.pkl"))


class Mapping(NamedTuple):
    to_flip: Piece
    permute: tuple[int, ...]


@dataclass(slots=True)
class Node:
    used: frozenset[Piece]
    mappings: frozenset[Mapping]
    children: dict[Piece, "Node"] = field(default_factory=dict)
    unique: frozenset[Piece] = field(init=False)


Root = Node


@cache
def get_available(used: frozenset[Piece]) -> frozenset[Piece]:
    assert AVAILABLE, 'TREE not loaded'
    if used in AVAILABLE:
        return AVAILABLE[used]
    return PIECES.difference(used)


def load_tree(path: os.PathLike = AVAILABLE_PATH):
    global AVAILABLE
    if os.path.isfile(path):
        with open(path, "rb") as fp:
            available = pickle.load(fp)
        AVAILABLE = frozendict(available)
        return
    if AVAILABLE:
        return
    logging.warning("Loading unique pieces")
    start = time.perf_counter()
    root = build_tree()
    data = {}
    load_data(root, data)
    AVAILABLE = frozendict(data)
    elapsed = time.perf_counter() - start
    logging.warning(f"Done\t({elapsed=:3f} s)")
    with open(path, "wb") as fp:
        pickle.dump(AVAILABLE, fp)


def load_data(node: Root, data: dict[frozenset[Piece], frozenset[Piece]]):
    data[node.used] = node.unique
    for child in node.children.values():
        load_data(child, data)


def build_tree() -> Root:
    root = Node(frozenset(), get_all_mappings())
    _build_tree(root)
    return root


def _build_tree(node: Node):
    unique = get_unique(node.used, node.mappings)
    node.unique = frozenset(unique)
    for piece in unique:
        mappings = get_invariant(piece, node.mappings)
        if len(mappings) == 1:
            continue
        resulting = node.used.union({piece})
        child = Node(resulting, frozenset(mappings))
        node.children[piece] = child
        _build_tree(child)


def get_unique(used: Collection[Piece], mappings: Collection[Mapping]) -> set[Piece]:
    remaining = PIECES.difference(used)
    unique = set()
    for piece in remaining:
        reduced = reduce(piece, mappings)
        unique.add(reduced)
    return unique


def reduce(piece: Piece, mappings: Iterable[Mapping]) -> Piece:
    return min(map_piece(piece, mapping) for mapping in mappings)


def get_invariant(piece: Piece, mappings: Iterable[Mapping]) -> set[Mapping]:
    return {mapping for mapping in mappings if map_piece(piece, mapping) == piece}


@cache
def map_piece(piece: Piece, mapping: Mapping) -> Piece:
    return permute(flip(piece, mapping.to_flip), mapping.permute)


@cache
def permute(piece: Piece, permutation: Sequence[int]) -> Piece:
    return ''.join(piece[i] for i in permutation)


@cache
def flip(piece: Piece, to_flip: Piece) -> Piece:
    return f"{int(piece, base=2)^int(to_flip, base=2):0{ATTRIBUTES}b}"


def get_all_mappings() -> frozenset[Mapping]:
    return frozenset(Mapping(piece, permutation) for piece, permutation in
                     product(PIECES, permutations(range(ATTRIBUTES))))


def inspect_tree():
    if not AVAILABLE:
        load_tree()
    assert AVAILABLE
    keys = AVAILABLE.keys()
    keys = map(lambda used: tuple(sorted(used)), keys)
    for used in sorted(keys, key=len):
        unique = sorted(AVAILABLE[frozenset(used)])
        print(f"{used=}\t{unique=}")
    print(f"{len(AVAILABLE)=}")


if __name__ == "__main__":
    inspect_tree()


load_tree()

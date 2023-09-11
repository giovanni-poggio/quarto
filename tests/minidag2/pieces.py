
from collections.abc import Generator
from functools import cache
from itertools import permutations, product
from typing import Any, NamedTuple

from quarto.representation.constants import ATTRIBUTES
from quarto.representation.piece import PIECES, Piece
from tests.minidag2.dag import Node, build_min_dag, dag_stats, plot_dag


SORTED_PIECES = tuple(sorted(PIECES))


class Mapping(NamedTuple):
    permutation: tuple[int, ...]
    flipping: Piece

    def __str__(self):
        return f"{''.join(map(str, self.permutation))}/{self.flipping}"


ALL_MAPPINGS = frozenset(Mapping(permutation, flipping) for permutation, flipping in product(permutations(range(ATTRIBUTES)), PIECES))
SORTED_MAPPINGS = tuple(sorted(ALL_MAPPINGS))
NULL_MAPPING = Mapping(permutation=tuple(range(ATTRIBUTES)), flipping=f"{0:0{ATTRIBUTES}b}")


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


def get_minimal(pieces: frozenset[Piece]) -> tuple[frozenset[Piece], Mapping]:
    mappings = dict[str, Mapping]()
    equivalents = dict[str, frozenset[Piece]]()
    for mapping in SORTED_MAPPINGS:
        equivalent = map_pieces(pieces, mapping)
        if (as_string := pieces_to_string(equivalent)) in equivalents:
            continue
        mappings[as_string] = mapping
        equivalents[as_string] = equivalent
    minimal_str = min(equivalents)
    return equivalents[minimal_str], mappings[minimal_str]


def get_pieces_children(parent: Node) -> Generator[tuple[Node, dict[str, Any]], None, None]:
    moves = PIECES.difference(parent.data["pieces"])
    produced = set[frozenset[Piece]]()
    for move in sorted(moves):
        pieces = parent.data["pieces"] | {move}
        minimal, mapping = get_minimal(pieces)
        if minimal in produced:
            continue
        produced.add(minimal)
        score = get_entropy(minimal)
        node_data = {"pieces": minimal, "score": score, "depth": len(minimal)}
        delta = score - parent.data["score"]
        edge_data = {"move": move, "mapping": mapping, "score": score,
                     "label": f"{move},{mapping}\n{score},{delta}"}
        yield Node(pieces_to_string(minimal), node_data), edge_data


def get_entropy(minimal: frozenset[Piece]) -> int:
    score = 0
    for mapping in SORTED_MAPPINGS:
        equivalent = map_pieces(minimal, mapping)
        if equivalent == minimal:
            score += 1
    return score


def build_pieces_dag():
    empty = frozenset()
    root = Node(pieces_to_string(empty), {"pieces": empty, "depth": 0, "score": len(ALL_MAPPINGS)})
    dag = build_min_dag(root, get_pieces_children, "depth", 2**ATTRIBUTES)
    return dag


def main():
    dag = build_pieces_dag()
    dag_stats(dag, 2**ATTRIBUTES)
    if ATTRIBUTES > 3:
        return
    plot_dag(dag)


if __name__ == "__main__":
    main()

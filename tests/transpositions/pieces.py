from functools import cache
from itertools import permutations, product

from quarto.representation.constants import ATTRIBUTES, SIDE
from quarto.representation.piece import NULL_PIECE, Piece, PIECES


Mapping = tuple[Piece, tuple[int, ...]]
ALL_MAPPINGS = frozenset((piece, permutation) for piece, permutation in
                         product(PIECES, permutations(range(SIDE))))


@cache
def flip(piece: Piece, to_flip: Piece) -> Piece:
    if piece == NULL_PIECE:
        return piece
    return f"{int(piece, base=2)^int(to_flip, base=2):0{ATTRIBUTES}b}"


@cache
def permute(piece: Piece, permutation: tuple[int, ...]) -> Piece:
    if piece == NULL_PIECE:
        return piece
    return ''.join(piece[i] for i in permutation) 


@cache
def map_piece(piece: Piece, mapping: Mapping) -> Piece:
    if piece == NULL_PIECE:
        return piece
    to_flip, permutation = mapping
    return permute(flip(piece, to_flip), permutation)

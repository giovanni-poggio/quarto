from quarto.representation.constants import ATTRIBUTES, SIDE

Piece = str
NULL_PIECE = '-' * ATTRIBUTES
PIECES = frozenset(f"{piece:0{ATTRIBUTES}b}" for piece in range(2**ATTRIBUTES))

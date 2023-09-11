from collections.abc import Collection

from frozendict import frozendict

from quarto.compression.pieces import ALL_MAPPINGS
from quarto.representation.logic import PIECE, State, get_phase
from quarto.representation.move import Move
from quarto.representation.phase import Phase
from quarto.representation.piece import Piece
from quarto.representation.square import Square


def get_moves(state: State) -> Collection[Move]:
    if get_phase(state) == Phase.PUT:
        return get_free(frozenset(state.keys()))
    return get_available(frozenset(state.values()))


FIRST_PUT = frozenset({(0, 0), (0, 1), (1, 1)})
SECOND_PUT = frozendict({
    frozenset({PIECE, (0, 0)}): RIGHT_TRI.difference()
    frozenset({PIECE, (1, 1)}): 
    frozenset({PIECE, (0, 1)}): 
})


def get_free(occupied: frozenset[Square]) -> frozenset[Square]:
    if (n_occupied := len(occupied)) == 1:
        return get_fis
    if n_occupied == 2:
        return get_second_free(occupied)


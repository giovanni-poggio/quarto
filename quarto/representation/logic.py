from functools import cache
from itertools import pairwise
from operator import itemgetter

from quarto.representation.constants import SIDE, ATTRIBUTES
from quarto.representation.payoffs import Payoffs
from quarto.representation.piece import Piece, NULL_PIECE, PIECES
from quarto.representation.square import Square, NULL_SQUARE, SQUARES, ROWS, COLS, DIAG, ADIAG
from quarto.representation.phase import Phase
from quarto.representation.player import Player, get_plying
from quarto.representation.move import Move


State = dict[Square, Piece]
PIECE = NULL_SQUARE
LAST_PLY = len(PIECES)


get_ply = len


def get_phase(state: State) -> Phase:
    if PIECE not in state:
        return Phase.GIVE
    return Phase.PUT


def get_pieces(state: State, squares: frozenset[Square]) -> frozenset[Piece]:
    squares = squares.intersection(state.keys())
    return frozenset(state[square] for square in squares)


def play(state: State, move: Move, inplace: bool = False) -> State:
    if not inplace:
        state = state.copy()
    if get_phase(state) == Phase.GIVE:
        state[PIECE] = move  # type: ignore
    else:
        state[move] = state[PIECE]  # type: ignore
        del state[PIECE]
    return state


def get_moves(state: State) -> tuple[Piece, ...] | tuple[Square, ...]:
    if get_phase(state) == Phase.GIVE:
        return get_available(frozenset(state.values()))
    return get_free(frozenset(state.keys()))


@cache
def get_available(used: frozenset[Piece]) -> tuple[Piece, ...]:
    return tuple(sorted(PIECES.difference(used)))


@cache
def get_free(occupied: frozenset[Square]) -> tuple[Square, ...]:
    return tuple(sorted(SQUARES.difference(occupied)))


def get_winner(state: State) -> Player | None:
    if (ply := get_ply(state)) < SIDE or get_phase(state) == Phase.PUT:
        return None
    i, j = square = list(state.keys())[-1]
    if is_quarto(get_pieces(state, ROWS[i])):
        return get_plying(ply)
    if is_quarto(get_pieces(state, COLS[j])):
        return get_plying(ply)
    if square in DIAG and is_quarto(get_pieces(state, DIAG)):
        return get_plying(ply)
    if square in ADIAG and is_quarto(get_pieces(state, ADIAG)):
        return get_plying(ply)
    return None 


@cache
def is_quarto(pieces: frozenset[Piece]) -> bool:
    if len(pieces) < SIDE:
        return False
    return any(
        all(piece[i] == other[i] for piece, other in pairwise(pieces))
        for i in range(ATTRIBUTES)
    )
    

def is_over(state: State) -> bool:
    if get_ply(state) == LAST_PLY and get_phase(state) == Phase.GIVE:
        return True
    winner = get_winner(state)
    return winner is not None


def get_payoffs(state: State) -> Payoffs:
    winner = get_winner(state)
    if winner == Player.PLAYER1:
        return {Player.PLAYER1: 1, Player.PLAYER2: -1}
    elif winner == Player.PLAYER2:
        return {Player.PLAYER1: -1, Player.PLAYER2: 1}
    return {Player.PLAYER1: 0, Player.PLAYER2: 0}


def board_to_string(state: State) -> str:
    return '\n'.join(
        ' '.join(state.get((i, j), NULL_PIECE) for j in range(SIDE))
        for i in range(SIDE)
    )


def state_to_string(state: State) -> str:
    ply = get_ply(state)
    phase = get_phase(state)
    phase = 'PUT' if phase == Phase.PUT else 'GIVE'
    plying = get_plying(ply)
    plying = 'PLAYER1' if plying == Player.PLAYER1 else 'PLAYER2'
    piece = state.get(PIECE, NULL_PIECE)
    return (f"{plying=}\n"
            f"{ply=:>2d}\t{phase=}\n"
            f"{board_to_string(state)}\n"
            f"{piece=}")



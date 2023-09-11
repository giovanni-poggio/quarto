from itertools import combinations, product
import logging
from frozendict import frozendict
import numpy as np
from tqdm import tqdm
from quarto.representation.constants import SIDE

from quarto.representation.logic import PIECE, State, get_phase
from quarto.representation.move import Move
from quarto.representation.phase import Phase
from quarto.representation.piece import NULL_PIECE, Piece
from quarto.representation.square import NULL_SQUARE, Square
from quarto.mindag.board import NULL_TRANSFORM, Transform, build_board_dag, get_connectedness, map_square
from quarto.mindag.pieces import NULL_MAPPING, Mapping, build_pieces_dag, map_piece


AVAILABLE = frozendict[frozenset[Piece], tuple[Piece]]()
FREE = frozendict[frozenset[Square], tuple[Square]]()
MAPPINGS = frozendict[tuple[frozenset[Piece], Piece], Mapping]()
# TRANSFORMS = frozendict[tuple[frozenset[Square], Square], Transform]()




def play(state: State, move: Move, inplace: bool = False) -> State:
    if not inplace:
        state = state.copy()
    if isinstance(move, Piece):
        return give(state, move)
    return put(state, move)


def give(state: State, move: Piece) -> State:
    if not MAPPINGS:
        build_pieces_cache()
    key = frozenset(state.values()), move
    state[PIECE] = move
    if (mapping := MAPPINGS[key]) != NULL_MAPPING:
        logging.debug(f"{mapping=}")
        state = {square: map_piece(piece, mapping) for square, piece in state.items()}
    return state


# def put(state: State, move: Square) -> State:
#     if not TRANSFORMS:
#         build_board_cache()
#     key = frozenset(state.keys()), move
#     state[move] = state[PIECE]
#     del state[PIECE]
#     if (transform := TRANSFORMS[key]) != NULL_TRANSFORM:
#         logging.debug(f"{transform=}")
#         state = {map_square(square, transform): piece for square, piece in state.items()}
#     return state

# def put(state: State, move: Square) -> State:
#     state[move] = state[PIECE]
#     del state[PIECE]
#     return state


# def get_moves(state: State) -> tuple[Move]:
#     if get_phase(state) == Phase.GIVE:
#         return AVAILABLE[frozenset(state.values())]
#     return FREE[frozenset(state.keys())]


def build_pieces_cache():
    dag = build_pieces_dag()
    availables = dict()
    mappings = dict()
    for u in dag.nodes:
        used = dag.nodes[u]["pieces"]
        available = {}
        for _, _, data in dag.edges(u, data=True):
            piece, score = data["move"], data["score"]
            available[piece] = score
            mappings[used, piece] = data["mapping"]
        available = sorted(available, key=available.get)
        # available = sorted(available, key=available.get, reverse=True)
        availables[used] = tuple(available)
    global AVAILABLE, MAPPINGS
    AVAILABLE = frozendict(availables)
    MAPPINGS = frozendict(mappings)


# def build_board_cache():
#     dag = build_board_dag()
#     frees = dict()
#     transforms = dict()
#     for u in dag.nodes:
#         occupied = frozenset(map(tuple, np.argwhere(dag.nodes[u]["board"] == 1))) | {NULL_SQUARE}
#         free = {}
#         for _, _, data in dag.edges(u, data=True):
#             square, score = data["move"], data["score"]
#             free[square] = score
#             transforms[occupied, square] = data["transform"]
#         free = sorted(free, key=free.get, reverse=True)
#         frees[occupied] = tuple(free)
#     global FREE, TRANSFORMS
#     FREE = frozendict(frees)
#     TRANSFORMS = frozendict(transforms)


def build_board_cache():
    global FREE
    frees = {}
    tq = tqdm(total=2**(SIDE**2))
    for board in product([0, 1], repeat=SIDE**2):
        board = np.array(board).reshape((SIDE, SIDE))
        free = {}
        for i, j in np.argwhere(board == 0):
            board[i, j] = 1
            score = get_connectedness(board)
            free[i, j] = score
            board[i, j] = 0
        free = tuple(sorted(free, key=free.get, reverse=True))
        occupied = frozenset(map(tuple, np.argwhere(board == 1))).union({NULL_SQUARE})
        frees[occupied] = free
        tq.update()
    # tri = tuple(np.argwhere(np.tri(SIDE, SIDE)))
    frees[frozenset({NULL_SQUARE})] = ((0, 0), (0, 1), (1, 1))
    # for n in range(4):
    #     for combo in combinations(range(4), n):
    #         used = frozenset((i, i) for i in combo)
    #         frees.update({used: tri})
    FREE = frozendict(frees)


build_board_cache()
build_pieces_cache()
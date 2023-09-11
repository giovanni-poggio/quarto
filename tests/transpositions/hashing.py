import cProfile
from collections.abc import Hashable
from functools import cache, partial
from itertools import product
import pstats
from tqdm import tqdm

from quarto.representation._logic import State
from quarto.representation.piece import NULL_PIECE, PIECES, Piece
from quarto.representation.square import NULL_SQUARE, SQUARES, Square
from quarto.transpositions.pieces import ALL_MAPPINGS, Mapping, map_piece
from quarto.transpositions.squares import ALL_TRANSFORMATIONS, Transformation, map_square
from tests.representation import random_game


ItemMapping = tuple[Mapping, Transformation]



@cache
def map_item(item: tuple[Square, Piece], t: Transformation, m: Mapping) -> tuple[Square, Piece]:
    square, piece = item
    return map_square(square, t), map_piece(piece, m)


def base_state_to_hashable(state: State, t, m) -> frozenset[tuple[Square, Piece]]:
    return frozenset(map(lambda item: map_item(item, t, m), state.items()))


def state_to_hashable(state: State) -> Hashable:
    minimal = float('inf')
    for m, t in product(ALL_MAPPINGS, ALL_TRANSFORMATIONS):
        candidate = base_state_to_hashable(state, t, m)
        candidate = hash(candidate)
        if candidate < minimal:
            minimal = candidate
    return minimal


def load_map_items():
    total = (len(PIECES)+1)*(len(SQUARES)+1)*len(ALL_MAPPINGS)*len(ALL_TRANSFORMATIONS)
    prod = product(SQUARES|{NULL_SQUARE}, PIECES|{NULL_PIECE}, ALL_MAPPINGS, ALL_TRANSFORMATIONS)
    for s, p, m, t in tqdm(prod, total=total):
        map_item((s, p), t, m)

load_map_items()


states = [random_game(State()) for _ in range(100)]


for _ in tqdm(range(len(states))):
    state_to_hashable(State())


for state in tqdm(states):
    state_to_hashable(state)

with cProfile.Profile() as profile:
    for state in tqdm(states):
        state_to_hashable(state)
stats = pstats.Stats(profile)
stats.dump_stats('tmp.prof')
     
from collections import defaultdict
from functools import cache
from itertools import combinations, filterfalse, permutations, product
from pprint import pprint
from frozendict import frozendict
import numpy as np
import numpy.typing as npt

from quarto.compression.pieces import AVAILABLE, Mapping, get_all_mappings, map_piece
from quarto.compression.squares import FREE
from quarto.representation.constants import SIDE
from quarto.representation._logic import PIECE, State, get_moves
from quarto.representation.piece import Piece, NULL_PIECE, PIECES
from quarto.representation.square import NULL_SQUARE


@cache
def common_attributes(piece: Piece, other: Piece) -> int:
    return sum(1 for bp, bo in zip(piece, other) if bp == bo)


def test():
    assert AVAILABLE
    for used in sorted(AVAILABLE):
        available = sorted(AVAILABLE[used])
        used = sorted(used)
        if len(used) > 4 and len(used) % 2:
            continue
        print(f"{used=}\t{available=}")

        # for piece, other in product(available, used):
        #     attributes = common_attributes(piece, other)
        #     print(f"{piece=}\t{other=}\t{attributes=}")
        # input("continue")

        
# classes = equivalence_classes()
# for piece in sorted(equivalence_classes()):
#     print(f"{piece=}")
#     for n in sorted(classes[piece]):
#         cls = sorted(classes[piece][n])
#         print(f"{n=}\t{cls=}")   


test()

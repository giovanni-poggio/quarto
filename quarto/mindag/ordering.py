


from itertools import combinations
from frozendict import frozendict
from tqdm import tqdm
import scipy.stats as sps
from quarto.representation.piece import PIECES, Piece
from quarto.representation.square import Square 


AVAILABLE: frozendict[frozenset[Piece], tuple[Piece]]
FREE: frozendict[frozenset[Square], tuple[Square]]


def load_piece_cache():
    n_pieces = len(PIECES)
    tq = tqdm(total=2**n_pieces)
    availables = {frozenset(): ('0000',)}
    for k in range(1, n_pieces):
        tmp = {}
        for used in filter(lambda used: len(used) != k, availables.values()):
            remaining = PIECES.difference(used)
            for piece in remaining:
        combos = combinations(PIECES, k)
        for combo in combos:
            used = frozenset(combo)
            remaining = PIECES.difference(used)
            n0 = sum(1 for piece in used for b in piece for piece in used if b == '0')
            h0 = sps.entropy([n0, 4*k-n0])
            for piece in remaining:
                n = n0 + sum(1 for b in piece if b == '0')
                h = sps.entropy([n, 4*(k+1)*n])
                print(f"{used=}\t{piece=}\t{h0=:.3f}\t{h=}")


load_piece_cache()
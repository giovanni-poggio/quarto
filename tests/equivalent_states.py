from collections.abc import Collection, Iterable, Sequence
from collections import deque
from dataclasses import dataclass, field
from functools import cache
from itertools import permutations, product
from typing import NamedTuple
import numpy as np
import numpy.typing as npt
from tqdm import tqdm

from quarto.representation.constants import ATTRIBUTES, SIDE
from quarto.representation.piece import PIECES, Piece
from quarto.representation.square import Square


Board = npt.NDArray


def board_to_string(board: Board) -> str:
    return ''.join(map(str, board.flat))


class Transform(NamedTuple):
    flip: bool
    rotate: int


ALL_TRANSFORMS = frozenset(Transform(flip, rotate) for flip, rotate in product([False, True], range(4)))
NULL_TRANSFORM = Transform(flip=False, rotate=0)


@cache
def get_inverse(transform: Transform) -> Transform:
    return Transform(transform.flip, -transform.rotate % 4)


rotate = np.rot90
flip = np.fliplr


def transform_board(board: Board, transform: Transform) -> Board:
    if transform.flip:
        return rotate(flip(board), transform.rotate)
    return rotate(board, transform.rotate)


def get_derived(canonical: Board, transforms: Iterable[Transform] = ALL_TRANSFORMS) -> dict[Transform, Board]:
    output = {}
    unique = {board_to_string(canonical)}
    for transform in sorted(transforms):
        equivalent = transform_board(canonical, transform)
        as_string = board_to_string(equivalent)
        if as_string in unique:
            continue
        output[transform] = equivalent
        unique.add(as_string)
    return output


@dataclass(slots=True)
class BoardNode:
    canonical: Board
    equivalents: dict[Transform, Board] = field(default_factory=dict)
    parent: "BoardNode | None" = None
    children: dict[Square, "BoardNode"] = field(default_factory=dict)


def build_board_tree() -> BoardNode:
    tq = tqdm(desc="building board tree", total=2**16)
    empty_board = np.zeros((SIDE, SIDE), dtype=int)
    root = BoardNode(empty_board, get_derived(empty_board))
    to_visit = deque([root])
    explored = {board_to_string(root.canonical)}
    while to_visit:
        visiting = to_visit.popleft()
        board = visiting.canonical
        for i, j in product(range(SIDE), repeat=2):
            if board[i, j] != 0:
                continue
            new_board = board.copy()
            new_board[i, j] = 1
            as_string = board_to_string(new_board)
            if as_string in explored:
                continue
            equivalents = get_derived(new_board)
            visiting.children[(i, j)] = new_node = BoardNode(new_board, equivalents, visiting)
            for equivalent in equivalents.values():
                explored.add(board_to_string(equivalent))
            explored.add(as_string)
            to_visit.append(new_node)
            tq.update(len(equivalents)+1)
    return root


build_board_tree()


Pieces = frozenset[Piece]


def pieces_to_string(pieces: Pieces) -> str:
    return '-'.join(sorted(pieces))


class Mapping(NamedTuple):
    flip: Piece
    permute: tuple[int, ...]


ALL_MAPPINGS = frozenset(Mapping(flip, permute) for flip, permute in product(PIECES, permutations(range(ATTRIBUTES))))
NULL_MAPPING = Mapping(f"{0:0{ATTRIBUTES}b}", tuple(range(ATTRIBUTES)))


@cache
def bitflip(piece: Piece, flip: str) -> Piece:
    piece_int = int(piece, base=2)
    flip_int = int(flip, base=2)
    return f"{piece_int^flip_int:0{ATTRIBUTES}b}"


@cache
def bitpermute(piece: Piece, permute: tuple[int, ...]) -> Piece:
    return ''.join(piece[i] for i in permute)


@cache
def bitmap(piece: Piece, mapping: Mapping) -> Piece:
    return bitpermute(bitflip(piece, mapping.flip), mapping.permute)


def map_pieces(pieces: Collection[Piece], mapping: Mapping) -> Pieces:
    return Pieces(bitmap(piece, mapping) for piece in pieces)


def get_mapped(minimal: Pieces, mappings: Iterable[Mapping] = ALL_MAPPINGS) -> dict[Mapping, Pieces]:
    output = {}
    unique = {pieces_to_string(minimal)}
    for mapping in sorted(mappings):
        mapped = map_pieces(minimal, mapping)
        as_string = pieces_to_string(mapped)
        if as_string in unique:
            continue
        output[mapping] = mapped
        unique.add(as_string)
    return output


@dataclass(slots=True)
class PiecesNode:
    minimal: Pieces
    mapped: dict[Mapping, Pieces] = field(default_factory=dict)
    parent: "PiecesNode | None" = None
    children: dict[Piece, "PiecesNode"] = field(default_factory=dict)


def build_pieces_tree() -> PiecesNode:
    tq = tqdm(desc="building piece tree", total=2**16)
    null_set = frozenset()
    root = PiecesNode(null_set, get_mapped(null_set))
    to_visit = deque([root])
    explored = {pieces_to_string(root.minimal)}
    while to_visit:
        visiting = to_visit.popleft()
        used = visiting.minimal
        remaining = sorted(PIECES.difference(used))
        for piece in remaining:
            resulting = used.union({piece})
            as_string = pieces_to_string(resulting)
            if as_string in explored:
                continue
            mapped = get_mapped(resulting)
            visiting.children[piece] = new_node = PiecesNode(resulting, mapped, visiting)
            for pieces in mapped.values():
                explored.add(pieces_to_string(pieces))
            explored.add(as_string)
            to_visit.append(new_node)
            tq.update(len(mapped)+1)
    return root


build_pieces_tree()
exit()


# def pieces_equivalents(pieces: Collection[Piece]) -> set[frozenset[Piece]]:
#     output = set()
#     for flip, permute in product(PIECES, permutations(range(ATTRIBUTES))):
#         output.add(map_pieces(pieces, flip, permute))
#     return output


# def pieces_to_string(pieces: Collection[Piece]) -> str:
#     return '-'.join(sorted(pieces))


# def unique_piece_sets() -> dict[frozenset[Piece], frozenset[Piece]]:
#     to_visit = deque([frozenset()])
#     as_strings = set()
#     visited = {}
#     while to_visit:
#         previous = to_visit.popleft()
#         remaining = PIECES.difference(previous)
#         unique = set()
#         for piece in sorted(remaining):
#             current = previous.union({piece})
#             as_string = pieces_to_string(current)
#             if as_string in as_strings:
#                 continue
#             equivalents = pieces_equivalents(current)
#             for pieces in sorted(equivalents):
#                 as_string = pieces_to_string(pieces)
#                 as_strings.add(as_string)
#             to_visit.append(current)
#         visited[previous] = frozenset(unique)
#     return visited



# sets_stats = defaultdict(int)
# sets = unique_piece_sets()
# print("DISTINCT PIECE SETS")
# for used, unique in sets.items():
#     print(sorted(used), sorted(unique))
#     input("continue")
#     n_used = len(used) 
#     sets_stats[n_used] += 1
# for n_pieces, n_sets in sets_stats.items():
#     print(f"{n_pieces=}\t{n_sets=}")
# total = sum(sets_stats.values())
# print(f"{total=}")


# boards_stats = defaultdict(int)
# boards = unique_placements()
# print("UNIQUE PLACEMENTS of INDISTINGUSHABLE PIECES")
# for board in boards:
#     # print(board)
#     # print('-'*80)
#     boards_stats[np.sum(board)] += 1
# for n_pieces, placements in boards_stats.items():
#     print(f"{n_pieces=}\t{placements=}")
# total = sum(boards_stats.values())
# print(f"{total=}")


# print("PRODUCT")
# prod_stats = {}
# for s, b in zip(sets_stats, boards_stats):
#     assert s == b
#     n_pieces = s
#     n_sets, n_boards = sets_stats[n_pieces], boards_stats[n_pieces]
#     prod = n_sets * n_boards
#     print(f"{n_pieces=}\t{n_sets=}\t{n_boards=}\t{prod}")
#     prod_stats[n_pieces] = prod
# total = sum(prod_stats.values())
# print(f"{total=}")
# exit()


# def unique_sorted_placements(to_visit: Iterable[Board]):
#     as_strings = set()
#     visited = list()
#     tq = tqdm(to_visit)
#     for visiting in tq:
#         n_pieces = np.sum(visiting)
#         tq.set_description(f"{n_pieces=}")
#         # print(f"visiting=\n{visiting}")
#         ones = sorted(map(tuple, np.argwhere(visiting == 1)))
#         # print(f"{ones=}")
#         for sorting in permutations(ones):
#             current = visiting.copy()
#             for k, (i, j) in enumerate(sorting):
#                 current[i, j] = k+1
#             # print(f"current=\n{current}")
#             as_string = board_to_string(current)
#             # print(f"{as_string=}")
#             if as_string in as_strings:
#                 # print("NOT UNIQUE")
#                 continue
#             for board in board_equivalents(current):
#                 as_strings.add(board_to_string(board))
#             visited.append(current)
#     return visited


# boards_stats = defaultdict(int)
# boards = unique_placements()
# print("UNIQUE PLACEMENTS of N 1's")
# for board in boards:
#     # print(board)
#     # print('-'*80)
#     boards_stats[np.sum(board)] += 1
# for n_pieces, placements in boards_stats.items():
#     print(f"{n_pieces=}\t{placements=}")
# total = sum(boards_stats.values())
# print(f"{total=}")


# boards_stats = defaultdict(int)
# boards = unique_sorted_placements(boards)
# for board in boards:
#     # print(board)
#     # print('-'*80)
#     boards_stats[np.sum(board)] += 1
# print("UNIQUE PLACEMENTS of 1-N")
# for n_pieces, placements in boards_stats.items():
#     print(f"{n_pieces=}\t{placements=}")
# total = sum(boards_stats.values())
# print(f"{total=}")


# exit()


# def bfs2():
#     to_visit = deque([np.zeros((SIDE, SIDE), dtype=int)])
#     unique = set()
#     visited = defaultdict(list)
#     while to_visit:
#         board = to_visit.popleft()
#         k = np.max(board) + 1
#         for i, j in product(range(SIDE), repeat=2):
#             if board[i, j] != 0:
#                 continue
#             copy = board.copy()
#             copy[i, j] = k
#             # bin = np.zeros((SIDE, SIDE), dtype=int)
#             # bin[copy != 0] = 1
#             str = board_to_string(copy)
#             if str in unique:
#                 continue
#             for b in board_equivalents(copy):
#                 unique.add(board_to_string(b))
#             to_visit.append(copy)
#         k = np.sum(board != 0)
#         visited[k].append(board)
#     return visited


# def bfs3():
#     to_visit = bfs2()
#     unique = set()
#     for n in sorted(to_visit):
#         print(f"{n=}")
#         boards = to_visit[n] 
#         for board in boards:
#             tmp = np.full((SIDE, SIDE), NULL_PIECE)
#             fill(tmp, board, unique)


# def fill(tmp: Board, board: Board, unique: set[str]):
#     assert AVAILABLE
#     mask = tmp != NULL_PIECE
#     used = frozenset(tmp[mask])
#     k = np.sum(mask)
#     if k+1 not in board or used not in AVAILABLE:
#         print(tmp)
#         str = board_to_string(tmp)
#         if str in unique:
#             print(f"NOT UNIQUE" + '-' * 70)
#             input("continue")
#             return
#         for b in board_equivalents(tmp):
#             unique.add(board_to_string(b))
#         print('-' * 80)
#         input("continue")
#         return
#     for piece in sorted(AVAILABLE[used]):
#         tmp[board == k+1] = piece
#         fill(tmp, board, unique)
#         tmp[board == k+1] = NULL_PIECE


# for n, bs in bfs2().items():
#     print(f"{n=}\t{len(bs)=}")
# input("continue")
# bfs3()

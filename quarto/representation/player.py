from enum import IntFlag, auto


class Player(IntFlag):
    PLAYER1 = 0
    PLAYER2 = auto()


def get_plying(ply: int) -> Player:
    return Player(ply % 2)


def get_plyed(ply: int) -> Player:
    return Player((ply + 1) % 2)

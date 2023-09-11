from dataclasses import dataclass, field
from quarto.representation.logic import Payoffs, State, Player, Move, get_ply, get_plying, is_over, get_winner, play
from quarto.mcts.cumdict import cumdict, normalize


@dataclass(slots=True)
class Node:
    state: State
    plying: Player
    game_over: bool
    winner: Player | None
    
    depth: int = 0
    parent: "Node | None" = None
    children: dict[Move, "Node"] = field(init=False, default_factory=dict)

    payoffs: cumdict[Player, float] = field(init=False, default_factory=cumdict)
    visits: int = field(init=False, default=0)

    fully_expanded: bool = field(init=False, default=False)


def get_root(state: State) -> Node:
    plying = get_plying(get_ply(state))
    game_over = is_over(state)
    winner = None if not game_over else get_winner(state)
    return Node(state, plying, game_over, winner)


def get_child(parent: Node, move: Move) -> Node:
    state = play(parent.state, move)
    plying = get_plying(get_ply(state))
    game_over = is_over(state)
    winner = None if not game_over else get_winner(state)
    child = Node(state, plying, game_over, winner, parent.depth+1, parent)
    parent.children[move] = child
    return child


def back_propagate(node: Node, payoffs: Payoffs):
    while True:
        node.payoffs.update(payoffs)
        node.visits += 1
        if node.parent is None:
            break
        node = node.parent


def node_to_string(node: Node) -> str:
    return (f"{normalize(node.payoffs, node.visits)=}")

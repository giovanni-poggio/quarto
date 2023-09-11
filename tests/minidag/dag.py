from collections.abc import Iterable, Mapping
from collections import deque
import logging
from typing import Any, Callable, NamedTuple, Protocol
from matplotlib import pyplot as plt
import networkx as nx
from tqdm import tqdm


Label = str
   

class Node(NamedTuple):
    label: Label
    data: Mapping[str, Any]


Move = Any


class NodeFactory(Protocol):

    def __call__(self, parent: Node | None = None, move: Move | None = None) -> Node: ...


MovesGetter = Callable[[Node], Iterable[Move]]
Transform = Any
TransformGetter = Callable[[Node], tuple[str, Transform]]


def build_dag(get_node: NodeFactory, get_moves: Callable[[Node], Any],
              get_transform: TransformGetter, n: int | None = None) -> nx.DiGraph:
    tq = tqdm(total=n)
    root = get_node()
    to_visit = deque[Node]([root])
    explored: set[Label] = {root.label}
    dag = nx.DiGraph()
    dag.add_node(root.label, **root.data)
    while to_visit:
        visiting = to_visit.popleft()
        logging.debug(f"{visiting.label=}")
        for move in get_moves(visiting):
            new_node = get_node(visiting, move)
            logging.debug(f"{new_node.label=}")
            dag.add_node(new_node.label, **new_node.data)
            dag.add_edge(visiting.label, new_node.label, move=move)
            if new_node.label in explored:
                continue
            if new_node.data["canonical"]:
                logging.debug(f"CANONICAL")
                to_visit.append(new_node)
            else:
                canonical_label, transform = get_transform(new_node)
                dag.add_edge(new_node.label, canonical_label, transform=transform)
                logging.debug(f"{canonical_label=}")
                logging.debug(f"{transform=}")
            explored.add(new_node.label)
            tq.n = new_node.data["depth"]
            tq.refresh()
    return dag


def build_min_dag(get_node: NodeFactory, get_moves: Callable[[Node], Any],
                  get_transform: TransformGetter, n: int | None = None) -> nx.DiGraph:
    tq = tqdm(total=n)
    root = get_node()
    to_visit = deque[Node]([root])
    explored: set[Label] = {root.label}
    dag = nx.DiGraph()
    dag.add_node(root.label, **root.data)
    while to_visit:
        visiting = to_visit.popleft()
        logging.debug(f"{visiting.label=}")
        for move in get_moves(visiting):
            new_node = get_node(visiting, move)
            logging.debug(f"{new_node.label=}")
            dag.add_node(new_node.label, **new_node.data)
            dag.add_edge(visiting.label, new_node.label, move=move)
            if new_node.label in explored:
                continue
            if new_node.data["canonical"]:
                logging.debug(f"CANONICAL")
                to_visit.append(new_node)
            else:
                canonical_label, transform = get_transform(new_node)
                dag.add_edge(new_node.label, canonical_label, transform=transform)
                logging.debug(f"{canonical_label=}")
                logging.debug(f"{transform=}")
            explored.add(new_node.label)
            tq.n = new_node.data["depth"]
            tq.refresh()
    return dag


def plot_dag(dag: nx.DiGraph, block: bool = False):
    _, ax = plt.subplots()
    pos = nx.multipartite_layout(dag, subset_key="depth")
    plot_nodes(dag, pos, ax)
    plot_edges(dag, pos, ax)
    plt.show(block=block)


def plot_nodes(dag: nx.DiGraph, pos: Mapping, ax: plt.Axes):
    colors = ['tab:green' if data["canonical"] else 'tab:orange' for _, data in dag.nodes(data=True)]
    nx.draw_networkx_nodes(dag, pos, node_shape='s', node_color=colors, edgecolors='black', ax=ax)
    nx.draw_networkx_labels(dag, pos, font_size=6, ax=ax)


def plot_edges(dag: nx.DiGraph, pos: Mapping, ax: plt.Axes):
    labels = {}
    styles = []
    nodes_data = {label: data for label, data in dag.nodes(data=True)}
    for u, v, data in dag.edges(data=True):
        label = []
        if (move := data.get("move")):
            label.append(str(move))
            if nodes_data[v]["canonical"]:
                styles.append('-')
            else:
                styles.append('--')
        if (transform := data.get("transform")):
            label.append(str(transform))
            styles.append(':')
        labels[u, v] = '\n'.join(label)
    nx.draw_networkx_edges(dag, pos, style=styles, ax=ax)
    nx.draw_networkx_edge_labels(dag, pos, labels,  font_size=6, ax=ax)


def get_canonical_out_edges():
    pass


def dag_stats(dag: nx.DiGraph, n: int):
    canonical_nodes = {label for label, data in dag.nodes(data=True) if data["canonical"]}

    maximum = 2**n
    total = dag.number_of_nodes()
    canonical = len(canonical_nodes)
    compression = maximum / canonical
    saved = (1 - canonical / maximum) * 100
    logging.warning("NODES")
    logging.warning(f"{canonical=:,}\t/\t{total=:,}\t/\t{maximum=:,}")
    logging.warning(f"{saved=:.1f}%\t\t{compression=:.1f}x")

    maximum = 2**(n - 1) * n
    total = dag.number_of_edges()
    canonical = sum(1 for u, _ in dag.edges if u in canonical_nodes)
    compression = maximum / canonical
    saved = (1 - canonical / maximum) * 100
    logging.warning("OUT EDGES")
    logging.warning(f"{canonical=:,}\t/\t{total=:,}\t/\t{maximum=:,}")
    logging.warning(f"{saved=:.1f}%\t\t{compression=:.1f}x")



from collections.abc import Iterable, Mapping
from collections import deque
from dataclasses import dataclass, field
import logging
from typing import Any, Protocol
from matplotlib import pyplot as plt
import networkx as nx
from tqdm import tqdm


@dataclass(slots=True, eq=True)
class Node:
    label: str
    data: Mapping[str, Any] = field(default_factory=dict, compare=False)

    def __hash__(self) -> int:
        return hash(self.label)


class ChildrenGetter(Protocol):
    def __call__(self, parent: Node) -> Iterable[tuple[Node, Mapping[str, Any]]]: ...


def build_min_dag(root: Node, get_children: ChildrenGetter, subset_key: str | None = None,
                  last_subset: int | None = None) -> nx.DiGraph:
    tq = tqdm(total=last_subset)
    to_visit = deque[Node]([root])
    explored = set[Node]()
    dag = nx.DiGraph()
    while to_visit:
        visiting = to_visit.popleft()
        logging.debug(visiting)
        dag.add_node(visiting.label, **visiting.data)
        for child, edge_data in get_children(visiting):
            logging.debug(child)
            logging.debug(edge_data)
            dag.add_edge(visiting.label, child.label, **edge_data)
            if child in explored:
                continue
            explored.add(child)
            to_visit.append(child)
        if subset_key is not None:
            tq.n = visiting.data[subset_key]
            tq.refresh()
        else:
            tq.update()
    return dag


def plot_dag(dag: nx.DiGraph):
    pos = nx.multipartite_layout(dag, subset_key="depth")
    nx.draw(dag, pos)
    nx.draw_networkx_labels(dag, pos)
    labels = {(u, v): data["label"] for u, v, data in dag.edges(data=True)}
    nx.draw_networkx_edge_labels(dag, pos, labels)
    plt.show()


def dag_stats(dag: nx.DiGraph, n: int):
    maximum = 2**n
    total = dag.number_of_nodes()
    compression = maximum / total
    saved = (1 - total / maximum) * 100
    logging.warning("NODES")
    logging.warning(f"{total=:,}\t/\t{maximum=:,}")
    logging.warning(f"{saved=:.1f}%\t\t{compression=:.1f}x")

    maximum = 2**(n - 1) * n
    total = dag.number_of_edges()
    compression = maximum / total
    saved = (1 - total / maximum) * 100
    logging.warning("OUT EDGES")
    logging.warning(f"{total=:,}\t/\t{maximum=:,}")
    logging.warning(f"{saved=:.1f}%\t\t{compression=:.1f}x")

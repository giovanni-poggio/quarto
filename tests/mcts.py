import concurrent.futures as cf
import cProfile
import logging
import pstats
import time
from typing import Callable

from quarto.representation.logic import State
from quarto.solver.dummy_executor import DummyExecutor
from quarto.solver.expand import Expand
from quarto.solver.node import Node
from quarto.solver.simulate import BatchSimulator
from quarto.solver.stoppers import MaxTime
from quarto.solver.search import MCTS


def timing(f: Callable[[State], Node]) -> float:
    logging.info("TIMING")
    start = time.perf_counter()
    root = f(State())
    elapsed = time.perf_counter() - start
    logging.info(f"DONE")
    logging.info(f"{root.payoffs=}")
    itps = root.visits / elapsed
    logging.info(f"{root.visits=:,d}\t{elapsed=:.3f} s\t({itps:.3f} it / s)")
    return itps


def profile_functions(f: Callable[[State], Node]):    
    logging.info("Profiling MCTS")
    with cProfile.Profile() as profile:
        f(State())
    path = __file__.replace('.py', '_fn.prof')
    stats = pstats.Stats(profile)
    stats.dump_stats(path)
    logging.info(f"done: profile @ {path}")


def thue_morse_timing(f0: Callable[[State], Node], f1: Callable[[State], Node], log2_rounds: int = 3):
    seq = [0, 1]
    for _ in range(log2_rounds-1):
        seq += [n ^ 1 for n in seq]
    logging.info(seq)
    f = {0: f0, 1: f1}
    lists = {0: [], 1: []}
    n = len(seq)
    for k, i in enumerate(seq):
        logging.info(f"{k+1} / {n}")
        lists[i].append(timing(f[i]))
    n //= 2
    for i in [0, 1]:
        avg = sum(lists[i]) / n
        logging.info(f"{f[i]}\t{avg}")


def test_parallelism(max_time: float = 5, expand_n: int = 1, n_sims: int = 1):
    logging.info("=" * 80)
    logging.info(f"{max_time=}\t{expand_n=}\t{n_sims=}")
    stop = MaxTime(max_time)
    expand = Expand(expand_n)
    mcts = MCTS(DummyExecutor(), stop, expand=expand)

    mcts.simulate = BatchSimulator(DummyExecutor(), n_sims)
    logging.info(f"DummyExecutor's")
    timing(mcts.search)

    with cf.ThreadPoolExecutor() as mcts_pool, cf.ThreadPoolExecutor() as sim_pool:
        mcts.executor = mcts_pool
        mcts.simulate = BatchSimulator(sim_pool, n_sims)
        logging.info(f"ThreadPoolExecutor's")
        timing(mcts.search)
        
    with cf.ThreadPoolExecutor() as mcts_pool, cf.ProcessPoolExecutor() as sim_pool:
        mcts.executor = mcts_pool
        mcts.simulate = BatchSimulator(sim_pool, n_sims)
        logging.info(f"ThreadPoolExecutor +  ProcessPoolExecutor")
        timing(mcts.search)


def main():
    logging.basicConfig(level=logging.DEBUG)
    # thue_morse_timing()
    # profile_functions()
    # profile_classes()
    test_parallelism()
    test_parallelism(expand_n=16)
    test_parallelism(n_sims=64)
    test_parallelism(expand_n=16, n_sims=64)


if __name__ == "__main__":
    main()

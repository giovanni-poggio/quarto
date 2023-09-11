from collections.abc import Collection
from dataclasses import dataclass
from typing import Callable
import threading
import time


StopF = Callable[[int], bool]


@dataclass(slots=True)
class MaxTime:
    max_time: float
    start: float = float('-inf')

    def __call__(self, iteration: int) -> bool:
        if iteration == 0:
            self.start = time.perf_counter()
        return time.perf_counter() - self.start >= self.max_time
    

@dataclass(slots=True)
class MaxIters:
    max_iterations: int

    def __call__(self, iteration: int) -> bool:
        return iteration >= self.max_iterations


@dataclass(slots=True)
class Asynchronous:
    stop: threading.Event

    def __call__(self, _: int) -> bool:
        return self.stop.is_set()


@dataclass(slots=True)
class FirstOf:
    stops: Collection[StopF]

    def __call__(self, iteration: int) -> bool:
        return any(stop(iteration) for stop in self.stops)

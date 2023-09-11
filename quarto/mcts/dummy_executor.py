from collections.abc import Callable, Iterable, Iterator
from concurrent.futures._base import Future
from typing import Any, Callable, ParamSpec, TypeVar
import concurrent.futures as cf


_T = TypeVar('_T')
_P = ParamSpec('_P')


class DummyExecutor(cf.Executor):

    def map(self, fn: Callable[..., _T], *iterables: Iterable[Any],
            timeout: float | None = None, chunksize: int = 1) -> Iterator[_T]:
        del timeout, chunksize
        return map(fn, *iterables)

    def submit(self, __fn: Callable[_P, _T], *args: _P.args, **kwargs: _P.kwargs) -> Future[_T]:
        return super().submit(__fn, *args, **kwargs)
    
    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        return super().shutdown(wait, cancel_futures=cancel_futures)

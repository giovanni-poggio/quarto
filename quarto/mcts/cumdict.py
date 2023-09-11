from collections import defaultdict
from collections.abc import Hashable, Mapping, MutableMapping
from typing import Any, Callable, ItemsView, Iterator, KeysView, Protocol, TypeVar, ValuesView
import fractions

class SupportsAdd(Protocol):

    def __add__(self, __value: "SupportsAdd") -> "SupportsAdd": ...


K = TypeVar('K', bound=Hashable)
V = TypeVar('V', int, float, complex, fractions.Fraction, list, tuple, SupportsAdd)


class cumdict(MutableMapping[K, V]):
    __data: defaultdict[K, V]

    def __init__(self, __default_factory: Callable[[], V] = float):
        self.__data = defaultdict[K, V](__default_factory)
        super().__init__()

    def __getitem__(self, __key: K) -> V:
        return self.__data[__key]
    
    def __setitem__(self, __key: K, __value: V) -> None:
        self.__data[__key] += __value

    def keys(self) -> KeysView[K]:
        return self.__data.keys()
    
    def values(self) -> ValuesView[V]:
        return self.__data.values()
    
    def items(self) -> ItemsView[K, V]:
        return self.__data.items()
    
    def update(self, __other: Mapping[K, V]):
        for key, value in __other.items():
            self.__data[key] += value

    def __delitem__(self, __key: K) -> None:
        del self.__data[__key]

    def __iter__(self) -> Iterator[K]:
        return self.__data.__iter__()
    
    def __len__(self) -> int:
        return self.__data.__len__()

    def __str__(self) -> str:
        return str(dict(self.__data))

    def __repr__(self) -> str:
        return repr(dict(self.__data))
    
    def to_dict(self) -> dict[K, V]:
        return dict(self.__data)
    

class SupportsAddAndIntTrueDiv(SupportsAdd, Protocol):

    def __truediv__(self, __value: int) -> Any: ...


D = TypeVar('D', int, float, complex, fractions.Fraction, SupportsAddAndIntTrueDiv)
    

def normalize(cd: cumdict[K, D], n: int) -> dict[K, Any]:
    return {key: value / n for key, value in cd.items()}

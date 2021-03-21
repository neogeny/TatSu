# from https://github.com/LuminosoInsight/ordered-set/blob/master/ordered_set.py
# removed Sequence behavior
import itertools
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    MutableSet,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
)

T = TypeVar("T")

def _is_atomic(obj: Any) -> bool:
    return isinstance(obj, str) or isinstance(obj, tuple)


class OrderedSet(MutableSet[T]):
    def __init__(self, iterable: Optional[Iterable[T]] = None):
        if iterable is not None:
            self._map = dict.fromkeys(iterable)
        else:
            self._map = {}  # type: Dict[T, int]

    def __len__(self):
        return len(self._map)

    def copy(self) -> "OrderedSet[T]":
        return self.__class__(self)

    def __getstate__(self):
        if len(self) == 0:
            return (None,)
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key: Any) -> bool:
        return key in self._map

    def add(self, key: T):
        self._map[key] = len(self._map)

    def update(self, sequence: Iterable[T]):
        self._map.update(dict.fromkeys(sequence))

    def pop(self) -> T:
        key = next(iter(self._map.keys()))
        self._map.pop(key)
        return key

    def discard(self, key: T):
        self._map.pop(key, None)

    def clear(self):
        self._map = {}

    def __iter__(self) -> Iterator[T]:
        return iter(self._map.keys())

    def __repr__(self) -> str:
        return "{%s}" % ', '.join(repr(e) for e in self)

    def __eq__(self, other: Set) -> bool:
        return all(item in other for item in self)

    def union(self, *other: Iterable[T]) -> "OrderedSet[T]":
        cls = self.__class__ if isinstance(self, OrderedSet) else OrderedSet
        items = itertools.chain.from_iterable(itertools.chain([self], *other))
        return cls(itertools.chain(items))

    def __and__(self, other: Union[Sequence[T], Set[T]]) -> "OrderedSet[T]":
        return self.intersection(other)

    def intersection(self, *other: Iterable[T]) -> "OrderedSet[T]":
        cls = self.__class__ if isinstance(self, OrderedSet) else OrderedSet
        common = set.intersection(*other)
        items = (item for item in self if item in common)
        return cls(items)

    def difference(self, *other: Iterable[T]) -> "OrderedSet[T]":
        cls = self.__class__
        other = set.union(*other)
        items = (item for item in self if item not in other)
        return cls(items)

    def issubset(self, other: Set[T]) -> bool:
        return all(item in other for item in self)

    def issuperset(self, other: Set[T]) -> bool:
        if len(self) < len(other):  # Fast check for obvious cases
            return False
        return all(item in self for item in other)

    def symmetric_difference(self, other: Set[T]) -> "OrderedSet[T]":
        cls = self.__class__ if isinstance(self, OrderedSet) else OrderedSet
        diff1 = cls(self).difference(other)
        diff2 = cls(other).difference(self)
        return diff1.union(diff2)

    def difference_update(self, *other: Union[Sequence[T], Set[T]]):
        self._map = dict.fromkeys(self.difference(*other))

    def intersection_update(self, other: Union[Sequence[T], Set[T]]):
        self._map = dict.fromkeys(self.intersection(*other))

    def symmetric_difference_update(self, other: Union[Sequence[T], Set[T]]):
        self._map = dict.fromkeys(self.difference(*other))

from typing import Any


class BoundedDict[KT, VT](dict[KT, VT]):
    def __init__(self, capacity: int, *args: Any, **kwargs: Any) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity: int = capacity
        super().__init__(*args, **kwargs)
        self._enforce_limit()

    def __setitem__(self, key: KT, value: VT) -> None:
        # If the key exists, delete it first to update its position
        # to "most recent" (standard LRU/Bounded behavior)
        if key in self:
            del self[key]

        super().__setitem__(key, value)
        self._enforce_limit()

    # The base update() doesn't always call __setitem__,
    # so we override it to ensure limits are respected.
    def update(self, other, /, **kwargs):  # type: ignore
        super().update(other, **kwargs)
        self._enforce_limit()

    def _enforce_limit(self):
        while len(self) > self.capacity:
            # iter(self) returns keys in insertion order.
            # next() gets the first (oldest) key.
            oldest_key = next(iter(self))
            del self[oldest_key]

    def __repr__(self) -> str:
        return f"{super().__repr__()}[{self.capacity}]"

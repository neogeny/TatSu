class BoundedDict(dict):
    """
    A dictionary that inherits from the base dict class and
    maintains a maximum size by evicting the oldest items.
    """

    def __init__(self, capacity: int, *args, **kwargs):
        if capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")
        self.capacity = capacity
        # Initialize the base dict with any provided arguments
        super().__init__(*args, **kwargs)
        self._enforce_limit()

    def __setitem__(self, key, value):
        # If the key exists, delete it first to update its position
        # to "most recent" (standard LRU/Bounded behavior)
        if key in self:
            del self[key]

        super().__setitem__(key, value)
        self._enforce_limit()

    def update(self, *args, **kwargs):
        # The base update() doesn't always call __setitem__,
        # so we override it to ensure limits are respected.
        super().update(*args, **kwargs)
        self._enforce_limit()

    def _enforce_limit(self):
        while len(self) > self.capacity:
            # iter(self) returns keys in insertion order.
            # next() gets the first (oldest) key.
            oldest_key = next(iter(self))
            del self[oldest_key]

    def __repr__(self):
        return f"{super().__repr__()}[{self.capacity}]"

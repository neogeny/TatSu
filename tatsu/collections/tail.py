from collections.abc import MutableSequence
from collections import deque


class Tail(MutableSequence):
    def __init__(self, maxlen):
        self._tail = deque(maxlen=maxlen)
        self._start = 0

    @property
    def start(self):
        return self._start

    def tailfull(self):
        return len(self._tail) == self._tail.maxlen

    def insert(self, index, value):
        if self.tailfull():
            self._tail.popleft()
            self._start += 1
        self._tail.insert(index - self._start, value)

    def flush(self):
        self._start += len(self._tail)
        self._tail = deque(maxlen=self._tail.maxlen)

    def __getitem__(self, index):
        return self._tail[index - self._start]

    def __setitem__(self, index, value):
        self._tail[index - self._start] = value

    def __delitem__(self, index):
        del self._tail[index - self._start]

    def __len__(self):
        return len(self._tail) + self._start

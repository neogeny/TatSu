from collections.abc import MutableSequence
from collections import deque


class Tail(MutableSequence):
    def __init__(self, maxlen):
        self._tail = deque(maxlen=maxlen)
        self._start = 0

    def _tailfull(self):
        return len(self._tail) == self._tail.maxlen

    @property
    def start(self):
        return self._start

    def insert(self, i, x):
        if self._tailfull():
            self._tail.popleft()
            self._start += 1
        self._tail.insert(i - self._start, x)

    def flush(self):
        self._start += len(self._tail)
        self._tail = deque(maxlen=self._tail.maxlen)

    def __getitem__(self, i):
        return self._tail[i - self._start]

    def __setitem__(self, i, x):
        self._tail[i - self._start] = x

    def __delitem__(self, i):
        del self._tail[i - self._start]

    def __len__(self):
        return len(self._tail) + self._start

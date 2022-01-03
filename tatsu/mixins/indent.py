from __future__ import annotations

from contextlib import contextmanager


class IndentPrintMixin:
    def __init__(self):
        self._indent_level = 0

    @contextmanager
    def indent(self):
        self._indent_level += 1
        try:
            yield
        finally:
            self._indent_level -= 1

    def print(self, text: str = ''):
        indentation = ' ' * 4 * self._indent_level
        print((indentation + text).rstrip())

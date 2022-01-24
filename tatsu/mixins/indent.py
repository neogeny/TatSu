from __future__ import annotations

import sys
import io
from contextlib import contextmanager

from ..util import trim


class IndentPrintMixin:
    def __init__(self, indent=4):
        self.indent_amount = indent
        self.indent_level = 0
        self.output_stream = sys.stdout

    @property
    def current_indentation(self):
        return ' ' * self.indent_amount * self.indent_level

    @contextmanager
    def indent(self):
        self.indent_level += 1
        try:
            yield
        finally:
            self.indent_level -= 1

    def _do_print(self, line: str = ''):
        print((self.current_indentation + line).rstrip(), file=self.output_stream)

    def print(self, *args, **kwargs):
        kwargs.pop('file', None)  # do not allow redirection of output
        with io.StringIO() as output:
            print(*args, file=output, **kwargs)
            text = output.getvalue()
        text = trim(text)
        lines = text.splitlines(keepends=True)
        if not lines:
            self._do_print()
        else:
            for line in lines:
                self._do_print(line)

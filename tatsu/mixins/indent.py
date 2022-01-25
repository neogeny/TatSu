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

    def print(self, *args, **kwargs):
        lines = self.as_printed_lines(*args, **kwargs)
        self._do_print_lines(lines)

    def as_printed(self, *args, **kwargs):
        lines = self.as_printed_lines(*args, **kwargs)
        return '\n'.join(lines)

    def as_printed_lines(self, *args, **kwargs):
        text = self.io_print(*args, **kwargs)
        return self.indented_lines(text)

    @contextmanager
    def indent(self):
        self.indent_level += 1
        try:
            yield
        finally:
            self.indent_level -= 1

    @property
    def current_indentation(self):
        return ' ' * self.indent_amount * self.indent_level

    @staticmethod
    def io_print(*args, **kwargs):
        kwargs.pop('file', None)  # do not allow redirection of output
        with io.StringIO() as output:
            print(*args, file=output, **kwargs)
            text = output.getvalue()
        return text

    def _do_print_lines(self, lines: list[str] = None):
        if not lines:
            print(file=self.output_stream)
            return

        for line in lines:
            print(line, file=self.output_stream)

    def indented_lines(self, text):
        text = trim(text)
        return [
            (self.current_indentation + line).rstrip()
            for line in text.splitlines(keepends=False)
        ]

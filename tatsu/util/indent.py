# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import io
import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from tatsu.util import isiter, notnone
from tatsu.util.strtools import trim

BLACK_LINE_LENGTH = 88


__all__ = ['IndentPrintMixin', 'fold']


class IndentPrintMixin:
    def __init__(self, amount: int = 4, initial: int = 0):
        self.amount = amount
        self.indent_stack: list[int] = [initial]
        self.output_stream = io.StringIO()

    def clear(self):
        self.__init__(amount=self.amount)

    def printed_text(self):
        return self.output_stream.getvalue()

    def print(self, *args, **kwargs):
        args = [trim(str(arg)) for arg in args if arg is not None]
        lines = self.as_printed_lines(*args, **kwargs)
        self._do_print_lines(lines, **kwargs)

    def as_printed(self, *args, **kwargs) -> str:
        lines = self.as_printed_lines(*args, **kwargs)
        return '\n'.join(lines)

    def as_printed_lines(self, *args, **kwargs) -> list[str]:
        text = self.io_print(*args, **kwargs)
        return self.indented_lines(text)

    def fitsfmt(self, line: str, addlevels: int = 1):
        assert addlevels >= 0
        if re.search(r"(?m)[\r\n]", line):
            return False
        total = self.indentation + len(line)
        total += addlevels * self.amount
        return total <= BLACK_LINE_LENGTH

    def prefixlen(self, addindents: int = 0):
        return addindents * self.amount + self.indentation

    @contextmanager
    def indent(self, amount: int = -1, levels: int = 1) -> Iterator:
        assert amount < 0 or amount > 0
        amount = amount if amount > 0 else self.amount

        self.indent_stack.append(amount * levels + self.indent_stack[-1])
        try:
            yield
        finally:
            self.indent_stack.pop()

    @property
    def indentation(self) -> int:
        return self.indent_stack[-1]

    @property
    def indentstr(self) -> str:
        return ' ' * self.indentation

    @staticmethod
    def io_print(*args, **kwargs) -> str:
        kwargs.pop('file', None)  # do not allow redirection of output
        with io.StringIO() as output:
            print(*args, file=output, **kwargs)
            return output.getvalue()

    def _do_print_lines(self, lines: list[str] | None = None, **kwargs):
        if not lines:
            print(file=self.output_stream, **kwargs)
            return

        for line in lines:
            print(line, file=self.output_stream, **kwargs)

    def indented_lines(self, text: str) -> list[str]:
        text = trim(text)
        return [
            (self.indentstr + line).rstrip() for line in text.splitlines(keepends=False)
        ]


def fold(
    prefix: str,
    value: Any,
    *,
    reprs: bool = True,
    addlevels: int = 0,
    lbrack: str | None = None,
    rbrack: str | None = None,
    amount: int = 2,
    initial: int = 0,
) -> str:
    brackets = {
        dict: ('{', '}'),
        list: ('[', ']'),
        tuple: ('(', ')'),
        None: ('', ''),
    }
    lb, rb = brackets.get(type(value), ('', ''))
    lbrack = notnone(lbrack, lb)
    rbrack = notnone(rbrack, rb)
    assert lbrack is not None and rbrack is not None

    def tostr(s: Any) -> str:
        if isinstance(s, str):
            return s
        return repr(s)

    im = IndentPrintMixin(amount=amount, initial=initial)
    if not isiter(value):
        im.print(f'{prefix}{lbrack}{value!r}{rbrack}')
        return im.printed_text().rstrip()

    if isinstance(value, dict):
        repr_list = [
            f'{(reprs and repr(k)) or k}: {(reprs and repr(v)) or v}'
            for k, v in value.items()
        ]
    elif reprs:
        repr_list = [repr(v) for v in value]
    else:
        repr_list = value

    valuestr = f'{prefix}{lbrack}{', '.join(repr_list)}{rbrack}'
    if im.fitsfmt(valuestr, addlevels=addlevels):
        im.print(valuestr)
    else:
        im.print(f'{prefix}{lbrack}')
        with im.indent():
            im.print(',\n'.join(repr_list))
        im.print(rbrack)
    return im.printed_text().rstrip()

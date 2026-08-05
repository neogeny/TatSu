# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from functools import cached_property
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from .base import Leaf
from .math import ffset


EOF_SYM = '$'
EOL_SYM = '⏎'

# Words that the `literal` rule in the constant syntax evaluates to
# non-string values (booleans, None, and the JSON names).
_LITERAL_KEYWORDS = frozenset(
    {'True', 'False', 'None', 'true', 'false', 'null'},
)

# Bodies that the '`' =literal '`' alternative of the `constant` rule would
# consume whole and evaluate, so writing them bare would not read back as
# the original string (see grammar/tatsu.ebnf).
_LITERAL_LOOKALIKES = (
    re.compile(r'[-+]?\d+'),  # int
    re.compile(r'[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[Ee][-+]?\d+)?'),  # float
    re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?'),  # number
    re.compile(r'\s+[_\w][_\w\d]*'),  # word, which drops leading whitespace
)


def _bare_safe(literal: str) -> bool:
    """Whether ``literal`` written bare between backticks reads back as itself."""
    if '`' in literal:
        return False  # /`(.*?)`/ would stop at the first embedded backtick
    if literal.splitlines() not in ([], [literal]):
        return False  # pretty() output is re-indented line by line
    if literal in _LITERAL_KEYWORDS:
        return False
    if literal[:1] in '\'"' or literal[:2] in {"r'", 'r"'}:
        return False  # could be consumed as a (raw) string literal
    return not any(lookalike.fullmatch(literal) for lookalike in _LITERAL_LOOKALIKES)


def constant_source(literal: Any) -> str:
    """Render a constant literal as grammar source that parses back to it."""
    if not isinstance(literal, str):
        return f'`{literal}`'  # int/float/bool/None read back via `literal`
    if _bare_safe(literal):
        return f'`{literal}`'
    if "'" not in literal or '"' not in literal:
        # repr() picks a quote character not present in the string, so the
        # result contains no escaped quotes, on which the single-line string
        # patterns stop short
        return f'`{literal!r}`'
    # Both quote characters present: use a multiline string with every quote
    # escaped so the body cannot contain the closing delimiter.  Line breaks
    # and tabs are escaped because multiline strings are trimmed of common
    # indentation when read back, and whitespace at either end is escaped
    # because it is stripped.
    escaped = literal.replace('\\', '\\\\').replace("'", "\\'")
    for char in '\n\r\t\v\f\x1c\x1d\x1e\x85\u2028\u2029':
        escaped = escaped.replace(char, f'\\u{ord(char):04x}')
    if escaped[:1].isspace():
        escaped = f'\\u{ord(escaped[0]):04x}' + escaped[1:]
    if escaped[-1:].isspace():
        escaped = escaped[:-1] + f'\\u{ord(escaped[-1]):04x}'
    return f"`'''{escaped}'''`"


@nodedataclass
class Dot(Leaf):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.dot()

    def _pretty(self, lean=False):
        _ = lean
        return '/./'

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {('.',)}


@nodedataclass
class Fail(Leaf):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.fail()

    def _pretty(self, lean=False):
        _ = lean
        return '!()'


@nodedataclass
class Comment(Leaf):
    comment: str = ''

    def _pretty(self, lean: bool = False):
        _ = lean
        return f'(* {self.comment} *)'


@nodedataclass
class EOLComment(Comment):
    def _pretty(self, lean=False):
        _ = lean
        return f'  # {self.comment}\n'


@nodedataclass
class EOF(Leaf):
    def __post_init__(self):
        super().__post_init__()
        self.ast = None

    def _parse(self, ctx: Ctx) -> Any:
        ctx.eofcheck()

    def _pretty(self, lean=False):
        _ = lean
        return '$'


@nodedataclass
class EOL(Leaf):
    def __post_init__(self):
        super().__post_init__()
        self.ast = None

    def _parse(self, ctx: Ctx) -> Any:
        ctx.eolcheck()

    @cached_property
    def _nullable(self) -> bool:
        return True

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {('$->',)}

    def _pretty(self, lean=False):
        _ = lean
        return EOL_SYM


@nodedataclass
class Token(Leaf):
    token: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.token = self.token or self.ast

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.token(self.token)

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {(self.token,)}

    def _pretty(self, lean=False):
        _ = lean
        return repr(self.token)


@nodedataclass
class Constant(Leaf):
    literal: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.literal = self.literal or self.ast

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.constant(self.literal)

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {()}

    def _pretty(self, lean=False):
        _ = lean
        return constant_source(self.literal)

    @cached_property
    def _nullable(self) -> bool:
        return True


@nodedataclass
class Alert(Constant):
    level: int = 0

    def __post_init__(self):
        super().__post_init__()
        if self.ast:
            self.literal = self.ast.message.literal
            self.level = len(self.ast.level)

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.alert(message=self.literal, level=self.level)

    def _pretty(self, lean=False):
        _ = lean
        return f'{"^" * self.level}{super()._pretty()}'


@nodedataclass
class Cut(Leaf):
    def __post_init__(self):
        super().__post_init__()
        self.ast = None

    def _parse(self, ctx: Ctx) -> Any:
        ctx.cut()

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {()}

    def _pretty(self, lean=False):
        _ = lean
        return '~'

    @cached_property
    def _nullable(self) -> bool:
        return True

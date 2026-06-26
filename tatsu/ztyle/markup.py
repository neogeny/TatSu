# Copyright © 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import contextlib
import inspect
import re
from collections.abc import Callable
from enum import Enum
from typing import NamedTuple, assert_never

from .style import DEFAULT_COLOR, Color, Style


class StyleZ(str):
    __slots__ = ("_color", "_styles")

    def __new__(cls, *args, **_kwargs):
        assert args and isinstance(args[0], list)
        styles = args[0]
        assert not styles or isinstance(styles[0], Style)
        value = "".join(s.value for s in styles)
        new = super().__new__(cls, value)
        new._styles = styles
        return new

    def __init__(self, styles: list[Style]):
        self._styles = styles

    @property
    def value(self) -> str:
        return super().__str__()

    @property
    def style(self) -> list[Style]:
        return self._styles

    def __str__(self) -> str:
        return "".join(str(s) for s in self._styles)

    def __repr__(self) -> str:
        return "".join(repr(s) for s in self._styles)


class TokenType(Enum):
    ESC = "ESC"
    RET = "RET"
    CAL = "CAL"
    TXT = "TXT"


class Token(NamedTuple):
    type: TokenType
    value: str


def apply_style_stack(
    stack: list[str],
    text: str,
    color: Color = DEFAULT_COLOR,
) -> Style:
    s = Style(text, color=color)

    for name in stack:
        if style := s.get_style_method(name):
            s = style()
    assert s is not None
    return s


def markup(*texts: str, color: Color = DEFAULT_COLOR) -> StyleZ:
    stack: list[str] = []

    out: list[Style] = []
    part: str = ""
    for text in texts:
        text = str(text)  # noqa: PLW2901
        for token in tokenize(text):
            if part and token.type != TokenType.TXT:
                out += [apply_style_stack(stack, part, color=color)]
                part = ""
            match token.type:
                case TokenType.CAL:
                    for style in token.value.split(" "):
                        stack += [style]
                case TokenType.RET:
                    if not token.value:
                        stack = stack[:-1]
                    elif token.value in {"all", "*"}:
                        stack = []
                    elif stack and stack[-1] == token.value:
                        stack.pop()
                case TokenType.ESC:
                    part += "["
                case TokenType.TXT:
                    part += token.value
                case _:
                    assert_never(token.type)

    if part:
        out += [apply_style_stack(stack, part, color=color)]

    return StyleZ(out)


def tokenize(text: str) -> list[Token]:
    """Tokenize a Rich markup string into unbracketed tag data and text."""
    pattern = r"""(?x)
        (?P<ESC>\[\[)
        |
        \[/(?P<RET>[^\]]*)\]
        |
        \[(?P<CAL>[^\]]+)\]
        |
        (?P<TXT>[^\[]+)
    """

    tokens = []
    for match in re.finditer(pattern, text):
        kind = match.lastgroup
        assert kind is not None
        val = match.group(kind)

        match kind:
            case "CAL":
                tokens.append(Token(TokenType.CAL, val))
            case "RET":
                tokens.append(Token(TokenType.RET, val))
            case "TXT":
                tokens.append(Token(TokenType.TXT, val))
            case "ESC":
                tokens.append(Token(TokenType.TXT, "["))
            case _ as never:
                raise AssertionError(f"Unexpected kind: {never}")

    return tokens


def tokenize_to_values(text: str) -> list[str]:
    tokens = tokenize(text)
    return [t.value for t in tokens]

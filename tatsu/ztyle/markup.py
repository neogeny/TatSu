# Copyright © 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import contextlib
import re
from enum import Enum
from typing import NamedTuple, assert_never

from .style import Color, Style


class TokenType(Enum):
    ESC = "ESC"
    RET = "RET"
    CAL = "CAL"
    TXT = "TXT"


class Token(NamedTuple):
    type: TokenType
    value: str


def apply(stack: list[str], text: str) -> Style:
    s = Style(text, color=Color.default())
    for name in stack:
        if style := getattr(s, name, None):
            with contextlib.suppress(TypeError):
                s = style()
    return s


def parse(text: str) -> str:
    stack: list[str] = []

    out: list[Style] = []
    part: str = ""
    for token in tokenize(text):
        if part and token.type != TokenType.TXT:
            out += [apply(stack, part)]
            part = ""
        match token.type:
            case TokenType.CAL:
                for style in token.value.split(" "):
                    stack += [style]
            case TokenType.RET:
                if token.value == "all":
                    stack = []
                    continue
                if not token.value:
                    stack.pop()
                    continue
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i] == token.value:
                        stack.pop(i)
                        break
            case TokenType.ESC:
                part += "["
            case TokenType.TXT:
                part += token.value
            case _:
                assert_never(token.type)

    if part:
        out += [apply(stack, part)]

    return "".join(str(s) for s in out)


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

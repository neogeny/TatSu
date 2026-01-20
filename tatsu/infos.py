from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from .parserconfig import (  # re-export from legacy
    ParserConfig,
    UndefinedStr,
    _undefined_str,
)

# package
from .tokenizing import Tokenizer

assert ParserConfig and UndefinedStr and _undefined_str  # type: ignore


class Alert(NamedTuple):
    level: int = 1
    message: str = ''


class ParseInfo(NamedTuple):
    tokenizer: Tokenizer
    rule: str
    pos: int
    endpos: int
    line: int
    endline: int
    alerts: list[Alert] = []  # noqa: RUF012

    def text_lines(self) -> list[str]:
        return self.tokenizer.get_lines(self.line, self.endline)

    def line_index(self):
        return self.tokenizer.line_index(self.line, self.endline)

    @property
    def buffer(self):
        return self.tokenizer


class RuleInfo(NamedTuple):
    name: str
    impl: Callable
    is_leftrec: bool
    is_memoizable: bool
    is_name: bool
    params: list[Any] | tuple[Any]
    kwparams: dict[str, Any]

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

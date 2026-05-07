# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple, Protocol

from ..input import Cursor


class MemoKey(NamedTuple):
    pos: int
    ruleinfo: RuleInfo


class RuleResult(NamedTuple):
    node: Any
    newpos: int


class RuleLike(Protocol):
    no_memo: bool = False
    no_stak: bool = False
    is_name: bool = False
    is_tokn: bool = False
    is_memo: bool = True
    is_lrec: bool = False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class RuleInfo(NamedTuple):
    name: str
    instance: Any
    func: Callable[..., Any]
    no_memo: bool
    no_stak: bool
    is_name: bool
    is_tokn: bool

    is_lrec: bool
    is_memo: bool

    params: tuple[Any, ...]
    kwparams: dict[str, Any]

    @staticmethod
    def new(instance: Any, func: Callable, params=None, kwparams=None) -> RuleInfo:
        name = getattr(func, '__name__', '<?>')
        is_tokn = name.lstrip('_')[:1].isupper()
        return RuleInfo(
            name=name,
            instance=instance,
            func=func,
            no_memo=getattr(func, 'no_memo', False),
            no_stak=getattr(func, 'no_stak', False),
            is_name=getattr(func, 'is_name', False),
            is_tokn=getattr(func, 'is_tokn', is_tokn),
            is_lrec=getattr(func, 'is_lrec', False),
            is_memo=getattr(func, 'is_memo', True),
            params=params or (),
            kwparams=kwparams or {},
        )

    @staticmethod
    def bind(ri: RuleInfo, instance: Any) -> RuleInfo:
        return ri._replace(instance=instance)

    @property
    def memoizable(self) -> bool:
        return self.is_memo and not self.no_memo

    @property
    def should_trace(self) -> bool:
        return not self.no_stak

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class ParseInfo(NamedTuple):
    cursor: Cursor
    rule: str
    pos: int
    endpos: int
    line: int
    endline: int
    alerts: list[Alert] = []  # noqa: RUF012


class CommentInfo(NamedTuple):
    inline: list
    eol: list

    @staticmethod
    def new_comment():
        return CommentInfo([], [])


class Alert(NamedTuple):
    level: int = 1
    message: str = ''

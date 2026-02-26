# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple, Protocol


class MemoKey(NamedTuple):
    pos: int
    ruleinfo: RuleInfo


class RuleResult(NamedTuple):
    node: Any
    newpos: int


class RuleLike(Protocol):
    is_leftrec: bool = False
    is_memoizable: bool = False
    is_name: bool = False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class closure(list[Any]):
    def __hash__(self) -> int:  # pyright: ignore[reportIncompatibleVariableOverride]
        return hash(tuple(self))


class RuleInfo(NamedTuple):
    name: str
    obj: Any
    func: Callable[..., None]
    is_lrec: bool
    is_memo: bool
    is_name: bool
    params: tuple[Any, ...]
    kwparams: dict[str, Any]

    @staticmethod
    def new(obj: Any, func: Callable, params=None, kwparams=None):
        name = getattr(func, '__name__', '<?>')
        is_leftrec = getattr(func, 'is_leftrec', False)
        is_memoizable = getattr(func, 'is_memoizable', True)
        is_name = getattr(func, 'is_name', False)

        return RuleInfo(
            name=name,
            obj=obj,
            func=func,
            is_lrec=is_leftrec,
            is_memo=is_memoizable,
            is_name=is_name,
            params=params or (),
            kwparams=kwparams or {},
        )

    def is_token_rule(self):
        return self.name.lstrip('_')[:1].isupper()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

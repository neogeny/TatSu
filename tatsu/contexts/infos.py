from __future__ import annotations

from typing import Any, NamedTuple, Protocol

from ..infos import RuleInfo


class MemoKey(NamedTuple):
    pos: int
    ruleinfo: RuleInfo
    state: Any


class RuleResult(NamedTuple):
    node: Any
    newpos: int
    newstate: Any


class RuleLike(Protocol):
    is_leftrec: bool = False
    is_memoizable: bool = False
    is_name: bool = False

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class closure(list[Any]):
    def __hash__(self) -> int:  # type: ignore
        return hash(tuple(self))

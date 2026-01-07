from __future__ import annotations

import inspect
from collections.abc import Callable

from .contexts import (  # noqa: F401
    ParseContext,
    isname,
    leftrec,
    nomemo,
    tatsumasu,
)
from .exceptions import FailedRef


class Parser(ParseContext):
    def _find_rule(self, name: str) -> Callable:
        rule = getattr(self, '_' + name + '_', None)
        if isinstance(rule, type(self._find_rule)):
            return rule
        rule = getattr(self, name, None)
        if isinstance(rule, type(self._find_rule)):
            return rule
        return self._error(name, exclass=FailedRef)

    @classmethod
    def rule_list(cls) -> list[str]:
        methods = inspect.getmembers(cls, predicate=inspect.isroutine)
        result = []
        for m in methods:
            name = m[0]
            if len(name) < 3:
                continue
            if name.startswith('__') or name.endswith('__'):
                continue
            if name.startswith('_') and name.endswith('_'):
                result.append(name[1:-1])
        return result

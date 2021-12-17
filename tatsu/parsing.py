from __future__ import annotations

import inspect

from tatsu.exceptions import FailedRef
from tatsu.contexts import ParseContext
from tatsu.contexts import tatsumasu, leftrec, nomemo, isname  # noqa pylint: disable=unused-import


class Parser(ParseContext):
    def _find_rule(self, name):
        rule = getattr(self, '_' + name + '_', None)
        if isinstance(rule, type(self._find_rule)):
            return rule
        rule = getattr(self, name, None)
        if isinstance(rule, type(self._find_rule)):
            return rule
        self._error(name, exclass=FailedRef)

    @classmethod
    def rule_list(cls):
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

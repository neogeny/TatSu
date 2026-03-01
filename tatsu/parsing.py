# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import cache
from typing import Any

from .contexts import ParseContext, isname, name, leftrec, nomemo, rule, tatsumasu
from .exceptions import FailedRef

from .parserconfig import ParserConfig
from .util import safe_name, typename
from .util.genericmain import generic_main

__all__ = [
    'Parser',
    'generic_main',
    'isname',
    'name',
    'leftrec',
    'nomemo',
    'rule',
    'tatsumasu',
]


@cache
def find_rule(source: Any, name: str) -> Callable[[ParseContext], Any] | None:
    for rulename in {name, name.strip('_'), f'_{name}_', f'_{name}'}:
        action = getattr(source, safe_name(rulename), None)
        if callable(action):
            return action
    return None


class Parser(ParseContext):
    def __init__(
        self,
        rulesource: Any = None,
        /,
        *,
        config: ParserConfig | None = None,
        **settings: Any,
    ) -> None:
        self.rulesource = rulesource

        config = ParserConfig.new(config, **settings)
        srcconfig = ParserConfig.new(getattr(rulesource, 'config', None))
        config = srcconfig.override_config(config)

        super().__init__(config=config)

    def _find_rule(self, name: str) -> Callable[[ParseContext], Any]:
        if self.rulesource:
            action = find_rule(self.rulesource, name)
        else:
            action = find_rule(self, name)
        if not action:
            raise self.newexcept(f'{name}', excls=FailedRef)
        return action

    def rule_list(self) -> list[str]:
        source = self.rulesource or type(self)

        def isdunder(name: str) -> bool:
            return name.startswith('__') and name.endswith('__')

        methods = inspect.getmembers(source, predicate=inspect.ismethod)
        return [m[0] for m in methods if not isdunder(m[0])]

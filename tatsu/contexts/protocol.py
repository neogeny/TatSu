# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol, runtime_checkable

from ..infos import RuleInfo


type MethodContextManager = AbstractContextManager[Any, None]


@runtime_checkable
class ParseContextProtocol(Protocol):

    def _call(self, ruleinfo: RuleInfo) -> Any: ...

    def _option(self) -> Any: ...

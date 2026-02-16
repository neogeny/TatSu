# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import types
from typing import Any

from .ast import AST
from .objectmodel import BaseNode

__all__ = ['SynthNode', 'registered_synthetics', 'synthesize']

# NOTE:
#   __registry is an alias for the modules vars()/ __dict__.
#   This allows for synthesized types to reside within this module.
__registry: dict[str, Any] = vars()


class SynthNode(BaseNode):
    def __init__(self, ast: Any = None, **attributes: Any):
        super().__init__(ast=ast, **attributes)
        if not isinstance(ast, AST):
            return
        # NOTE:
        #   synthetic objects have no attributes prior to this __init__()
        #   During parsing, the Synth is known at the start of a rule invocation,
        #   and the possible attributes known at the end
        for name, value in ast.items():
            setattr(self, name, value)
        self.ast = None


def synthesize(name: str, bases: tuple[type, ...], **kwargs: Any) -> type:
    # by Apalala 2026/02/16 <- 2017
    # by Gemini  2026/02/16
    if not isinstance(bases, tuple):
        raise TypeError(f'bases must be a tuple, not {type(bases)}')

    if SynthNode not in bases:
        bases = (*bases, SynthNode)

    found = __registry.get(name)
    if isinstance(found, type):
        return found
    elif found:
        raise TypeError(f'Found {name!r} in context but its type is {type(found)!r}')

    def build_body(ns: dict[str, Any]) -> None:
        ns.update({"__module__": __name__})
        ns.update(kwargs)

    newcls: type = types.new_class(name, bases, exec_body=build_body)
    __registry[name] = newcls

    return newcls


def registered_synthetics() -> dict[str, SynthNode]:
    return {
        name: value
        for name, value in __registry.items()
        if isinstance(value, SynthNode)
    }

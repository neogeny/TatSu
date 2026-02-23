# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


def fromany(ss: Any) -> ParserStateStack:
    """
    Safely promotes an opaque state object to a ParserStateStack.
    This acts as the type-safe gateway for Engine contexts.
    """
    if not isinstance(ss, ParserStateStack):
        raise TypeError(
            f"Parser expected ParserStateStack, received {type(ss).__name__}"
        )
    return ss

# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: MIT OR Apache-2.0

"""
json - Direct Value to Grammar translator

This module translates json directly to Grammar,
bypassing the TatSuModel deserializer which fails on modified JSON.
"""

from __future__ import annotations

import json
from typing import Any

from .. import peg as g
from ..util.fromjson import fromjson


def loads_grammar(json_str: str) -> g.Grammar:
    """Parse JSON string and return a Grammar object."""
    value = json.loads(json_str)
    return load_grammar(value)


def load_grammar(value: Any) -> g.Grammar:
    """Parse JSON value and return a Grammar object."""
    result = fromjson(value)
    assert isinstance(result, g.Grammar)
    return result

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Unit tests for asjson utility.
# by Gemini (2026-01-26)
# by [apalala@gmail.com](https://github.com/apalala)
"""
from __future__ import annotations

import enum
import weakref
from typing import Any, NamedTuple

from tatsu.util.asjson import asjson


class Color(enum.Enum):
    RED = 1
    BLUE = "blue"


class Point(NamedTuple):
    x: int
    y: int


class CustomNode:
    def __init__(self, name: str, child: Any = None):
        self.name = name
        self.child = child

    def __json__(self, seen: set[int] | None = None) -> dict[str, Any]:
        return {
            "name": self.name,
            "child": asjson(self.child, seen=seen),
        }


def test_primitives():
    assert asjson(1) == 1
    assert asjson("test") == "test"
    assert asjson(True) is True
    assert asjson(None) is None


def test_containers():
    # Tuples and Sets must become lists
    data = {"a": [1, 2], "b": (3, 4), "c": {5, 6}}
    result = asjson(data)
    assert result["a"] == [1, 2]
    assert result["b"] == [3, 4]
    assert isinstance(result["b"], list)
    assert isinstance(result["c"], list)
    assert sorted(result["c"]) == [5, 6]


def test_enum_handling():
    assert asjson(Color.RED) == 1
    assert asjson(Color.BLUE) == "blue"


def test_namedtuple_handling():
    p = Point(10, 20)
    assert asjson(p) == {"x": 10, "y": 20}


def test_weakref_proxy():
    class Data:
        pass
    obj = Data()
    proxy = weakref.proxy(obj)
    result = asjson(proxy)
    # Matches type(node).__name__ + hex ID
    assert "proxytype@0x" in result.lower()


def test_circular_reference() -> None:
    """Tests that the 'seen' set catches infinite loops."""
    node: dict[str, Any] = {}
    node["loop"] = node
    result = asjson(node)
    assert "dict@" in result["loop"]


def test_custom_json_protocol_with_cycle():
    """Tests that __json__ correctly uses the shared 'seen' set."""
    parent = CustomNode("parent")
    child = CustomNode("child", child=parent)
    parent.child = child

    result = asjson(parent)
    assert result["name"] == "parent"
    assert result["child"]["name"] == "child"
    assert "CustomNode@" in result["child"]["child"]


def test_mapping_key_conversion():
    """JSON keys must be strings."""
    data = {123: "integer_key", (1, 2): "tuple_key"}
    result = asjson(data)
    assert result["123"] == "integer_key"
    assert result["(1, 2)"] == "tuple_key"

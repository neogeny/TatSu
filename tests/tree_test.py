# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from tatsu.treez import Tree


def test_empty():
    t = Tree("root")
    assert t.render() == "root"


def test_one_child():
    t = Tree("root")
    t.add("child")
    assert t.render() == "root\n└── child"


def test_two_children():
    t = Tree("root")
    t.add("a")
    t.add("b")
    assert t.render() == "root\n├── a\n└── b"


def test_nested():
    t = Tree("root")
    a = t.add("a")
    a.add("x")
    t.add("b")
    assert t.render() == "root\n├── a\n│   └── x\n└── b"


def test_deep_nesting():
    t = Tree("r")
    c1 = t.add("c1")
    c2 = c1.add("c2")
    c2.add("c3")
    assert t.render() == "r\n└── c1\n    └── c2\n        └── c3"


def test_add_returns_child():
    t = Tree("root")
    child = t.add("child")
    assert child.label == "child"
    assert child in t.children


def test_str_delegates_to_render():
    t = Tree("x")
    t.add("y")
    assert str(t) == t.render()


def test_style_is_accepted():
    t = Tree("root")
    t.add("child")
    assert t.render() == "root\n└── child"


def test_no_style_default():
    t = Tree("root")
    child = t.add("child")
    assert child.label == "child"


def test_children_list():
    t = Tree("root")
    a = t.add("a")
    b = t.add("b")
    assert t.children == [a, b]


def test_three_children():
    t = Tree("root")
    t.add("a")
    t.add("b")
    t.add("c")
    expected = "root\n├── a\n├── b\n└── c"
    assert t.render() == expected


def test_single_branch_multi_level():
    t = Tree("x")
    t.add("y").add("z")
    assert t.render() == "x\n└── y\n    └── z"

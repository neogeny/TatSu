# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import pytest

from tatsu.objectmodel import Node, tatsudataclass


def test_init_attributes():
    node = Node()
    assert hasattr(node, 'ast')
    assert hasattr(node, 'parseinfo')


def test_init_attributes_transferred():
    node = Node(ast='Hello!')
    assert node.ast == 'Hello!'

    node = Node(ctx=object(), ast='Hello!')
    assert node.ast == 'Hello!'
    assert node.ctx


def test_attributes_through_shell():
    node = Node(ast='Hello')

    assert hasattr(node, 'ast')
    assert hasattr(node, 'parseinfo')


@tatsudataclass
class Inner(Node):
    id: str


@tatsudataclass
class Outer(Node):
    left: Inner
    right: Inner


def test_children():
    with pytest.raises(TypeError):
        Outer()

    with pytest.raises(TypeError):
        Inner()

    with pytest.raises(TypeError):
        Inner('x')

    a_inner = Inner(id='a')
    b_inner = Inner(id='b')
    outer = Outer(left=a_inner, right=b_inner)
    assert outer
    assert isinstance(outer.left, Inner)
    assert isinstance(outer.right, Inner)
    children = outer.children()
    assert set(children) == {a_inner, b_inner}

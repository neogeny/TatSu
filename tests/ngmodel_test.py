# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from dataclasses import dataclass

import pytest

from tatsu.objectmodel import Node


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


@dataclass(kw_only=True, unsafe_hash=True)
class Inner(Node):
    id: str


@dataclass(kw_only=True, unsafe_hash=True)
class Outer(Node):
    left: Inner
    right: Inner


def test_children():
    with pytest.raises(TypeError):
        outer = Outer()  # pyright: ignore[reportCallIssue]  # ty:ignore[missing-argument]
        pytest.fail('Should have raised TypeError')

    with pytest.raises(TypeError):
        Inner()  # ty: ignore[missing-argument] # pyright: ignore[reportCallIssue]

    with pytest.raises(TypeError):
        Inner('x')  # ty: ignore[missing-argument, too-many-positional-arguments] # pyright: ignore[reportCallIssue]

    a_inner = Inner(id='a')
    b_inner = Inner(id='b')
    outer = Outer(left=a_inner, right=b_inner)
    assert outer
    assert isinstance(outer.left, Inner)
    assert isinstance(outer.right, Inner)
    children = outer.children()
    assert children == (a_inner, b_inner)

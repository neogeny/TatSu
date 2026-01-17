from dataclasses import dataclass

import pytest

from tatsu.ngmodel import NGNode, children_of, nodeshell


def test_init_attributes():
    node = NGNode()
    assert hasattr(node, 'ast')
    assert hasattr(node, '_parseinfo')


def test_init_attributes_transferred():
    node = NGNode(ast='Hello!')
    assert node.ast == 'Hello!'

    node = NGNode(ctx=object(), ast='Hello!')  # type: ignore
    assert node.ast == 'Hello!'
    assert node.ctx


def test_attributes_through_shell():
    node = NGNode(ast='Hello')
    shell = nodeshell(node)

    assert hasattr(shell, 'ast')
    assert hasattr(shell, 'parseinfo')


@dataclass(kw_only=True, unsafe_hash=True)
class Inner(NGNode):
    id: str


@dataclass(kw_only=True, unsafe_hash=True)
class Outer(NGNode):
    left: Inner
    right: Inner


def test_children():
    with pytest.raises(TypeError):
        outer = Outer()  # type: ignore
        pytest.fail('Should have raised TypeError')

    with pytest.raises(TypeError):
        Inner()  # type: ignore

    with pytest.raises(TypeError):
        Inner('x')  # type: ignore

    a_inner = Inner(id='a')
    b_inner = Inner(id='b')
    outer = Outer(left=a_inner, right=b_inner)
    assert outer
    assert isinstance(outer.left, Inner)
    assert isinstance(outer.right, Inner)
    children = children_of(outer)
    assert children == (a_inner, b_inner)

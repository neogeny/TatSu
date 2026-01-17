from tatsu import ngmodel


def test_init_attributes_deleted():
    node = ngmodel.NGNode()
    assert not hasattr(node, 'ast')
    assert not hasattr(node, 'ctx')
    assert not hasattr(node, 'parseinfo')
    assert not hasattr(node, 'attributes')

    assert hasattr(node, '_ast')
    assert hasattr(node, '_ctx')
    assert hasattr(node, '_parseinfo')
    assert hasattr(node, '_attributes')


def test_init_attributes_transferred():
    node = ngmodel.NGNode(ast='Hello')
    assert node._ast

    node = ngmodel.NGNode(ctx=object(), ast='Hello')
    assert node._ast
    assert node._ctx


def test_attributes_through_shell():
    node = ngmodel.NGNode(ast='Hello')
    shell = ngmodel.nodeshell(node)

    assert hasattr(shell, 'ast')
    assert hasattr(shell, 'ctx')
    assert hasattr(shell, 'parseinfo')
    assert hasattr(shell, 'attributes')


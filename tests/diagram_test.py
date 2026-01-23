import pytest

from tatsu.tool import compile
from tatsu.util.misc import module_missing


@pytest.mark.skipif(module_missing('graphviz'), reason='graphviz is not available')
def test_dot():
    from tatsu.diagrams import draw

    grammar = """
        start = "foo\\nbar" $;
    """
    m = compile(grammar, 'Diagram')
    draw('tmp/diagram.svg', m)

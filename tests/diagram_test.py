import pytest

from tatsu import diagrams
from tatsu.tool import compile


@pytest.mark.skipif(not diagrams.available(), reason='graphviz is not available')
def test_dot():
    grammar = """
        start = "foo\\nbar" $;
    """
    m = compile(grammar, 'Diagram')
    diagrams.draw('tmp/diagram.svg', m)

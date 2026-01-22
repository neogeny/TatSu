from tatsu.tool import compile


def test_dot():
    grammar = """
        start = "foo\\nbar" $;
    """
    try:
        from tatsu.diagrams import draw
    except ImportError:
        return

    m = compile(grammar, 'Diagram')
    draw('tmp/diagram.svg', m)

import random
from pathlib import Path

import pytest

from tatsu import parse
from tatsu.buffering import Buffer


@pytest.fixture
def text():
    testfile = Path(__file__).with_suffix('.py')
    return testfile.read_text()


@pytest.fixture
def buf(text):
    return Buffer(text, whitespace='')


def test_pos_consistency(text, buf):
    line = col = 0
    for p, c in enumerate(text):
        bl, bc = buf.line_info(p)[1:3]
        d = buf.next()
        # print('tx', line, col, repr(c))
        # print('bu', bl, bc, repr(d))
        assert line == bl
        assert col == bc
        assert c == d
        if c == '\n':
            col = 0
            line += 1
        else:
            col += 1


def test_next_consisntency(buf):
    while not buf.atend():
        bl, bc = buf.line_info()[1:3]
        #            print('li', bl, bc)
        #            print('bu', buf.line, buf.col)
        assert buf.line == bl
        assert buf.col == bc
        buf.next()


def test_goto_consistency(text, buf):
    for _ in range(100):
        buf.goto(random.randrange(len(text)))  # noqa: S311
        bl, bc = buf.line_info()[1:3]
        #            print('li', bl, bc)
        #            print('bu', buf.line, buf.col)
        assert buf.line == bl
        assert buf.col == bc


def test_line_consistency(text, buf):
    lines = buf.split_block_lines(text)
    for n, line in enumerate(lines):
        assert buf.get_line(n) == line


def test_line_info_consistency(text, buf):
    lines = buf.split_block_lines(text)
    line = 0
    col = 0
    start = 0
    for n, char in enumerate(text):
        info = buf.line_info(n)
        assert line == info.line
        assert col == info.col
        assert start == info.start
        assert lines[line] == info.text
        col += 1
        if char == '\n':
            line += 1
            col = 0
            start = n + 1
    text_len = len(text)
    info = buf.line_info(1 + text_len)
    assert len(text.splitlines()) - 1 == info.line
    assert text_len == info.end


def test_linecount():
    b = Buffer('')
    assert b.linecount == 1

    b = Buffer('Hello World!')
    assert b.linecount == 1

    b = Buffer('\n')
    assert b.linecount == 2


def test_namechars():
    grammar = """
        @@namechars :: '-'
        start =
            | "key" ~ ";"
            | "key-word" ~ ";"
            | "key-word-extra" ~ ";"
            ;
    """
    ast = parse(grammar, 'key-word-extra;')
    assert ast == ('key-word-extra', ';')

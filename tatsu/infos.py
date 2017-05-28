# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from collections import namedtuple

from .ast import AST


class PosLine(namedtuple('_PosLine', ['start', 'line', 'length'])):
    __slots__ = ()

    @staticmethod
    def build_line_cache(lines):
        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for c in line:
                cache.append(pl)
            i += len(line)
        n += 1
        if lines and lines[-1] and lines[-1][-1] in '\r\n':
            n += 1
        cache.append(PosLine(i, n, 0))
        return cache, n


class LineIndexInfo(namedtuple('_LineIndexInfoBase', ['filename', 'line'])):
    __slots__ = ()

    @staticmethod
    def block_index(name, n):
        return list(LineIndexInfo(l, i) for l, i in zip(n * [name], range(n)))


class LineInfo (namedtuple('_LineInfo', ['filename', 'line', 'col', 'start', 'end', 'text'])):
    __slots__ = ()


class CommentInfo(namedtuple('_CommentInfo', ['inline', 'eol'])):
    __slots__ = ()

    @staticmethod
    def new_comment():
        return CommentInfo([], [])


_ParseInfo = namedtuple(
    '_ParseInfoTuple',
    [
        'buffer',
        'rule',
        'pos',
        'endpos',
        'line',
        'endline',
    ]
)


class ParseInfo(_ParseInfo):
    __slots__ = ()

    def text_lines(self):
        return self.buffer.get_lines(self.line, self.endline)

    def line_index(self):
        return self.buffer.line_index(self.line, self.endline)


MemoKey = namedtuple(
    'MemoKey',
    [
        'pos',
        'name',
        'state'
    ]
)


RuleInfo = namedtuple(
    'RuleInfo',
    [
        'name',
        'impl',
        'params',
        'kwparams',
    ]
)


RuleResult = namedtuple(
    'RuleResult',
    [
        'node',
        'newpos',
        'newstate',
    ]
)


class TreeInfo(object):
    __slots__ = (
        'ast',
        'cst'
    )

    def __init__(self, ast=None, cst=None):
        self.ast = AST() if ast is None else ast
        self.cst = cst

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import unittest

from tatsu.tool import compile


class LookaheadTests(unittest.TestCase):
    def test_skip_to(self, trace=False):
        grammar = """
            start = 'x' ab $ ;

            ab
                =
                | 'a' 'b'
                | ->'a' 'b'
                ;
        """
        m = compile(grammar, trace=trace)
        ast = m.parse('x xx yyy a b')
        self.assertEqual(['x', ['a', 'b']], ast)

        grammar = """
            start = 'x' ab $ ;

            ab
                =
                | 'a' 'b'
                | ->&'a' 'a' 'b'
                ;
        """
        m = compile(grammar, trace=trace)
        ast = m.parse('x xx yyy a b')
        self.assertEqual(['x', ['a', 'b']], ast)

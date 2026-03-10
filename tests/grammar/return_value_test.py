# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import tatsu


def test_mixed_return():
    grammar = r"""
        start: ('a' b='b') 'c' [d='d']
    """

    model = tatsu.compile(grammar)
    value = model.parse('a b c')
    assert value == {'b': 'b', 'd': None}
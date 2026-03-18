# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import tatsu
from tatsu.util.strtools import trim


def test_multiline_string():
    grammar = r'''
        @@grammar :: Test

        start: longone | shortone $

        shortone: "short"

        # longone: 'long'
        longone: """
            this "" \" \"""
            is a long "string"
            """
    '''
    m = tatsu.compile(grammar)
    m.parse('short')
    input = trim("""
            this "" \" \"""
            is a long "string"
            """).strip()
    m.parse(input)

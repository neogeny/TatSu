# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import pytest

import tatsu
from tatsu.exceptions import FailedParse


class TestFailedParseRender:
    def test_render_features_present(self):
        grammar = r'''
            @@grammar :: Test

            start = 'hello' 'world' ;
        '''
        model = tatsu.compile(grammar=grammar)

        with pytest.raises(FailedParse) as exc_info:
            model.parse('hello missing', source="example")

        e = exc_info.value
        r = e.render()
        # print(r)
        # assert False

        assert 'error' in r
        assert '->' in r
        assert '│' in r
        assert 'start' in r
        assert isinstance(r, str)

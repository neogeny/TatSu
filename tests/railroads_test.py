# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path

from tatsu import grammars, railroads
from tatsu.tool import api
from tatsu.util import trim


def test_railroads():
    grammar = Path('./grammar/tatsu.tatsu').read_text()
    model = api.compile(grammar)
    print('RAILROADS')
    railroads.draw(model)

    tracks = railroads.tracks(model)
    assert len(tracks) == 250

    track0 = "start ●─grammar─■"
    assert tracks[0] == track0
    trackm2 = "eof[EOF] ●─'$' ✂ ──■"
    assert tracks[-2] == trackm2
    assert not tracks[-1].rstrip()

def test_per_node():
    grammar = r"""
        start: options

        options: number | 'hello'

        number: /\d+/
    """
    model = api.compile(grammar)
    assert isinstance(model, grammars.Grammar)
    optrule = model.rules[1]
    expected = """
         options ●───┬─number──┬──■
                     └─'hello'─┘
    """
    assert optrule.railroads() == trim(expected)

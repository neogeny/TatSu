# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path

from tatsu import railroads
from tatsu.tool import api


def test_railroads():
    grammar = Path('./grammar/tatsu.tatsu').read_text()
    model = api.compile(grammar)
    print('RAILROADS')
    railroads.draw(model)

    tracks = railroads.tracks(model)
    assert len(tracks) == 245

    track0 = "start ●─grammar■"
    assert tracks[0] == track0
    trackm2 = "eof ●──'$'─ ✂ ■"
    assert tracks[-2] == trackm2
    assert not tracks[-1].rstrip()

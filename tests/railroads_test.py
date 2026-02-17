# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path

import pytest

from tatsu import railroads
from tatsu.tool import api


def test_railroads():
    grammar = Path('./grammar/tatsu.tatsu').read_text()
    model = api.compile(grammar)
    print('RAILROADS')
    railroads.draw(model)
    pytest.fail()

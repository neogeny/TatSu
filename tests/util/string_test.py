# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# from: https://www.unicode.org/charts/nameslist/n_2500.html
from __future__ import annotations

from tatsu.util import string


def test_visible_width():
    assert string.unicode_display_len("abc") == 3
    assert string.unicode_display_len("Python") == 6
    assert string.unicode_display_len("蛇") == 2
    assert string.unicode_display_len("🐍 Py") == 5

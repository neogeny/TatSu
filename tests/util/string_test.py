# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from tatsu.util.string import asregex


def test_sregex():
    assert asregex("'") == "r'''"
    assert asregex('\'') == "r'''"
    assert asregex("\"") == "r'\"'"
    assert asregex("\"") == 'r\'"\''

    assert asregex("\n") == "r'\\n'"
    assert asregex(r"\n") == "r'\\n'"
    assert asregex(r"\\n") == "r'\\\\n'"
    assert asregex(r"\\n") == r"r'\\n'"

    assert asregex('[abc]') == r"r'[abc]'"
    assert asregex(r'[abc]') == r"r'[abc]'"
    assert asregex('a.*?b') == r"r'a.*?b'"
    assert asregex(r'a.*?b') == r"r'a.*?b'"

    assert asregex('\\') == r"r'\\'"
    assert asregex(r'\\') == r"r'\\'"

    # FIXME
    # with pytest.warns(SyntaxWarning, match=r'.*?invalid escape sequence'):
    # assert asregex('\w') == r"r'\w'"
    assert asregex(r'\w') == r"r'\w'"

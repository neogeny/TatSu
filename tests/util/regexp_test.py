# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import pytest

from tatsu.util import regexpp


def test_patterns_quotes():
    assert regexpp("'") == 'r"\'"'
    assert regexpp('\'') == 'r"\'"'

    # Input: a'b -> Result: r'a\'b'
    assert regexpp("a'b") == 'r"a\'b"'

    assert regexpp('"') == "r'\"'"
    assert regexpp('"') == r"r'" + '"' + "'"


def test_backslash_edge_cases() -> None:
    assert regexpp(r"\'") == 'r"\\\'"'

    # raw string r"r'\\\''" represents exactly three backslashes
    assert regexpp(r"\\'") == 'r"\\\\\'"'


def test_patterns_newlines():
    assert regexpp("\n") == r"r'\n'"
    assert regexpp(r"\n") == r"r'\n'"
    assert regexpp(r"\\n") == r"r'\\n'"


def test_patterns_expr():
    assert regexpp('[abc]') == r"r'[abc]'"

    with pytest.raises(ValueError, match=r"Invalid regex passed to regexp\(\)"):
        assert regexpp('\\') == r"r'\\'"

    assert regexpp(r'\\') == r"r'\\'"


def test_patterns_real():
    e = r"(REM\s|')[^\r\n]*(\r?\n|\r)"
    # Result preserves the original \r \n and escapes the '
    assert regexpp(e) == 'r"(REM\\s|\')[^\\r\\n]*(\\r?\\n|\\r)"'


def test_roundtrip_verification() -> None:
    # Standard case
    assert eval(regexpp("it's")) == "it's"  # noqa: S307

    # Trailing backslash case: Now safe to eval()
    with pytest.raises(ValueError, match=r"Invalid regex passed to regexp\(\)"):
        assert eval(regexpp("\\")) == "\\\\"  # noqa: S307


def test_edge_cases() -> None:
    assert regexpp("'''") == 'r"\'\'\'"'
    assert regexpp("") == "r''"
    assert regexpp(123) == "r'123'"


def test_regexp_is_runnable():
    pattern = r"\'"
    generated_code = regexpp(pattern)

    # This ensures the generated code is actually valid Python
    # and evaluates back to the original pattern.
    assert eval(generated_code) == pattern  # noqa: S307

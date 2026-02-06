# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from tatsu.util.string import regexp


def test_regexp_quotes():
    # single quotes are escaped
    assert regexp("'") == r"r'\''"
    assert regexp('\'') == "r'\\''"
    assert regexp("'") == r"r'\''"
    assert regexp('\'') == r"r'\''"

    assert regexp('a\'b') == "r'a\\'b'"
    assert regexp("a'b") == "r'a\\'b'"
    assert regexp('a\'b') == r"r'a\'b'"
    assert regexp("a'b") == r"r'a\'b'"

    assert regexp("\"") == "r'\"'"
    assert regexp("\"") == 'r\'"\''

    assert regexp(r"\'") == r"r'\''"
    assert regexp('\\\'') == "r'\\\''"
    assert regexp(r"\\'") == "r'\\\''"   # 1
    assert regexp(r"\\'") == r"r'\''"  # 2
    assert regexp("\\'") == "r'\\\''"    # 3


def test_regexp_newlines():
    assert regexp("\n") == "r'\\n'"
    assert regexp(r"\n") == "r'\\n'"
    assert regexp(r"\\n") == "r'\\\\n'"
    assert regexp(r"\\n") == r"r'\\n'"


def test_regexp_expr():
    assert regexp('[abc]') == r"r'[abc]'"
    assert regexp(r'[abc]') == r"r'[abc]'"
    assert regexp('a.*?b') == r"r'a.*?b'"
    assert regexp(r'a.*?b') == r"r'a.*?b'"

    assert regexp('\\') == r"r'\\'"
    assert regexp(r'\\') == r"r'\\'"

    # NOTE:
    #   SyntaxWarning emitted at compile time
    #   assert aregexss('\w') == r"r'\w'"
    assert regexp(r'\w') == r"r'\w'"


def test_regexp_real():
    e = r"(REM\s|')[^\r\n]*(\r?\n|\r)"
    assert regexp(e) == r"r'(REM\s|\')[^\r\n]*(\r?\n|\r)'"

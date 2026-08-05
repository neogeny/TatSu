# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
import sys
from functools import cache
from typing import Any

from .strtools import trim


if sys.version_info >= (3, 13):
    from re import PatternError
else:
    PatternError = re.error


# The pretty printer works on lines, so a regex holding any of the characters
# str.splitlines() breaks on comes back reindented, or split across rules.
_LAYOUT_ESCAPES = {
    '\n': r'\n',
    '\v': r'\v',
    '\f': r'\f',
    '\r': r'\r',
    '\x1c': r'\x1c',
    '\x1d': r'\x1d',
    '\x1e': r'\x1e',
    '\x85': r'\x85',
    '\u2028': r'\u2028',
    '\u2029': r'\u2029',
}

_SLASH_ESCAPE = {'/': r'\/'}


@cache
def cached_re_compile(
    pattern: str | bytes | re.Pattern,
    /,
    flags: int = 0,
) -> re.Pattern:
    if isinstance(pattern, re.Pattern):
        return pattern
    pattern = str(pattern)
    return re.compile(pattern, flags=flags)


def _rewrite(pattern: str, escapes: dict[str, str]) -> str:
    """Apply ``escapes`` to a regex, leaving escaped characters alone."""
    result = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == '\\' and index + 1 < len(pattern):
            index += 1
            char = pattern[index]
            if char not in escapes:
                result.append('\\')
        result.append(escapes.get(char, char))
        index += 1
    return ''.join(result)


def delimited_regex(pattern: str) -> str:
    """Write a regex in the ``/.../`` or ``?"..."`` form of the grammar syntax."""
    if not pattern:
        return '?""'  # `//` would open an end-of-line comment
    if '/' in pattern and '"' not in pattern and '\n' not in pattern:
        # DOUBLEQUOTED holds neither double quotes nor line breaks
        return f'?"{pattern}"'
    return f'/{_rewrite(pattern, _SLASH_ESCAPE)}/'


def regex_source(pattern: str) -> str:
    """Write a regex as grammar source that reads back as the same regex."""
    if cached_re_compile(pattern).flags & re.VERBOSE:
        # layout is not significant under (?x), where escaping it would be
        pattern = trim(pattern)
    else:
        # pretty() reindents its output line by line, so a regex spanning
        # lines otherwise reads back with the new indentation inside it
        pattern = _rewrite(pattern, _LAYOUT_ESCAPES)
    return delimited_regex(pattern)


def regexpp(regex: Any) -> str:
    """
    Returns a printable version of the regexp pattern as a Python raw string.
    Validates input and ensures generated output is syntactically valid.
    """
    # by Gemini (2026-02-04 - 2026-02-07)
    # by [apalala@gmail.com](https://github.com/apalala)

    pattern_text = regex.pattern if hasattr(regex, "pattern") else str(regex)

    try:
        re.compile(pattern_text)
    except PatternError as e:
        raise ValueError(
            f"Invalid regex passed to regexp(): {pattern_text!r}\n{e}",
        ) from e

    ctrl_map: dict[str, str] = {
        "\n": r"\n",
        "\r": r"\r",
        "\t": r"\t",
        "\v": r"\v",
        "\f": r"\f",
        "\b": r"\b",
        "\a": r"\a",
        "\0": r"\0",
    }

    result = "".join(ctrl_map.get(c, c) for c in pattern_text)

    # Handle trailing backslashes (odd count check for raw string safety)
    if result.endswith("\\") and (len(result) - len(result.rstrip("\\"))) % 2 != 0:
        result += "\\"

    if result.endswith("'") or result.count("'") > result.count('"'):
        output = f'r"{re.sub(r'(?<!\\)"', r"\"", result)}"'
    else:
        output = f"r'{re.sub(r"(?<!\\)'", r"\'", result)}'"

    try:
        evaluated = eval(output)  # noqa: S307
        re.compile(evaluated)
    except SyntaxError as e:
        raise RuntimeError(
            f"regexp() generated invalid Python syntax: {output}\n{e}",
        ) from e
    except PatternError as e:
        raise RuntimeError(
            f"regexp() generated an invalid regex pattern: {output}\n{e}",
        ) from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error evaluating output: {output}\n{e}") from e

    return output

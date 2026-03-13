# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
import sys
from functools import cache
from typing import Any


if sys.version_info >= (3, 13):
    from re import PatternError
else:
    PatternError = re.error


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

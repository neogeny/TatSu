# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import codecs
import functools
import hashlib
import re
import unicodedata
from collections import namedtuple
from collections.abc import Iterable
from io import StringIO
from typing import Any

from .common import isreserved


def linecount(s: str) -> int:
    """
    Return the number of lines in the string using the "editor view".

    In this convention, a string is treated as a sequence of lines separated
    by line breaks. An empty string is considered to contain a single
    empty line (Line 1), ensuring consistency with how IDEs and text
    editors represent buffers.
    """
    return 1 + sum(1 for _ in re.finditer(r"(?m)\r?\n|\r", s))


def ismultiline(s: str) -> int:
    return bool(re.search(r"(?m)[\r\n]", s))


lcnt = namedtuple('lcnt', 'totl blnk cmnt code')


def countlines(s: str, cmtstr: str = r'#') -> lcnt:
    """
    Counts Source Lines of Code (SLOC) using an 'Editor View' semantic.

    Categorizes lines as code, comment, or blank based on the first
    meaningful character. Line totals follow the '1 + separators' rule.
    An empty string is treated as 0 lines.

    Args:
        s: The input string to analyze.
        cmtstr: The character or regex class representing a comment start.

    Returns:
        An lcnt namedtuple: (totl, blnk, cmnt, code).
    """
    # by Gemini 2026-03-15
    # if not s:
    #     return lcnt(totl=0, blnk=0, cmnt=0, code=0)

    pattern = re.compile(fr"""(?xm)
        (?:
              (?P<cmnt> [ \t]* [{cmtstr}] )
            | (?P<code> [ \t]* \S )
            | (?P<blnk> [ \t]* )
        )
        .*?
        (?P<brks> \r?\n | \r | $ )
    """)

    # Every non-empty string produces one extra zero-width match at EOF.
    # Initializing at -1 compensates for this phantom match.
    totl = 0
    blnk_count = 0
    cmnt_count = 0
    code_count = 0
    brks_count = 0

    for match in pattern.finditer(s):
        if match.start() == len(s) and totl > 0:
            break
        groups = match.groupdict()

        is_cmnt = groups['cmnt'] is not None
        is_code = groups['code'] is not None
        is_blnk = groups['blnk'] is not None
        is_brks = groups['brks'] is not None

        totl += 1
        cmnt_count += is_cmnt
        code_count += is_code
        blnk_count += is_blnk
        brks_count += is_brks

    result = lcnt(
        totl=totl,
        blnk=blnk_count,
        cmnt=cmnt_count,
        code=code_count,
    )

    assert totl == blnk_count + cmnt_count + code_count, f'{totl} != {blnk_count} + {cmnt_count} + {code_count}'
    return result


def unicode_display_len(text: str) -> int:
    # by Gemini 2026/02/17 (with many ammendments)
    """
    Calculates the display width of a string in a terminal or
    fixed-width font context.
    """
    assert isinstance(text, str), repr(text)

    def uwidth(c: str) -> int:
        status = unicodedata.east_asian_width(c)
        return 1 + int(status in {'W', 'F'})

    return sum(uwidth(s) for s in text)


def hasha(text: Any) -> str:
    """
    Generates an SHA-256 hex digest of the provided object.
    """
    # by Gemini (- 2026-02-08)
    # by [apalala@gmail.com](https://github.com/apalala)

    # hashlib requires bytes, so encode the string to UTF-8
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()


def eval_escapes(s: str | bytes) -> str | bytes:
    """
    Given a string, evaluate escape sequences starting with backslashes as
    they would be evaluated in Python source code. For a list of these
    sequences, see: https://docs.python.org/3/reference/lexical_analysis.html

    This is not the same as decoding the whole string with the 'unicode-escape'
    codec, because that provides no way to handle non-ASCII characters that are
    literally present in the string.
    """
    # by Rob Speer

    escape_sequence_re: re.Pattern = re.compile(r"""(?ux)
        ( \\U........      # 8-digit Unicode escapes
        | \\u....          # 4-digit Unicode escapes
        | \\x..            # 2-digit Unicode escapes
        | \\[0-7]{1,3}     # Octal character escapes
        | \\N\{[^}]+}      # Unicode characters by name
        | \\[\\'"abfnrtv]  # Single-character escapes
        )""")

    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return escape_sequence_re.sub(decode_match, s)  # type: ignore[no-matching-overload]


def trim(text, tabwidth=4):
    """
    Trim text of common, leading whitespace.

    Based on the trim algorithm of PEP 257:
        http://www.python.org/dev/peps/pep-0257/
    """
    if not text:
        return ''
    lines = text.expandtabs(tabwidth).splitlines()
    maxindent = len(text)
    indent = maxindent
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    trimmed = [lines[0].strip()] + [line[indent:].rstrip() for line in lines[1:]]
    i = 0
    while i < len(trimmed) and not trimmed[i]:
        i += 1
    return '\n'.join(trimmed[i:])


def indent(text, indent=1, multiplier=4):
    """Indent the given block of text by indent*4 spaces"""
    if text is None:
        return ''
    text = str(text)
    if indent >= 0:
        sindent = ' ' * multiplier * indent
        text = '\n'.join((sindent + t).rstrip() for t in text.splitlines())
    return text


def mangle(name: str) -> str:
    return safe_name(name)


@functools.lru_cache(maxsize=2 * 1024)
def safe_name(name: str, plug: str = "_") -> str:
    """
    Utility to transform a string into a valid Python identifier.
    Raises ValueError for empty inputs or illegal plugs. Handles
    leading digits and reserved hard/soft keywords.
    """
    # with Gemini - January 24, 2026

    if not name:
        raise ValueError("Input string cannot be empty.")
    if not plug or not all(c.isalnum() or c == "_" for c in plug):
        raise ValueError(f"Invalid plug: '{plug}'. Must be non-empty and alphanumeric.")
    if not plug.isidentifier():
        raise ValueError(f"Invalid plug: '{plug}'. Must be valid in identifiers.")

    res = re.sub(r"\W", plug, name)

    if not res.isidentifier():
        res = ''.join(c if c.isalnum() or c == '_' else plug for c in name)

    if not res.isidentifier():
        if res[0].isdigit():
            res = f"_{res}" if plug[0].isdigit() else f"{plug}{res}"
        else:
            res = f"{plug}{res}"

    assert res.isidentifier(), f"Failed to sanitize '{name}' into '{res}'"

    while isreserved(res):
        res = f"{res}{plug}"

    return res


def pythonize_name(name: str) -> str:
    # by Copilot 2026-03-06
    if not name:
        return name
    # Convert CamelCase to snake_case
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    # Ensure it's a valid Python identifier
    return safe_name(name)


def prints(*args, **kwargs: Any) -> str:
    with StringIO() as f:
        kwargs['file'] = f
        # kwargs['end'] = ''
        print(*args, **kwargs)
        out = f.getvalue()
        return '\n'.join(out.splitlines(False)).rstrip()


def longest_common_prefix(strs: Iterable[str], suffix: str = '') -> str:
    if not strs:
        return ''

    strs = [s + suffix for s in sorted(strs)]
    if len(strs) == 1:
        return strs[0]

    first = strs[0]
    last = strs[-1]

    i = 0
    m = min(len(first), len(last))
    while i < m and first[i] == last[i]:
        i += 1

    return first[:i]


def without_common_prefix(strs: Iterable[str], suffix: str = '') -> list[str]:
    if not strs:
        return []
    prefix = longest_common_prefix(strs, suffix=suffix)
    return [s.lstrip(prefix) for s in strs]

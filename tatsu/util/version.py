# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause

# NOTE
#   PEP 440: Version Identification and Dependency Specification
#   https://peps.python.org/pep-0440/
#   https://github.com/pypa/packaging

from __future__ import annotations

import re
from collections import namedtuple
from dataclasses import asdict, dataclass
from itertools import takewhile
from typing import Any

from .abctools import rowselect

__all__ = ['Version']


STRIC_VERSION_RE = r'''(?x)
    ^v?
    (?P<epoch>\d+!)?
    (?P<release>\d+(\.\d+)*)
    (?P<pre>[-._]?(a|b|rc)\d*)?
    (?P<post>[-._]?post\d*)?
    (?P<dev>[-._]?dev\d*)?
    (?P<local>\+.*)?
    $
'''

VERSION_RE = r'''(?x)
    ^[vV]?
    (?:(?P<epoch>\d+)!)?
    (?P<release>\d+(\.\d+)*)
    (?:[-._]?(?P<pre>(?!post|dev)(\w+)\d+))?
    (?:[-._]?(?P<post>post\d+))?
    (?:[-._]?(?P<dev>dev\d+))?
    (?:\+(?P<local>[\w\.]+))?
    $
'''

LETTER_NORMALIZATION = {
    'alpha': 'a',
    'beta': 'b',
    'c': 'rc',
    'pre': 'rc',
    'preview': 'rc',
    'rev': 'post',
    'r': 'post',
}


@dataclass(slots=True, kw_only=True)
class Version:
    epoch: Any = None
    major: int | None = None
    minor: int | None = None
    micro: int | None = None
    nano: tuple[int, ...] | None = None
    level: str | None = None
    serial: int | None = None
    post: Any = None
    dev: Any = None
    local: Any = None

    def __str__(self):
        return str(self.astuple())

    def astuple(self):
        notnone = {
            name: value for name, value in asdict(self).items() if value is not None
        }
        return namedtuple('version_info', notnone.keys())(*notnone.values())

    @staticmethod
    def parse(versionstr: str) -> Version:
        match = re.match(VERSION_RE, versionstr)
        if not match:
            raise ValueError(f'Invalid version string: {versionstr!r}')

        def alphadigit_split(s: str) -> tuple[str, int | str]:
            if not s:
                return None, None  # type: ignore

            alpha = ''.join(takewhile(str.isalpha, s))
            digits = s[len(alpha) :]
            if digits.isdigit():
                digits = int(digits)
            return alpha, digits

        parts = match.groupdict()
        release = tuple(int(d) for d in parts['release'].split('.'))
        parts['release'] = release

        pre = parts['pre'] or ''
        pre, num = alphadigit_split(pre.lstrip('_-.'))
        pre = LETTER_NORMALIZATION.get(pre, pre)
        pre = (pre, num)
        parts['pre'] = pre
        level, serial = pre
        serial = int(serial) if serial else None

        major, minor, micro, *nano = release + (None,) * 3
        nano = tuple(int(n) for n in nano if n is not None) or None

        for key in ('epoch', 'post', 'dev', 'local'):
            parts[key] = alphadigit_split(parts[key])[1]

        return Version(
            major=major,
            minor=minor,
            micro=micro,
            nano=nano,
            level=level,
            serial=serial,
            **rowselect({'epoch', 'post', 'dev', 'local'}, parts),
        )

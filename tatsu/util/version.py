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
    (?P<epoch>\d+!)?
    (?P<release>\d+(\.\d+)*)
    # (?P<nano>\.\d+(\.d+)*)?
    # (?P<pre>(a|b|rc)\d+)?
    (?P<pre>(\w+)\d+)?
    (?P<post>\.post\d+)?
    (?P<dev>\.dev\d+)?
    (?P<local>\+[\w\.]+)?
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
    major: int | None = None
    minor: int | None = None
    micro: int | None = None
    nano: tuple[int, ...] | None = None
    releaselevel: str | None = None
    serial: int | None = None

    def __str__(self):
        return str(self.astuple())

    def astuple(self):
        notnone = (
            {
                name: value
                for name, value in asdict(self).items()
                if value is not None
            }
        )
        return namedtuple('version_info', notnone.keys())(*notnone.values())

    @staticmethod
    def parse(versionstr: str) -> Version:
        match = re.match(VERSION_RE, versionstr)
        if not match:
            raise ValueError(f'Invalid version string: {versionstr!r}')

        parts = match.groupdict()
        release = tuple(int(d) for d in re.split(r'[.]', parts['release']))
        parts['release'] = release

        nano = parts.get('nano')
        if nano:
            nano = tuple(int(d) for d in re.split(r'[.]', nano[1:]))
            parts['nano'] = nano

        pre = parts['pre']
        if not pre:
            pre = ()
        else:
            _, pre, num = re.split(r'(\D+)', pre, maxsplit=1)
            pre = LETTER_NORMALIZATION.get(pre, pre)
            pre = (pre, int(num))
            parts['pre'] = pre

        major, minor, micro, *nano = release + (None,) * 3
        nano = tuple(n for n in nano if n is not None)
        nano = tuple(int(n) for n in nano) if nano else None

        releaselevel, serial, *_ = pre + (None,) * 2
        releaselevel = str(releaselevel) if releaselevel else None
        serial = int(serial) if serial else None

        return Version(
            major=major, minor=minor, micro=micro, nano=nano,
            releaselevel=releaselevel, serial=serial,
        )

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..util import unicode_display_len as ulen

type Rails = list[str]

ETX = '␃'


def assert_one_length(rails: Rails) -> Rails:
    if not rails:
        return []

    length = ulen(rails[0])

    def one_length(rail: str) -> bool:
        check = isinstance(rail, str) and ulen(rail) == length
        assert check, f'ulen({rail=!r}) != {length=}'
        return check

    assert all(one_length(rail) for rail in rails), 'lengths differ'
    return rails


def pad(rrl: str, c: str, maxl: int) -> str:
    return f'{rrl}{c * (maxl - ulen(rrl))}'


def railpad_(rrl: str, maxl: int) -> str:  # name_ for visual alignment
    return pad(rrl, '─', maxl=maxl)


def blankpad(rrl: str, maxl: int) -> str:
    return pad(rrl, ' ', maxl=maxl)


def lay_out(tracks: list[Rails]) -> Rails:
    # by Gemini 2026/02/17

    if not tracks:
        return []
    if len(tracks) == 1:
        return tracks[0]

    maxl = max(ulen(p[0]) if p else 0 for p in tracks)
    out: Rails = []

    for rails in tracks[:-1]:
        assert isinstance(rails, list), f'{rails=!r}'
        if not rails:
            continue

        joint = rails[0]
        if ETX not in joint:
            out += [f"  ├─{railpad_(joint, maxl)}─┤ "]
        else:
            out += [f"  ├─{blankpad(joint, maxl)} │ "]

        for rail in rails[1:]:
            out += [f"  │ {blankpad(rail, maxl)} │ "]

    # the last set of rails
    rails = tracks[-1]
    joint = rails[0]
    if ETX not in joint:
        out += [f"  └─{railpad_(joint, maxl)}─┘ "]
    else:
        corner = "─┘ "
        out[-1] = out[-1][: -len(corner)] + corner
        out += [f"  └─{blankpad(joint, maxl)}   "]

    for rail in rails[1:]:
        out += [f"    {blankpad(rail, maxl)}   "]

    # the first rail
    joint = tracks[0][0] if tracks[0] else ''
    if ETX not in joint:
        out[0] = f"──┬─{railpad_(joint, maxl)}─┬─"
    else:
        out[0] = f"──┬─{blankpad(joint, maxl)} ┬─"

    return assert_one_length(out)


def looptail(rails: Rails, maxl: int) -> Rails:
    out = []
    for line in rails:
        out += [f"  │ {blankpad(line, maxl)} │  "]

    out += [f"  └─{railpad_('', maxl)}<┘  "]

    return assert_one_length(out)


def stopnloop(rails: Rails) -> Rails:
    # by Gemini 2026/02/17
    if not rails:
        return ["───>───"]

    maxl = max(ulen(line) for line in rails)
    out = []

    first = rails[0]
    out += [f"──┬─{railpad_(first, maxl)}─┬──"]

    out += looptail(rails[1:], maxl)
    return assert_one_length(out)


def loop(rails: Rails) -> Rails:
    # by Gemini 2026/02/17
    if not rails:
        return ["───>───"]

    maxl = max(ulen(line) for line in rails)
    out = []

    out += [f"──┬→{railpad_('', maxl)}─┬──"]

    first = rails[0]
    out += [f"  ├→{railpad_(first, maxl)}─┤  "]  # xxx

    out += looptail(rails[1:], maxl)
    return assert_one_length(out)


def weldtwo(left: Rails, right: Rails) -> Rails:
    assert isinstance(left, list), f'{left=!r}'
    assert isinstance(right, list), f'{right=!r}'

    if not right or ETX in left:
        return left[:]
    if not left:
        return right[:]

    len_left = ulen(left[0])
    len_right = ulen(right[0])
    out_height = max(len(left), len(right))
    common_height = min(len(left), len(right))

    out = left[:]
    for i in range(out_height):
        if i < common_height:
            out[i] += right[i]
        elif i < len(out):
            out[i] += f'{'':{len_right}}'
        else:
            out += [f'{'':{len_left}}{right[i]}']

    return assert_one_length(out)


def weld(*tracks: Rails) -> Rails:
    if not tracks:
        return []
    out = tracks[0][:]
    for rails in tracks[1:]:
        out = weldtwo(out, rails)
    return assert_one_length(out)

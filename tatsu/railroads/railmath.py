# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..util import unicode_display_len as ulen

type Rail = str
type Rails = list[Rail]

ETX = '␃'


def assert_one_length(rails: Rails) -> Rails:
    if not rails:
        return []

    length = ulen(rails[0])
    for rail in rails:
        assert isinstance(rail, str), f'{rail=!r}'
        assert ulen(rail) == length
    return rails


def lay_out(tracks: list[Rails]) -> Rails:
    # by Gemini 2026/02/17

    if not tracks:
        return []
    if len(tracks) == 1:
        return tracks[0]

    maxl = max(ulen(p[0]) if p else 0 for p in tracks)
    out: Rails = []

    def lay(rrl: str, c: str) -> str:
        return f'{rrl}{c * (maxl - ulen(rrl))}'

    for rails in tracks[:-1]:
        assert isinstance(rails, list), f'{rails=!r}'
        if not rails:
            continue

        joint = rails[0]
        if ETX not in joint:
            out += [f"  ├─{lay(joint, '─')}─┤ "]
        else:
            out += [f"  ├─{lay(joint, ' ')} │ "]

        for rail in rails[1:]:
            out += [f"  │ {lay(rail, ' ')} │ "]

    # the last set of rails
    rails = tracks[-1]
    joint = rails[0]
    if ETX not in joint:
        out += [f"  └─{lay(joint, '─')}─┘ "]
    else:
        out[-1][-3:-1] = '─┘ '
        out += [f"  └─{lay(joint, ' ')}   "]

    for rail in rails[1:]:
        out += [f"    {lay(rail, ' ')}   "]

    # the first rail
    joint = tracks[0][0] if tracks[0] else ''
    if ETX not in joint:
        out[0] = f"──┬─{lay(joint, '─')}─┬─"
    else:
        out[0] = f"──┬─{lay(joint, ' ')} ┬─"

    return assert_one_length(out)


def looptail(rails: Rails, maxl: int) -> Rails:
    out = []
    for line in rails:
        pad = " " * (maxl - ulen(line))
        out += [f"  │ {line}{pad} │  "]

    loop_rail = "─" * maxl
    out += [f"  └─{loop_rail}<┘  "]

    return assert_one_length(out)


def stopnloop(rails: Rails) -> Rails:
    # by Gemini 2026/02/17
    if not rails:
        return ["───>───"]

    max_w = max(ulen(line) for line in rails)
    out = []

    first = rails[0]
    first_pad = "─" * (max_w - ulen(first))
    out += [f"──┬─{first}{first_pad}─┬──"]

    out += looptail(rails[1:], max_w)
    return assert_one_length(out)


def loop(rails: Rails) -> Rails:
    # by Gemini 2026/02/17
    if not rails:
        return ["───>───"]

    maxl = max(ulen(line) for line in rails)
    out = []

    bypass_pad = "─" * maxl
    out += [f"──┬→{bypass_pad}─┬──"]

    first = rails[0]
    first_pad = "─" * (maxl - ulen(first))
    out += [f"  ├→{first}{first_pad}─┤  "]  # xxx

    out += looptail(rails[1:], maxl)
    return assert_one_length(out)


def weld(left: Rails, right: Rails) -> Rails:
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

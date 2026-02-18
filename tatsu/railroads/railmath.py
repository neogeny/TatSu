# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..util import unicode_display_len as ulen


def assert_one_width(block: list[str]) -> list[str]:
    if not block:
        return []

    width = ulen(block[0])
    for rail in block:
        assert isinstance(rail, str), f'{rail=!r}'
        assert ulen(rail) == width
    return block


def merge(tracks: list[list[str]]) -> list[str]:
    # by Gemini 2026/02/17

    if not tracks:
        return []
    if len(tracks) == 1:
        return [f"───{tracks[0][0]}───"]

    max_w = max(ulen(p[0]) if p else 0 for p in tracks)
    out = []

    main = tracks[0][0] if tracks[0] else ''
    pad0 = "─" * (max_w - ulen(main))
    out += [f"──┬─{main}{pad0}─┬─"]

    for track in tracks[1:-1]:
        if not track:
            continue

        junction = track[0]
        pad_m = "─" * (max_w - ulen(junction))
        out += [f"  ├─{junction}{pad_m}─┤ "]

        for mid in track[1:]:
            pad_m = "─" * (max_w - ulen(mid))
            out += [f"  │ {mid}{pad_m} │ "]

    last = tracks[-1][0] if tracks[-1] else ''
    pad_l = "─" * (max_w - ulen(last))
    out += [f"  └─{last}{pad_l}─┘ "]

    return assert_one_width(out)


def loop_tail(rails: list[str], max_w: int) -> list[str]:
    out = []
    for line in rails:
        pad = " " * (max_w - ulen(line))
        out += [f"  │ {line}{pad} │  "]

    loop_rail = "─" * max_w
    out += [f"  └─{loop_rail}<┘  "]

    return assert_one_width(out)


def loop_plus(rails: list[str]) -> list[str]:
    # by Gemini 2026/02/17
    if not rails:
        return ["───>───"]

    max_w = max(ulen(line) for line in rails)
    out = []

    first = rails[0]
    first_pad = "─" * (max_w - ulen(first))
    out += [f"──┬─{first}{first_pad}─┬──"]

    out += loop_tail(rails[1:], max_w)
    return assert_one_width(out)


def loop(rails: list[str]) -> list[str]:
    # by Gemini 2026/02/17
    if not rails:
        return ["───>───"]

    max_w = max(ulen(line) for line in rails)
    out = []

    bypass_pad = "─" * max_w
    out += [f"──┬→{bypass_pad}─┬──"]

    first = rails[0]
    first_pad = "─" * (max_w - ulen(first))
    out += [f"  ├→{first}{first_pad}─┤  "]  # xxx

    out += loop_tail(rails[1:], max_w)
    return assert_one_width(out)


def concatenate(left: list[str], right: list[str]) -> list[str]:
    assert isinstance(left, list), f'{left=!r}'
    assert isinstance(right, list), f'{right=!r}'

    if not right:
        return left.copy()
    if not left:
        return right.copy()

    left_width = ulen(left[0])
    right_width = ulen(right[0])
    final_height = max(len(left), len(right))
    common_height = min(len(left), len(right))

    out = left.copy()
    for i in range(final_height):
        if i < common_height:
            out[i] += right[i]
        elif i < len(out):
            out[i] += f'{' ' * right_width}'
        else:
            out += [f'{' ' * left_width}{right[i]}']

    return assert_one_width(out)

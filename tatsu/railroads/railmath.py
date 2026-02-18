# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..util import unicode_display_len as ulen

type RailTracks = list[str]


def assert_one_length(tracks: RailTracks) -> RailTracks:
    if not tracks:
        return []

    length = ulen(tracks[0])
    for rail in tracks:
        assert isinstance(rail, str), f'{rail=!r}'
        assert ulen(rail) == length
    return tracks


def lay_out(tracklist: list[RailTracks]) -> RailTracks:
    # by Gemini 2026/02/17

    if not tracklist:
        return []

    maxw = max(ulen(p[0]) if p else 0 for p in tracklist)
    out: RailTracks = []

    for tracks in tracklist[:-1]:
        if not tracks:
            continue
        assert isinstance(tracks, list), f'{tracks=!r}'

        junction = tracks[0]
        pad = "─" * (maxw - ulen(junction))
        out += [f"  ├─{junction}{pad}─┤ "]

        for rail in tracks[1:]:
            pad = " " * (maxw - ulen(rail))
            out += [f"  │ {rail}{pad} │ "]

    last_track = tracklist[-1]
    last_junction = last_track[0]
    pad_l = "─" * (maxw - ulen(last_junction))
    out += [f"  └─{last_junction}{pad_l}─┘ "]

    for rail in last_track[1:]:
        pad = " " * (maxw - ulen(rail))
        out += [f"    {rail}{pad}   "]

    main_junction = tracklist[0][0] if tracklist[0] else ''
    pad = "─" * (maxw - ulen(main_junction))
    out[0] = f"──┬─{main_junction}{pad}─┬─"

    return assert_one_length(out)


def loop_tail(rails: RailTracks, max_w: int) -> RailTracks:
    out = []
    for line in rails:
        pad = " " * (max_w - ulen(line))
        out += [f"  │ {line}{pad} │  "]

    loop_rail = "─" * max_w
    out += [f"  └─{loop_rail}<┘  "]

    return assert_one_length(out)


def stopnloop(rails: RailTracks) -> RailTracks:
    # by Gemini 2026/02/17
    if not rails:
        return ["───>───"]

    max_w = max(ulen(line) for line in rails)
    out = []

    first = rails[0]
    first_pad = "─" * (max_w - ulen(first))
    out += [f"──┬─{first}{first_pad}─┬──"]

    out += loop_tail(rails[1:], max_w)
    return assert_one_length(out)


def loop(rails: RailTracks) -> RailTracks:
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
    return assert_one_length(out)


def weld(left: RailTracks, right: RailTracks) -> RailTracks:
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
            out[i] += f'{'':{right_width}}'
        else:
            out += [f'{'':{left_width}}{right[i]}']

    return assert_one_length(out)

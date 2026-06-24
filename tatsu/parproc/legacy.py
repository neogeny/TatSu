# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable, Generator, Iterable
from pathlib import Path
from typing import Any

from ..packetz import PacketLike
from ..util import identity
from .parproc import parproc
from .task import Func
from .visual import VisualPayload, parproc_visual


def parallel_proc(
    payloads: Iterable[Any],
    process: Callable,
    /,
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    **kwargs: Any,
) -> Generator[PacketLike | None, None, None]:
    yield from parproc(
        process,
        payloads,
        *args,
        pickable=pickable,
        parallel=parallel,
        reraise=reraise,
        **kwargs,
    )


def processing_loop(
    filenames: Iterable[str],
    process: Callable,
    /,
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    max_workers: int | None = None,
    **kwargs: Any,
) -> Generator[PacketLike, None, None]:
    paths = [Path(f) for f in filenames]
    payloads = [VisualPayload(p, p.read_text()) for p in paths]
    yield from parproc_visual(
        process,
        payloads,
        *args,
        pickable=pickable,
        parallel=parallel,
        reraise=reraise,
        max_workers=max_workers,
        **kwargs,
    )

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import multiprocessing
import threading
from collections.abc import Generator, Iterable
from typing import Any, Protocol

from ..util import identity
from .packetz import PacketLike
from .pmap import HAS_MULTITHREADING_SUPPORT, active_pmap
from .task import Event, Func, Task, taskproc


__all__ = [
    'Progress',
    'parproc',
]


class Progress(Protocol):
    def update(self, *args, **kwargs) -> None: ...
    def stop(self) -> None: ...


def parproc(
    func: Func,
    payloads: Iterable[Any],
    /,
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    max_workers: int | None = None,
    **kwargs: Any,
) -> Generator[PacketLike, None, None]:
    stop: Event = threading.Event()
    if not HAS_MULTITHREADING_SUPPORT:
        stop = multiprocessing.Manager().Event()

    tasks = [
        Task(
            stop=stop,
            func=func,
            payload=payload,
            pickable=pickable,
            reraise=reraise,
            args=args,
            kwargs=kwargs,
        )
        for payload in payloads
    ]
    if len(tasks) == 1:
        yield taskproc(tasks[0])
        return

    if not parallel:
        yield from map(taskproc, tasks)
    else:
        pmap = active_pmap()
        yield from pmap(stop, taskproc, tasks, max_workers)

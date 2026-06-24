# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import multiprocessing
import threading
from collections.abc import Generator, Iterable
from typing import Any, Protocol

from ..packetz import PacketLike
from ..packetz.api import init_queue
from ..util import identity
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

    queue = init_queue()
    tasks = [
        Task(
            stop=stop,
            func=func,
            payload=payload,
            queuepath=queue.path,
            pickable=pickable,
            reraise=reraise,
            args=args,
            kwargs=kwargs,
        )
        for payload in payloads
    ]

    yield from queue.receive()
    if len(tasks) == 1:
        yield taskproc(tasks[0])
        yield from queue.receive()
        return

    yield from queue.receive()
    if not parallel:
        yield from map(taskproc, tasks)
    else:
        pmap = active_pmap()
        for r in pmap(stop, taskproc, tasks, max_workers):
            yield from queue.receive()
            yield r
    yield from queue.receive()

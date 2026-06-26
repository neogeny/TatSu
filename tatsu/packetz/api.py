# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Process-safe packet queue for cross-worker communication.

Defines a Packet protocol, a default dataclass implementation, and
sync/async receivers for draining a multiprocessing.Queue.
"""

from __future__ import annotations

import atexit
import contextlib
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

from .packet import Packet, PacketLike, WithID
from .queue import PACKETZ_DIR, PacketzQueue


__all__ = [
    'send',
    'receive',
    'receive_async',
    'Packet',
    'PacketLike',
    'WithID',
]

_the_queue: PacketzQueue | None = None
_cleanup_registered = False
_defer_deinit_queues: set[PacketzQueue] = set()


def init_queue(
    q: PacketzQueue | None = None,
    keep: bool | None = None,
) -> PacketzQueue:
    global _the_queue, _cleanup_registered  # noqa: PLW0603

    path = q.path if q is not None else None
    q = PacketzQueue(path)
    _the_queue = q

    if keep is None:
        keep = bool(k := os.environ.get("PACKETZ_KEEP", "").lower()) and (
            k
            not in {
                "0",
                "false",
                "no",
            }
        )

    if not keep:
        _defer_deinit_queues.add(q)
        if not _cleanup_registered:
            atexit.register(_cleanup_queue_files)
            _cleanup_registered = True

    return q


def send(*, to: str | None = None, data: Any = None) -> PacketLike:
    assert _the_queue is not None
    return _the_queue.send(to=to, data=data)


def receive() -> Generator[PacketLike, None, None]:
    assert _the_queue is not None
    return _the_queue.receive()


async def receive_async() -> AsyncGenerator[PacketLike, None]:
    assert _the_queue is not None
    async for pkt in _the_queue.receive_async():
        yield pkt


def _cleanup_queue_files():
    import multiprocessing

    if multiprocessing.current_process().name != "MainProcess":
        return
    for q in list(_defer_deinit_queues):
        path = q.path
        with contextlib.suppress(OSError):
            path.unlink(missing_ok=True)
    with contextlib.suppress(OSError):
        PACKETZ_DIR.rmdir()

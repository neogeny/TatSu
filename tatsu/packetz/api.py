# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Process-safe packet queue for cross-worker communication.

Defines a Packet protocol, a default dataclass implementation, and
sync/async receivers for draining a multiprocessing.Queue.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

from .packet import Packet, PacketLike, WithID
from .queue import QueueState, new_file_path


__all__ = [
    'send',
    'receive',
    'receive_async',
    'Packet',
    'PacketLike',
    'WithID',
]


_the_queue: QueueState | None = None


def init_queue(path: Path | str | None = None) -> QueueState:
    global _the_queue  # noqa: PLW0603
    if path is None:
        path = new_file_path()
    _the_queue = QueueState(path)
    return _the_queue


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

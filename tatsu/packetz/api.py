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
from .queue import QueueState


__all__ = [
    'send',
    'receive',
    'receive_async',
    'Packet',
    'PacketLike',
    'WithID',
]


PACKETZ_QUEUE: Path = QueueState.path
QueueState.init()


def send(*, to: str | None = None, data: Any = None) -> PacketLike:
    return QueueState.send(to=to, data=data)


def receive() -> Generator[PacketLike, None, None]:
    return QueueState.receive()


async def receive_async() -> AsyncGenerator[PacketLike, None]:
    async for pkt in QueueState.receive_async():
        yield pkt

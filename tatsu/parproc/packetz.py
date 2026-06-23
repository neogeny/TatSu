# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Process-safe packet queue for cross-worker communication.

Defines a Packet protocol, a default dataclass implementation, and
sync/async receivers for draining a multiprocessing.Queue.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

from ..util.asjson import AsJSONMixin, asjson
from ..util.fromjson import JSONBase, fromjson
from ..util.misc import new_id


PACKETZ_QUEUE = Path(f"./{__name__.split('.')[-1]}.jsonl")
PACKETZ_QUEUE.unlink(missing_ok=True)
with PACKETZ_QUEUE.open("w") as f:
    pass
_the_queue = PACKETZ_QUEUE.open("rt")
_the_seek: int = 0
_the_seen: dict[str, PacketLike] = {}


class HasID(AsJSONMixin):
    id: str


class PacketLike(HasID):
    """Minimal packet: anything with a uuid attribute."""

    to: str | None
    data: Any


class WithID(HasID, JSONBase):
    id: str = "0xBAAD"

    def __new__(cls, *args, **kwargs):
        new = super().__new__(cls)
        new.id = new_id()
        return new


class Packet(PacketLike, WithID):
    """Default packet implementation with an auto-generated UUID."""

    to: str | None = None
    data: Any = None

    def __init__(self, /, *, to: str | None = None, data: Any = None):
        if to is not None:
            self.to = to
        if data is not None:
            self.data = data


def tty_escape(s: str) -> str:
    return s.replace('\\u001b', '\\e')


def tty_unescape(s: str) -> str:
    return s.replace('\\e', '\\u001b')


def pack(packet: PacketLike) -> str:
    value = asjson(packet)
    serial = json.dumps(
        value,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return tty_escape(serial)


def unpack(serial: str) -> PacketLike:
    value = json.loads(tty_unescape(serial))
    packet = fromjson(value)
    return packet


def send(*, to: str | None = None, data: Any = None) -> PacketLike:
    """Push a packet onto the shared process-safe queue."""
    packet = Packet(to=to, data=data)
    serial = pack(packet)
    with PACKETZ_QUEUE.open("at") as queue:
        queue.write(serial + "\n")
    return packet


def receive() -> Generator[PacketLike, None, None]:
    """Drain all currently available packets from the queue."""
    global _the_seek  # noqa: PLW0603
    with PACKETZ_QUEUE.open("rt") as queue:
        queue.seek(_the_seek)
        for serial in queue.readlines():
            packet = unpack(serial)
            if packet.id in _the_seen:
                continue
            _the_seen[packet.id] = packet
            _the_seek = queue.tell()
            assert _the_seek > 0
            yield packet


async def receive_async() -> AsyncGenerator[PacketLike, None]:
    """Drain available packets in bursts, yielding control to the event loop when empty."""
    try:
        while True:
            for msg in receive():
                yield msg

            await asyncio.sleep(0.01)

    except asyncio.CancelledError:  # noqa # type: ignore
        raise

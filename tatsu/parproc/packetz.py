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
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import cast

from ..util.asjson import AsJSONMixin, asjson
from ..util.fromjson import JSONBase, fromjson


PACKETZ_QUEUE = Path("./queue.jsonl")
PACKETZ_QUEUE.unlink(missing_ok=True)
with PACKETZ_QUEUE.open("w") as f:
    pass
_the_queue = PACKETZ_QUEUE.open("rt")
_the_seek: int = 0
_the_seen: dict[str, Packet] = {}


def new_uuid_hex() -> str:
    """Generate a random hex UUID string."""
    return uuid.uuid1().hex


class Packet(AsJSONMixin):
    """Minimal packet: anything with a uuid attribute."""

    uuid_id: str
    uuid_to: str | None


class PacketImpl(Packet, JSONBase):
    """Default packet implementation with an auto-generated UUID."""

    uuid_id: str = "0xBAAD"
    uuid_to: str | None = None

    def __new__(cls, *args, **kwargs):
        new = super().__new__(cls)
        new.uuid_id = new_uuid_hex()
        return new

    def __init__(self, to: str | None = None):
        if to is not None:
            self.uuid_to = to


def send(packet: Packet) -> None:
    """Push a packet onto the shared process-safe queue."""
    value = asjson(packet)
    serial = json.dumps(value, separators=(",", ":"))
    with PACKETZ_QUEUE.open("at") as queue:
        queue.write(serial + "\n")


def receive() -> Generator[Packet, None, None]:
    """Drain all currently available packets from the queue."""
    global _the_seek  # noqa: PLW0603
    with PACKETZ_QUEUE.open("rt") as queue:
        queue.seek(_the_seek)
        for serial in _the_queue.readlines():
            value = json.loads(serial)
            packet = fromjson(value)
            print(f"HERE {packet.uuid_id}")
            yield cast(Packet, packet)
        _the_seek = queue.tell()


async def receive_async() -> AsyncGenerator[Packet, None]:
    """Drain available packets in bursts, yielding control to the event loop when empty."""
    try:
        while True:
            for msg in receive():
                yield msg

            await asyncio.sleep(0.01)

    except asyncio.CancelledError:  # noqa # type: ignore
        raise

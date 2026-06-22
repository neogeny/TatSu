# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Process-safe packet queue for cross-worker communication.

Defines a Packet protocol, a default dataclass implementation, and
sync/async receivers for draining a multiprocessing.Queue.
"""

from __future__ import annotations

import asyncio
import dataclasses
import multiprocessing
import queue
import uuid
from collections.abc import AsyncGenerator, Generator
from typing import Protocol


__the_queue: multiprocessing.Queue = multiprocessing.Queue()


class Packet(Protocol):
    """Minimal packet: anything with a uuid attribute."""

    uuid: str


def new_uuid_hex() -> str:
    """Generate a random hex UUID string."""
    return uuid.uuid4().hex


@dataclasses.dataclass(slots=True, order=True)
class PacketImpl:
    """Default packet implementation with an auto-generated UUID."""

    _uuid: str = dataclasses.field(init=False, default_factory=new_uuid_hex)

    @property
    def uuid(self) -> str:
        return self._uuid


def send(packet: Packet) -> None:
    """Push a packet onto the shared process-safe queue."""
    __the_queue.put(packet)


def receive() -> Generator[Packet, None, None]:
    """Drain all currently available packets from the queue."""
    while True:
        try:
            yield __the_queue.get_nowait()
        except queue.Empty:
            break


async def receive_async() -> AsyncGenerator[Packet, None]:
    """Drain available packets in bursts, yielding control to the event loop when empty."""
    try:
        while True:
            for msg in receive():
                yield msg

            option = 1
            if option == 1:
                await asyncio.sleep(0.01)
            elif option == 2:
                loop = asyncio.get_running_loop()
                msg = await loop.run_in_executor(None, __the_queue.get)
                yield msg

    except asyncio.CancelledError:  # noqa # type: ignore
        raise

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Process-safe packet queue for cross-worker communication.

Defines a Packet protocol, a default dataclass implementation, and
sync/async receivers for draining a multiprocessing.Queue.
"""

from __future__ import annotations

import asyncio
import multiprocessing
import queue
import uuid
from collections.abc import AsyncGenerator, Generator
from typing import Protocol, runtime_checkable


__the_queue: multiprocessing.Queue = multiprocessing.Queue()


def new_uuid_hex() -> str:
    """Generate a random hex UUID string."""
    return uuid.uuid4().hex


@runtime_checkable
class Packet(Protocol):
    """Minimal packet: anything with a uuid attribute."""

    @property
    def uuid(self) -> str: ...

    @property
    def dest_uuid(self) -> str | None: ...


class PacketImpl(Packet):
    """Default packet implementation with an auto-generated UUID."""

    _uuid: str = "0xBAAD"
    _dest_uuid: str | None = None

    def __new__(cls, *args, **kwargs):
        new = super().__new__(cls)
        new._uuid = new_uuid_hex()
        return new

    def __init__(self, dest_uuid: str | None = None):
        if dest_uuid is not None:
            self._dest_uuid = dest_uuid

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def dest_uuid(self) -> str | None:
        return self._dest_uuid


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

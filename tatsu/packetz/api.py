# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Process-safe packet queue for cross-worker communication.

Defines a Packet protocol, a default dataclass implementation, and
sync/async receivers for draining a multiprocessing.Queue.
"""

from __future__ import annotations

from .packet import Packet, PacketLike, WithID
from .queue import PacketzQueue


__all__ = [
    'Packet',
    'PacketLike',
    'PacketzQueue',
    'WithID',
]

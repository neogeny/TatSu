# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import json
import re
from typing import Any

from ..util.asjson import AsJSONMixin, asjson
from ..util.debugging import ERROR_print
from ..util.fromjson import JSONBase, fromjson
from ..util.misc import hash2str, new_id
from ..util.tty import tty_escape, tty_unescape
from .compact import compact_value, decompact_value


HASH_PATTERN = r'^\{"hash":"([\w\d]+)","data":(.*?)\}$'


class PacketError(Exception):
    pass


class CannotUnPacketError(PacketError):
    pass


class BadPacketError(PacketError):
    pass


class PacketHashError(BadPacketError):
    pass


class HasID(AsJSONMixin):
    id: str


class PacketLike(HasID):
    to: str | None
    data: Any


class WithID(HasID, JSONBase):
    id: str = "0xBAAD"

    def __new__(cls, *_args, **_kwargs):
        new = super().__new__(cls)
        new.id = new_id()
        return new


class Packet(PacketLike, WithID):
    to: str | None = None
    data: Any = None

    def __init__(self, /, *, to: str | None = None, data: Any = None):
        if to is not None:
            self.to = to
        if data is not None:
            self.data = data


def hashed(data: str) -> str:
    hash = hash2str(data)
    hashed = f'{{"hash":"{hash}","data":{data}}}'
    return hashed


def unhashed(hashed: str) -> str:
    if not (m := re.match(HASH_PATTERN, hashed)):
        raise ERROR_print(
            f"checksum missing: {hashed}",
            extype=BadPacketError,
        )
    try:
        hash, data = m.group(1, 2)
    except (AttributeError, IndexError, re.error) as e:
        raise ERROR_print(
            f"invalid packet: {hashed}",
            extype=BadPacketError,
        ) from e

    actual = hash2str(data)
    if hash != actual:
        raise ERROR_print(
            f"checksum mismatch: {hash} != {actual}",
            extype=PacketHashError,
        )
    return data


def pack(packet: PacketLike) -> str:
    value: Any = asjson(packet)
    value = compact_value(value)
    value = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    value = class_escape(value)
    value = tty_escape(value)
    return hashed(value)


def unpack(hashed: str) -> PacketLike:
    try:
        value: Any = unhashed(hashed)
        value = tty_unescape(value)
        value = class_unescape(value)
        value = json.loads(value)
        value = decompact_value(value)
        return fromjson(value)
    except PacketError:
        raise
    except Exception as e:
        raise CannotUnPacketError(e) from e


def class_escape(s: str) -> str:
    return s.replace(r'"__class__":', '"@":')


def class_unescape(s: str) -> str:
    return s.replace(r'"@":', r'"__class__":')

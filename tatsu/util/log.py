# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import io
import sys
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


__all__ = ['logctx', 'iso_logpath', 'startscript']


def startscript() -> str:
    import __main__ as main

    if main.__package__:
        return main.__package__
    elif isinstance(getattr(main, '__file__', None), str):
        return Path(main.__file__).name
    else:
        return 'unknown'


def iso_timestamp() -> str:
    now = datetime.now(UTC)
    isostr = now.isoformat(timespec='seconds')
    return isostr.replace(':', '-').replace('+00-00', 'Z')


def iso_logpath(prefix: str, basdir: str = "log", suffix: str = '.log') -> Path:
    ts = iso_timestamp()
    logdir = Path(basdir)
    logdir.mkdir(parents=True, exist_ok=True)
    suffix = suffix if suffix.startswith('.') else '.' + suffix
    return logdir / f"{prefix}_{ts}{suffix}"


@contextmanager
def logctx(logpath: Path | None) -> Generator[io.TextIOBase, None, None]:
    if isinstance(logpath, Path):
        with logpath.open(mode="a", encoding="utf-8") as logfile:
            yield logfile
    else:
        yield sys.stderr

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def iso_timestamp() -> str:
    """
    Returns an ISO 8601 string with UTC timezone (Z).
    Example: '2026-02-15T22-15-01Z'
    """
    now = datetime.now(timezone.utc)
    isostr = now.isoformat(timespec='seconds')
    return isostr.replace(':', '-').replace('+00-00', 'Z')

def iso_logpath(prefix: str, basdir: str = "log", suffix='.log') -> Path:
    """Helper to generate a pathlib.Path using the ISO timestamp."""
    ts = iso_timestamp()
    logdir = Path(basdir)
    logdir.mkdir(parents=True, exist_ok=True)
    suffix = suffix if suffix.startswith('.') else '.' + suffix
    return logdir / f"{prefix}_{ts}{suffix}"

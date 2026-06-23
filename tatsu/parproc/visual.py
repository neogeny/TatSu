# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
import time
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import Any

from ..log import iso_logpath, logctx, startscript
from ..util import debugging, identity
from .packetz import Packet
from .parproc import Progress, parproc
from .payload import VisualPayload
from .result import Result
from .summary import show_result, show_summary
from .task import Func, VisualFunc


def parproc_visual(
    func: VisualFunc,
    payloads_in: Iterable[VisualPayload | str],
    /,
    progress_in: Progress | None = None,
    *args: Any,
    eprint: Func = debugging.eprint,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    summary: bool = True,
    verbose: bool = True,
    max_workers: int | None = None,
    usecolor: bool = True,
    **kwargs: Any,
) -> Generator[Packet, None, None]:
    from ..barz import BarRow, Col, Multi
    from ..ztyle import Color

    # NOTE resolve iterator now because we know that processing will do it anyway
    payloads_in = list(payloads_in)
    total = len(payloads_in)

    style = Color(usecolor).style()
    f = style.green()

    b = style.black().bold()

    multi = None
    if progress_in is not None:
        progress: Progress = progress_in  # type: ignore # pyright: ignore[reportAssignmentType]
    else:
        progress = BarRow(
            total=total,
            fill="---",
            style=[f, f, b],
            cols=[Col.bar, Col.padding, Col.label],
            width=47,
        )
        multi = Multi([], out=sys.stderr)
        eprint = multi.print

        multi.add_row(progress)
        progress.start()
        multi.start()

    # HACK backwards compatibility
    is_legacy = all(isinstance(p, str) for p in payloads_in)
    payloads: list[VisualPayload] = (  # type: ignore # pyright: ignore[reportAssignmentType]
        payloads_in  # type: ignore
        if not is_legacy
        else [VisualPayload(path=Path(str(p)), payload=None) for p in payloads_in]
    )
    filenames = [str(p.path) for p in payloads]

    logpath = None
    if len(filenames) > 1:
        prefix = startscript().replace('.', '_')
        logpath = iso_logpath(prefix=prefix)

    start_time = time.time()
    packets: Iterable[Packet] = parproc(
        func,
        payloads,
        *args,
        pickable=pickable,
        parallel=parallel,
        reraise=reraise,
        max_workers=max_workers,
        **kwargs,
    )

    def process_packets(results: Iterable[Packet]) -> Generator[Packet]:
        count = 0
        for packet in results:
            if packet is None:
                continue
            if not isinstance(packet, Result):
                yield packet
                continue

            result: Result = packet
            count += 1
            path = result.payload.path
            progress.update(count, total, label=path.name)
            if verbose:
                show_result(eprint, result)

            if result.exception:
                with logctx(logpath) as log:
                    print('ERROR:', result.payload, file=log)
                    print(result.exception, file=log)
                if reraise:
                    raise result.exception

            if is_legacy:
                result.payload = result.payload.path
            yield result

    packets = process_packets(packets)
    if summary or is_legacy:
        results: list[Result] = [p for p in packets if isinstance(p, Result)]
        packets = show_summary(
            start_time,
            results,
            # eprint=multi.print if multi else eprint,
            verbose=True,
        )

    if is_legacy:
        packets = list(packets)

    if multi is not None:
        multi.stop()

    yield from packets

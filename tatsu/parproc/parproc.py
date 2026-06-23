# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import multiprocessing
import sys
import sysconfig
import threading
import time
from collections.abc import Callable, Generator, Iterable, Mapping
from dataclasses import dataclass
from itertools import batched
from pathlib import Path
from pickle import PickleError, PicklingError
from threading import Event
from typing import Any, NamedTuple, Protocol

from ..log import iso_logpath, logctx, startscript
from ..util import debugging, identity, memory_use
from . import packetz
from .packetz import Packet
from .result import Result
from .summary import show_result, show_summary


__all__ = [
    'TaskID',
    'Progress',
    'parallel_proc',
    'parproc',
    'processing_loop',
    'GIL_DISABLED',
    'HAS_MULTITHREADING_SUPPORT',
]

GIL_DISABLED = sysconfig.get_config_var("Py_GIL_DISABLED")
HAS_MULTITHREADING_SUPPORT = GIL_DISABLED


class TaskID(Protocol): ...


class Progress(Protocol):
    def update(self, *args, **kwargs) -> None: ...
    def stop(self) -> None: ...


type Func = Callable[..., Any]
type VisualFunc = Callable[..., Any]


class Payload(Protocol):
    path: Path
    payload: Any

    def raises(self) -> tuple[type[Exception], ...]:
        return ()


class StrPayload(str, Payload):
    __slots__ = ()

    @property
    def path(self) -> Path:  # type: ignore
        return Path(self)

    @property
    def payload(self) -> Any:  # type: ignore
        return Path(self).read_text()


@dataclass(slots=True)
class VisualPayload(Payload):
    path: Path
    payload: Any


class TaskStop(Exception):
    pass


class Task(NamedTuple):
    stop: Event
    func: Func
    payload: Any
    pickable: Callable
    reraise: bool
    args: Iterable[Any]
    kwargs: Mapping[str, Any]


# NOTE: backwards compatibility
def parallel_proc(
    payloads: Iterable[Any],
    process: Callable,
    /,
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    **kwargs: Any,
) -> Generator[Packet | None, None, None]:
    yield from parproc(
        process,
        payloads,
        *args,
        pickable=pickable,
        parallel=parallel,
        reraise=reraise,
        **kwargs,
    )


def parproc(
    func: Func,
    payloads: Iterable[Any],
    /,
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    max_workers: int | None = None,
    **kwargs: Any,
) -> Generator[Packet, None, None]:
    stop: Event = threading.Event()
    if not HAS_MULTITHREADING_SUPPORT:
        stop = multiprocessing.Manager().Event()

    tasks = [
        Task(
            stop=stop,
            func=func,
            payload=payload,
            pickable=pickable,
            reraise=reraise,
            args=args,
            kwargs=kwargs,
        )
        for payload in payloads
    ]
    if len(tasks) == 1:
        yield taskproc(tasks[0])
        return

    if not parallel:
        yield from map(taskproc, tasks)
    else:
        pmap = active_pmap()
        yield from pmap(stop, taskproc, tasks, max_workers)


def taskproc(task: Task) -> Result:
    if task.stop.is_set():
        return Result(task.stop, task.payload)

    result = Result(task.stop, task.payload)
    outcome: Any = None
    elapsed: float = 0.0
    prev_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(2**16)
    try:
        start_time = time.thread_time()
        try:
            outcome = task.func(task.payload, *task.args, **task.kwargs)
        except TypeError:
            if not isinstance(task.payload, VisualPayload):
                raise

            # HACK add backwards compatibility
            outcome = task.func(task.payload.path, *task.args, **task.kwargs)

        elapsed = time.thread_time() - start_time
    except RuntimeError:
        raise
    except (Exception, RecursionError) as e:
        result.exception = e
        if task.reraise or (
            (raises := task.payload.raises())
            and not any(isinstance(e, r) for r in raises)
        ):
            raise
    finally:
        sys.setrecursionlimit(prev_limit)
        result.runtime = elapsed
        result.outcome = task.pickable(outcome)
    result.linecount = getattr(outcome, 'linecount', 0)
    result.memory = memory_use()
    return result


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


# NOTE: backwards compatibility
def processing_loop(
    filenames: Iterable[str],
    process: Callable,
    /,
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    max_workers: int | None = None,
    **kwargs: Any,
) -> Generator[Packet, None, None]:
    paths = [Path(f) for f in filenames]
    payloads = [VisualPayload(p, p.read_text()) for p in paths]
    yield from parproc_visual(
        process,
        payloads,
        *args,
        pickable=pickable,
        parallel=parallel,
        reraise=reraise,
        max_workers=max_workers,
        **kwargs,
    )


def active_pmap() -> Callable[
    [Event, Func, Iterable[Any], int | None], Iterable[Packet]
]:
    import multiprocessing
    from concurrent.futures import (
        Executor,
        # NOTE from Python 3.14 onwards
        ProcessPoolExecutor,
        ThreadPoolExecutor,
        as_completed,
    )

    def executor_pmap(
        executorcls: type[Executor],
        stop_event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Packet]:
        # by Copilot 2026-03-06

        if not tasks:
            return

        with executorcls(max_workers=max_workers) as ex:  # type: ignore
            try:
                futures = [ex.submit(process, task) for task in tasks]
                while futures:
                    yield from packetz.receive()
                    finished = [f for f in futures if f.done()]
                    for f in finished:
                        futures.remove(f)
                        yield f.result()
                    if futures:
                        time.sleep(0.01)
                yield from packetz.receive()
                # futures = [ex.submit(process, task) for task in tasks]
                # yield from packetz.receive()
                # for future in as_completed(futures):
                #     yield from packetz.receive()
                #     yield future.result()
            except KeyboardInterrupt:
                stop_event.set()

                print(file=sys.stderr)
                print(file=sys.stderr)
                print("Wait...", file=sys.stderr)
                sys.stderr.flush()

                ex.shutdown(wait=False, cancel_futures=True)

                print("           ", end="\r", file=sys.stderr)
                sys.stderr.flush()

                raise
        yield from packetz.receive()

    def thread_pmap(
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Packet]:
        yield from executor_pmap(
            ThreadPoolExecutor,
            event,
            process,
            tasks,
            max_workers=max_workers or multiprocessing.cpu_count(),
        )

    def process_pmap(
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Packet]:
        try:
            yield from executor_pmap(
                ProcessPoolExecutor,
                event,
                process,
                tasks,
                max_workers=max_workers or multiprocessing.cpu_count(),
            )
        except (TypeError, PicklingError, PickleError):
            raise
            # yield from thread_pmap(event, process, tasks, max_workers)
        except KeyboardInterrupt:
            return

    if sys.version_info >= (3, 14):
        from concurrent.futures import InterpreterPoolExecutor

        def interpreter_pmap(
            event: Event,
            process: Func,
            tasks: Iterable[Any],
            max_workers: int | None = None,
        ) -> Iterable[Packet]:
            try:
                yield from executor_pmap(
                    InterpreterPoolExecutor,
                    event,
                    process,
                    tasks,
                    max_workers=max_workers or multiprocessing.cpu_count(),
                )
            except (TypeError, PicklingError, PickleError):
                yield from thread_pmap(event, process, tasks, max_workers)

    def imap_pmap(process: Func, tasks: Iterable[Any]) -> Iterable[Packet]:
        tasks = list(tasks)
        nworkers = 4 * max(1, multiprocessing.cpu_count())

        n = nworkers * 4
        chunks = batched(tasks, n)

        count = 0
        with multiprocessing.Pool(processes=nworkers) as pool:
            for chunk in chunks:
                count += len(chunk)
                yield from pool.imap_unordered(process, chunk)
        if len(tasks) != count:
            raise RuntimeError(
                'number of chunked tasks different %d != %d' % (len(tasks), count),
            )

    if HAS_MULTITHREADING_SUPPORT:
        return thread_pmap
    return thread_pmap
    # return process_pmap

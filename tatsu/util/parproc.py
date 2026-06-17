# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import io
import sys
import sysconfig
import time
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import batched
from pathlib import Path
from pickle import PickleError, PicklingError
from typing import Any, NamedTuple, Protocol

import rich  # type: ignore
from rich.progress import (  # type: ignore
    BarColumn,
    Progress,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from . import identity, memory_use, startscript, try_read
from .timetools import iso_logpath
from .unicode_characters import U_CHECK_MARK, U_CROSSED_SWORDS


__all__ = [
    'parallel_proc',
    'parproc',
    'processing_loop',
    '_old_file_process_progress',
]

EOLCH = '\r' if sys.stderr.isatty() else '\n'

try:
    import _thread  # pyright: ignore[reportUnusedImport]

    HAS_MULTITHREADING_SUPPORT = True
except ImportError:
    # This block triggers if compiled without thread support (like basic WebAssembly)
    HAS_MULTITHREADING_SUPPORT = False

GIL_DISABLED = sysconfig.get_config_var("Py_GIL_DISABLED")
HAS_MULTITHREADING_SUPPORT = GIL_DISABLED

if HAS_MULTITHREADING_SUPPORT:
    from threading import Event
else:
    # NOTE import from multiprocessing instead of threading to support both
    # threading.Event is not pickleable, so multiprocessing.Event is used instead
    from multiprocessing import Manager

    Event = Manager().Event

type Func = Callable[..., Any]
type VisualFunc = Callable[..., Any]
type ProgressPair = tuple[Progress, TaskID]
type GetProgressFunc = Callable[[int], ProgressPair]


class Payload(Protocol):
    pass


@dataclass(slots=True)
class VisualPayload(Payload):
    path: Path
    payload: Any

    def __hash__(self) -> int:
        return id(self)

    def __lt__(self, other: Any) -> bool:
        return id(self) < id(other)


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


@dataclass(slots=True, order=True)
class Result:
    stop: Event
    payload: Any
    outcome: Any = None
    exception: Any = None
    linecount: int = 0
    runtime: float = 0
    memory: int = 0

    @property
    def success(self):
        return self.exception is None

    def __str__(self):
        return str(self.__dict__)


def _build_progressbar(total: int) -> tuple[Progress, TaskID]:
    progress = Progress(
        TextColumn(f"[progress.description]{startscript()}"),
        BarColumn(),
        # *Progress.get_default_columns(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        TextColumn("[progress.description]{task.description}"),
        refresh_per_second=1,
        speed_estimate_period=30.0,
    )
    task = progress.add_task('', total=total)
    return progress, task


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
) -> Generator[Result | None, None, None]:
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
) -> Generator[Result | None, None, None]:
    stop = Event()
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
    try:
        start_time = time.thread_time()
        try:
            outcome = task.func(task.payload, *task.args, **task.kwargs)
        except TypeError:
            if not isinstance(task.payload, VisualPayload):
                raise

            # HACK add backwards compatibility
            prev_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(2**16)
            try:
                outcome = task.func(task.payload.path, *task.args, **task.kwargs)
            finally:
                sys.setrecursionlimit(prev_limit)

        elapsed = time.thread_time() - start_time
    except Exception as e:
        result.exception = e
        if task.reraise:
            raise
    finally:
        result.runtime = elapsed
        result.outcome = task.pickable(outcome)
    result.linecount = getattr(outcome, 'linecount', 0)
    result.memory = memory_use()
    return result


def parproc_visual(
    func: VisualFunc,
    payloads_in: Iterable[VisualPayload | str],
    /,
    build_progressbar: GetProgressFunc = _build_progressbar,
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    summary: bool = True,
    max_workers: int | None = None,
    **kwargs: Any,
) -> Generator[Result, None, None]:
    # note: resolve iterator now because we know that processing will do it anyway
    payloads_in = list(payloads_in)

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

    maxwidth = max(len(Path(f).name) for f in filenames)

    @contextmanager
    def logctx() -> Generator[io.TextIOBase | Any, None, None]:
        if isinstance(logpath, Path):
            with logpath.open(mode="a", encoding="utf-8") as logfile:
                yield logfile
        else:
            yield sys.stderr

    total = len(filenames)
    total_time = 0.0
    run_time = 0.0
    start_time = time.time()
    results = parproc(
        func,
        payloads,
        *args,
        pickable=pickable,
        parallel=parallel,
        reraise=reraise,
        max_workers=max_workers,
        **kwargs,
    )
    count = 0
    success_count = 0
    success_linecount = 0

    progress, progress_task = build_progressbar(total)
    if is_legacy:
        # HACK backwards compatibility: resolve the iterator
        results = list(results)  # type: ignore
    with progress:
        for result in results:
            if result is None:
                continue
            count += 1

            total_time = time.time() - start_time
            filename = Path(result.payload.path).name
            if result.exception:
                icon = f'{U_CROSSED_SWORDS}'
                color = '[red]'
            else:
                icon = f'{U_CHECK_MARK}'
                color = '[green]'

            progress.update(
                progress_task,
                advance=1,
                description=f'{color}{filename:{maxwidth}} {icon}',
                color='green',
            )

            # with logctx() as log:
            #     print(result.payload, file=log)
            if result.exception:
                try:
                    with logctx() as log:
                        print('ERROR:', result.payload, file=log)
                        print(result.exception, file=log)
                except Exception:
                    # in case of errors while serializing the exception
                    with logctx() as log:
                        print(
                            'EXCEPTION',
                            type(result.exception).__name__,
                            file=log,
                        )
                if reraise:
                    raise result.exception
            elif result.outcome is not None:
                success_count += 1
                if isinstance(result.linecount, int | float):
                    success_linecount += result.linecount
                run_time += result.runtime

            if result.exception and reraise:
                raise result.exception
            if is_legacy:
                result.payload = result.payload.path
            yield result

        progress.update(progress_task, advance=0, description='')
        progress.remove_task(progress_task)
        progress.stop()

    if summary or is_legacy:
        with logctx() as log:
            _file_process_summary(
                filenames,
                total_time,
                run_time,
                success_count,
                success_linecount,
                log,
            )


def _old_file_process_progress(
    latest_result: Result,
    count: int,
    total: int,
    total_time: float,
):
    filename = latest_result.payload

    percent = count / total
    mb_memory = (latest_result.memory + memory_use()) // (1024 * 1024)

    eta = (total - count) * 0.8 * total_time / (0.2 * count)
    bar = '[%-24s]' % ('#' * round(24 * percent))

    print(
        '%3d/%-3d' % (count, total),
        bar,
        '%3d%%' % (100 * percent),
        # format_hours(total_time),
        f'{_format_hours(eta)}ETA',
        _format_minutes(latest_result),
        '%3dMiB' % mb_memory if mb_memory else '',
        (Path(filename).name + ' ' * 80)[:40],
        file=sys.stderr,
        end=EOLCH,
    )


def _format_minutes(result: Result) -> str:
    return f'{result.runtime / 60:3.0f}:{result.runtime % 60:04.1f}'


def _format_hours(time: float) -> str:
    return f'{time // 3600:2.0f}:{(time // 60) % 60:02.0f}:{time % 60:02.0f}'


def _file_process_summary(
    filenames: Sequence[str],
    total_time: float,
    run_time: float,
    success_count: int,
    success_linecount: int,
    log,
):
    filecount = 0
    linecount = 0
    for fname in filenames:
        filecount += 1

        nlines = len(try_read(fname).splitlines())
        linecount += nlines

    failures = filecount - success_count
    lines_per_second = success_linecount / run_time if run_time > 0 else 0
    success_rate = 100 * success_count / filecount if filecount != 0 else 0

    # ──────────────────────────────────────────────────────────────────────
    summary_text = '''\
                {filecount:12,d}   files input
                {linecount:12,d}   source lines input
        {success_linecount:12,d}   total lines processed
       {lines_per_second:12,.0f}   lines/sec
            {success_count:12,d}   successes
                 {failures:12,d}   failures
            {success_rate:12.1f}%  success rate
           {total_time_str:>12s}   time
             {run_time_str:>12s}   run time
    '''
    summary_text = '\n'.join(s.strip() for s in summary_text.splitlines())

    summary = summary_text.format(
        filecount=filecount,
        linecount=linecount,
        success_linecount=success_linecount,
        lines_per_second=lines_per_second,
        success_count=success_count,
        failures=failures,
        success_rate=success_rate,
        total_time_str=_format_hours(total_time),
        run_time_str=_format_hours(run_time),
    )
    print(summary, file=log)
    print(EOLCH + 80 * ' ', file=sys.stderr)

    print(summary, file=sys.stderr)
    if failures:
        rich.print(f'[red bold]FAILURES: [green]{log.name}')
        print(file=sys.stderr)
        sys.exit(1)


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
) -> Generator[Result, None, None]:
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
    [Event, Func, Iterable[Any], int | None], Iterable[Result]
]:
    import multiprocessing
    from concurrent.futures import (
        Executor,
        InterpreterPoolExecutor,
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
    ) -> Iterable[Result]:
        # by Copilot 2026-03-06

        if not tasks:
            return

        with executorcls(max_workers=max_workers) as ex:  # type: ignore
            try:
                futures = [ex.submit(process, task) for task in tasks]
                for future in as_completed(futures):
                    yield future.result()
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

    def thread_pmap(
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Result]:
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
    ) -> Iterable[Result]:
        try:
            yield from executor_pmap(
                ProcessPoolExecutor,
                event,
                process,
                tasks,
                max_workers=max_workers or multiprocessing.cpu_count(),
            )
        except (TypeError, PicklingError, PickleError):
            yield from thread_pmap(event, process, tasks, max_workers)

    def interpreter_pmap(
        event: Event,
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Result]:
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

    def imap_pmap(process: Func, tasks: Iterable[Any]) -> Iterable[Result]:
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
    return process_pmap

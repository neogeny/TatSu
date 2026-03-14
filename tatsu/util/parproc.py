# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import io
import multiprocessing
import sys
import time
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from concurrent.futures import (
    Executor,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
)
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from itertools import batched
from pathlib import Path
from typing import Any, NamedTuple

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
from .datetimetools import iso_logpath
from .unicode_characters import U_CHECK_MARK, U_CROSSED_SWORDS

__all__: list[str] = ['parallel_proc', 'parproc', 'processing_loop']

EOLCH = '\r' if sys.stderr.isatty() else '\n'
sys.setrecursionlimit(2**16)

type Func = Callable[[Any], Any]


class Task(NamedTuple):
    func: Func
    payload: Any
    pickable: Callable
    reraise: bool
    args: Iterable[Any]
    kwargs: Mapping[str, Any]


@dataclass(slots=True)
class Result:
    payload: Any
    outcome: Any = None
    exception: Any = None
    linecount: int = 0
    time: float = 0
    memory: int = 0

    @property
    def success(self):
        return self.exception is None

    def __str__(self):
        return str(self.__dict__)


# NOTE: BWCOMP
def parallel_proc(
    payloads: Iterable[Any],
    process: Callable,
    *args: Any,
    **kwargs: Any,
):
    yield from parproc(process, payloads, *args, **kwargs)


def parproc(
    func: Func,
    payloads: Iterable[Any],
    *args: Any,
    pickable: Func = identity,
    parallel: bool = True,
    reraise: bool = False,
    **kwargs: Any,
) -> Iterable[Result | None]:

    tasks = [
        Task(
            func=func,
            payload=payload,
            pickable=pickable,
            reraise=reraise,
            args=args,
            kwargs=kwargs,
        )
        for payload in payloads
    ]
    try:
        if len(tasks) == 1:
            yield taskproc(tasks[0])
            return

        pmap = active_pmap() if parallel else map
        yield from pmap(taskproc, tasks)
    except KeyboardInterrupt:
        return


def taskproc(task: Task) -> Result | None:
    start_time = time.process_time()
    result = Result(task.payload)
    try:
        outcome = task.func(task.payload, *task.args, **task.kwargs)
        result.memory = memory_use()
        if hasattr(outcome, 'linecount'):
            result.linecount = outcome.linecount
        else:
            count = 0
            with Path(task.payload).open() as f:
                for _line in f:
                    count += 1
            result.linecount = count
        result.outcome = task.pickable(outcome)
    except KeyboardInterrupt:
        return None
    except Exception as e:
        result.exception = e
    finally:
        result.time = time.process_time() - start_time

    return result


# NOTE: BWCOMP
def processing_loop(
    filenames: Iterable[str],
    process: Callable,
    *args: Any,
    reraise: bool = False,
    **kwargs: Any,
) -> Iterable[Result]:
    yield from parproc_visual(process, filenames, *args, **kwargs)


def parproc_visual(
    func: Func,
    filenames: Iterable[str],
    *args: Any,
    reraise: bool = False,
    **kwargs: Any,
) -> Iterable[Result]:
    try:
        # note: resolve iterator now because we know that processing will do it anyway
        filenames = list(filenames)

        logpath = None
        if len(filenames) > 1:
            prefix = startscript().replace('.', '_')
            logpath = iso_logpath(prefix=prefix)

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
        results = parproc(func, filenames, *args, **kwargs)
        results = results or []
        count = 0
        success_count = 0
        success_linecount = 0

        progress, progress_task = _build_progressbar(total)
        with progress:
            for result in results:
                if result is None:
                    continue
                count += 1

                total_time = time.time() - start_time
                filename = Path(result.payload).name
                if result.exception:
                    icon = f'[red]{U_CROSSED_SWORDS}'
                else:
                    icon = f'[green]{U_CHECK_MARK}'

                progress.update(
                    progress_task,
                    advance=1,
                    description=f'{icon} {filename}',
                )

                # with logctx() as log:
                #     print(result.payload, file=log)
                if result.exception:
                    # noinspection PyBroadException
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
                    success_linecount += result.linecount
                    run_time += result.time
                    yield result

            progress.update(progress_task, advance=0, description='')
            progress.stop()
        with logctx() as log:
            _file_process_summary(
                filenames,
                total_time,
                run_time,
                success_count,
                success_linecount,
                log,
            )
    except KeyboardInterrupt:
        return


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


def _format_minutes(result: Result) -> str:
    return f'{result.time / 60:3.0f}:{result.time % 60:04.1f}'


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

    summary_text = '''\
                ──────────────────────────────────────────────────────────────────────
                {filecount:12,d}   files input
                {linecount:12,d}   source lines input
        {success_linecount:12,d}   total lines processed
       {lines_per_second:12,.0f}   lines/sec
            {success_count:12,d}   successes
                 {failures:12,d}   failures
            {success_rate:12.1f}%  success rate
           {total_time_str:>13s}   time
             {run_time_str:>13s}   run time
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

    if log != sys.stderr:
        print(summary, file=sys.stderr)
    if failures:
        rich.print(f'[red bold]FAILURES: [green]{log.name}')
        print(file=sys.stderr)
        sys.exit(1)


def active_pmap() -> Callable[[Func, Iterable[Any]], Iterable[Result]]:
    def executor_pmap(
        executorcls: type[Executor],
        process: Func,
        tasks: Iterable[Any],
        max_workers: int | None = None,
    ) -> Iterable[Result]:
        # by Copilot 2026-03-06

        if not tasks:
            return

        with executorcls(max_workers=max_workers) as ex:  # type: ignore
            futures = [ex.submit(process, task) for task in tasks]
            for future in as_completed(futures):
                yield future.result()

    def thread_pmap(process: Func, tasks: Iterable[Any]) -> Iterable[Result]:
        yield from executor_pmap(ThreadPoolExecutor, process, tasks)

    def process_pmap(process: Func, tasks: Iterable[Any]) -> Iterable[Result]:
        yield from executor_pmap(
            ProcessPoolExecutor, process, tasks, max_workers=multiprocessing.cpu_count()
        )

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

    return process_pmap

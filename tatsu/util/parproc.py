import sys
import time
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from functools import partial
from multiprocessing import Pool, cpu_count
from pathlib import Path

import rich
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from tatsu.util.unicode_characters import (
    U_CHECK_MARK,
    U_CROSSED_SWORDS,
)

from ..util import identity, memory_use, program_name, try_read

__all__ = ['parallel_proc', 'processing_loop']


ERROR_LOG_FILENAME = 'ERROR.log'
EOLCH = '\r' if sys.stderr.isatty() else '\n'
sys.setrecursionlimit(2**16)

__Task = namedtuple('__Task', 'payload args kwargs')


class ParprocResult:
    def __init__(self, payload):
        self.payload = payload
        self.outcome = None
        self.exception = None
        self.linecount = 0
        self.time = 0
        self.memory = 0

    @property
    def success(self):
        return self.exception is None

    def __str__(self):
        return str(self.__dict__)


def process_payload(process, task, pickable=identity, reraise=False):
    start_time = time.process_time()
    result = ParprocResult(task.payload)
    try:
        outcome = process(task.payload, *task.args, **task.kwargs)
        result.memory = memory_use()
        if hasattr(outcome, 'linecount'):
            result.linecount = outcome.linecount
        else:
            result.linecount = len(try_read(task.payload).splitlines())
        result.outcome = pickable(outcome)
    except KeyboardInterrupt:
        return None
    except Exception as e:
        result.exception = e
    finally:
        result.time = time.process_time() - start_time

    return result


def _executor_pmap(executor, process, tasks):
    nworkers = max(1, cpu_count())
    n = nworkers * 8
    chunks = [tasks[i:i + n] for i in range(0, len(tasks), n)]
    for chunk in chunks:
        with executor(max_workers=nworkers) as ex:
            futures = [ex.submit(process, task) for task in chunk]
            for future in as_completed(futures):
                yield future.result()


def _thread_pmap(process, tasks):
    yield from _executor_pmap(ThreadPoolExecutor, process, tasks)


def _process_pmap(process, tasks):
    yield from _executor_pmap(ProcessPoolExecutor, process, tasks)


def _imap_pmap(process, tasks):
    nworkers = max(1, cpu_count())

    n = nworkers * 4
    chunks = [tasks[i:i + n] for i in range(0, len(tasks), n)]

    count = sum(len(c) for c in chunks)
    if len(tasks) != count:
        raise RuntimeError('number of chunked tasks different %d != %d' % (len(tasks), count))
    for chunk in chunks:
        with Pool(processes=nworkers) as pool:
            yield from pool.imap_unordered(process, chunk)


_pmap = _imap_pmap


def parallel_proc(payloads, process, *args, **kwargs):
    pickable = kwargs.pop('pickable', identity)
    parallel = kwargs.pop('parallel', True)
    reraise = kwargs.pop('reraise', False)

    process = partial(process_payload, process, pickable=pickable, reraise=reraise)
    tasks = [__Task(payload, args, kwargs) for payload in payloads]

    try:
        if len(tasks) == 1:
            yield process(tasks[0])
        else:
            pmap = _pmap if parallel else map
            yield from pmap(process, tasks)
    except KeyboardInterrupt:
        return


def _build_progressbar(total):
    progress = Progress(
        TextColumn(f"[progress.description]{program_name()}"),
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


def processing_loop(filenames, process, *args, reraise=False, **kwargs):  # pylint: disable=too-many-locals
    try:
        total = len(filenames)
        total_time = 0
        run_time = 0
        start_time = time.time()
        results = parallel_proc(filenames, process, *args, **kwargs)
        results = results or []
        count = 0
        success_count = 0
        success_linecount = 0
        progress, progress_task = _build_progressbar(total)

        if total == 1:
            log = sys.stderr
        else:
            log = Path(ERROR_LOG_FILENAME).open('w')

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

                if result.exception:
                    print(file=log)
                    try:
                        print('ERROR:', result.payload, file=log)
                        print(result.exception, file=log)
                    except Exception:
                        # in case of errors while serializing the exception
                        print('EXCEPTION', type(result.exception).__name__, file=log)
                    if reraise:
                        raise result.exception
                elif result.outcome is not None:
                    success_count += 1
                    success_linecount += result.linecount
                    run_time += result.time
                    yield result

                log.flush()

            progress.update(progress_task, advance=0, description='')
            progress.stop()
        file_process_summary(
            filenames, total_time, run_time, success_count, success_linecount, log,
        )
    except KeyboardInterrupt:
        return


def file_process_progress(latest_result, count, total, total_time):
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
        f'{format_hours(eta)}ETA',
        format_minutes(latest_result),
        '%3dMiB' % mb_memory if mb_memory else '',
        (Path(filename).name + ' ' * 80)[:40],
        file=sys.stderr,
        end=EOLCH)


def format_minutes(result):
    return f'{result.time / 60:3.0f}:{result.time % 60:04.1f}'


def format_hours(time):
    return f'{time // 3600:2.0f}:{(time // 60) % 60:02.0f}:{time % 60:02.0f}'


def file_process_summary(
        filenames, total_time, run_time, success_count, success_linecount, log,
):
    filecount = 0
    linecount = 0
    for fname in filenames:
        filecount += 1

        nlines = len(try_read(fname).splitlines())
        linecount += nlines

    failures = filecount - success_count

    summary_text = '''\
        -----------------------------------------------------------------------
        {:12,d}   files input
        {:12,d}   source lines input
        {:12,d}   total lines processed
        {:12,d}   successes
        {:12,d}   failures
        {:12.1f}%  success rate
         {:>13s}  time
         {:>13s}  run time
    '''
    summary_text = '\n'.join(s.strip() for s in summary_text.splitlines())

    summary = summary_text.format(
        filecount,
        linecount,
        success_linecount,
        success_count,
        failures,
        100 * success_count / filecount if filecount != 0 else 0,
        format_hours(total_time),
        format_hours(run_time),
    )
    print(EOLCH + 80 * ' ', file=log)
    print(summary, file=log)
    print(EOLCH + 80 * ' ', file=sys.stderr)

    if failures:
        rich.print(f'[red bold]FAILURES logged to [green]{log.name}!')
        print(file=sys.stderr)
    if log != sys.stderr:
        print(summary, file=sys.stderr)
    if failures:
        sys.exit(1)

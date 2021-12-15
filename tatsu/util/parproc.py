import sys
import time
from collections import namedtuple
from multiprocessing import cpu_count, Pool, Lock
from concurrent.futures import as_completed, ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
from pathlib import Path
from statistics import mean
from dataclasses import dataclass
from typing import Any

from .import identity, try_read, memory_use, short_relative_path


SUCCESSCH = '\u2705'
FAILURECH = '\u274C'
EOLCH = '\r' if sys.stderr.isatty() else '\n'


__Task = namedtuple('__Task', 'payload args kwargs')

console_lock = Lock()


@dataclass
class ParprocResult:
    payload: str
    outcome: Any = None
    exception: Any = None
    linecount: int = 0
    time: float = 0
    memory: int = 0

    @property
    def success(self):
        return self.exception is None


def processing_loop(process, filenames, *args, verbose=False, exitfirst=False, **kwargs):
    all_results = []
    successful_results = []
    total = len(filenames)
    total_time = 0
    start_time = time.time()
    try:
        results = process_in_parallel(filenames, process, *args, **kwargs)
        results = results or []
        for _, result in enumerate(results, start=1):
            if result is None:
                continue
            all_results.append(result)

            total_time = time.time() - start_time
            file_process_progress(all_results, successful_results, total, total_time, verbose=verbose)

            if result.exception:
                if verbose:
                    with console_lock:
                        print(file=sys.stderr)
                        print(f'{result.exception.split()[0]:16} {result.payload}', file=sys.stderr)
                if exitfirst:
                    raise KeyboardInterrupt
            else:
                successful_results.append(result)
    except KeyboardInterrupt:
        pass
    finally:
        file_process_summary(filenames, total_time, all_results, verbose=verbose)
    return all_results


def process_payload(process, task, pickable=identity, **kwargs):
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
        raise
    except Exception as e:
        result.exception = f'{type(e).__name__}: {str(e)}'
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
        raise Exception('number of chunked tasks different %d != %d' % (len(tasks), count))
    for chunk in chunks:
        with Pool(processes=nworkers) as pool:
            try:
                yield from pool.imap_unordered(process, chunk)
            except KeyboardInterrupt:
                raise


_pmap = _imap_pmap


def process_in_parallel(payloads, process, *args, **kwargs):
    pickable = kwargs.pop('pickable', identity)
    parallel = kwargs.pop('parallel', True)
    verbose = kwargs.pop('verbose', False)

    process = partial(process_payload, process, pickable=pickable, verbose=verbose)
    tasks = [__Task(payload, args, kwargs) for payload in payloads]

    try:
        if len(tasks) == 1:
            return [process(tasks[0])]
        else:
            pmap = _pmap if parallel else map
            return pmap(process, tasks)
    except KeyboardInterrupt:
        raise


def file_process_progress(results, successful, total, total_time, verbose=False):
    i = len(results)
    latest_result = results[-1]
    filename = latest_result.payload

    percent = i / total
    success_percent = len(successful) / total
    mb_memory = (latest_result.memory + memory_use()) // (1024 * 1024)

    eta = (total - i) * 0.8 * total_time / (0.2 * i)
    bar = '[%-16s]' % ('#' * round(16 * percent))

    if not latest_result.success:
        print(EOLCH + 90 * ' ' + EOLCH, end='', file=sys.stderr)
        print(
            f'{short_relative_path(latest_result.payload):60} '
            f'{latest_result.exception.split()[0]} ',
            file=sys.stderr,
        )
        if verbose:
            print(f'{latest_result.exception}')

    with console_lock:
        print(
            '%3d/%-3d' % (i, total),
            bar,
            '%0.1f%%(%0.1f%%%s)' % (100 * percent, 100 * success_percent, SUCCESSCH),
            # format_hours(total_time),
            '%sETA' % format_hours(eta),
            format_minutes(latest_result),
            '%3dMiB' % mb_memory if mb_memory else '',
            SUCCESSCH if latest_result.success else FAILURECH,
            (Path(filename).name + ' ' * 80)[:32],
            end=EOLCH,
            file=sys.stderr
        )
        sys.stderr.flush()


def format_minutes(result):
    return '%3.0f:%04.1f' % (result.time / 60, result.time % 60)


def format_hours(time):
    return '%2.0f:%02.0f:%02.0f' % (time // 3600, (time // 60) % 60, time % 60)


def file_process_summary(filenames, total_time, results, verbose=False):
    runtime = sum(r.time for r in results)
    filecount = len(filenames)
    success_count = sum(1 for result in results if result.outcome and not result.exception)
    failure_count = sum(1 for result in results if result.exception)

    line_counts = {
        filename: len(try_read(filename).splitlines())
        for filename in filenames
    }
    linecount = sum(line_counts.values())
    parsed = [r for r in results if r.outcome or r.exception]
    lines_parsed = sum(line_counts[r.payload] for r in parsed)

    mb_memory = (
        max(result.memory // (1024 * 1024) for result in results)
        if results else 0
    )

    lines_sec = round(mean(r.linecount / r.time for r in results if r.time))

    dashes = '-' * 80
    summary_text = '''\
        {:12,d}   files input
        {:12,d}   files parsed
        {:12,d}   lines input
        {:12,d}   lines parsed
        {:12,d}   successes
        {:12,d}   failures
      {:11.1f}%   success rate
        {:>12s}   elapsed time
        {:>12s}   runtime
        {:>12d}   lines/sec
        {:>12d}   mib max memory
    '''
    summary_text = '\n'.join(line.strip() for line in summary_text.splitlines())

    summary = summary_text.format(
        filecount,
        success_count + failure_count,
        linecount,
        lines_parsed,
        success_count,
        failure_count,
        100 * success_count / filecount if filecount != 0 else 0,
        format_hours(total_time),
        format_hours(runtime),
        lines_sec,
        mb_memory,
    )
    print(EOLCH + 80 * ' ', file=sys.stderr)
    print(file=sys.stderr)
    print(dashes, file=sys.stderr)
    print(summary, file=sys.stderr)
    print(dashes, file=sys.stderr)

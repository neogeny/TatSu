import sys
import time
from collections import namedtuple
from multiprocessing import cpu_count, Pool, Lock
from concurrent.futures import as_completed, ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from .import identity, try_read
from .import memory_use

EOLCH = '\r' if sys.stderr.isatty() else '\n'


__Task = namedtuple('__Task', 'payload args kwargs')

console_lock = Lock()


@dataclass
class ParprocResult:
    payload: str
    outcome: Any = None
    exception: BaseException= None
    linecount: int = 0
    time: float = 0
    memory: int = 0

    @property
    def success(self):
        return self.exception is None


def processing_loop(process, filenames, reraise=False, *args, **kwargs):
    all_results = []
    successful_results = []
    total = len(filenames)
    total_time = 0
    start_time = time.time()
    try:
        results = process_in_parallel(filenames, process, *args, **kwargs)
        results = results or []
        for i, result in enumerate(results, start=1):
            if result is None:
                continue
            all_results.append(result)

            total_time = time.time() - start_time
            file_process_progress(all_results, successful_results, total, total_time)

            if result.exception and reraise:
                print(file=sys.stderr)
                try:
                    print('ERROR:', result.payload, file=sys.stderr)
                    print(result.exception, file=sys.stderr)
                except Exception:
                    print('EXCEPTION', type(result.exception).__name__, file=sys.stderr)
                raise result.exception from result.exception
            elif result.outcome is not None:
                successful_results.append(result)

        file_process_summary(filenames, total_time, successful_results)
    except KeyboardInterrupt:
        pass
    return all_results


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
        raise
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
        raise Exception('number of chunked tasks different %d != %d' % (len(tasks), count))
    for chunk in chunks:
        with Pool(processes=nworkers) as pool:
            try:
                yield from pool.imap_unordered(process, chunk)
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
                raise


_pmap = _imap_pmap


def process_in_parallel(payloads, process, *args, **kwargs):
    pickable = kwargs.pop('pickable', identity)
    parallel = kwargs.pop('parallel', True)
    reraise = kwargs.pop('reraise', False)

    process = partial(process_payload, process, pickable=pickable, reraise=reraise)
    tasks = [__Task(payload, args, kwargs) for payload in payloads]

    try:
        if len(tasks) == 1:
            return [process(tasks[0])]
        else:
            pmap = _pmap if parallel else map
            return pmap(process, tasks)
    except KeyboardInterrupt:
        raise


def file_process_progress(results, successful, total, total_time):
    i = len(results)
    latest_result = results[-1]
    filename = latest_result.payload

    percent = i / total
    success_percent = len(successful) / total
    mb_memory = (latest_result.memory + memory_use()) // (1024 * 1024)

    eta = (total - i) * 0.8 * total_time / (0.2 * i)
    bar = '[%-16s]' % ('#' * round(16 * percent))

    with console_lock:
        print(
            '%3d/%-3d' % (i, total),
            bar,
            '%3d%%(%3d%%)' % (100 * percent, 100 * success_percent),
            # format_hours(total_time),
            '%sETA' % format_hours(eta),
            format_minutes(latest_result),
            '%3dMiB' % mb_memory if mb_memory else '',
            (Path(filename).name + ' ' * 80)[:32],
            end=EOLCH,
            file=sys.stderr
        )
        sys.stderr.flush()


def format_minutes(result):
    return '%3.0f:%04.1f' % (result.time / 60, result.time % 60)


def format_hours(time):
    return '%2.0f:%02.0f:%02.0f' % (time // 3600, (time // 60) % 60, time % 60)


def file_process_summary(filenames, total_time, results):
    successes = {result.payload for result in results}
    success_linecount = sum(r.linecount for r in results)
    run_time = sum(r.time for r in results)

    filecount = 0
    linecount = 0
    success_count = 0
    for fname in filenames:
        filecount += 1

        nlines = len(try_read(fname).splitlines())
        linecount += nlines

        if fname in successes:
            success_count += 1

    summary_text = '''\
        {:12,d}   files input
        {:12,d}   source lines input
        {:12,d}   total lines processed
        {:12,d}   successes
        {:12,d}   failures
        {:12.1f}%  success rate
         {:>13s}  time
         {:>13s}  run time
    '''
    summary_text = '\n'.join(l.strip() for l in summary_text.splitlines())
    summary_text = '-' * 80 + '\n' + summary_text

    summary = summary_text.format(
        filecount,
        linecount,
        success_linecount,
        success_count,
        filecount - success_count,
        100 * success_count / filecount if filecount != 0 else 0,
        format_hours(total_time),
        format_hours(run_time),
    )
    # print(EOLCH + 80 * ' ', file=sys.stderr)
    print()
    print(summary, file=sys.stderr)

    for result in results:
        if result.success:
            continue
        print()
        print(result.payload)
        print(result.exception)

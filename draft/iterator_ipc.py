from concurrent.futures import Executor, as_completed
import multiprocessing
import queue
import sys
from typing import Any, Callable, Iterable, Union

# The global status queue accessible by any worker process
_status_queue = multiprocessing.Queue()

def executor_pmap(
    executorcls: type[Executor],
    stop_event: multiprocessing.Event,
    process: Callable[..., Any],
    tasks: Iterable[Any],
    max_workers: int | None = None,
) -> Iterable[Union[Any, dict]]:  # Yields Results or Message dicts
    
    if not tasks:
        return

    with executorcls(max_workers=max_workers) as ex:
        try:
            futures = [ex.submit(process, task) for task in tasks]
            active_futures = set(futures)
            
            # The generator loop drives everything
            while active_futures:
                # 1. Drain the global queue and pass the "messages in a bottle" outside
                while True:
                    try:
                        # Non-blocking pull from the global queue
                        msg = _status_queue.get_nowait()
                        yield msg
                    except queue.Empty:
                        break
                
                # 2. Check for completed tasks without blocking indefinitely
                done_futures = [f for f in active_futures if f.done()]
                for future in done_futures:
                    yield future.result()  # Pass the final result outside
                    active_futures.remove(future)
                    
        except KeyboardInterrupt:
            stop_event.set()
            print(file=sys.stderr)
            print("Wait...", file=sys.stderr)
            sys.stderr.flush()
            ex.shutdown(wait=False, cancel_futures=True)
            raise

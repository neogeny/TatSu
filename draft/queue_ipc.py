from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import os
import queue
import time

# This global variable will hold the queue instance inside each worker process
_worker_queue = None

def _init_worker(q):
    """Initializes the global queue inside the child process."""
    global _worker_queue
    _worker_queue = q

def long_task(data_chunk):
    """A long-running task that emits intermediate status reports."""
    pid = os.getpid()
    counter = 0
    
    # 3-step simulated workload
    for step in range(1, 4):
        time.sleep(0.5)  # Simulate real work
        
        # Generate a lightweight, unique ID for this status update
        counter += 1
        status_id = f"{pid}-{counter}"
        
        # Send an intermediate update back to the main process
        _worker_queue.put({
            "id": status_id,
            "status": "processing",
            "msg": f"Task working on {data_chunk}: Step {step}/3 complete"
        })
        
    return f"Result for {data_chunk}"

def main():
    # Standard queue used for worker -> main communication
    status_queue = multiprocessing.Queue()
    
    # Items to process
    work_items = ["Dataset_A", "Dataset_B", "Dataset_C"]
    
    # Pass the queue to the initializer so workers can access it globally
    with ProcessPoolExecutor(initializer=_init_worker, initargs=(status_queue,)) as executor:
        
        # Submit tasks normally
        futures = {executor.submit(long_task, item): item for item in work_items}
        
        # Process results as they complete, driving the loop via the generator
        while futures:
            # 1. Drain the status queue completely to catch intermediate updates
            while True:
                try:
                    update = status_queue.get_nowait()
                    print(f"[STATUS] [ID: {update['id']}] {update['msg']}")
                except queue.Empty:
                    break
            
            # 2. Check for any finished futures without blocking indefinitely
            done_futures = [f for f in futures if f.done()]
            
            for future in done_futures:
                result = future.result()
                item = futures[future]
                print(f"--> [FINAL] {item} finished with: {result}")
                del futures[future]
            
            # Tiny sleep to keep CPU usage low while waiting for work to complete
            time.sleep(0.1)

if __name__ == "__main__":
    main()

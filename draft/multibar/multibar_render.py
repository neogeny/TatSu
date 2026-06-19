import copy
import threading
import time


class MultiProgress:
    def __init__(self):
        self._bars = []
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def add_bar(self, bar_instance: Bar) -> Bar:
        """Accepts any pre-configured Bar or custom subclass instance."""
        with self._lock:
            self._bars.append(bar_instance)
        return bar_instance

    def start(self):
        self._running = True
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        self._thread = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        with self._lock:
            num_bars = len(self._bars)
        sys.stdout.write(f"\033[{num_bars}B\n\033[?25h")
        sys.stdout.flush()

    def _render_loop(self):
        while self._running:
            with self._lock:
                snapshot = copy.deepcopy(self._bars)

            if not snapshot:
                time.sleep(0.05)
                continue

            lines = []
            for b in snapshot:
                # Ask the data object to render its chunks
                chunks = b.bar()
                # Join the actual text payload together
                line_string = "".join(text for text, _ in chunks)
                lines.append(line_string)

            sys.stdout.write("\n".join(lines))
            sys.stdout.flush()

            time.sleep(0.05)  # 20 FPS
            sys.stdout.write(f"\033[{len(snapshot)}A")

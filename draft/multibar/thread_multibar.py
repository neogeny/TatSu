import copy
import sys
import threading
import time


class Bar:
    """A rich, lightweight, fully picklable data object given to the user."""

    def __init__(self, label: str, total: int = 100):
        self.label = label
        self.total = total
        self.current = 0

    def advance(self, delta: int = 1):
        """Write-only operation from the user's side."""
        self.current = min(self.current + delta, self.total)

    def update(self, value: int):
        """Write-only operation from the user's side."""
        self.current = min(value, self.total)


class MultiProgress:
    def __init__(self):
        self._bars = []
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def add_bar(self, label: str, total: int = 100) -> Bar:
        """Creates a bar, stores it internally, and returns it to the user."""
        bar = Bar(label, total)
        with self._lock:
            self._bars.append(bar)
        return bar

    def start(self):
        """Starts the completely isolated background rendering thread."""
        self._running = True
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.flush()

        self._thread = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Gracefully shuts down the rendering thread."""
        self._running = False
        if self._thread:
            self._thread.join()
        # Clean up terminal lines
        with self._lock:
            num_bars = len(self._bars)
        sys.stdout.write(f"\033[{num_bars}B\n\033[?25h")
        sys.stdout.flush()

    def _render_loop(self):
        """The isolated thread handler. Read-only side."""
        while self._running:
            # 1. LOCK INSTANTLY: Take a snapshot copy of the data objects
            with self._lock:
                snapshot = copy.deepcopy(self._bars)

            # 2. RELEASED LOCK: Do the slow I/O printing out-of-band
            if not snapshot:
                time.sleep(0.05)
                continue

            lines = []
            for b in snapshot:
                pct = int((b.current / b.total) * 100) if b.total > 0 else 0
                fill = int(pct / 5)
                lines.append(f"{b.label}: [{'█' * fill}{'-' * (20 - fill)}] {pct}%")

            sys.stdout.write("\n".join(lines))
            sys.stdout.flush()

            time.sleep(0.05)  # 20 FPS
            sys.stdout.write(f"\033[{len(snapshot)}A")  # Reset cursor up

import copy
import sys
import time


class MultiProgress:
    def __init__(self):
        self._bars = []
        self._lock = threading.Lock()  # Protects only the orchestrator's list structure
        self._running = False
        self._thread = None

    def add_bar(self, bar_instance: Bar) -> Bar:
        """User retains full, uninhibited ownership of the Bar instance."""
        with self._lock:
            self._bars.append(bar_instance)
        return bar_instance

    def _render_loop(self):
        self._set_low_priority()

        while self._running:
            # 1. Capture a structural snapshot of the registry list
            with self._lock:
                current_bars = self._bars[:]

            if not current_bars:
                time.sleep(0.04)  # Target ~24 FPS (1/24 ≈ 0.041)
                continue

            try:
                screen_cols, _ = Color.default().terminal_size()
            except Exception:
                screen_cols = 80

            lines = []
            for b in current_bars:
                # 2. Shallow copy the Bar object instantly on the orchestrator's time.
                # Captures current primitive value states (integers/strings).
                bar_snapshot = copy.copy(b)

                # 3. Process telemetry and extract the immutable rendering tuple
                render_tuple = bar_snapshot.call_render(screen_cols)
                lines.append("".join(render_tuple))

            # 4. Flush the complete immutable frame to the console
            sys.stdout.write("\n".join(lines))
            sys.stdout.flush()

            time.sleep(0.04)
            sys.stdout.write(f"\033[{len(lines)}A")


def run(self):
    def drpped_key(bar) -> bool:
        return bar.dropped

    while True:
        with self.lock:
            snapbars = sorted((copy.copy(b) for b in self.bars), dropped_key)
            # NOTE drop _after_ redrawing
            self.bars = [b for b in self.bars if not b.dropped]
        self.render_snapshot(snapbars)
        ...


def add_bar(self, bar):
    with self.lock:
        self.bars = [*self.bars, bar]
        # WARNING Do not drop before redrawing
        # self.bars = [b for b in [*self.bars, bar] if not b.dropped]

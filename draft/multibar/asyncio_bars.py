import asyncio
import sys


class MultiProgressBar:
    def __init__(self, total_bars: int):
        # State tracking for all bars
        self.bars = [
            {"current": 0, "total": 100, "label": f"Task {i}"}
            for i in range(total_bars)
        ]
        self.running = True

    def update(self, bar_index: int, value: int):
        """Workers call this to increment their progress."""
        self.bars[bar_index]["current"] = min(value, self.bars[bar_index]["total"])

    async def render_loop(self):
        """The single task that handles terminal I/O rendering."""
        # Hide the terminal cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

        try:
            while self.running:
                output = []
                for bar in self.bars:
                    pct = int((bar["current"] / bar["total"]) * 100)
                    filled = int(pct / 5)  # 20 blocks total
                    blocks = "█" * filled + "-" * (20 - filled)
                    output.append(f"{bar['label']}: [{blocks}] {pct}%")

                # Join with newlines
                full_screen = "\n".join(output)
                sys.stdout.write(full_screen)
                sys.stdout.flush()

                await asyncio.sleep(0.05)  # ~20 FPS refresh rate

                # Move cursor back up to the top of our progress bars
                sys.stdout.write(f"\033[{len(self.bars)}A")
        finally:
            # Clean up: Move cursor past the bars and show it again
            sys.stdout.write(f"\033[{len(self.bars)}B\n\033[?25h")
            sys.stdout.flush()


# --- Simulation of Parallel Workers ---


async def worker(bar_id: int, manager: MultiProgressBar):
    """Simulates an I/O bound worker updating its progress."""
    for i in range(1, 101):
        await asyncio.sleep(0.02 + (bar_id * 0.01))  # Staggered speeds
        manager.update(bar_id, i)


async def main():
    num_tasks = 4
    manager = MultiProgressBar(num_tasks)

    # Start the single rendering loop task
    renderer_task = asyncio.create_task(manager.render_loop())

    # Start all parallel workers
    workers = [worker(i, manager) for i in range(num_tasks)]
    await asyncio.gather(*workers)

    # Stop the renderer once workers finish
    manager.running = False
    await renderer_task


if __name__ == "__main__":
    asyncio.run(main())

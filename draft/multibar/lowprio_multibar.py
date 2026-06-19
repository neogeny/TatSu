from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class Bar:
    name: str
    total: int = 100
    current: int = 0
    start_time: float = field(default_factory=time.time)

    def advance(self, delta: int = 1):
        self.current = min(self.current + delta, self.total)

    def call_render(self, width: int) -> list[Style]:
        """
        The private bridge execution method. Runs completely on the background
        thread time. Computes all fields before calling render().
        """
        now = time.time()
        elapsed = now - self.start_time
        pct = (self.current / self.total * 100) if self.total > 0 else 0.0
        rate = self.current / elapsed if elapsed > 0 else 0
        eta = (self.total - self.current) / rate if rate > 0 else 0.0

        return self.render(
            width=width,
            pos=self.current,
            total=self.total,
            pct=pct,
            elapsed=elapsed,
            eta=eta,
        )

    def render(self, *, width: int, pct: float, eta: float, **kwargs) -> list[Style]:
        """
        The default user-overridable hook. Simple, predictable, and
        gives the user exactly the computed values they want.
        """
        color = Color.default()
        prefix = f"{self.name:<20} "
        suffix = f" {pct:>3.0f}% (ETA: {eta:.1f}s)"

        fixed_len = len(prefix) + len(suffix) + 2
        bar_budget = max(0, width - fixed_len)

        fill_len = int(bar_budget * (pct / 100))
        empty_len = bar_budget - fill_len
        blocks_str = f"[{'█' * fill_len}{'-' * empty_len}]"

        return [
            color.style(prefix, bold=True),
            color.style(blocks_str, fg=8),
            color.style(suffix, fg=2),
        ]

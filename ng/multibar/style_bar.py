import time
from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class Bar:
    name: str
    total: int = 100
    current: int = 0
    start_time: float = field(default_factory=time.time)

    def advance(self, delta: int = 1):
        self.current = min(self.current + delta, self.total)

    def render(self, width: int, metrics: dict[str, float]) -> list[Style]:
        """
        The Default Protocol.
        Returns a rich list of Style components. The manager expands '{bar}'
        using the leftover column width budget.
        """
        color = Color.default()

        # Build pieces using your rich Style architecture
        return [
            color.style(f"{self.name:<20}", bold=True),
            color.style(" "),
            color.style("{bar}"),  # Structural marker
            color.style(" "),
            color.style(f"{metrics['pct']:>3.0f}%", fg=2),  # Green index text
        ]

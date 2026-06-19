@dataclass(slots=True, kw_only=True)
class ColorBar(Bar):
    color_code: str = "\033[32m"  # Default to Green ANSI

    def bar(self) -> list[tuple[str, int]]:
        pct = int((self.current / self.total) * 100) if self.total > 0 else 0
        fill = int(pct / 5)

        # Build chunks: (String with ANSI controls, actual screen character length)
        return [
            (f"{self.label}: [", len(self.label) + 4),
            (f"{self.color_code}{'█' * fill}\033[0m", fill),
            (f"{'-' * (20 - fill)}] {pct}%", (20 - fill) + 2 + len(str(pct)) + 1),
        ]

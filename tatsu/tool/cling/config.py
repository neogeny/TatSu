import os
import sys
from dataclasses import dataclass, field


DEFAULT_PYGMENTS_STYLE = "nord"


@dataclass
class CLIConfig:
    """Parsed command-line configuration, matching ogopego's CLIConfig struct."""

    # Global flags
    color: str = "auto"
    output: str | None = None
    style: str = DEFAULT_PYGMENTS_STYLE
    verbose: bool = False
    quiet: bool = False
    profile: bool = False
    trace: bool = False

    # Subcommand state
    command: str = ""
    grammar: str | None = None
    optimized: bool = False
    path: str | None = None
    inputs: list[str] = field(default_factory=list)

    # format flags
    json: bool = False
    model: bool = False
    pretty: bool = False
    railroads: bool = False

    # run flags
    start: str | None = None
    nproc: int | None = None

    def usecolor(self) -> bool:
        return self.color == "always" or (  # pyright: ignore[reportReturnType]
            not bool(os.environ.get("NO_COLOR", None))
            and self.color == "auto"
            and sys.stderr.isatty()
        )

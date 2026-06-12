from dataclasses import dataclass, field


DEFAULT_PYGMENTS_STYLE = "nord"


@dataclass
class CLIConfig:
    """Parsed command-line configuration, matching ogopego's CLIConfig struct."""

    # Global flags
    color: str = "auto"
    output: str = ""
    style: str = DEFAULT_PYGMENTS_STYLE
    verbose: bool = False
    quiet: bool = False
    profile: bool = False
    trace: bool = False

    # Subcommand state
    command: str = ""
    path: str = ""
    inputs: list[str] = field(default_factory=list)

    # format flags
    json: bool = False
    model: bool = False
    pretty: bool = False
    railroads: bool = False

    # run flags
    start: str = ""
    nproc: int = 0

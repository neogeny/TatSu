<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.23.0] new features + bugfixes + (- dependencies)

[v5.23.0]: https://github.com/neogeny/tatsu/compare/v5.22.1...HEAD

## Added

- _Added_ `--generate-parser` option to the `cling` CLI tool.
- _Added_ `tatsu.util.barz` — self-contained progress bar rendering (replaces `rich.progress`).
- _Added_ `tatsu.util.treez` — self-contained dependency tree rendering (replaces `rich.tree`).
- _Added_ `tests/tree_test.py`.
- _Added_ `g2e` subcommand to `cling` CLI — translates ANTLR grammars to TatSu.
- _Added_ `bench` and `ideps` subcommands to `cling` CLI.
- _Added_ `add_argparse_options(parser)` pattern to `bench.py`, `ideps.py`, `g2etool.py` for uniform CLI interface.
- _Added_ `tatsu.ztyle.markup` — Rich-style markup parser (`[bold]text[/]`, `[red]...[/all]`). Parse with `markup()` → returns `StyleZ` (a `str` subclass wrapping `list[Style]`; styles via `.style` property). Optionally pass a `color` policy.
- _Added_ `Style.from_raw()` — reconstruct a `Style` from an ANSI escape string (e.g. `"\e[31mhello\e[0m"`) for roundtrip support.
- _Added_ `Style.apply_style()` — applies ANSI rendering to an arbitrary string directly.
- _Added_ `tatsu.util.tty` — shared TTY/ANSI utilities (`ANSI_RE`, `SGR_RE`, `tty_escape`, `tty_unescape`, `descape`, `visual_len`, cursor hide/show, `pushup`, `blankpad`).
- _Added_ `etc/RICH_MARKUP.md` — specification for the Rich-style markup syntax.
- _Added_ `Style.__json__()` protocol — `Style` now serializes through `asjson`/`fromjson` (any object with `__json__` method is supported).
- _Added_ `tatsu/packetz/` — inter-task communication via filesystem-based message passing queues that work across threading and multiprocessing.
- _Added_ `tatsu/barz/` — self-contained progress bar rendering with `ztyle` coloring support and a single background rendering thread.
- _Added_ `rich` dependency removed from core: `pygments` optional for colored `cling` output; `graphviz` optional for graphical diagrams (text-based railroad diagrams remain default).

## Changed

- **No more `colorama`**: All mentions of `colorama` removed. The project consistently uses its own `ztyle` library.
- **No more `rich` dependency**: `cling` CLI no longer pulls in `rich`. Progress bars use `tatsu.util.barz`. Dependency trees use `tatsu.util.treez`. Summaries use `ztyle`.
- `colorize` module renamed to `ztyle` to avoid confusion with the `colorize` package on PyPI.
- `tatsu.grammars` renamed to `tatsu.peg` (kept `grammars.py` shim).
- `tatsu.api` moved into its own `tatsu.api` package.
- `ideps.py` refactored to use own `Tree` + `Style` instead of `rich.tree`.
- `bench.py`, `ideps.py`, `g2etool.py` migrated from ad-hoc argument parsing to `add_argparse_options(parser)` + `main(parser) -> int`.
- Bar metrics refactored: `Metrics` class with lazy `@cached_property` per column; `BarRowData` base class extracted to break circular dependency; `Col` enum moved to own module.
- `tatsu/util/escapes.py` renamed to `tatsu/util/tty.py` with expanded API (cursor controls, `pushup`, `blankpad`, etc.).
- `Style.__repr__` now uses `\e` notation consistently and encodes `fmt` specs for roundtrip via `f{...:...}`.
- `Style.__len__` uses `visual_len()` from `util.tty` (ignores ANSI escapes in length).
- `packetz` serialization simplified: removed hash validation; `__class__` compressed to `@` in JSON.
- `barz.BarRow` switched from private accessors to public attributes; `stop_on_complete` → `selfstop`.
- `parproc.task` uses `PacketzQueue` directly instead of `init_queue()` helper.

## Fixed

- _Fixed:_ `Group` no longer optimized away if `Group.exp` contains non-leaf nodes. The optimization made EBNF representation semantically incorrect. Re-introducing a group for `--pretty` had several special cases (group if part of `Sequence`, `Named`, ...).
- _Fixed:_ Exporting `cling` CLI no longer pulls in `rich` as a dependency.
- _Fixed:_ ANSI escape utilities no longer duplicated across `ztyle.style` and `packetz.packet`; consolidated in `util.tty`.

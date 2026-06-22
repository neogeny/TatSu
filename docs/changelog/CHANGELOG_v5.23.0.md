<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.23.0] bugfix

[v5.23.0]: https://github.com/neogeny/tatsu/compare/v5.22.1...HEAD

## Added

- _Added_ `--generate-parser` option to the `cling` CLI tool.
- _Added_ `tatsu.util.barz` — self-contained progress bar rendering (replaces `rich.progress`).
- _Added_ `tatsu.util.treez` — self-contained dependency tree rendering (replaces `rich.tree`).
- _Added_ `tests/tree_test.py`.
- _Added_ `g2e` subcommand to `cling` CLI — translates ANTLR grammars to TatSu.
- _Added_ `bench` and `ideps` subcommands to `cling` CLI.
- _Added_ `add_argparse_options(parser)` pattern to `bench.py`, `ideps.py`, `g2etool.py` for uniform CLI interface.

## Changed

- **No more `colorama`**: All mentions of `colorama` removed. The project consistently uses its own `ztyle` library.
- **No more `rich` dependency**: `cling` CLI no longer pulls in `rich`. Progress bars use `tatsu.util.barz`. Dependency trees use `tatsu.util.treez`. Summaries use `ztyle`.
- `colorize` module renamed to `ztyle` to avoid confusion with the `colorize` package on PyPI.
- `tatsu.grammars` renamed to `tatsu.peg` (kept `grammars.py` shim).
- `tatsu.api` moved into its own `tatsu.api` package.
- `ideps.py` refactored to use own `Tree` + `Style` instead of `rich.tree`.
- `bench.py`, `ideps.py`, `g2etool.py` migrated from ad-hoc argument parsing to `add_argparse_options(parser)` + `main(parser) -> int`.
- Bar metrics refactored: `Metrics` class with lazy `@cached_property` per column; `BarRowData` base class extracted to break circular dependency; `Col` enum moved to own module.

## Fixed

- _Fixed:_ `Group` no longer optimized away if `Group.exp` contains non-leaf nodes. The optimization made EBNF representation semantically incorrect. Re-introducing a group for `--pretty` had several special cases (group if part of `Sequence`, `Named`, ...).
- _Fixed:_ Exporting `cling` CLI no longer pulls in `rich` as a dependency.

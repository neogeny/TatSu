<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.22.2] bugfix

[v5.22.2]: https://github.com/neogeny/tatsu/compare/v5.22.0...5.22.2

## Changed

- There are no longer features enabled by the  `colorama` library. Mentions of `colorama` in the source code and documentation have been removed. The project consistently uses its own `colorize` library for colorized output. `progress` is used to provide progress bars for the `cling` version of the CLI.

## Fixed

- _Fixed:_ Exporting the new `cling` CLI pulled in `rich` as a dependency.
- _Fixed:_ `Group` is no longer optimized away if `Group.exp` may contain other nodes (most except leaf nodes like `Token` and `Pattern`). The optimization made the EBNF representation of the optimized grammar not semantically equivalent to the original, and thus incorrect. 

  The additional no-op call that a `Group` would produce during parsing can be optimized away by model nodes like `Sequence`. Re-introducing a group for EBNF (`--pretty`) had several special cases (must be grouped if part of a `Sequence`, `Named`, ...).

<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.21.1] Update

[v5.21.1]: https://github.com/neogeny/tatsu/compare/v5.21.0...HEAD


## Added

- `@name`, `@int`, `@uint`, `@float`, `@bool` meta-expressions for typed matching (identifiers, signed/unsigned integers, floating point literals, and boolean literals)
- `FailedMeta` exception for `@` meta failures
- `@name` now matches identifiers starting with `_`
- `-z` / `--optimize` CLI option to optimize the grammar model before generating output

## Changed

- Cache optimized grammar models; inline single-element sequences and call chains in `Rule.optimized()`
- `Cursor`/`Text` protocols moved from `input/text.py` → `input/cursor.py`
- Versioning via `uv-dynamic-versioning`; `_version.py` reads from `importlib.metadata`
- CI: upgrade to `checkout@v6`, `setup-uv@v7`, `setup-python@v6`; all dependencies via `uv sync`

## Removed

- Deprecated `override_single_deprecated` (bare `@` as override) from grammar and boot parser to allow the symbol to be used for the new _meta_-expressions

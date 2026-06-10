<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.21.1] Update

[v5.21.1]: https://github.com/neogeny/tatsu/compare/v5.21.0...HEAD


## Added

### New `colorize` module in `tatsu/util/colorize/`:

- `Color`/`Style` ANSI colour library in `tatsu/util/colorize/` with zero dependencies, dynamic TTY/`NO_COLOR`/`FORCE_COLOR` support, 256-colour palettes, 24-bit RGB, and 148 CSS named colours
- `Color.default()` factory method for the system-default colour policy
- `Style` chainable modifier methods (`bold()`, `dim()`, `fg()`, `bg()`, etc.) all returning immutable copies; `apply()` wraps arbitrary text in self-terminating ANSI sequences without leaking into non-TTY output
- Lazy-loaded `named_color()` and `css_color()` standalone lookup functions re-exported from the package
- `ConsoleTracer` and `_ColorSet` (`exceptions.py`) now compose `Style` objects instead of concatenating ANSI strings, eliminating bleeding between trace/error colour spans

### `Meta` expressions in grammars

- `@name`, `@int`, `@uint`, `@float`, `@bool` meta-expressions for typed matching (identifiers, signed/unsigned integers, floating point literals, and boolean literals)
- `FailedMeta` exception for `@` meta failures
- `-z` / `--optimize` CLI option to optimize the grammar model before generating output

## Changed

- Cache optimized grammar models; inline single-element sequences and call chains in `Rule.optimized()`
- `Cursor`/`Text` protocols moved from `input/text.py` → `input/cursor.py`
- Versioning via `uv-dynamic-versioning`; `_version.py` reads from `importlib.metadata`
- CI: upgrade to `checkout@v6`, `setup-uv@v7`, `setup-python@v6`; all dependencies via `uv sync`

## Removed

- Deprecated `override_single_deprecated` (bare `@` as override) from grammar and boot parser to allow the symbol to be used for the new _meta_-expressions

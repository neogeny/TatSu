<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# v5.20.1 Update

[修TieXiu]: https://github.com/neogeny/tiexiu
[⻰OGoPEGo]: https://github.com/neogeny/ogopego 
[꘩TS'emekwes]: https://github.com/neogeny/tsemekwes
[pegen]: https://we-like-parsers.github.io/pegen/grammar.html

## Grammar, Optimization & Regex

* `Grammar.parse()` now eagerly calls `self.optimized()` before parsing,
  producing a *new* `Grammar` instance rather than mutating in place.
  `Grammar.optimize()` and the `optrules` property have been removed.
  Code generators (`pythongen`, `parsermodel_gen`) also call
  `model.optimized()` before emitting source.

* All model nodes support deep optimization: `Model.optimized()` returns
  `copy(self)`; `Option`, `Group`, `Choice`, `Box`, `NamedBox`, `Sequence`,
  `Rule`, and `RuleInclude` each optimize their children recursively,
  unwrapping single-element containers; `Call.optimized()` collapses
  `Call -> Rule(exp=Call)` chains; `Closure`/`Join` overrides removed
  (handled by `Box`); `EmptyClosure.__post_init__` sets `self.ast = None`.
  Lazy attributes (`_lookahead`, `_firstset`, `_follow_set`) use `getattr()`
  for safety with copied nodes. `Model._set_grammar()` renamed to `link()`.

* The `Func` type replaces `Callable[..., Any]` in `find_rule()` and related
  interfaces. `to_parsermodel_sourcecode` and `compile_to_parser` are now
  exported from `tatsu.tool` and `tatsu.tool.api`.

* The bootstrap parser and rules were regenerated to eliminate skeletal
  `Group`/`Option` wrapping.

* For compatibility with sibling projects [修TieXiu] (Rust), [⻰OGoPEGo] (Go),
  and [꘩TS'emekwes] (TypeScript), all `Pattern`-based regex lookaheads in the
  meta-grammar have been replaced with grammar-level `&`/`!` lookaheads. The
  `comments` and multiline string regexes were simplified (dropped `(?:.|\n)`
  and `(?!""")`/`(?!''')` guards). The `DEDENT` rule's `(?=\S)` became `&/\S/`,
  `raw_string` was split into a two-step check, and `path`/`word` patterns now
  use explicit `[_a-zA-Z]` instead of `(?!\d)\w` lookarounds.

## Left Recursion Analysis

* The left-recursion modules have been renamed: `leftrecmarker.py` → `depthf.py`,
  `pegen_leftrec.py` → `pegen.py`, `graphtools.py` → `tools.py`. A new
  `autumn.py` provides an alternative depth-framed algorithm. The SCC entry
  point in `pegen.py` is now `mark_left_recursion()`.

## Error Reporting

* `FailedParse.__str__()` uses `str.splitlines()` and prints the error marker
  unconditionally (not just when the error lands on the current line).

## Tooling, Build & Documentation

* The `tatsu.tool.bench` now supports benchmarking the [⻰OGoPEGo][] `Go` port
  via `--ogo`, and a `--both` mode restricts to TatSu parsers only.
  `failed_files` appears at the top in verbose output.

* The `Justfile` received formatting cleanups and now omits `--no-summary`
  from pytest invocations. `docs/accept.txt` accepts `Justfile` as a token.

* `README.rst` now has a **Sibling Projects** section.

* CLI tests use a `uv_run()` helper with diagnostic assertions.
  The bootstrap test sets `trace=False` and removes the redundant
  `g9.optimized()` call (optimization is now inside `parse()`).

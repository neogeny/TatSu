<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# v5.20.1 Update

## Left Recursion Analysis

* All versionf of left recursion analysis once used in **TatSu** are included
  in the project as modules, with the active one being the _SCC_ (Strongly
  Connected Components) version ported from [pegen].

[pegen]: https://we-like-parsers.github.io/pegen/grammar.html

## Regular Expressions

* For compatibility with the optimal _regex_ implementations in sibling projects
  [修TieXiu] (Rust) and [⻰OGoPEGo] (Go), the **TatSu** meta-grammar has been
  stripped of regexp lookahead expressions like `(?=)` and `(?!)`) replacing
  them with grammar-level lookaheads (`&` and `!`) when required. All tests
  pass.

  [修TieXiu]: https://github.com/neogeny/tiexiu
  [⻰OGoPEGo]: https://github.com/neogeny/ogopego 

### Optimized

* Now `Grammar` keeps a parallel list (tuple) of optimized `Rule` that is used
  for parsing. Optimization consists on the elimination of `Model` nodes that
  don't affect the semantics of parsing. The optimized rules are available as
  `Grammar.optrules`. The original `Grammar.rules` remains as before as to be
  able to reconstruct the original input with `repr(g)` or `g.pretty()`.

<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.22.1] optimizations

[v5.22.1]: https://github.com/neogeny/tatsu/compare/v5.22.0...v5.22.1

## Added

- _Added_ missing formats to `tatsu.cling` CLI tool. They are `--pretty-lean`, `--object-model`, `--parser-model`, `--generate-parser`.

## Changed

- Now parsing for the `Sequence` model node does folding of the parsed elements like the generated procedural parser does through the `Context.states: StateStack`.

- Several inline optimizations added to the parsing engine in `Context`.

## Unchanged

- **TatSu** continues to use a state stack to keep track of the parse _Tree_ and exceptions to baktrack during parsing. The approach allows for straightforward generation of parsers that are efficient and simple to understand because there's no mention of input position or _Tree_ management. 


## Benchmarks

These benchmark was available but not included in previous updates:

```bash
grammar: grammar/java.ebnf
input files: 62

--- in-memory model ---
failed files:

datasets/Ternary1.java

typename: Grammar
one-time setup:                   1.57 s
total parsing time (62 files):   36.28 s
errors (1/62 files):              1.61 %
average parsing time:             0.59 s/file
average speed:                  331.12 sloc/sec

--- generated python parser ---
failed files:

datasets/Ternary1.java

typename: JavaParser
one-time setup:                   3.29 s
total parsing time (62 files):   26.76 s
errors (1/62 files):              1.61 %
average parsing time:             0.43 s/file
average speed:                  449.00 sloc/sec

--- tiexiu (rust) parser ---
failed files:

datasets/Ternary1.java

typename: tiexiu.parse
one-time setup:                   2.99 s
total parsing time (62 files):  234.70 s
errors (1/62 files):              1.61 %
average parsing time:             3.79 s/file
average speed:                   51.19 sloc/sec

--- ogopego (go) parser ---
failed files:

datasets/Ternary1.java

typename: ogopego.parse
one-time setup:                   5.16 s
total parsing time (62 files):   33.19 s
errors (1/62 files):              1.61 %
average parsing time:             0.54 s/file
average speed:                  361.98 sloc/sec

--- comparison (sloc/sec ratios) ---
         sloc/s      1      2      3      4
mem (1)  331.12      -   0.74   6.47   0.91
gen (2)  449.00   1.36      -   8.77   1.24
xiu (3)   51.19   0.15   0.11      -   0.14
ogo (4)  361.98   1.09   0.81   7.07      -
```

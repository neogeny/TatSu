<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.21.1] Update

[v5.21.1]: https://github.com/neogeny/tatsu/compare/v5.21.0...HEAD


## Added

### `cling` — new default CLI

- Three subcommands: `tatsu run` (parse files), `tatsu boot` (show boot grammar), `tatsu grammar` (grammar transformations)
- Multi-file batch parsing with live dual-column progress bars — overall progress + per-file heartbeat powered by the new parser-level heartbeat hook
- Per-file verbose output (`--verbose`) with timing and error details
- Summary table with file/line counts, successes, failures, success rate, lines/sec, and elapsed time
- `--quiet` to suppress progress and summary, `--nproc` for parallel workers
- Files read once; all reports use cached content
- The previous CLI is still available as `otatsu`

### `Heartbeat` protocol — per-token progress hook

- `Heart` protocol in `tatsu/util/heart.py` with a single `beat(mark, total)` method; `NullHeart` no-op for parallel or unobserved parsing
- `ParserConfig.heart` field lets applications inject a heartbeat receiver; `ParserCore` issues a `heart.beat(pos, len)` on token advancement and rule calls with a 0.128s cooldown for real-time reporting of parsing progress

### New `colorize` module in `tatsu/util/colorize/`:

- `Color`/`Style` ANSI colour library in `tatsu/util/colorize/` with zero dependencies, dynamic TTY/`NO_COLOR`/`FORCE_COLOR` support, 256-colour palettes, 24-bit RGB, and 148 CSS named colours
- `Color.default()` factory method for the system-default colour policy
- `Style` chainable modifier methods (`bold()`, `dim()`, `fg()`, `bg()`, etc.) all returning immutable copies; instances are callable (equivalent to `.apply()`), so a single style can be reused: `hl = Style().red().bold(); print(hl("text"))`
- Lazy-loaded `named_color()` and `css_color()` standalone lookup functions re-exported from the package
- `ConsoleTracer` and `_ColorSet` (`exceptions.py`) now compose `Style` objects instead of concatenating ANSI strings, eliminating bleeding between trace/error colour spans

    ```python
    from tatsu.colorize import Style
    
    style = Style().red().bold()
    print(style("text"))
    ```

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

## CLING The New Console Interface

#### Options  the `run` subcommand

```bash
sage: tatsu run [-h] [-q] [-v] [-t] [-o OUTPUT] [-c {auto,always,never}] [-j] [-m] [-s START] [-n NPROC]
                 path inputs [inputs ...]

positional arguments:
  path                  Path to a grammar in EBNF or JSON format
  inputs                The files to be parsed

options:
  -h, --help            show this help message and exit
  -j, --json            Print output in JSON format
  -m, --model           Print the model code
  -s, --start START     Name of the start rule
  -n, --nproc NPROC     Number of concurrent workers

global options:
  -q, --quiet           Suppress progress bar and spinner output
  -v, --verbose         Provide more detailed information about the parsing process
  -t, --trace           Display a detailed trace of the parsing process
  -o, --output OUTPUT   Output to a file or directory instead of stdout
  -c, --color {auto,always,never}
                        Control colorized output (default: auto)
```


#### Consoloe output for the `run` subcommand

```bash
results:
✗ Ternary1.java                             0.0s
✓ Ternary2.java                             0.2s
✓ JavaTernaryOperatorExamples.java          0.2s
✓ NavPanelCore.java                         2.3s
✓ GwpCreditcardOperations.java              3.8s


FAILURES: 1

error: Expected one of: ';' 'annotation_type_declaration' 'class_declaration' 'enum_declaration' 'interface_declaration' 'type_declaration'

  --> datasets/Ternary1.java@23[1:1]
   |
 1 | #public class Ternary1
   | ^ Expected one of: ';' 'annotation_type...

→ compilation_unit
→ start


        files input             5
 source lines input          2047
      success lines          2019
               sloc          1724
          successes             4
           failures             1
       success rate            80 %
           sloc/sec           318 sl/s
           run time          0:06
          wall time          0:00
```

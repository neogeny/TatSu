# `tatsu` — TatSu CLI (`cling`)

A three-subcommand CLI for TatSu, mirroring the ogopego tool.

## Usage

```console
tatsu [global-options] <command> [command-options] [arguments]
```

## Global Options

Available on every subcommand (placed before the subcommand name):

| Short | Long         | Description                                          |
|-------|--------------|------------------------------------------------------|
| `-V`  | `--version`  | Print version information and exit                   |
| `-q`  | `--quiet`    | Suppress progress bars, summary, and non-output text |
| `-v`  | `--verbose`  | Show per-file results with timing and error details  |
| `-t`  | `--trace`    | Display a detailed trace of the parsing process      |
| `-o`  | `--output`   | Write output to a file or directory instead of stdout |
| `-c`  | `--color`    | Control colorized output: `auto`, `always`, `never`  |
| `-h`  | `--help`     | Show help message and exit                           |

### `-q` / `--quiet`

Suppresses the live progress bar (during multi-file `run`) and the post-run summary table. Errors and parse results are still shown.

### `-v` / `--verbose`

In `run`, prints a per-file result line after processing:

```
results:
✓  0.34s  file1.java
✗  0.12s  file2.java
     ...
```

Failures also print the exception details below the file line.

### `-o` / `--output`

- **Single file path**: all output is written to that file.
- **Directory path**: each input file gets its own output file, named after the input stem with the appropriate extension.
- **Unset** (default): output goes to stdout.

JSON is the default serialization format. When there are multiple input
files and output is **not** a directory (stdout or single file path),
output uses JSONL (one JSON object per line with `input`/`result` keys),
unless output is to a TTY, in which case indented JSON is used:
```json
{"input": "path/to/file", "result": { ... parsed output ... }}
```
- **Directory output** (`-o dir/` or an existing directory path): each input
  file gets its own `.json` file in the directory. The directory is created
  automatically if it does not already exist. No JSONL wrapper is used.
- **Single file path** (`-o path` to a non-existent path or an existing file):
  multiple input files produce JSONL. A single input file produces indented
  JSON.
- **Stdout** (no `-o`): multiple input files produce JSONL unless stdout is a
  TTY (indented JSON instead). A single input file produces indented JSON.

### `-c` / `--color`

- `auto` (default): color if stdout is a TTY and `$NO_COLOR` is not set.
- `always`: always emit ANSI color codes.
- `never`: strip all ANSI color codes.

When output is colorized (TTY with `--color=auto` and no `$NO_COLOR`, or
`--color=always`), the output is syntax-highlighted using Pygments — JSON
with `JsonLexer`, Python model output with `PythonLexer`, and EBNF grammar
text with `EbnfLexer`.

### `-e` / `--theme`

Pygments style name for syntax highlighting (e.g. `monokai`, `one-dark`,
`solarized-light`, `native`). Use `--theme=list` to print the list of
available styles. Defaults to the terminal's configured theme or Pygments'
default. Only effective when colorization is active (see `--color`).

---

## Subcommands

### `tatsu run`

Parse one or more input files against a grammar.

```console
tatsu [global-options] run [options] <grammar> <input> [input...]
```

**Arguments:**

| Argument    | Description                                      |
|-------------|--------------------------------------------------|
| `grammar`   | Path to a TatSu grammar (`.ebnf` or `.json`)    |
| `input`     | One or more files to parse                       |

**Options:**

| Short | Long        | Description                                          |
|-------|-------------|------------------------------------------------------|
| `-j`  | `--json`    | Output results as JSON (indented for single file, JSONL for multiple files) |
| `-m`  | `--model`   | Output the Python model representation of results    |
| `-s`  | `--start`   | Name of the start rule (defaults to grammar default) |
| `-n`  | `--nproc`   | Number of parallel worker processes (0 = serial)     |

**Output formats:**

- **Default** (no `-j`/`-m`): results are serialized as indented JSON via `asjsons()`.
- **`--json`**: same as default, but when processing multiple files outputs
  newline-delimited JSON (JSONL) with `{"input": <path>, "result": <value>}` entries.
- **`--model`**: each result is `repr()` of the parse model.

For a **single input file**, the result is written directly (indented JSON by default).
For **multiple input files** with `--json` to stdout, output is JSONL format.

**Progress display:**

When `rich` is available and `-q` is not set, `tatsu run` shows a live
dual-column progress bar:
- **Main bar** (yellow): overall file-level progress.
- **Per-file bars** (green): line-level heartbeat progress during parsing
  (serial mode only).

After processing, a summary table is printed to stderr:

```
        files input             2
 source lines input            42
      success lines            42
              sloc            38
         successes             2
          failures             0
      success rate           100 %
          sloc/sec       38000 sl/s
          run time          0:00
         wall time          0:00
```

The summary includes file counts, line counts (total, code, comment, blank),
success/failure counts, success rate, lines per second, and timing.

Use `-q` to suppress both the progress bar and the summary.

**Processing modes:**

| Mode                   | Condition                                                                 |
|------------------------|---------------------------------------------------------------------------|
| Single file (direct)   | One input file — parsed immediately, no progress bar                      |
| Multi-file with bar    | `rich` available, `-q` not set — `parproc_visual` with `DualProgress`     |
| Multi-file without bar | `rich` unavailable or `-q` set — `parproc` with no progress display       |

---

### `tatsu boot`

Print the internal boot grammar used by TatSu.

```console
tatsu [global-options] boot [options]
```

**Options:**

| Short | Long           | Description                                |
|-------|----------------|--------------------------------------------|
| `-j`  | `--json`       | Output the grammar as JSON                 |
| `-m`  | `--model`      | Output the Python model representation     |
| `-p`  | `--pretty`     | Pretty-print the grammar (default)         |
| `-r`  | `--railroads`  | Print a railroad diagram of the grammar    |

These options are mutually exclusive. Default is `--pretty`.

---

### `tatsu grammar`

Load a grammar and display it in the requested format.

```console
tatsu [global-options] grammar [options] <grammar>
```

**Arguments:**

| Argument    | Description                                      |
|-------------|--------------------------------------------------|
| `grammar`   | Path to a TatSu grammar (`.ebnf` or `.json`)    |

**Options:**

Same mutually-exclusive format options as `boot`: `-j`/`--json`, `-m`/`--model`,
`-p`/`--pretty`, `-r`/`--railroads`.

---

## Input File Reading

For the `run` subcommand, input files are read exactly once. The file content
is stored in a `VisualPayload` and passed through the processing pipeline.
All reporting (line counts, per-file status) uses the cached content — there
is no double read.

## The `Heart` Protocol

The parser core exposes a per-token progress hook via the `Heart` protocol.
When `rich` is available and `-v` is set, the `run` subcommand injects a
`ProgressHeart` into the parser configuration, providing real-time line-level
progress during serial (`-n 0`) parsing. Parallel mode (`-n > 0`) uses a
`NullHeart` that performs no progress tracking.

## Entry Points

- `python -m tatsu.tool.cling` — run the CLI (`__main__.py`)
- `from tatsu.tool.cling import main, parse_args, CLIConfig` — programmatic use

## Related

The previous `tatsu` CLI (the original tool interface) is still available as
`otatsu`.

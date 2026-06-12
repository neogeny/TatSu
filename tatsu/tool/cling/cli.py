# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""CLI for TatSu, mirroring ogopego's three-subcommand structure."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from tatsu import __toolname__, __version__
from tatsu.exceptions import ParseError

from ...grammars.model import Grammar
from .config import DEFAULT_PYGMENTS_STYLE, CLIConfig
from .fmt import _colorize, _should_colorize
from .lib import Results, load_grammar


def parse_args(argv: list[str] | None = None) -> CLIConfig:
    """Parse command-line arguments and return a CLIConfig.

    Matches ogopego's subcommand structure (run / boot / grammar).
    """
    if argv is None:
        argv = sys.argv[1:]

    # Handle --version before argparse to match ogopego's pre-dispatch check
    parser = argparse.ArgumentParser(
        prog="tatsu",
        description="TatSu: a PEG parser generator",
    )

    sub = parser.add_subparsers(
        dest="command",
        description="Main execution mode",
        required=False,
        help="Available subcommands",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"{__toolname__} {__version__}",
        help="Print version information and exit",
    )
    add_global_options(parser)
    # _help_cmd = add_help_cmd(subparsers)
    _boot_cmd = add_boot_cmd(sub)
    _grammar_cmd = add_grammar_cmd(sub)
    _run_cmd = add_run_cmd(sub)

    if "--version" in argv or "-V" in argv or "version" in argv:
        print(f"{__toolname__} {__version__}")
        sys.exit(0)

    # if len(argv) <= 1 or argv[0] in ("-h", "--help"):
    #     parser.print_help()
    #     sys.exit(0)

    args = parser.parse_args(argv)
    command = args.command
    if command == "help" or "-h" in argv or "--help" in argv:
        parser.print_help()
        sys.exit(0)

    cfg = CLIConfig()
    for name, value in vars(args).items():
        if name == "name":
            continue
        if not hasattr(cfg, name):
            raise RuntimeError(f"Unknown option: {name}")
        setattr(cfg, name, value)
    return cfg


def _output_ext(cfg: CLIConfig) -> str:
    """Return file extension for the current output format."""
    if cfg.model:
        return ".py"
    if cfg.railroads:
        return ".railroads.txt"
    if cfg.pretty:
        return ".ebnf"
    return ".json"


def _output_path(cfg: CLIConfig, *, name: str | None = None) -> Path | None:
    """Return output path, or None for stdout.

    If cfg.output is a directory, appends *name* (with format extension).
    Otherwise returns the file path.
    """
    if not cfg.output:
        return None
    out = Path(cfg.output)
    if out.is_dir():
        if name is None:
            return None
        return out / (name + _output_ext(cfg))
    return out


def _show(payload: str, output: Path | None) -> None:
    """Write payload to a file or stdout."""
    if output is None:
        print(payload)
    else:
        output.write_text(payload)


def _render_grammar(
    gram: Grammar,
    cfg: CLIConfig,
    *,
    name: str | None = None,
) -> str:
    """Render a Grammar in the selected mode.

    Sets *name* to the output basename (without extension) when -o is a directory.
    """
    _ = name
    if cfg.json:
        payload = gram.asjsons()
    elif cfg.model:
        payload = repr(gram)
    elif cfg.railroads:
        payload = gram.railroads()
    elif cfg.pretty:
        payload = gram.pretty()
    else:
        payload = gram.asjsons()
    return payload


def boot_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``boot`` subcommand."""
    from ..api import boot_grammar

    payload = _render_grammar(
        boot_grammar(),
        cfg,
        name="boot",
    )
    return [("boot", payload)]


def grammar_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``grammar`` subcommand."""
    gram = load_grammar(cfg.path)

    payload = _render_grammar(
        gram,
        cfg,
        name=Path(cfg.path).stem,
    )
    return [(cfg.path, payload)]


def output_results(cfg: CLIConfig, results: list[tuple[str, Any]]) -> None:
    out_path = Path(cfg.output) if cfg.output else None

    # Directory output: each input gets its own .json file
    if out_path and (
        str(cfg.output).rstrip().endswith((os.sep, "/")) or out_path.is_dir()
    ):
        out_path.mkdir(parents=True, exist_ok=True)
        ext = _output_ext(cfg)
        for input_path, single_payload in results:
            name = Path(input_path).stem
            out = (out_path / name).with_suffix(ext)
            _show(single_payload, out)
        return

    # JSONL for multiple input files (JSON is the default format)
    # Skip JSONL when output is to a TTY — use indented JSON instead.
    if (
        not cfg.model
        and len(results) > 1
        and not (not cfg.output and sys.stdout.isatty())
    ):
        import json

        jsonl = "\n".join(
            json.dumps(
                {"input": input_path, "result": json.loads(outcome)},
                separators=(",", ":"),
            )
            for input_path, outcome in results
        )
        _show(jsonl, _output_path(cfg))
        return

    # Single result or model output: write sequentially
    single_out = _output_path(cfg)
    should_colorize = _should_colorize(cfg) and single_out is None and not cfg.railroads

    language = "json"
    if cfg.model:
        language = "python"
    elif cfg.pretty:
        language = "ebnf"

    payloads = [payload for _, payload in results]
    if should_colorize:
        payloads = [_colorize(payload, language, cfg.style) for payload in payloads]

    single_payload = "\n".join(payloads)
    if single_out is None:
        print(single_payload)
    else:
        single_out.write_text(single_payload)


def main() -> None:
    """Entry point for the cling CLI (not wired to console_scripts yet)."""
    sys.setrecursionlimit(2**16)
    try:
        cfg = parse_args()

        if (
            os.environ.get("NO_COLOR") and cfg.color == "auto"
        ) or not sys.stderr.isatty:
            cfg.color = "never"

        if cfg.style == "list":
            from pygments.styles import get_all_styles

            for style in sorted(get_all_styles()):
                print(style)
            sys.exit(0)
        match cfg.command:
            case "boot":
                results = boot_cmd(cfg)
            case "grammar":
                results = grammar_cmd(cfg)
            case "run":
                from .run_cmd import run_cmd

                results = run_cmd(cfg)
            case _:
                print(cfg, file=sys.stderr)
                return
        output_results(cfg, results)
    except KeyboardInterrupt:
        sys.exit(0)
    except ParseError:
        sys.exit(1)


def add_global_options(parser):
    group = parser.add_argument_group("global options")
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress bar and spinner output",
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Provide more detailed information about the parsing process",
    )
    group.add_argument(
        "-t",
        "--trace",
        action="store_true",
        help="Display a detailed trace of the parsing process",
    )
    group.add_argument(
        "-o",
        "--output",
        default="",
        help="Output to a file or directory instead of stdout",
    )
    group.add_argument(
        "-c",
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Control colorized output (default: auto)",
    )
    group.add_argument(
        "-l",
        "--style",
        dest="style",
        default=DEFAULT_PYGMENTS_STYLE,
        help="Pygments style name for syntax highlighting",
    )
    # group.add_argument(
    #     "--profile",
    #     action="store_true",
    #     help="Enable CPU and memory profiling",
    # )


def add_help_cmd(subparsers):
    help_parser = subparsers.add_parser(
        "help",
        help="Provide command help",
        add_help=False,
    )
    return help_parser


def add_grammar_options(parser):
    format = parser.add_mutually_exclusive_group()
    format.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json",
        default=True,
        help="Output the grammar in JSON format",
    )
    format.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="model",
        help="Output the model code according to the grammar",
    )
    format.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        dest="pretty",
        help="Output the grammar in pretty-printed EBNF format",
    )
    format.add_argument(
        "-r",
        "--railroads",
        action="store_true",
        dest="railroads",
        help="Output a railroad diagram of the grammar",
    )


def add_boot_cmd(subparsers):
    boot_parser = subparsers.add_parser(
        "boot",
        help="The internal boot grammar",
    )
    add_global_options(boot_parser)
    add_grammar_options(boot_parser)
    return boot_parser


def add_grammar_cmd(subparsers):
    grammar_parser = subparsers.add_parser(
        "grammar",
        help="Grammar transformations",
        add_help=True,
    )
    add_global_options(grammar_parser)
    add_grammar_options(grammar_parser)
    grammar_parser.add_argument(
        "path", help="Path to the grammar source (.ebnf or .json)"
    )
    return grammar_parser


def add_run_cmd(subparsers):
    run_parser = subparsers.add_parser(
        "run",
        help="Parse input files with the given grammar",
    )
    add_global_options(run_parser)
    run_parser.add_argument("path", help="Path to a grammar in EBNF or JSON format")
    run_parser.add_argument("inputs", nargs="+", help="The files to be parsed")
    format = run_parser.add_mutually_exclusive_group()
    format.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json",
        default=True,
        help="Output the grammar in JSON format",
    )
    format.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="model",
        help="Output the model code according to the grammar",
    )
    run_parser.add_argument(
        "-s", "--start", default="", dest="start", help="Name of the start rule"
    )
    run_parser.add_argument(
        "-n",
        "--nproc",
        type=int,
        default=0,
        dest="nproc",
        help="Number of concurrent workers",
    )
    return run_parser

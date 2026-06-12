# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""CLI for TatSu, mirroring ogopego's three-subcommand structure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tatsu import __toolname__, __version__
from tatsu.exceptions import ParseError

from .lib import CLIConfig, Results, load_grammar


if TYPE_CHECKING:
    from ...grammars.model import Grammar


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
        required=True,
        # help="Available subcommands",
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
    if not command or command == "help" or "-h" in argv or "--help" in argv:
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
    if cfg.json or cfg.json or cfg.json:
        return ".json"
    if cfg.model or cfg.model or cfg.model:
        return ".py"
    if cfg.railroads or cfg.railroads:
        return ".railroads.txt"
    if cfg.pretty or cfg.pretty:
        return ".ebnf"
    return ".txt"


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
        with output.open("w", encoding="utf-8") as f:
            f.write(payload)
            f.write("\n")
            f.flush()


def _render_grammar(
    gram: Grammar,
    cfg: CLIConfig,
    *,
    json: bool = False,
    model: bool = False,
    pretty: bool = False,
    railroads: bool = False,
    name: str | None = None,
) -> str:
    """Render a Grammar in the selected mode.

    Sets *name* to the output basename (without extension) when -o is a directory.
    """
    if json:
        payload = gram.asjsons()
    elif model:
        payload = repr(gram)
    elif railroads:
        payload = gram.railroads()
    else:
        payload = gram.pretty()
    return payload


def boot_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``boot`` subcommand."""
    from ..api import boot_grammar

    payload = _render_grammar(
        boot_grammar(),
        cfg,
        json=cfg.json,
        model=cfg.model,
        pretty=cfg.pretty,
        railroads=cfg.railroads,
        name="boot",
    )
    return [("boot", payload)]


def grammar_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``grammar`` subcommand."""
    gram = load_grammar(cfg.path)

    payload = _render_grammar(
        gram,
        cfg,
        json=cfg.json,
        model=cfg.model,
        pretty=cfg.pretty,
        railroads=cfg.railroads,
        name=Path(cfg.path).stem,
    )
    return [(cfg.path, payload)]


def output_results(cfg: CLIConfig, results: list[tuple[str, Any]]) -> None:
    out_path = Path(cfg.output)
    if cfg.output and out_path.is_dir():
        ext = _output_ext(cfg)
        for input_path, payload in results:
            name = Path(input_path).stem
            out = (out_path / name).with_suffix(ext)
            _show(payload, out)
        return

    # NOTE output is not a directory at this point
    if cfg.json and len(results) > 1:
        import json

        jsonl = "\n".join(
            json.dumps(
                {
                    "input": input_path,
                    "result": json.loads(outcome),
                }
            )
            for input_path, outcome in results
        )
        _show(jsonl, _output_path(cfg))
        return

    single_out = _output_path(cfg)
    for i, (_, payload) in enumerate(results):
        if single_out is None:
            print(payload)
        else:
            with single_out.open("a" if i > 0 else "w", encoding="utf-8") as f:
                f.write(str(payload))
                f.write("\n")
                f.flush()


def main() -> None:
    """Entry point for the cling CLI (not wired to console_scripts yet)."""
    try:
        cfg = parse_args()
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
    except (ParseError, KeyboardInterrupt):
        return
    except Exception as e:
        print(e, file=sys.stderr)
        return


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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json",
        help="Print the boot grammar in JSON format",
    )
    mode.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="model",
        help="Print the model code",
    )
    mode.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        dest="pretty",
        help="Pretty-print the boot grammar",
    )
    mode.add_argument(
        "-r",
        "--railroads",
        action="store_true",
        dest="railroads",
        help="Print a railroad diagram",
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
    run_parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json",
        help="Print output in JSON format",
    )
    run_parser.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="model",
        help="Print the model code",
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

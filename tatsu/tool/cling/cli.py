# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""CLI for TatSu, mirroring ogopego's three-subcommand structure."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tatsu.util.asjson import asjsons


if TYPE_CHECKING:
    from ...grammars.model import Grammar

type Results = list[tuple[str, Any]]


@dataclass
class CLIConfig:
    """Parsed command-line configuration, matching ogopego's CLIConfig struct."""

    # Global flags
    color: str = "auto"
    output: str = ""
    trace: bool = False
    quiet: bool = False
    profile: bool = False

    # Subcommand state
    command: str = ""
    grammar: str = ""
    inputs: list[str] = field(default_factory=list)

    # run flags
    run_json: bool = False
    run_model: bool = False
    run_start: str = ""
    run_nproc: int = 0

    # boot flags
    boot_json: bool = False
    boot_model: bool = False
    boot_pretty: bool = False
    boot_railroads: bool = False

    # grammar flags
    grammar_json: bool = False
    grammar_model: bool = False
    grammar_pretty: bool = False
    grammar_railroads: bool = False


def parse_args(argv: list[str] | None = None) -> CLIConfig:
    """Parse command-line arguments and return a CLIConfig.

    Matches ogopego's subcommand structure (run / boot / grammar).
    """
    if argv is None:
        argv = sys.argv[1:]

    # Handle --version before argparse to match ogopego's pre-dispatch check
    if "--version" in argv:
        from ..._version import __toolname__, __version__

        print(f"{__toolname__} {__version__}")
        sys.exit(0)

    parser = argparse.ArgumentParser(
        prog="tatsu",
        description="TatSu: a PEG parser generator",
    )

    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Control colorized output (default: auto)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="Output to a file or directory instead of stdout",
    )
    parser.add_argument(
        "-t",
        "--trace",
        action="store_true",
        help="Display a detailed trace of the parsing process",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress bar and spinner output",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable CPU and memory profiling",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- run ---
    run_parser = subparsers.add_parser(
        "run",
        help="Parse input files with the given grammar",
    )
    run_parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default=argparse.SUPPRESS,
        help="Control colorized output (default: auto)",
    )
    run_parser.add_argument(
        "-o",
        "--output",
        default=argparse.SUPPRESS,
        help="Output to a file or directory instead of stdout",
    )
    run_parser.add_argument(
        "-t",
        "--trace",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Display a detailed trace of the parsing process",
    )
    run_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Suppress progress bar and spinner output",
    )
    run_parser.add_argument(
        "--profile",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Enable CPU and memory profiling",
    )
    run_parser.add_argument(
        "grammar", help="Path to the grammar in EBNF or JSON format"
    )
    run_parser.add_argument("inputs", nargs="+", help="The files to be parsed")
    run_parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="run_json",
        help="Print output in JSON format",
    )
    run_parser.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="run_model",
        help="Print the model code",
    )
    run_parser.add_argument(
        "-s", "--start", default="", dest="run_start", help="Name of the start rule"
    )
    run_parser.add_argument(
        "-n",
        "--nproc",
        type=int,
        default=0,
        dest="run_nproc",
        help="Number of concurrent workers",
    )

    # --- boot ---
    boot_parser = subparsers.add_parser(
        "boot",
        help="The internal boot grammar",
    )
    boot_parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default=argparse.SUPPRESS,
        help="Control colorized output (default: auto)",
    )
    boot_parser.add_argument(
        "-o",
        "--output",
        default=argparse.SUPPRESS,
        help="Output to a file or directory instead of stdout",
    )
    boot_parser.add_argument(
        "-t",
        "--trace",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Display a detailed trace of the parsing process",
    )
    boot_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Suppress progress bar and spinner output",
    )
    boot_parser.add_argument(
        "--profile",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Enable CPU and memory profiling",
    )
    boot_parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="boot_json",
        help="Print the boot grammar in JSON format",
    )
    boot_parser.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="boot_model",
        help="Print the model code",
    )
    boot_parser.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        dest="boot_pretty",
        help="Pretty-print the boot grammar",
    )
    boot_parser.add_argument(
        "-r",
        "--railroads",
        action="store_true",
        dest="boot_railroads",
        help="Print a railroad diagram",
    )

    # --- grammar ---
    grammar_parser = subparsers.add_parser(
        "grammar",
        help="Grammar transformations",
    )
    grammar_parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default=argparse.SUPPRESS,
        help="Control colorized output (default: auto)",
    )
    grammar_parser.add_argument(
        "-o",
        "--output",
        default=argparse.SUPPRESS,
        help="Output to a file or directory instead of stdout",
    )
    grammar_parser.add_argument(
        "-t",
        "--trace",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Display a detailed trace of the parsing process",
    )
    grammar_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Suppress progress bar and spinner output",
    )
    grammar_parser.add_argument(
        "--profile",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Enable CPU and memory profiling",
    )
    grammar_parser.add_argument(
        "grammar", help="Path to the grammar source (.ebnf or .json)"
    )
    grammar_parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="grammar_json",
        help="Print the grammar in JSON format",
    )
    grammar_parser.add_argument(
        "-m",
        "--model",
        action="store_true",
        dest="grammar_model",
        help="Print the model code",
    )
    grammar_parser.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        dest="grammar_pretty",
        help="Pretty-print the grammar (EBNF)",
    )
    grammar_parser.add_argument(
        "-r",
        "--railroads",
        action="store_true",
        dest="grammar_railroads",
        help="Print a railroad diagram",
    )

    args = parser.parse_args(argv)

    cfg = CLIConfig(
        color=getattr(args, "color", "auto"),
        output=getattr(args, "output", ""),
        trace=getattr(args, "trace", False),
        quiet=getattr(args, "quiet", False),
        profile=getattr(args, "profile", False),
        command=args.command,
    )

    if args.command == "run":
        cfg.grammar = args.grammar
        cfg.inputs = args.inputs
        cfg.run_json = args.run_json
        cfg.run_model = args.run_model
        cfg.run_start = args.run_start
        cfg.run_nproc = args.run_nproc

    elif args.command == "boot":
        cfg.boot_json = args.boot_json
        cfg.boot_model = args.boot_model
        cfg.boot_pretty = args.boot_pretty
        cfg.boot_railroads = args.boot_railroads

    elif args.command == "grammar":
        cfg.grammar = args.grammar
        cfg.grammar_json = args.grammar_json
        cfg.grammar_model = args.grammar_model
        cfg.grammar_pretty = args.grammar_pretty
        cfg.grammar_railroads = args.grammar_railroads

    return cfg


def _output_ext(cfg: CLIConfig) -> str:
    """Return file extension for the current output format."""
    if cfg.run_json or cfg.boot_json or cfg.grammar_json:
        return ".json"
    if cfg.run_model or cfg.boot_model or cfg.grammar_model:
        return ".py"
    if cfg.boot_railroads or cfg.grammar_railroads:
        return ".railroads.txt"
    if cfg.boot_pretty or cfg.grammar_pretty:
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


def _load_grammar(path: str) -> Grammar:
    """Load a Grammar from an .ebnf or .json file."""
    from ...grammars.model import Grammar as _Grammar

    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        return _Grammar.loads(source)
    from ..api import compile

    return compile(source)


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
        json=cfg.boot_json,
        model=cfg.boot_model,
        pretty=cfg.boot_pretty,
        railroads=cfg.boot_railroads,
        name="boot",
    )
    return [("boot", payload)]


def grammar_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``grammar`` subcommand."""
    gram = _load_grammar(cfg.grammar)

    payload = _render_grammar(
        gram,
        cfg,
        json=cfg.grammar_json,
        model=cfg.grammar_model,
        pretty=cfg.grammar_pretty,
        railroads=cfg.grammar_railroads,
        name=Path(cfg.grammar).stem,
    )
    return [(cfg.grammar, payload)]


def _format_result(cfg: CLIConfig, result: Any) -> str:
    """Format a parse result as a string."""
    if cfg.run_json:
        return asjsons(result)
    if cfg.run_model:
        return repr(result)
    return f"{result!s}"


def run_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``run`` subcommand."""
    from ...util.parproc import parproc_visual

    grammar = _load_grammar(cfg.grammar)
    start = cfg.run_start or None

    results: list[tuple[str, Any]] = []
    if len(cfg.inputs) == 1:
        path = cfg.inputs[0]
        text = Path(path).read_text(encoding="utf-8")
        result = grammar.parse(text, start=start)
        results.append((path, result))
    else:

        def parse_file(path: str) -> Any:
            text = Path(path).read_text(encoding="utf-8")
            return grammar.parse(text, start=start)

        results += [
            (r.payload, _format_result(cfg, r.outcome))
            for r in parproc_visual(
                parse_file,
                cfg.inputs,
                parallel=cfg.run_nproc > 0,
            )
        ]
    return results


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
    if cfg.run_json and len(results) > 1:
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
                f.write(payload)
                f.write("\n")
                f.flush()


def main() -> None:
    """Entry point for the cling CLI (not wired to console_scripts yet)."""
    cfg = parse_args()
    match cfg.command:
        case "boot":
            results = boot_cmd(cfg)
        case "grammar":
            results = grammar_cmd(cfg)
        case "run":
            results = run_cmd(cfg)
        case _:
            print(cfg, file=sys.stderr)
            return
    output_results(cfg, results)

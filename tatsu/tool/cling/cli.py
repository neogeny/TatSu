# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""CLI for TatSu, mirroring ogopego's three-subcommand structure."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ...grammars.model import Grammar


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
    boot_parser: bool = False
    boot_parser_model: bool = False
    boot_object_model: bool = False

    # grammar flags
    grammar_json: bool = False
    grammar_model: bool = False
    grammar_pretty: bool = False
    grammar_railroads: bool = False
    grammar_parser: bool = False
    grammar_parser_model: bool = False
    grammar_object_model: bool = False


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
    boot_parser.add_argument(
        "--parser",
        action="store_true",
        dest="boot_parser",
        help="Generate Python parser source code from the boot grammar",
    )
    boot_parser.add_argument(
        "--parser-model",
        action="store_true",
        dest="boot_parser_model",
        help="Generate model-based parser from the boot grammar",
    )
    boot_parser.add_argument(
        "--object-model",
        action="store_true",
        dest="boot_object_model",
        help="Generate object model from the boot grammar",
    )

    # --- grammar ---
    grammar_parser = subparsers.add_parser(
        "grammar",
        help="Grammar transformations",
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
    grammar_parser.add_argument(
        "-x",
        "--parser",
        action="store_true",
        dest="grammar_parser",
        help="Generate Python parser source code from the grammar",
    )
    grammar_parser.add_argument(
        "--parser-model",
        action="store_true",
        dest="grammar_parser_model",
        help="Generate model-based parser from the grammar",
    )
    grammar_parser.add_argument(
        "--object-model",
        action="store_true",
        dest="grammar_object_model",
        help="Generate object model from the grammar",
    )

    args = parser.parse_args(argv)

    cfg = CLIConfig(
        color=args.color,
        output=args.output,
        trace=args.trace,
        quiet=args.quiet,
        profile=args.profile,
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
        cfg.boot_parser = args.boot_parser
        cfg.boot_parser_model = args.boot_parser_model
        cfg.boot_object_model = args.boot_object_model

    elif args.command == "grammar":
        cfg.grammar = args.grammar
        cfg.grammar_json = args.grammar_json
        cfg.grammar_model = args.grammar_model
        cfg.grammar_pretty = args.grammar_pretty
        cfg.grammar_railroads = args.grammar_railroads
        cfg.grammar_parser = args.grammar_parser
        cfg.grammar_parser_model = args.grammar_parser_model
        cfg.grammar_object_model = args.grammar_object_model

    return cfg


def _show(cfg: CLIConfig, payload: str) -> None:
    """Write payload to stdout or to a file."""
    if cfg.output:
        Path(cfg.output).write_text(payload, encoding="utf-8")
    else:
        print(payload)


def _load_grammar(path: str) -> Grammar:
    """Load a Grammar from an .ebnf or .json file."""
    from ...grammars.model import Grammar as _Grammar

    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        return _Grammar.loads(source)
    from ..api import compile

    return compile(source)


def _render(
    gram: Grammar,
    cfg: CLIConfig,
    *,
    json: bool = False,
    model: bool = False,
    pretty: bool = False,
    railroads: bool = False,
    parser: bool = False,
    parser_model: bool = False,
    object_model: bool = False,
) -> None:
    """Render a Grammar in the selected mode, writing to cfg.output or stdout."""
    from ...ngcodegen import modelgen as _modelgen, parsergen, pythongen

    if json:
        _show(cfg, gram.asjsons())
    elif model:
        _show(cfg, repr(gram))
    elif railroads:
        _show(cfg, gram.railroads())
    elif parser:
        _show(cfg, pythongen(gram))
    elif parser_model:
        _show(cfg, parsergen(gram))
    elif object_model:
        _show(cfg, _modelgen(gram))
    else:
        _show(cfg, gram.pretty())


def boot_cmd(cfg: CLIConfig) -> None:
    """Handle the ``boot`` subcommand."""
    from ..api import boot_grammar

    _render(
        boot_grammar(),
        cfg,
        json=cfg.boot_json,
        model=cfg.boot_model,
        pretty=cfg.boot_pretty,
        railroads=cfg.boot_railroads,
        parser=cfg.boot_parser,
        parser_model=cfg.boot_parser_model,
        object_model=cfg.boot_object_model,
    )


def grammar_cmd(cfg: CLIConfig) -> None:
    """Handle the ``grammar`` subcommand."""
    gram = _load_grammar(cfg.grammar)

    _render(
        gram,
        cfg,
        json=cfg.grammar_json,
        model=cfg.grammar_model,
        pretty=cfg.grammar_pretty,
        railroads=cfg.grammar_railroads,
        parser=cfg.grammar_parser,
        parser_model=cfg.grammar_parser_model,
        object_model=cfg.grammar_object_model,
    )


def main() -> None:
    """Entry point for the cling CLI (not wired to console_scripts yet)."""
    cfg = parse_args()
    if cfg.command == "boot":
        boot_cmd(cfg)
    elif cfg.command == "grammar":
        grammar_cmd(cfg)
    else:
        print(cfg, file=sys.stderr)

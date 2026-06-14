# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""CLI for TatSu, mirroring ogopego's three-subcommand structure."""

from __future__ import annotations

import argparse
import signal
import sys
from argparse import ArgumentParser

from tatsu import __toolname__, __version__
from tatsu.exceptions import ParseError

from .boot_cmd import add_boot_cmd, boot_cmd
from .config import CLIConfig, CLIError
from .global_opt import add_global_options
from .grammar_cmd import add_grammar_cmd, grammar_cmd
from .out import output_results


TITLE = "竜TatSu"
VERSION = f"{TITLE} v{__version__}"
DESCRIPTION = (
    f'{TITLE} takes a grammar in extended EBNF'
    ' as input, and outputs a memoizing'
    ' PEG/Packrat parser in Python.'
)


def create_argument_parser() -> ArgumentParser:
    # Handle --version before argparse to match ogopego's pre-dispatch check
    parser = argparse.ArgumentParser(
        prog="tatsu",
        description=DESCRIPTION,
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

    return parser


def run_cling_cli(parser: argparse.ArgumentParser) -> CLIConfig:
    """Parse command-line arguments and return a CLIConfig.

    Matches ogopego's subcommand structure (run / boot / grammar).
    """
    cfg = CLIConfig()
    namespace = parser.parse_args(namespace=cfg)

    for name, value in vars(namespace).items():
        if name == "name":
            continue
        if not hasattr(cfg, name):
            raise RuntimeError(f"Unknown option: {name}")
        setattr(cfg, name, value)
    return cfg


def cling_main() -> None:
    """Entry point for the cling CLI (not wired to console_scripts yet)."""

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    sys.setrecursionlimit(2**16)

    try:
        parser = create_argument_parser()
        # args = sys.argv[1:]
        # argset = set(args)
        # if not argset:
        #     print(VERSION, file=sys.stderr)
        #     print(f"\n{DESCRIPTION}\n", file=sys.stderr)
        #     parser.print_usage()
        #     return

        # if {'-h', '--help'} & argset:
        #     parser.print_help()
        #     return

        # if {'version', '--version', '-V'} & argset:
        #     print(VERSION, file=sys.stderr)
        #     return

        cfg = run_cling_cli(parser)

        if cfg.style == "list":
            from pygments.styles import get_all_styles

            for style in sorted(get_all_styles()):
                print(style)
            return
        match cfg.command:
            case "boot":
                results = boot_cmd(cfg)
            case "grammar":
                results = grammar_cmd(cfg)
            case "run":
                from .run_cmd import run_cmd

                results = run_cmd(cfg)
            case _:
                parser.print_usage()
                return
        output_results(cfg, results)

    except CLIError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except ParseError:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(signal.SIGPIPE + signal.SIG_DFL)
    except KeyboardInterrupt:
        sys.exit(0)


def add_help_cmd(subparsers):
    help_parser = subparsers.add_parser(
        "help",
        help="Provide command help",
        add_help=False,
    )
    return help_parser


def add_run_cmd(subparsers):
    run_parser = subparsers.add_parser(
        "run",
        help="Parse input files with the given grammar",
    )
    add_global_options(run_parser)
    run_parser.add_argument(
        "grammar",
        help="Path to a grammar in EBNF or JSON format",
    )
    run_parser.add_argument(
        "inputs",
        nargs="+",
        help="The files to be parsed",
    )

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

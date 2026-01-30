from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from .._version import __version__
from ..exceptions import ParseException
from ..ngcodegen import modelgen, pythongen
from ..util import eval_escapes
from .api import compile

__all__ = ['tatsu_main']


DESCRIPTION = (
    'TatSu takes a grammar'
    ' in a variation of EBNF as input, and outputs a memoizing'
    ' PEG/Packrat parser in Python.'
)


def parse_args():
    argparser = argparse.ArgumentParser(
        prog='tatsu', description=DESCRIPTION, add_help=False,
    )

    main_mode = argparser.add_mutually_exclusive_group()
    main_mode.add_argument(
        '--generate-parser',
        help='generate parser code from the grammar (default)',
        action='store_true',
    )
    main_mode.add_argument(
        '--draw',
        '-d',
        help=(
            'generate a diagram of the grammar'
            ' (.svg, .png, .jpeg, .dot, ...'
             ' / requres --outfile)'
        ),
        action='store_true',
    )
    main_mode.add_argument(
        '--object-model',
        '-g',
        help='generate object model from the class names given as rule arguments',
        action='store_true',
    )
    main_mode.add_argument(
        '--pretty',
        '-p',
        help='generate a prettified version of the input grammar',
        action='store_true',
    )
    main_mode.add_argument(
        '--pretty-lean',
        help='like --pretty, but without name: or ::Parameter annotations',
        action='store_true',
    )

    ebnf_opts = argparser.add_argument_group('parse-time options')
    argparser.add_argument(
        'filename',
        metavar='GRAMMAR',
        help='the filename of the TatSu grammar to parse',
    )
    ebnf_opts.add_argument(
        '--color',
        '-c',
        help='use color in traces (requires the colorama library)',
        action='store_true',
    )
    ebnf_opts.add_argument(
        '--trace',
        '-t',
        help='produce verbose parsing output',
        action='store_true',
    )

    generation_opts = argparser.add_argument_group('generation options')
    generation_opts.add_argument(
        '--left-recursion',
        '-l',
        help='turns left-recursion support off',
        dest='left_recursion',
        action='store_false',
        default=None,
    )
    generation_opts.add_argument(
        '--name',
        '-m',
        metavar='NAME',
        help='Name for the grammar (defaults to GRAMMAR base name)',
    )
    generation_opts.add_argument(
        '--nameguard',
        '-n',
        help='allow tokens that are prefixes of others',
        dest='nameguard',
        action='store_false',
        default=None,  # None allows grammar specified
    )
    generation_opts.add_argument(
        '--outfile',
        '--output',
        '-o',
        metavar='FILE',
        help='output file (default is stdout)',
    )
    generation_opts.add_argument(
        '--object-model-outfile',
        '-G',
        metavar='FILE',
        help='generate object model and save to FILE',
    )
    generation_opts.add_argument(
        '--whitespace',
        '-w',
        metavar='CHARACTERS',
        help='characters to skip during parsing (use "" to disable)',
    )

    def import_class(path):
        try:
            spath = path.rsplit('.', 1)
            module = importlib.import_module(spath[0])

            return getattr(module, spath[1])
        except Exception as e:
            raise argparse.ArgumentTypeError(
                f"Couldn't find class {path}",
            ) from e

    generation_opts.add_argument(
        '--base-type',
        metavar='CLASSPATH',
        help='class to use as base type for the object model, for example "mymodule.MyNode"',
        type=import_class,
    )

    std_args = argparser.add_argument_group('common options')
    std_args.add_argument(
        '--help', '-h', help='show this help message and exit', action='help',
    )
    std_args.add_argument(
        '--version',
        '-V',
        help='provide version information and exit',
        action='version',
        version=f'TatSu {__version__}',
    )

    args = argparser.parse_args()

    if args.draw and not args.outfile:
        argparser.error('--draw requires --outfile')

    return args


def prepare_for_output(filename: str):
    if filename:
        f = Path(filename)
        if f.is_file():
            f.unlink()
        dirname = f.parent
        if dirname.exists():
            dirname.mkdir(parents=True, exist_ok=True)


def save(filename: str, content: str):
    Path(filename).write_text(content, encoding='utf-8')


def tatsu_main():
    args = parse_args()

    if args.whitespace:
        args.whitespace = eval_escapes(args.whitespace)

    outfile = args.outfile
    prepare_for_output(outfile)
    prepare_for_output(args.object_model_outfile)

    grammar = Path(args.filename).read_text()

    try:
        model = compile(
            grammar,
            args.name,
            asmodel=True,
            trace=args.trace,
            filename=args.filename,
            colorize=args.color,
            left_recursion=args.left_recursion,
            nameguard=args.nameguard,
            whitespace=args.whitespace,

        )

        if args.draw:
            from .. import diagrams
            diagrams.draw(outfile, model)
        else:
            if args.pretty:
                result = model.pretty()
            elif args.pretty_lean:
                result = model.pretty_lean()
            elif args.object_model:
                result = modelgen(model)
            else:
                result = pythongen(model)

            if outfile:
                save(outfile, result)
            else:
                print(result)

        # if requested, always save it
        if args.object_model_outfile:
            save(
                args.object_model_outfile,
                modelgen(model),
            )

        print('-' * 72, file=sys.stderr)
        print(
            f'{len(grammar.split()):12,d}  lines in grammar', file=sys.stderr,
        )
        print(f'{len(model.rules):12,d}  rules in grammar', file=sys.stderr)
        print(f'{model.nodecount():12,d}  nodes in AST', file=sys.stderr)
    except ParseException as e:
        print(e, file=sys.stderr)
        sys.exit(1)

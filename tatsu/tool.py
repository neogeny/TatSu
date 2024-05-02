"""
Parse and translate an EBNF grammar into a Python parser for
the described language.
"""
# ruff: noqa: PLR0912
from __future__ import annotations

import argparse
import codecs
import importlib
import sys
from pathlib import Path

from ._version import __version__
from .exceptions import ParseException
from .infos import ParserConfig
from .ngcodegen import codegen as ngpythoncg
from .ngcodegen import objectmodel as ngobjectmodel
from .parser import GrammarGenerator
from .semantics import ModelBuilderSemantics
from .util import eval_escapes

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
        help='generate a diagram of the grammar (requires --outfile)',
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
        '--no-left-recursion',
        '-l',
        help='turns left-recursion support off',
        dest='left_recursion',
        action='store_false',
        default=True,
    )
    generation_opts.add_argument(
        '--name',
        '-m',
        metavar='NAME',
        help='Name for the grammar (defaults to GRAMMAR base name)',
    )
    generation_opts.add_argument(
        '--no-nameguard',
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
        version=__version__,
    )

    args = argparser.parse_args()

    if args.draw and not args.outfile:
        argparser.error('--draw requires --outfile')

    return args


__compiled_grammar_cache = {}  # type: ignore[var-annotated]


def compile(
    grammar,
    name=None,
    semantics=None,
    asmodel=False,
    config: ParserConfig | None = None,
    **settings,
):
    cache = __compiled_grammar_cache

    key = (name, grammar, id(semantics))
    if key in cache:
        model = cache[key]
    else:
        gen = GrammarGenerator(name, config=config, **settings)
        model = cache[key] = gen.parse(grammar, config=config, **settings)

    if semantics is not None:
        model.semantics = semantics
    elif asmodel:
        model.semantics = ModelBuilderSemantics()

    return model


def parse(
    grammar,
    input,
    start=None,
    name=None,
    semantics=None,
    asmodel=False,
    config: ParserConfig | None = None,
    **settings,
):
    model = compile(
        grammar,
        name=name,
        semantics=semantics,
        asmodel=asmodel,
        config=config,
        **settings,
    )
    return model.parse(
        input, start=start, semantics=semantics, config=config, **settings,
    )


def to_python_sourcecode(
    grammar,
    name=None,
    filename=None,
    config: ParserConfig | None = None,
    **settings,
):
    model = compile(
        grammar, name=name, filename=filename, config=config, **settings,
    )
    return ngpythoncg(model)


def to_python_model(
    grammar,
    name=None,
    filename=None,
    base_type=None,
    config: ParserConfig | None = None,
    **settings,
):
    model = compile(
        grammar, name=name, filename=filename, config=config, **settings,
    )
    return ngobjectmodel.modelgen(model, base_type=base_type)


# for backwards compatibility. Use `compile()` instead
def genmodel(
    name=None,
    grammar=None,
    semantics=None,
    config: ParserConfig | None = None,
    **settings,
):
    if grammar is None:
        raise ParseException('grammar is None')

    return compile(
        grammar, name=name, semantics=semantics, config=config, **settings,
    )


def gencode(
    name=None,
    grammar=None,
    trace=False,
    filename=None,
    codegen=ngpythoncg,
    config: ParserConfig | None = None,
    **settings,
):
    model = compile(
        grammar,
        name=name,
        filename=filename,
        trace=trace,
        config=config,
        **settings,
    )
    return codegen(model)


def prepare_for_output(filename):
    if filename:
        filename = Path(filename)
        if filename.is_file():
            filename.unlink()
        dirname = filename.parent
        if dirname.exists():
            dirname.mkdir(parents=True, exist_ok=True)


def save(filename, content):
    with codecs.open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    args = parse_args()

    if args.whitespace:
        args.whitespace = eval_escapes(args.whitespace)

    outfile = args.outfile
    prepare_for_output(outfile)
    prepare_for_output(args.object_model_outfile)

    grammar = codecs.open(args.filename, encoding='utf-8').read()

    try:
        model = compile(
            grammar,
            args.name,
            trace=args.trace,
            filename=args.filename,
            colorize=args.color,
        )
        model.whitespace = args.whitespace
        model.nameguard = args.nameguard
        model.left_recursion = args.left_recursion

        if args.draw:
            from tatsu import diagrams

            diagrams.draw(outfile, model)
        else:
            if args.pretty:
                result = model.pretty()
            elif args.pretty_lean:
                result = model.pretty_lean()
            elif args.object_model:
                result = ngobjectmodel.modelgen(model, base_type=args.base_type)
            else:
                result = ngpythoncg(model)

            if outfile:
                save(outfile, result)
            else:
                print(result)

        # if requested, always save it
        if args.object_model_outfile:
            save(
                args.object_model_outfile,
                ngobjectmodel.modelgen(model, base_type=args.base_type),
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


if __name__ == '__main__':
    main()

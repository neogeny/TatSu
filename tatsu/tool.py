# -*- coding: utf-8 -*-
"""
Parse and translate an EBNF grammar into a Python parser for
the described language.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import codecs
import argparse
import os
import sys

from tatsu._version import __version__
from tatsu.util import eval_escapes
from tatsu.exceptions import ParseException
from tatsu.parser import GrammarGenerator
from tatsu.semantics import ModelBuilderSemantics

# we hook the tool to the Python code generator as the default
from tatsu.codegen.python import codegen as pythoncg
from tatsu.codegen import objectmodel

DESCRIPTION = (
    'TatSu takes a grammar'
    ' in a variation of EBNF as input, and outputs a memoizing'
    ' PEG/Packrat parser in Python.'
)


def parse_args():
    argparser = argparse.ArgumentParser(prog='tatsu',
                                        description=DESCRIPTION,
                                        add_help=False)

    main_mode = argparser.add_mutually_exclusive_group()
    main_mode.add_argument(
        '--generate-parser',
        help='generate parser code from the grammar (default)',
        action='store_true'
    )
    main_mode.add_argument(
        '--draw', '-d',
        help='generate a diagram of the grammar (requires --outfile)',
        action='store_true'
    )
    main_mode.add_argument(
        '--object-model', '-g',
        help='generate object model from the class names given as rule arguments',
        action='store_true'
    )
    main_mode.add_argument(
        '--pretty', '-p',
        help='generate a prettified version of the input grammar',
        action='store_true'
    )
    main_mode.add_argument(
        '--pretty-lean',
        help='like --pretty, but without name: or ::Parameter annotations',
        action='store_true'
    )

    ebnf_opts = argparser.add_argument_group('parse-time options')
    argparser.add_argument(
        'filename',
        metavar='GRAMMAR',
        help='the filename of the TatSu grammar to parse'
    )
    ebnf_opts.add_argument(
        '--color', '-c',
        help='use color in traces (requires the colorama library)',
        action='store_true'
    )
    ebnf_opts.add_argument(
        '--trace', '-t',
        help='produce verbose parsing output',
        action='store_true'
    )

    generation_opts = argparser.add_argument_group('generation options')
    generation_opts.add_argument(
        '--no-left-recursion', '-l',
        help='turns left-recusion support off',
        dest="left_recursion",
        action='store_false',
        default=True,
    )
    generation_opts.add_argument(
        '--name', '-m',
        metavar='NAME',
        help='Name for the grammar (defaults to GRAMMAR base name)'
    )
    generation_opts.add_argument(
        '--no-nameguard', '-n',
        help='allow tokens that are prefixes of others',
        dest="nameguard",
        action='store_false',
        default=None  # None allows grammar specified
    )
    generation_opts.add_argument(
        '--outfile', '--output', '-o',
        metavar='FILE',
        help='output file (default is stdout)'
    )
    generation_opts.add_argument(
        '--object-model-outfile', '-G',
        metavar='FILE',
        help='generate object model and save to FILE',
    )
    generation_opts.add_argument(
        '--whitespace', '-w',
        metavar='CHARACTERS',
        help='characters to skip during parsing (use "" to disable)',
    )

    std_args = argparser.add_argument_group('common options')
    std_args.add_argument(
        '--help', '-h',
        help='show this help message and exit',
        action='help'
    )
    std_args.add_argument(
        '--version', '-V',
        help='provide version information and exit',
        action='version',
        version=__version__
    )

    args = argparser.parse_args()

    if args.draw and not args.outfile:
        argparser.error('--draw requires --outfile')

    return args


__compiled_grammar_cache = {}  # type: ignore


def compile(grammar, name=None, semantics=None, asmodel=False, **kwargs):
    cache = __compiled_grammar_cache

    if (grammar, semantics) in cache:
        model = cache[(grammar, semantics)]
    else:
        gen = GrammarGenerator(name, **kwargs)
        model = cache[grammar] = gen.parse(grammar, **kwargs)
        model.semantics = semantics or asmodel and ModelBuilderSemantics()
    return model


def parse(grammar, input, name=None, semantics=None, asmodel=False, **kwargs):
    model = compile(grammar, name=name, semantics=semantics, asmodel=asmodel, **kwargs)
    return model.parse(input, semantics=semantics, **kwargs)


def to_python_sourcecode(grammar, name=None, filename=None, **kwargs):
    model = compile(grammar, name=name, filename=filename, **kwargs)
    return pythoncg(model)


def to_python_model(grammar, name=None, filename=None, **kwargs):
    model = compile(grammar, name=name, filename=filename, **kwargs)
    return objectmodel.codegen(model)


# for backwards compatibility. Use `compile()` instead
def genmodel(name=None, grammar=None, semantics=None, **kwargs):
    if grammar is None:
        raise ParseException('grammar is None')

    return compile(grammar, name=name, semantics=semantics, **kwargs)


# for backwards compatibility. Use `compile()` instead
def gencode(name=None, grammar=None, trace=False, filename=None, codegen=pythoncg, **kwargs):
    model = compile(grammar, name=name, filename=filename, trace=trace, **kwargs)
    return codegen(model)


def prepare_for_output(filename):
    if filename:
        if os.path.isfile(filename):
            os.unlink(filename)
        dirname = os.path.dirname(filename)
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)


def save(filename, content):
    with codecs.open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


def main(codegen=pythoncg):
    args = parse_args()

    if args.whitespace:
        args.whitespace = eval_escapes(args.whitespace)

    outfile = args.outfile
    prepare_for_output(outfile)
    prepare_for_output(args.object_model_outfile)

    grammar = codecs.open(args.filename, 'r', encoding='utf-8').read()

    try:
        model = compile(
            grammar,
            args.name,
            trace=args.trace,
            filename=args.filename,
            colorize=args.color
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
                result = objectmodel.codegen(model)
            else:
                result = codegen(model)

            if outfile:
                save(outfile, result)
            else:
                print(result)

        # if requested, always save it
        if args.object_model_outfile:
            save(args.object_model_outfile, objectmodel.codegen(model))

        print('-' * 72, file=sys.stderr)
        print('{:12,d}  lines in grammar'.format(len(grammar.split())), file=sys.stderr)
        print('{:12,d}  rules in grammar'.format(len(model.rules)), file=sys.stderr)  # noqa
        print('{:12,d}  nodes in AST'.format(model.nodecount()), file=sys.stderr)
    except ParseException as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

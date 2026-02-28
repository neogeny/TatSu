# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys


def generic_main(custom_main, parser_class, name='Unknown'):
    import argparse

    class ListRules(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print('Rules:')
            for r in parser_class.rule_list():
                print(r)
            print()
            sys.exit(0)

    argp = argparse.ArgumentParser(description=f'Simple parser for {name}.')
    addarg = argp.add_argument

    addarg(
        '-c',
        '--color',
        help='use color in traces (requires the colorama library)',
        action='store_true',
    )
    addarg('-l', '--list', action=ListRules, nargs=0, help='list all rules and exit')
    addarg(
        '-n',
        '--no-nameguard',
        action='store_true',
        dest='no_nameguard',
        help="disable the 'nameguard' feature",
    )
    addarg('-t', '--trace', action='store_true', help='output trace information')
    addarg(
        '-w',
        '--whitespace',
        type=str,
        default=None,
        help='whitespace specification',
    )
    addarg(
        'file',
        metavar='FILE',
        help="the input file to parse or '-' for standard input",
        nargs='?',
        default='-',
    )
    addarg(
        'startrule',
        metavar='STARTRULE',
        nargs='?',
        help='the start rule for parsing',
        default=None,
    )

    args = argp.parse_args()
    try:
        return custom_main(
            args.file,
            start=args.startrule,
            trace=args.trace,
            whitespace=args.whitespace,
            nameguard=not args.no_nameguard,
            colorize=args.color,
        )
    except KeyboardInterrupt:
        pass

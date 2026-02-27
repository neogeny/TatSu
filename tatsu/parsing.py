# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import inspect
import sys
from collections.abc import Callable
from typing import Any

from . import util
from .contexts import ParseContext, isname, name, leftrec, nomemo, rule, tatsumasu
from .exceptions import FailedRef

from .parserconfig import ParserConfig
from .util import debug, safe_name, typename

__all__ = [
    'Parser',
    'generic_main',
    'isname',
    'name',
    'leftrec',
    'nomemo',
    'rule',
    'tatsumasu',
]


def debug(*_args, **_kwargs) -> None:  # noqa: F811
    assert debug
    pass


class OldParser(ParseContext):
    pass


class Parser(ParseContext):
    def __init__(
        self,
        rulesource: Any = None,
        /,
        *,
        config: ParserConfig | None = None,
        **settings: Any,
    ) -> None:
        self.rulesource = rulesource

        config = ParserConfig.new(config, **settings)
        srcconfig = ParserConfig.new(getattr(rulesource, 'config', None))
        config = srcconfig.override_config(config)

        super().__init__(config=config)

    def _find_rule(self, name: str) -> Callable[[ParseContext], Any]:
        if not self.rulesource:
            return self._find_cls_rule(name)
        for rulename in {name, name.strip('_'), f'_{name}_', f'_{name}'}:
            action = getattr(self.rulesource, safe_name(rulename), None)
            if callable(action):
                return action
        raise self.newexcept(f'{name}', excls=FailedRef)

    def _find_cls_rule(self, name: str) -> Callable[[ParseContext], Any]:
        for rulename in {name, name.strip('_'), f'_{name}_', f'_{name}'}:
            action = getattr(self, safe_name(rulename), None)
            if callable(action):
                return action
        raise self.newexcept(f'{name!r}@{typename(self)}', excls=FailedRef)

    def rule_list(self) -> list[str]:
        source = self.rulesource or type(self)

        def isdunder(name: str) -> bool:
            return name.startswith('__') and name.endswith('__')

        methods = inspect.getmembers(source, predicate=inspect.ismethod)
        return [m[0] for m in methods if not isdunder(m[0])]


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


# HACK: backwards compatibility
util.generic_main = generic_main  # type: ignore ty: ignore[ # unresolved-attribute]

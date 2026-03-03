# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
import sys


sys.path.insert(0, '.')
from tatsu.grammars import *


g = Grammar(
    name='CALC',
    directives={'grammar': 'CALC'},
    rules=[
        Rule(
            name='start',
            exp=Sequence(sequence=[Call(name='expression'), EOF(ast='$')]),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=False,
            is_memoizable=False,
        ),
        Rule(
            name='expression',
            exp=Choice(
                options=[
                    Option(exp=Call(name='addition')),
                    Option(exp=Call(name='subtraction')),
                    Option(exp=Call(name='term')),
                ]
            ),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=True,
            is_memoizable=False,
        ),
        Rule(
            name='addition',
            exp=Sequence(
                sequence=[
                    Named(name='left', exp=Call(name='expression')),
                    Named(name='op', exp=Token(token='+')),
                    Cut(ast='~'),
                    Named(name='right', exp=Call(name='term')),
                ]
            ),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=False,
            is_memoizable=False,
        ),
        Rule(
            name='subtraction',
            exp=Sequence(
                sequence=[
                    Named(name='left', exp=Call(name='expression')),
                    Named(name='op', exp=Token(token='-')),
                    Cut(ast='~'),
                    Named(name='right', exp=Call(name='term')),
                ]
            ),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=False,
            is_memoizable=False,
        ),
        Rule(
            name='term',
            exp=Choice(
                options=[
                    Option(exp=Call(name='multiplication')),
                    Option(exp=Call(name='division')),
                    Option(exp=Call(name='factor')),
                ]
            ),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=True,
            is_memoizable=False,
        ),
        Rule(
            name='multiplication',
            exp=Sequence(
                sequence=[
                    Named(name='left', exp=Call(name='term')),
                    Named(name='op', exp=Token(token='*')),
                    Cut(ast='~'),
                    Named(name='right', exp=Call(name='factor')),
                ]
            ),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=False,
            is_memoizable=False,
        ),
        Rule(
            name='division',
            exp=Sequence(
                sequence=[
                    Named(name='left', exp=Call(name='term')),
                    Token(token='/'),
                    Cut(ast='~'),
                    Named(name='right', exp=Call(name='factor')),
                ]
            ),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=False,
            is_memoizable=False,
        ),
        Rule(
            name='factor',
            exp=Choice(
                options=[
                    Option(
                        exp=Sequence(
                            sequence=[
                                Token(token='('),
                                Cut(ast='~'),
                                Override(name='@', exp=Call(name='expression')),
                                Token(token=')'),
                            ]
                        )
                    ),
                    Option(exp=Call(name='number')),
                ]
            ),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=False,
            is_memoizable=True,
        ),
        Rule(
            name='number',
            exp=Pattern(pattern='\\d+'),
            params=(),
            kwparams={},
            decorators=[],
            is_name=False,
            is_leftrec=False,
            is_memoizable=True,
        ),
    ],
)
# print(repr(g))
print(g)

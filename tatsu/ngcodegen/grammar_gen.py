# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .. import grammars as g
from ..util.common import typename
from ..util.indent import IndentPrintMixin
from .boilerplt import FOOTER, HEADER


def parsermodel_gen(model: g.Grammar, name: str = '') -> str:
    generator = ParseWithModelGenerator()
    return generator.generate_parser(model, name=name)


def PARSER(name: str) -> str:
    return f"""\
    from typing import Any

    from tatsu.contexts import CanParse
    from tatsu.input import Text
    from tatsu.grammars import *


    class {name}Parser(CanParse):
        def __init__(self):
            self.model = GRAMMAR_MODEL

        def parse(
            self,
            text: str | Text,
            /,
            *,
            start: str | None = None,
            config: Any = None,
            asmodel: bool = False,
            **settings: Any,
        ) -> Any:
            return self.model.parse(
                text,
                start=start,
                config=config,
                asmodel=asmodel,
                **settings,
            )
    """


class ParseWithModelGenerator(IndentPrintMixin):
    def generate_parser(self, model: g.Grammar, name: str = '') -> str:
        self.clear()
        self.print(HEADER)
        self.print()

        self.print(PARSER(name))
        self.print()
        self.print()

        name = name or model.name
        self.print(f'GRAMMAR_MODEL: {typename(model)} = (')
        with self.indent():
            self.print(repr(model))
        self.print(')')
        self.print()
        self.print()

        self.print(FOOTER(name))

        return self.printed_text()

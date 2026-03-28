# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses as dc
from pathlib import Path
from typing import Any

from tatsu import grammars as g
from tatsu.util.indent import IndentPrintMixin


def rstype(type: Any, modelnames: set[str]) -> str:
    type = str(type)
    type = str(type).split('|')[0].strip()
    if type.startswith('tuple['):
        type = type.replace('tuple[', 'Vec<').replace('...]', '>')
    elif type.startswith('dict['):
        type = type.replace('dict[', 'HashMap<').replace(']', '>')
    elif type.startswith('list['):
        type = type.replace('list[', 'Vec<').replace(']', '>')
    else:
        type = type.replace('[', '{').replace(']', '}')
    if type == 'Model':
        type = 'Box<Model>'
    if type == 'Vec<Model>':
        type = 'Vec<Box<Model>>'
    # if type in modelnames:
    #     type = 'Box<dyn Model>'
    # type= type.replace('str', "'static &str")
    type = type.replace('str', "String")
    return type


def main():
    root = Path('./rustsrc')
    root.mkdir(exist_ok=True)

    modelnames = set()
    for cls in g.Model.model_classes():
        name = cls.__name__
        modelnames.add(name)

    n = 0
    for cls in g.Model.model_classes():
        name = cls.__name__
        if (
            name.endswith('Box')
            or 'Comment' in name
            or 'First' in name
            or 'Choice' in name
            or 'Sequence' in name
            or name in {'Option', 'Group'}
        ):
            continue

        fields = []
        for field in dc.fields(cls):  # pyright: ignore[reportArgumentType]
            if not field.init:
                continue
            if field.name.startswith('_'):
                continue
            if field.name in {'ast', 'ctx', 'parseinfo'}:
                continue
            fields.append(field)

        module = cls.__module__.split('.')[-1]
        path = root / f'{module.lower()}.rs'

        n += 1
        p = IndentPrintMixin()
        if not path.is_file():
            p.print("""\
                // Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
                // SPDX-License-Identifier: AGPL-3.0-or-later

                use crate::input::Cursor;
                use super::model::{CanParse, ParseResult};
                use crate::engine::{Cst, Ctx};
            """)
        p.print()
        p.print(f'// #{n}')
        p.print(f"""\
            pub struct {name}<M> {{
                pub exp: Box<M>,
            }}
        """)
        p.print()

        # for field in fields:
        #     type = rstype(field.type, modelnames)
        #     with p.indent():
        #         p.print(f'pub {field.name}: {type},')
        #
        # p.print("}")

        p.print(f"""\
            impl<M, C> CanParse<C> for {name}<M>
            where
                M: CanParse<C>,
                C: Cursor,
            {{
                fn parse(&self, mut ctx: Ctx<C>) -> ParseResult<C> {{
                    unimplemented!()
                }}
            }}
        """)
        p.print()
        with path.open('a') as f:
            f.write(p.printed_text())


if __name__ == '__main__':
    main()

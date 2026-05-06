# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .. import grammars as g
from ..exceptions import ParseException
from ..infos import ParserConfig
from ..input import Text
from ..ngcodegen.grammar_gen import parsermodel_gen
from ..ngcodegen.ngmodel_gen import modelgen
from ..ngcodegen.ngparser_gen import pythongen
from ..objectmodel import Node
from ..objectmodel.builder import (
    BuilderConfig,
    Constructor,
    ModelBuilderSemantics,
    TypeContainer,
)
from ..parser import TatSuParserGenerator
from ..util import hasha


__all__ = [
    'compile',
    'gencode',
    'genmodel',
    'modelgen',
    'parse',
    'pythongen',
    'to_python_model',
    'to_python_sourcecode',
]

__compiled_grammar_cache: dict[tuple[str | None, str, int], g.Grammar] = {}


def compile(
    grammar: str | Text,
    name: str | None = None,
    *,
    config: ParserConfig | None = None,
    filename: str | None = None,
    basetype: type | None = None,
    semantics: Any = None,
    asmodel: bool = False,
    builderconfig: BuilderConfig | None = None,
    synthok: bool = True,
    typedefs: list[TypeContainer] | None = None,
    constructors: list[Constructor] | None = None,
    **settings: Any,
) -> g.Grammar:
    filename = filename or settings.pop('source', None)
    ParserConfig.new(
        config=config,
        semantics=semantics,
        name=name,
        source=filename,
        **settings,
    )
    if isinstance(semantics, type):
        raise TypeError(
            f'semantics must be an object instance or None, not class {semantics!r}',
        )
    cache = __compiled_grammar_cache

    key = (name, hasha(grammar), id(semantics))
    if key in cache:
        model = cache[key]
    else:
        gen = TatSuParserGenerator(name, **settings)
        model = cache[key] = gen.parse(grammar, **settings)

    asmodel = not semantics and (
        asmodel
        or isinstance(builderconfig, BuilderConfig)
        or basetype is not None
        or typedefs is not None
        or constructors is not None
    )
    if semantics is not None:
        model.semantics = semantics
    elif asmodel:
        # HACK: cheating, but necessary for bw-compatibility
        builderconfig = BuilderConfig.new(
            config=builderconfig,
            synthok=synthok,
            basetype=basetype,
            typedefs=typedefs,
            constructors=constructors,
        )
        model.semantics = ModelBuilderSemantics(config=builderconfig)

    return model


def compile_to_parser(
    grammar: str | Text,
    name: str | None = None,
    *,
    config: ParserConfig | None = None,
    filename: str | None = None,
    basetype: type | None = None,
    semantics: Any = None,
    builderconfig: BuilderConfig | None = None,
    synthok: bool = True,
    typedefs: list[TypeContainer] | None = None,
    constructors: list[Constructor] | None = None,
    **settings: Any,
) -> g.Grammar:
    return compile(
        grammar,
        name=name,
        config=config,
        filename=filename,
        basetype=basetype,
        semantics=semantics,
        asmodel=True,
        builderconfig=builderconfig,
        synthok=synthok,
        typedefs=typedefs,
        constructors=constructors,
        **settings,
    )


def parse(
    grammar: str,
    text: str,
    /,
    *,
    config: ParserConfig | None = None,
    start: str | None = None,
    name: str | None = None,
    filename: str | None = None,
    semantics: Any | None = None,
    asmodel: bool = False,
    builderconfig: BuilderConfig | None = None,
    basetype: type | None = None,
    synthok: bool = True,
    typedefs: list[TypeContainer] | None = None,
    constructors: list[Constructor] | None = None,
    **settings: Any,
):
    filename = filename or settings.pop('source', None)
    config = ParserConfig.new(
        config=config,
        start=start,
        name=name,
        source=filename,
        semantics=semantics,
        **settings,
    )
    model = compile(grammar, config=config, asmodel=asmodel)
    config.semantics = semantics or model.semantics

    asmodel = not config.semantics and (
        asmodel
        or isinstance(builderconfig, BuilderConfig)
        or basetype is not None
        or typedefs is not None
        or constructors is not None
    )
    if asmodel:
        builderconfig = BuilderConfig.new(
            config=builderconfig,
            synthok=synthok,
            basetype=basetype,
            typedefs=typedefs,
            constructors=constructors,
        )
        config.semantics = ModelBuilderSemantics(config=builderconfig)
    return model.parse(text, start=start, semantics=semantics, config=config)


def to_python_sourcecode(
    grammar: str,
    /,
    *,
    name: str | None = None,
    filename: str | None = None,
    config: ParserConfig | None = None,
    **settings: Any,
):
    filename = filename or settings.pop('source', None)
    config = ParserConfig.new(config=config, name=name, source=filename, **settings)
    model = compile(grammar, config=config, name=name, source=filename)
    return pythongen(model)


def to_python_model(
    grammar: str,
    /,
    *,
    name: str | None = None,
    filename: str | None = None,
    basetype: type = Node,
    config: ParserConfig | None = None,
    **settings: Any,
):
    filename = filename or settings.pop('source', None)
    config = ParserConfig.new(config=config, name=name, source=filename, **settings)
    model = compile(grammar, name=name, source=filename, config=config)
    return modelgen(model, basetype=basetype)


def to_parsermodel_sourcecode(
    grammar: str,
    /,
    *,
    name: str | None = None,
    filename: str | None = None,
    config: ParserConfig | None = None,
    **settings: Any,
):
    filename = filename or settings.pop('source', None)
    model = compile(grammar, config=config, name=name, source=filename, **settings)
    return parsermodel_gen(model, name=name)


def to_grammar_json(grammar: str) -> str:
    from tatsu.parser.bootparser import TatSuBootstrapParser

    parser = TatSuBootstrapParser()
    model = parser.parse(grammar)
    return model.asjson()


# for backwards compatibility. Use `compile()` instead
def genmodel(
    *,
    name: str | None = None,
    grammar: str | None = None,
    semantics: type | None = None,
    config: ParserConfig | None = None,
    **settings: Any,
):
    if grammar is None:
        raise ParseException('grammar is None')

    return compile(grammar, name=name, semantics=semantics, config=config, **settings)


def gencode(
    *,
    name: str | None = None,
    grammar: str,
    trace: bool = False,
    filename: str | None = None,
    codegen: Callable = pythongen,
    config: ParserConfig | None = None,
    **settings: Any,
):
    filename = filename or settings.pop('source', None)
    model = compile(
        grammar,
        name=name,
        source=filename,
        trace=trace,
        config=config,
        **settings,
    )
    return codegen(model)

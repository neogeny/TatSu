# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Parse and translate a TatSu grammar into a Python parser for
the described language.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .. import grammars
from ..builder import BuilderConfig, Constructor, ModelBuilderSemantics, TypeContainer
from ..exceptions import ParseException
from ..infos import ParserConfig
from ..ngcodegen.modelgen import modelgen
from ..ngcodegen.pythongen import pythongen
from ..objectmodel import Node
from ..parser import TatSuParserGenerator
from ..tokenizing import Tokenizer
from ..util.string import hashsha

__all__ = [
    'compile',
    'gencode',
    'genmodel',
    'grammars',
    'modelgen',
    'parse',
    'pythongen',
    'to_python_model',
    'to_python_sourcecode',
]

__compiled_grammar_cache = {}


def compile(
    grammar: str | Tokenizer,
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
) -> grammars.Grammar:
    # check parameters
    ParserConfig.new(
        config=config,
        semantics=semantics,
        name=name,
        filename=filename,
        **settings,
    )
    if isinstance(semantics, type):
        raise TypeError(
            f'semantics must be an object instance or None, not class {semantics!r}',
        )
    cache = __compiled_grammar_cache

    key = (name, hashsha(grammar), id(semantics))
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
    config = ParserConfig.new(
        config=config,
        start=start,
        name=name,
        filename=filename,
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
    config = ParserConfig.new(config=config, name=name, filename=filename, **settings)
    model = compile(grammar, name=name, filename=filename, config=config)
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
    config = ParserConfig.new(config=config, name=name, filename=filename, **settings)
    model = compile(grammar, name=name, filename=filename, config=config)
    return modelgen(model, basetype=basetype)


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
    model = compile(
        grammar,
        name=name,
        filename=filename,
        trace=trace,
        config=config,
        **settings,
    )
    return codegen(model)

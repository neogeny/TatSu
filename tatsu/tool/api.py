"""
Parse and translate an EBNF grammar into a Python parser for
the described language.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .. import grammars
from ..exceptions import ParseException
from ..infos import ParserConfig
from ..ngcodegen.modelgen import modelgen
from ..ngcodegen.pythongen import pythongen
from ..objectmodel import Node
from ..parser import GrammarGenerator
from ..semantics import BuilderConfig, ModelBuilderSemantics
from ..tokenizing import Tokenizer

__compiled_grammar_cache = {}  # type: ignore[var-annotated]


def compile(
    grammar: str | Tokenizer,
    name: str | None = None,
    *,
    config: ParserConfig | None = None,
    builderconfig: BuilderConfig | None = None,
    semantics: Any = None,
    asmodel: bool = False,
    **settings: Any,
) -> grammars.Grammar:
    if isinstance(semantics, type):
        raise TypeError(
            f'semantics must be an object instance or None, not class {semantics!r}',
        )
    cache = __compiled_grammar_cache

    key = (name, grammar, id(semantics))
    if key in cache:
        model = cache[key]
    else:
        gen = GrammarGenerator(name, **settings)
        model = cache[key] = gen.parse(grammar, **settings)

    if semantics is not None:
        model.semantics = semantics
    elif asmodel:
        model.semantics = ModelBuilderSemantics(config=builderconfig)

    return model


def parse(
    grammar: str,
    text: str,
    /, *,
    config: ParserConfig | None = None,
    builderconfig: BuilderConfig | None = None,
    start: str | None = None,
    name: str | None = None,
    semantics: Any | None = None,
    asmodel: bool = False,
    **settings: Any,
):
    config = ParserConfig.new(
        config=config,
        start=start,
        name=name,
        semantics=semantics,
        **settings,
    )
    model = compile(grammar, config=config, asmodel=asmodel)
    config.semantics = semantics or model.semantics
    if not config.semantics and (asmodel or isinstance(builderconfig, BuilderConfig)):
        config.semantics = ModelBuilderSemantics(config=builderconfig)
    return model.parse(text, start=start, semantics=semantics, config=config)


def to_python_sourcecode(
    grammar: str, /, *,
    name: str | None = None,
    filename: str | None = None,
    config: ParserConfig | None = None,
    **settings: Any,
):
    config = ParserConfig.new(
        config=config,
        name=name,
        filename=filename,
        **settings,
    )
    model = compile(grammar, name=name, filename=filename, config=config)
    return pythongen(model)


def to_python_model(
    grammar: str, /, *,
    name: str | None = None,
    filename: str | None = None,
    nodebase: type = Node,
    config: ParserConfig | None = None,
    **settings: Any,
):
    config = ParserConfig.new(
        config=config,
        name=name,
        filename=filename,
        **settings,
    )
    model = compile(grammar, name=name, filename=filename, config=config)
    return modelgen(model, nodebase=nodebase)


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

    return compile(
        grammar, name=name, semantics=semantics, config=config, **settings,
    )


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

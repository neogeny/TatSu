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
from ..parser import GrammarGenerator
from ..semantics import ModelBuilderSemantics
from ..tokenizing import Tokenizer

__compiled_grammar_cache = {}  # type: ignore[var-annotated]


def compile(

        grammar: str | Tokenizer,
        name: str | None = None,
        *,
        semantics: Any = None,
        asmodel: bool = False,
        config: ParserConfig | None = None,
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
        gen = GrammarGenerator(name, config=config, **settings)
        model = cache[key] = gen.parse(grammar, config=config, **settings)

    if semantics is not None:
        model.semantics = semantics
    elif asmodel:
        model.semantics = ModelBuilderSemantics()

    return model


def parse(
    grammar: str, /,
    text: str, *,
    start: str | None = None,
    name: str | None = None,
    semantics: Any | None = None,
    asmodel: bool = False,
    config: ParserConfig | None = None,
    **settings: Any,
):
    model = compile(
        grammar,
        name=name,
        semantics=semantics,
        asmodel=asmodel,
        config=config,
        **settings,
    )
    semantics = semantics or model.semantics
    return model.parse(
        text, start=start, semantics=semantics, config=config, **settings,
    )


def to_python_sourcecode(
    grammar: str, /, *,
    name: str | None = None,
    filename: str | None = None,
    config: ParserConfig | None = None,
    **settings: Any,
):
    model = compile(
        grammar, name=name, filename=filename, config=config, **settings,
    )
    return pythongen(model)


def to_python_model(
    grammar: str, /, *,
    name: str | None = None,
    filename: str | None = None,
    base_type: type | None = None,
    config: ParserConfig | None = None,
    **settings: Any,
):
    model = compile(
        grammar, name=name, filename=filename, config=config, **settings,
    )
    return modelgen(model, base_type=base_type)


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

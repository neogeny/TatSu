[]: copyright (c) 2017-2026 juancarlo añez (apalala@gmail.com)
[]: spdx-license-identifier: bsd-4-clause

## Incompatible Changes
* Support for old generated Python parsers is dropped. In most cases it's best
to generate a new Python parser.

## Grammars / EBNF

* Now **TatSu**'s own grammar is written in EBNF notation.

* There's now a copy of the **TatSu** grammar unther the main package
  at `./tatsu/_tatsu.tatsu`. The grammar text is available as
  `tatsu.grammar`. The grammar remains available at `./grammar/tatsu.tatsu`
  by a symbolic link.

## Functional Changes
* Left recursion is detected at grammar model creation time, and a `GrammarError` 
is raised if left recursion was not enabled in the grammar or configuration 
parameters.

* Large Python modules continue to be factored into smaller modules within a package.

* Generated parsers and models now use `@tatsu.rule` and `@tatsu.dataclass` as
appropriate.

* Refactorings to avoid internal dependency cycles aind simplify imports.

## Model Representations

* Now `str(model)` returns the standard `__str__()` output and no longer
  returns `model.pretty()`. To obtain a grammar representation of a
  grammar model use `model.pretty()` directly.
* `repr(model)` no longer returns `asjsons(model)` but instead returns
  a representation that can be used to reconstruct the model:

    ```python
    model = tatsu.parse(grammar, asmodel=True)
    evalmodel = eval(repr(model), globals=vars(grammars))
    assert repr(model) == repr(evalmodel)
    ```
  
* Now in addition to the existing `rules` and `rulemap` attributes of `Grammar`,
  there is a `rule` attribute that allows access to rules as attributes:
 
    ```python
    class Grammar(Model):
        rules: tuple[Rule, ...]
        rulemap: dict[str, Rule]
        rule: SimpleNamespace
    ```

    ```python
    model = tatsu.compile(grammar)
    rule = mode.rule.start
    ```
* The multiple representations for a model node:
    ```python
    m.pretty()    -> str:   # pretty-printed grammar
    m.asjson()    -> Any:   # object compatible with json.dumps()
    m.asjsons()   -> str:   # json.dumps(m.asjson(), indent=2)
    m.railroads() -> str:   # a railroads diagram in Text/ASCII art
    repr(m)       -> str:   # can be passed to eval()
    ```


## Separation of State and Content

* `Tokenizer` classes provide implementations of the `Cursor` protocol
  which holds the state (e.g. the position) of a parse, while the tokenizer
  acts as the source of the input stream.

* All the bookkeeping for a parse with a `ParseContext` was moved to
  `StateStack` that only takes a `Cursor` as initialization parameter. It's
  possible to have more than one parse on the same input because the state
  of the parsing is separate from the `ParseContext` and the `Tokenizer.

* Methods to represent grammar rules no longer have to be declared in
  a sublclass of `Parser`, but can be declared in any class. The convention
  of naming the methods with a leading and a traling underscore was removed
  so methods are now named like the grammar rules they represent.

* When the name of grammar rules is the same as a reserved word in Python,
  the name is modified by appending one or more underscores to it.

* Methods that implement grammar rules now use a `ctx: Ctx` parameter
  to caccess and pass the invocation `ParsContext`. `Ctx` is the protocol
  that defines only the interface that methods for rules require to perform
  a parse according to the input grammar.

* The undocumented and unmaintained `ParseContext.substate` was removed.

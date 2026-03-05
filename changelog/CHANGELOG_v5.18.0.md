[]: copyright (c) 2017-2026 juancarlo añez (apalala@gmail.com)
[]: spdx-license-identifier: bsd-4-clause

## Grammars / EBNF

* Now **TatSu**'s own grammar is written in EBNF notation.
* There's now a copy of the **TatSu** grammar unther the main package
  at `./tatsu/_tatsu.tatsu`. The grammar text is available as
  `tatsu.grammar`. The grammar remains available at `./grammar/tatsu.tatsu`
  by a symbolic link.

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

.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. include:: links.rst
.. highlight:: none

v5.18.0
-------

Grammars / EBNF
~~~~~~~~~~~~~~~

-   Now |TatSu|’s own grammar is written in EBNF_ notation. Examples and documentation are converging to the syntax used by `pegen`_, the base for the Python PEG parser.

.. _pegen: https://we-like-parsers.github.io/pegen/grammar.html

-   Multi-line string literals in the grammar are now supported. Use triple
    quotes like ``"""…"""`` or ``'''…'''`` for multi-line string literals
    in the grammar.

-   The ``(?:…)`` expression was added to grammars. It works like a ``(…)`` group but the expression parsed is not captured.

-   There’s now a copy of the |TatSu| grammar under the main package at ``./tatsu/_grammar.tatsu``. The grammar text is available as ``tatsu.grammar``. The grammar remains available at ``./grammar/tatsu.tatsu`` by a symbolic link.


Semantics and Module Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-   The semantics of grammar representations and parsing where spread all over the codebase, in a way that made them hard to understand and maintain. Now each aspect of the semantics is defined in a single, small module. Some modules of interest, worth studying, are:

    -   `tatsu.contexts.cst`_ values for unnamed expressions and for AST_ entries
    -   `tatsu.contexts.ast`_ values for expressions with named elements
    -   `tatsu.contexts.sts`_ state and scope management during parsing
    -   `tatsu.objectmodel.node`_ the structured representation of parse results
    -   `tatsu.grammars.model`_ the structured representation of grammars

.. _tatsu.contexts.ast: https://github.com/neogeny/TatSu/blob/master/tatsu/contexts/ast.py
.. _tatsu.contexts.cst: https://github.com/neogeny/TatSu/blob/master/tatsu/contexts/cst.py
.. _tatsu.contexts.sts: https://github.com/neogeny/TatSu/blob/master/tatsu/contexts/sts.py
.. _tatsu.grammars.model: https://github.com/neogeny/TatSu/blob/master/tatsu/grammars/model.py
.. _tatsu.objectmodel.node: https://github.com/neogeny/TatSu/blob/master/tatsu/objectmodel/node.py

-   The module hierarchy has been refactored to avoid internal dependency cycles, to simplify imports, and to not require partial module parses by Python. Large modules have been factored at semantic boundaries into smaller modules within a package.

-   Left recursion is detected at grammar model creation time, and a ``GrammarError`` is raised if left recursion was not enabled in the grammar or configuration parameters.

-   Generated parsers and models now use ``@tatsu.rule`` and ``@tatsu.dataclass`` as appropriate.

-   Generated parsers now use anonymous functions to implement choices and closures:

    .. code:: python
        :force:

        with ctx.choice() as ch:
            @ch.option
            def _():
                self.word(ctx)

            @ch.option
            def _():
                self.string(ctx)

            ch.expecting('<string>', '<word>')

-   Now in addition to the existing ``rules`` and ``rulemap`` attributes of ``Grammar``, there is a ``rule`` attribute that allows access to rules as attributes:

    .. code:: python
        :force:

         class Grammar(Model):
             rules: tuple[Rule, ...]
             rulemap: dict[str, Rule]
             rule: SimpleNamespace

    .. code:: python
        :force:

         model = tatsu.compile(grammar)
         rule = mode.rule.start
         print(m.rule.longone.exp.token)

-   Rules and the different forms of closures are back to returning ``list`` instead of ``tuple``. The ``tuples`` were introduced as a not-thought-up shortcut and it has taken until now to fix that. Square brackets are much easier to discern in programs and output in a context in which parenthesis are already overloaded.


Model Representations
~~~~~~~~~~~~~~~~~~~~~

- Now ``str(model)`` returns the standard ``__str__()`` output and no longer returns ``model.pretty()``. To obtain a grammar representation of a grammar model use ``model.pretty()`` directly.

-   ``repr(model)`` no longer returns ``asjsons(model)`` but instead returns a representation that can be used to reconstruct the model:

    .. code:: python
        :force:

         model = tatsu.parse(grammar, asmodel=True)
         evalmodel = eval(repr(model), globals=vars(grammars))
         assert repr(model) == repr(evalmodel)

-   These are the multiple representations for a grammar model or node:

    .. code:: python
        :force:

        m.pretty()    -> str:   # pretty-printed grammar
        m.asjson()    -> Any:   # object compatible with json.dumps()
        m.asjsons()   -> str:   # json.dumps(m.asjson(), indent=2)
        m.railroads() -> str:   # a railroads diagram in Text/ASCII art
        repr(m)       -> str:   # as an expression can reconstruct the model


Separation of State and Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``Tokenizer`` classes provide implementations of the ``Cursor`` protocol which holds the state (e.g. the position) of a parse, while the tokenizer acts as the source of the input stream.

- All the bookkeeping for a parse with a ``ParseContext`` was moved to ``StateStack`` that only takes a ``Cursor`` as initialization parameter. It’s possible to have more than one parse on the same input because the state of the parsing is separate from the ``ParseContext`` and the ``Tokenizer``.

- Methods to represent grammar rules no longer have to be declared in a subclass of ``Parser``, but can be declared in any class. The convention of naming the methods with a leading and a trailing underscore was removed so methods are now named like the grammar rules they represent.

- When the name of grammar rules is the same as a reserved word in Python, the name is modified by appending one or more underscores to it.

- Methods that implement grammar rules now use a ``ctx: Ctx`` parameter to access and pass the invocation ``ParsContext``. ``Ctx`` is the protocol that defines only the interface that methods for rules require to perform a parse according to the input grammar.


Deprecations and Removals
~~~~~~~~~~~~~~~~~~~~~~~~~

- Support for generated parsers from legacy versions of |TatSu| has been dropped. The parsers may still work, but no effort to maintain compatibility is made any longer. In most cases it’s best to generate a new Python parser.

- Dropped support in the grammar for ``regex + regex``, adding regular expressions.

- Dropped support for ``?/…/?`` regexes in the grammar.

- The undocumented and unmaintained ``ParseContext.substate`` was removed.

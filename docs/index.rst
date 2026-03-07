.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. tatsu documentation master file, created by
   sphinx-quickstart on Mon May  1 18:01:31 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: links.rst


|TatSu|
=======

    *At least for the people who send me mail about a new language that
    they're designing, the general advice is: do it to learn about how
    to write a compiler. Don't have any expectations that anyone will
    use it, unless you hook up with some sort of organization in a
    position to push it hard. It's a lottery, and some can buy a lot of
    the tickets. There are plenty of beautiful languages (more beautiful
    than C) that didn't catch on. But someone does win the lottery, and
    doing a language at least teaches you something.*

    `Dennis Ritchie`_ (1941-2011) Creator of the C_ programming
    language and of Unix_


|TatSu| is a tool that takes grammars in extended `EBNF`_ as input, and
outputs `memoizing`_ (`Packrat`_) `PEG`_ parsers in `Python`_. The classic
variations of EBNF_ (Tomassetti, EasyExtend, Wirth) and `ISO EBNF`_ are
supported as input grammar formats.

Why use a `PEG`_ parser generator?
----------------------------------

Regular expressions are *“memory-less”*—they excel at finding flat patterns
like email addresses or phone numbers, but they fail once data becomes
hierarchical. Regular expressions cannot *"count"* or balance demarcations
(a regex cannot reliably validate whether opening and closing parenthesis are
matched in a nested math equation).

Parsing is the essential step up when you need to understand the **logic and
structure** of information rather than just its appearance. Parsing constructs
an **Abstract Syntax Tree** (AST_) of the input, a hierarchical map that
represents how different parts of a sequence relate to one another.

* **Recursive Structures:** Whenever a piece of data can contain
  a version of itself (like a folder inside a folder, or a conditional
  ``if`` statement inside another ``if``), you need a parser to track the
  depth and scope.

* **Translating Formats:** When converting one format into another, a
  parser ensures that the *meaning* of the original structure is
  preserved, preventing the *"data soup"* that occurs when using simple
  find-and-replace tools.

* **Ambiguity Resolution:** In complex sequences, the same sub-sequence might
  mean different things depending on where it sits in the tree. A parser
  uses the surrounding context to decide how to treat that sequence,
  whereas a regex treats every match in isolation.

* **Domain-Specific Languages (DSL):** Parsing allows the creation of
  specialized *"mini-languages"* tailored to a specific field, such as hardware
  description, music notation, or complex business rules.

* **Executable Logic:** While a regex can tell you if a string
  *looks* like a command, a parser turns that string into an object that a
  computer can actually execute, ensuring the order of operations and
  dependencies are strictly followed.

|TatSu| can compile a grammar stored in a string into a ``Grammar`` object that
can be used to parse any given input (much like the `re`_ module does with regular
expressions). |TatSu| can also generate a Python_ module that implements the parser.

|TatSu| supports `left-recursive`_  rules in PEG_ grammars using the
algorithm_ by *Laurent* and *Mens*. The generated AST_ has the expected left associativity.


.. toctree::
    :maxdepth: 4

    intro
    rationale
    install
    use
    parserconfig
    syntax
    directives
    ast
    semantics
    models
    translation
    left_recursion
    mini-tutorial
    traces
    antlr
    examples
    support
    credits
    contributors
    contributing
    license
    changelog

.. toctree::

..    :hidden:



.. comment out
    Indices and tables
    ==================
    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`

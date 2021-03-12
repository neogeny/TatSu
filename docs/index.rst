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



|TatSu| is a tool that takes grammars in a variation of `EBNF`_ as input,
and outputs `memoizing`_ (`Packrat`_) `PEG`_ parsers in `Python`_.

|TatSu| can compile a grammar stored in a string into a
``tatsu.grammars.Grammar`` object that can be used to parse any given
input, much like the `re`_ module does with regular expressions, or it can generate a Python_ module that implements the parser.

|TatSu| supports `left-recursive`_  rules in PEG_ grammars, and it honors *left-associativity* in the resulting parse trees.

.. toctree::
    :maxdepth: 2

    intro
    rationale
    install
    use
    syntax
    directives
    ast
    semantics
    models
    left_recursion
    mini-tutorial
    traces
    grako
    antlr
    examples
    support
    credits
    contributors
    contributing
    license

.. toctree::
    :hidden:



.. comment out
    Indices and tables
    ==================
    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`

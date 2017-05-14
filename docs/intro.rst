.. include:: links.rst

Introduction
------------

|TatSu| is *different* from other `PEG`_ parser generators:

-  Generated parsers use `Python`_'s very efficient exception-handling
   system to backtrack. |TatSu| generated parsers simply assert what
   must be parsed. There are no complicated *if-then-else* sequences for
   decision making or backtracking. Memoization allows going over the
   same input sequence several times in linear time.
-  *Positive and negative lookaheads*, and the *cut* element (with its
   cleaning of the memoization cache) allow for additional, hand-crafted
   optimizations at the grammar level.
-  Delegation to `Python`_'s `re`_ module for *lexemes* allows for
   (`Perl`_-like) powerful and efficient lexical analysis.
-  The use of `Python`_'s `context managers`_ considerably reduces the
   size of the generated parsers for code clarity, and enhanced
   CPU-cache hits.
-  Include files, rule inheritance, and rule inclusion give |TatSu|
   grammars considerable expressive power.
-  Automatic generation of Abstract Syntax Trees\_ and Object Models,
   along with *Model Walkers* and *Code Generators* make analysis and
   translation approachable

The parser generator, the run-time support, and the generated parsers
have measurably low `Cyclomatic complexity`_. At around 5 `KLOC`_ of
`Python`_, it is possible to study all its source code in a single
session.

The only dependencies are on the `Python`_ standard library, yet the
`regex`_ library will be used if installed, and `colorama`_ will be used
on trace output if available. `pygraphviz`_ is required for generating
diagrams.

|TatSu| is feature-complete and currently being used with complex
grammars to parse, analyze, and translate hundreds of thousands of lines
of input text, including source code in several programming languages.

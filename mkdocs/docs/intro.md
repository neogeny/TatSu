# Introduction

{{TatSu}} is *different* from other [PEG](http://en.wikipedia.org/wiki/Parsing_expression_grammar) parser generators:

- Generated parsers use [Python](http://python.org)'s very efficient exception-handling system to backtrack. {{TatSu}} generated parsers simply assert what must be parsed. There are no complicated *if-then-else* sequences for decision making or backtracking. Memoization allows going over the same input sequence several times in linear time.
- *Positive and negative lookaheads*, and the *cut* element (with its cleaning of the memoization cache) allow for additional, hand-crafted optimizations at the grammar level.
- Delegation to [Python](http://python.org)'s [re](https://docs.python.org/3.4/library/re.html) module for *lexemes* allows for ([Perl](http://www.perl.org/)-like) powerful and efficient lexical analysis.
- The use of [Python](http://python.org)'s [context managers](http://docs.python.org/2/library/contextlib.html) considerably reduces the size of the generated parsers for code clarity, and enhanced CPU-cache hits.
- Include files, rule inheritance, and rule inclusion give {{TatSu}} grammars considerable expressive power.
- Automatic generation of Abstract Syntax Trees\_ and Object Models, along with *Model Walkers* and *Code Generators* make analysis and translation approachable

The parser generator, the run-time support, and the generated parsers have measurably low [Cyclomatic complexity](http://en.wikipedia.org/wiki/Cyclomatic_complexity). At around 5 [KLOC](http://en.wikipedia.org/wiki/KLOC) of [Python](http://python.org), it is possible to study all its source code in a single session.

The only dependencies are on the [Python](http://python.org) standard library, yet the [regex](https://pypi.python.org/pypi/regex) library will be used if installed, and [colorama](https://pypi.python.org/pypi/colorama/) will be used on trace output if available. The [graphviz](https://pypi.python.org/pypi/graphviz) library is required for generating diagrams of the grammars.

{{TatSu}} is feature-complete and currently being used with complex grammars to parse, analyze, and translate hundreds of thousands of lines of input text, including source code in several programming languages.

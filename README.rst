|fury| |license| |pyversions| |travis| |landscape|

----

*At least for the people who send me mail about a new language that they're designing, the general advice is: do it to learn about how to write a compiler. Don't have any expectations that anyone will use it, unless you hook up with some sort of organization in a position to push it hard. It's a lottery, and some can buy a lot of the tickets. There are plenty of beautiful languages (more beautiful than C) that didn't catch on. But someone does win the lottery, and doing a language at least teaches you something.*
    `Dennis Ritchie`_ (1941-2011)
        Creator of the C_ programming language and of Unix_

.. _`Dennis Ritchie`: http://en.wikipedia.org/wiki/Dennis_Ritchie
.. _C: http://en.wikipedia.org/wiki/C_language
.. _Unix: http://en.wikipedia.org/wiki/Unix

=====
Tatsu
=====

.. code::

    Copyright (C) 2017 Juancarlo Añez


----

|donate|

*If you'd like to contribute to the future development of Tatsu,
please donate_ to the project*.

*Some of the planned new features are: grammar expressions for left
and right associativity, new algorithms for left-recursion, a
unified intermediate model for parsing and translating programming
languages, and more...*

----


.. _donate: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9PV7ZACB669J


**Tatsu** (for *grammar compiler*) is a tool that takes grammars in a variation of EBNF_ as input, and outputs memoizing_ (Packrat_) PEG_ parsers in Python_.

**Tatsu** can also compile a grammar stored in a string into a ``Grammar`` object that can be used to parse any given input, much like the re_ module does with regular expressions.

**Tatsu** is *different* from other PEG_ parser generators:

* Generated parsers use Python_'s very efficient exception-handling system to backtrack. **Tatsu** generated parsers simply assert what must be parsed. There are no complicated *if-then-else* sequences for decision making or backtracking. Memoization allows going over the same input sequence several times in linear time.

* *Positive and negative lookaheads*, and the *cut* element (with its cleaning of the memoization cache) allow for additional, hand-crafted optimizations at the grammar level.

* Delegation to Python_'s re_ module for *lexemes* allows for (Perl_-like) powerful and efficient lexical analysis.

* The use of Python_'s `context managers`_ considerably reduces the size of the generated parsers for code clarity, and enhanced CPU-cache hits.

* Include files, rule inheritance, and rule inclusion give **Tatsu** grammars considerable expressive power.

* Automatic generation of `Abstract Syntax Trees`_ and Object Models, along with *Model Walkers* and *Code Generators* make analysis and translation approachable

The parser generator, the run-time support, and the generated parsers have measurably low `Cyclomatic complexity`_.  At around 5 KLOC_ of Python_, it is possible to study all its source code in a single session.

The only dependencies are on the Python_ standard library, yet the regex_ library will be used if installed, and colorama_ will be used on trace output if available.  pygraphviz_ is required for generating diagrams.

**Tatsu** is feature-complete and currently being used with complex grammars to parse, analyze, and translate hundreds of thousands of lines of input text, including source code in several programming languages.

.. _`Cyclomatic complexity`: http://en.wikipedia.org/wiki/Cyclomatic_complexity
.. _KLOC: http://en.wikipedia.org/wiki/KLOC
.. _legacy: http://en.wikipedia.org/wiki/Legacy_code
.. _`legacy code`: http://en.wikipedia.org/wiki/Legacy_code
.. _PyPy: http://pypy.org/
.. _`context managers`: http://docs.python.org/2/library/contextlib.html
.. _Perl: http://www.perl.org/
.. _NATURAL: http://en.wikipedia.org/wiki/NATURAL
.. _COBOL: http://en.wikipedia.org/wiki/Cobol
.. _Java:  http://en.wikipedia.org/wiki/Java_(programming_language)
.. _VB6: http://en.wikipedia.org/wiki/Visual_basic_6
.. _regex: https://pypi.python.org/pypi/regex
.. _re: https://docs.python.org/3.4/library/re.html
.. _pygraphviz: https://pypi.python.org/pypi/pygraphviz
.. _colorama: https://pypi.python.org/pypi/colorama/

Rationale
=========

**Tatsu** was created to address some recurring problems encountered over decades of working with parser generation tools:

* Some programming languages allow the use of *keywords* as identifiers, or have different meanings for symbols depending on context (Ruby_). A parser needs control of lexical analysis to be able to handle those languages.

* LL and LR grammars become contaminated with myriads of lookahead statements to deal with ambiguous constructs in the source language. PEG_ parsers address ambiguity from the onset.

* Separating the grammar from the code that implements the semantics, and using a variation of a well-known grammar syntax (EBNF_) allows for full declarative power in language descriptions. General-purpose programming languages are not up to the task.

* Semantic actions *do not*  belong in a grammar. They create yet another programming language to deal with when doing parsing and translation: the source language, the grammar language, the semantics language, the generated parser's language, and the translation's target language. Most grammar parsers do not check the syntax of embedded semantic actions, so errors get reported at awkward moments, and against the generated code, not against the grammar.

* Preprocessing (like dealing with includes, fixed column formats, or structure-through-indentation) belongs in well-designed program code; not in the grammar.

* It is easy to recruit help with knowledge about a mainstream programming language like Python_, but help is hard to find for working with complex grammar-description languages. **Tatsu** grammars are in the spirit of a *Translators and Interpreters 101* course (if something is hard to explain to a college student, it's probably too complicated, or not well understood).

* Generated parsers should be easy to read and debug by humans. Looking at the generated source code is sometimes the only way to find problems in a grammar, the semantic actions, or in the parser generator itself. It's inconvenient to trust generated code that one cannot understand.

* Python_ is a great language for working with language parsing and translation.

.. _`Abstract Syntax Tree`: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _`Abstract Syntax Trees`: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _AST: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _ASTs: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _CST:  http://en.wikipedia.org/wiki/Concrete_syntax_tree
.. _EBNF: http://en.wikipedia.org/wiki/Ebnf
.. _memoizing: http://en.wikipedia.org/wiki/Memoization
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar
.. _Packrat: http://bford.info/packrat/
.. _Python: http://python.org
.. _Ruby: http://www.ruby-lang.org/


Documentation
=============

The `complete documentation`_ is available at **Tatsu**'s `home page`_.

.. _`complete documentation`: https://bitbucket.org/neogeny/tatsu/src/default/README.md
.. _`home page`: https://bitbucket.org/neogeny/tatsu/


License
=======

.. _`Juancarlo Añez`: mailto:apalala@gmail.com
.. _`Thomas Bragg`: mailto:tbragg95@gmail.com

You may use **Tatsu** under the terms of the BSD_-style license described in the enclosed **LICENSE.txt** file. *If your project requires different licensing* please email_.

.. _BSD: http://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29
.. _email: mailto:apalala@gmail.com


Changes
=======


See the CHANGELOG_ for details.

.. _CHANGELOG: https://bitbucket.org/neogeny/tatsu/src/default/CHANGELOG.md
.. |fury| image:: https://badge.fury.io/py/tatsu.svg
   :target: https://badge.fury.io/py/tatsu
.. |license| image:: https://img.shields.io/badge/license-BSD-blue.svg
   :target: https://raw.githubusercontent.com/neogeny/tatsu/master/LICENSE.txt
.. |pyversions| image:: https://img.shields.io/pypi/pyversions/tatsu.svg
   :target: https://pypi.python.org/pypi/tatsu
.. |travis| image:: https://secure.travis-ci.org/neogeny/tatsu.svg
   :target: http://travis-ci.org/neogeny/tatsu
.. |landscape| image:: https://landscape.io/github/neogeny/tatsu/release/landscape.png
   :target: https://landscape.io/github/neogeny/tatsu/release
.. |donate| image:: https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif
   :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9PV7ZACB669J


.. Google Analytics Script
    <script>
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
    (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
    m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');
    ga('create', 'UA-37745872-1', 'auto');
    ga('send', 'pageview');
    </script>

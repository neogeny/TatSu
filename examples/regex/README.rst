Regexp to Tatsu
===============

Parse a regular expression, translate it to CFGs_ in **Tatsu** EBNF_ grammar notation, and generate a **Tatsu** PEG_ parser for the grammar.

.. _CFGs: http://en.wikipedia.org/wiki/Context-free_grammar
.. _EBNF: http://en.wikipedia.org/wiki/Ebnf
.. _PEG:http://en.wikipedia.org/wiki/Parsing_expression_grammar

The project has no practical use, but it's complete yet concise example of how to implement translators in **Tatsu**'.

The parser builds an OO model of each parsed regexp using semantic actions. The model generates a **Tatsu** grammar with the help the *rendering* module using inline templates. The generated grammar is then parsed to generate a parser. The generated parser can be executed thus::

    $ python genparser.py data/valid S0

For a list of the generated parser rules use::

    $ python genparser.py -l

To build the project, issue::

    $ make

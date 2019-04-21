.. include:: links.rst


Examples
--------

Tatsu
~~~~~

The file ``grammar/tatsu.ebnf`` contains a grammar for the |TatSu| grammar
language written in its own grammar language. It is used in the
*bootstrap* test suite to prove that |TatSu| can generate a parser to
parse its own language, and the resulting parser is made the bootstrap
parser every time |TatSu| is stable (see ``tatsu/bootstrap.py`` for
the generated parser).

|TatSu| uses |TatSu| to translate grammars into parsers, so it is a
good example of end-to-end translation.


Calc
~~~~

The project ``examples/calc`` implements a calculator for simple
expressions, and is written as a tutorial over most of the features
provided by |TatSu|.


g2e
~~~

The project ``examples/g2e`` contains an example `ANTLR`_ to |TatSu| grammar
translation. The project is a good example of the use ``g2e``. It generates the
|TatSu| grammar on standard output, but because the model used is
|TatSu|'s own, the same code can be used to directly generate a parser
from any `ANTLR`_ grammar. Please take a look at the examples *README* to
know about limitations.

.. include:: links.rst


Examples
--------

Tatsu
~~~~~

The file ``etc/tatsu.ebnf`` contains a grammar for the **Tatsu** grammar
language written in its own grammar language. It is used in the
*bootstrap* test suite to prove that **Tatsu** can generate a parser to
parse its own language, and the resulting parser is made the bootstrap
parser every time **Tatsu** is stable (see ``tatsu/bootstrap.py`` for
the generated parser).

**Tatsu** uses **Tatsu** to translate grammars into parsers, so it is a
good example of end-to-end translation.

Regex
~~~~~

The project ``examples/regexp`` contains a regexp-to-EBNF translator and
parser generator. The project has no practical use, but it's a complete,
end-to-end example of how to implement a translator using **Tatsu**.

Calc
~~~~

The project ``examples/calc`` implements a calculator for simple
expressions, and is written as a tutorial over most of the features
provided by **Tatsu**.

g2e
~~~

The project ``examples/g2e`` contains a `ANTLR`_ to **Tatsu** grammar
translator. The project is a good example of the use of models and
templates in translation. The program, ``g2e.py`` generates the
**Tatsu** grammar on standard output, but because the model used is
**Tatsu**'s own, the same code can be used to directly generate a parser
from an `ANTLR`_ grammar. Please take a look at the examples *README* to
know about limitations.



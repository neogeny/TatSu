.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. include:: links.rst


Examples
--------

TatSu
~~~~~

The file ``grammar/tatsu.tatsu`` contains a grammar for the |TatSu| grammar
language written in the same language. The grammar is used in the
*bootstrap* test suite to prove that |TatSu| can generate a parser to
parse its own language. The parser output from the tests si made the main parser every time |TatSu| is stable (see ``tatsu/bootstrap.py`` for
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
translation. The project uses ``g2e`` to generate a |TatSu| grammar
from the ``Python3.g4`` ANTLR_ grammar. Because the model classes used are
|TatSu|'s own (``grammars.*``), the same strategy can be used to
generate a parser from any other `ANTLR`_ grammar. Please take a look at the
examples *README* to know about limitations.

.. include:: links.rst

Abstract Syntax Trees (ASTs)
----------------------------

By default, an `AST`_ is either a *list* (for *closures* and rules
without named elements), or *dict*-derived object that contains one item
for every named element in the grammar rule. Items can be accessed
through the standard ``dict`` syntax (``ast['key']``), or as attributes
(``ast.key``).

`AST`_ entries are single values if only one item was associated with a
name, or lists if more than one item was matched. There's a provision in
the grammar syntax (the ``+:`` operator) to force an `AST`_ entry to be
a list even if only one element was matched. The value for named
elements that were not found during the parse (perhaps because they are
optional) is ``None``.

When the ``parseinfo=True`` keyword argument has been passed to the
``Parser`` constructor, a ``parseinfo`` element is added to `AST`_ nodes
that are *dict*-like. The element contains a ``collections.namedtuple``
with the parse information for the node:

.. code:: python

    ParseInfo = namedtuple(
        'ParseInfo',
        [
            'buffer',
            'rule',
            'pos',
            'endpos',
            'line',
            'endline',
        ]
    )

With the help of the ``Buffer.line_info()`` method, it is possible to
recover the line, column, and original text parsed for the node. Note
that when ``ParseInfo`` is generated, the ``Buffer`` used during parsing
is kept in memory for the lifetime of the `AST`_.

Generation of ``parseinfo`` can also be controlled using the
``@@parseinfo :: True`` grammar directive.

.. _Abstract Syntax Tree: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _AST: http://en.wikipedia.org/wiki/Abstract_syntax_tree

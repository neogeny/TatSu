.. include:: links.rst

Semantic Actions
----------------

There are no constructs for semantic actions in |TatSu| grammars. This
is on purpose, because semantic actions obscure the declarative nature
of grammars and provide for poor modularization from the
parser-execution perspective.

Semantic actions are defined in a class, and applied by passing an
object of the class to the ``parse()`` method of the parser as the
``semantics=`` parameter. |TatSu| will invoke the method that matches
the name of the grammar rule every time the rule parses. The argument to
the method will be the `AST`_ constructed from the right-hand-side of
the rule:

.. code:: python

    class MySemantics:
        def some_rule_name(self, ast):
            return ''.join(ast)

        def _default(self, ast):
            pass

If there's no method matching the rule's name, |TatSu| will try to
invoke a ``_default()`` method if it's defined:

.. code:: python

    def _default(self, ast):
        ...

Nothing will happen if neither the per-rule method nor ``_default()``
are defined.

The per-rule methods in classes implementing the semantics provide
enough opportunity to do rule post-processing operations, like
verifications (for inadequate use of keywords as identifiers), or `AST`_
transformation:

.. code:: python

    class MyLanguageSemantics:
        def identifier(self, ast):
            if my_lange_module.is_keyword(ast):
                raise FailedSemantics('"%s" is a keyword' % str(ast))
            return ast

For finer-grained control it is enough to declare more rules, as the
impact on the parsing times will be minimal.

If preprocessing is required at some point, it is enough to place
invocations of empty rules where appropriate:

.. code:: python

    myrule = first_part preproc {second_part} ;

    preproc = () ;

The abstract parser will honor as a semantic action a method declared
as:

.. code:: python

    def preproc(self, ast):
        ...


.. _Abstract Syntax Tree: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _AST: http://en.wikipedia.org/wiki/Abstract_syntax_tree
.. _EBNF: http://en.wikipedia.org/wiki/Ebnf
.. _PEG: http://en.wikipedia.org/wiki/Parsing_expression_grammar
.. _Python: http://python.org
.. _keywords: https://en.wikipedia.org/wiki/Reserved_word

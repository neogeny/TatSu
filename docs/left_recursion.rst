.. include:: links.rst


Left Recursion
--------------

|TatSu| supports direct and indirect left recursion in grammar rules using the the algorithm described by *Nicolas Laurent* and *Kim Mens* in their 2015 paper_ *Parsing Expression Grammars Made Practical*.

Left recursive rules produce left-associative parse trees (AST_), as most users would expect.

.. _paper: http://norswap.com/pubs/sle2016.pdf

Left recursion support is enabled by default in |TatSu|. To disable it for a particular grammar, use the ``@@left_recursion`` directive:

.. code:: ocaml

    @@left_recursion :: False


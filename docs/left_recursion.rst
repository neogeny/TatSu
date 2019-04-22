.. include:: links.rst


Left Recursion
--------------

|TatSu| supports direct and indirect left recursion in grammar rules using the the algorithm described by *Nicolas Laurent* and *Kim Mens* in their 2015 paper_ *Parsing Expression Grammars Made Practical*.

The design and implementation of left recursion was done by `Vic Nightfall`_ with research and help by `Nicolas Laurent`_ on Autumn_, and research by `Philippe Sigaud`_ on PEGGED_.

.. _Autumn: https://github.com/norswap/autumn
.. _PEGGED: https://github.com/PhilippeSigaud/Pegged/wiki/Left-Recursion

Left recursive rules produce left-associative parse trees (AST_), as most users would expect.

.. _paper: http://norswap.com/pubs/sle2015.pdf

Left recursion support is enabled by default in |TatSu|. To disable it for a particular grammar, use the ``@@left_recursion`` directive:

.. code:: ocaml

    @@left_recursion :: False


.. warning::

    Not all left-recursive grammars that use the |TatSu| syntax are PEG_. The same happens with right-recursive grammars.  **The order of rules in matters in PEG**.

    For right-recursive grammars the choices that parse the most input must come first. The same is true  for left-recursive grammars.

    Additionally, for grammars with **indirect left recursion, the rules containing choices must be the first invoked during a parse**. The following grammar is correct,but it will not work if the start rule is changed to ```start = mul ;```.

    .. code:: ocaml

            start = expr ;

            expr
                =
                mul | identifier
                ;

            mul
                =
                expr '*' identifier
                ;

            identifier
                =
                /\w+/
                ;

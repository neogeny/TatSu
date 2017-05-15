.. include:: links.rst

Grako (In)compatibility
------------------------

Grako_ grammars can be used with |TatSu|, with these caveats:

*   The Python_ module name changed to ``tatsu``.

*   ``ignorecase`` no longer applies to regular expressions in grammars. Use ``(?i)`` in the pattern to enable ``re.IGNORECASE``

*   Left recursion is enabled by default because it works and has zero impact on non-recursive grammars.

*   Deprecated grammar syntax is no longer documented. It's best not to use it, as it will be removed in a future version of |TatSu|.

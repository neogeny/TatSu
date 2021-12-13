.. include:: links.rst

Grako Compatibility
-------------------

|TatSu| is routinely tested over major projects developed with Grako_. The
backwards-compatibility suite includes (at least) translators for COBOL_, Java_, and (Oracle) SQL_.

Grako_ grammars and projects can be used with |TatSu|, with these caveats:

*   The `AST`_ type retuned when a sequence of elements is matched is now ``tuple`` (instead of a descendant of ``list``). This change improves efficiency and avoids unwanted manipulations of a value that should be inmutable.

*   The Python_ module name changed to ``tatsu``.

*   ``ignorecase`` no longer applies to regular expressions in grammars. Use ``(?i)`` in the pattern to enable ``re.IGNORECASE``

*   Left recursion is enabled by default because it works and has zero impact on non-recursive grammars.

*   Deprecated grammar syntax is no longer documented. It's best not to use it, as it will be removed in a future version of |TatSu|.

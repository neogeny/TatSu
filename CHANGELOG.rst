.. |dragon| unicode:: 0x7ADC .. unicode dragon
.. |TatSu| replace:: |dragon| **TatSu**

Change Log
==========

|TatSu| uses `Semantic Versioning`_ for its releases, so parts
of the version number may increase without any significant changes or
backwards incompatibilities in the software.

The format of this *Change Log* is inspired by `keeapachangelog.org`_.

`X.Y.Z`_ @ 2017
---------------
.. _X.Y.Z: https://github.com/apalala/tatsu/compare/v4.1.1...master

*   Parse speeds on large files reduced by 2-10% by optimizing parse contexts and closures.


`4.1.1`_ @ 2017-05-21
---------------------
.. _4.1.1: https://github.com/apalala/tatsu/compare/v4.1.0...v4.1.1

Fixed
~~~~~

*   ``tatus.objectmodel.Node`` not setting attributes from ``AST``.



`4.1.0`_ @ 2017-05-21
---------------------
.. _4.1.0: https://github.com/apalala/tatsu/compare/v4.0.0...v4.1.0

Added
~~~~~

*  New support for *left recursion* with correct associativity. All test
   cases pass.

*  Left recursion is enabled by default. Use the
   ``@@left_recursion :: False`` directive to diasable it.

*  Renamed the decorator for generated rule methods to ``@tatsumasu``.

*  Refactored the ``tatsu.contexts.ParseContext`` for clarity.

*  The ``@@ignorecase`` directive and the ``ignorecase=`` parameter no
   longer appy to regular expressions (patterns) in grammars. Use
   ``(?i)`` in the pattern to ignore the case in a particular pattern.

*  Now ``tatsu.g2e`` is a library and executable module for translating
   `ANTLR`_ grammars to **TatSu**.

*  Modernized the ``calc`` example and made it part of the documentation
   as *Mini Tutorial*.

*  Simplified the generated object models using the semantics of class
   attributes in Python\_

`4.0.0`_ @ 2017-05-06
---------------------
.. _4.0.0: https://github.com/apalala/tatsu/compare/0.0.0...v4.0.0

-  First release.

.. _Semantic Versioning: http://semver.org/
.. _keeapachangelog.org: http://keepachangelog.com/
.. _ANTLR: http://www.antlr.org

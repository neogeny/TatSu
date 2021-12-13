Copyright (C) 2017-2021 Juancarlo Añez

This uses the tanslator from ANTLR grammars to Tatsu grammars. It shows how to build a translator using models, templates and Tatsu. The test case used is the Python grammar available on the ANTLR grammar repository.

The translator ignores:

    * The configuration sections of ANTLR grammars.
    * Semantic actions (not generally needed in Packrat parsers).
    * Tree construction syntax.

It is very likely that a translated grammar won't work as is. At the very least some reordering of rules will be required to match the requirements of PEG parsers.

----

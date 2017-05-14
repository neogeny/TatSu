.. include:: links.rst

Rationale
---------

|TatSu| was created to address some recurring problems encountered
over decades of working with parser generation tools:

-  Some programming languages allow the use of *keywords* as
   identifiers, or have different meanings for symbols depending on
   context (`Ruby`_). A parser needs control of lexical analysis to be
   able to handle those languages.
-  LL and LR grammars become contaminated with myriads of lookahead
   statements to deal with ambiguous constructs in the source language.
   `PEG`_ parsers address ambiguity from the onset.
-  Separating the grammar from the code that implements the semantics,
   and using a variation of a well-known grammar syntax (`EBNF`_) allows
   for full declarative power in language descriptions. General-purpose
   programming languages are not up to the task.
-  Semantic actions *do not* belong in a grammar. They create yet
   another programming language to deal with when doing parsing and
   translation: the source language, the grammar language, the semantics
   language, the generated parser's language, and the translation's
   target language. Most grammar parsers do not check the syntax of
   embedded semantic actions, so errors get reported at awkward moments,
   and against the generated code, not against the grammar.
-  Preprocessing (like dealing with includes, fixed column formats, or
   structure-through-indentation) belongs in well-designed program code;
   not in the grammar.
-  It is easy to recruit help with knowledge about a mainstream
   programming language like `Python`_, but help is hard to find for
   working with complex grammar-description languages. |TatSu|
   grammars are in the spirit of a *Translators and Interpreters 101*
   course (if something is hard to explain to a college student, it's
   probably too complicated, or not well understood).
-  Generated parsers should be easy to read and debug by humans. Looking
   at the generated source code is sometimes the only way to find
   problems in a grammar, the semantic actions, or in the parser
   generator itself. It's inconvenient to trust generated code that one
   cannot understand.
-  `Python`_ is a great language for working with language parsing and
   translation.

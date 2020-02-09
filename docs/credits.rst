.. include:: links.rst

Credits
-------

-   |TatSu| is the successor of Grako_, which was built by **Juancarlo Añez** and funded by **Thomas Bragg** to do analysis and translation of programs written in legacy programming languages.
-  **Niklaus Wirth** was the chief designer of the programming languages
   `Euler`_, `Algol W`_, `Pascal`_, `Modula`_, `Modula-2`_, `Oberon`_,
   and `Oberon-2`_. In the last chapter of his 1976 book `Algorithms +
   Data Structures = Programs`_, `Wirth`_ creates a top-down, descent
   parser with recovery for the `Pascal`_-like, `LL(1)`_ programming
   language `PL/0`_. The structure of the program is that of a `PEG`_
   parser, though the concept of `PEG`_ wasn't formalized until 2004.
-  **Bryan Ford** `introduced`_ `PEG`_ (parsing expression grammars) in
   2004.
-  Other parser generators like `PEG.js`_ by **David Majda** inspired
   the work in |TatSu|.
-  **William Thompson** inspired the use of context managers with his
   `blog post`_ that I knew about through the invaluable `Python
   Weekly`_ newsletter, curated by **Rahul Chaudhary**
-  **Jeff Knupp** explains why |TatSu|'s use of `exceptions`_ is
   sound, so I don't have to.
-  **Terence Parr** created `ANTLR`_, probably the most solid and
   professional parser generator out there. *Ter*, *ANTLR*, and the
   folks on the *ANLTR* forums helped me shape my ideas about |TatSu|.
-  **JavaCC** (originally `Jack`_) looks like an abandoned project. It
   was the first parser generator I used while teaching.
-  |TatSu| is very fast. But dealing with millions of lines of legacy
   source code in a matter of minutes would be impossible without
   `PyPy`_, the work of **Armin Rigo** and the `PyPy team`_.
-  **Guido van Rossum** created and has lead the development of the
   `Python`_ programming environment for over a decade. A tool like
   |TatSu|, at under 10K lines of code, would not have been
   possible without `Python`_.
-  **Kota Mizushima** welcomed me to the `CSAIL at MIT`_ `PEG and
   Packrat parsing mailing list`_, and immediately offered ideas and
   pointed me to documentation about the implementation of *cut* in
   modern parsers. The optimization of memoization information in
   |TatSu| is thanks to one of his papers.
-  **My students** at `UCAB`_ inspired me to think about how
   grammar-based parser generation could be made more approachable.
-  **Gustavo Lau** was my professor of *Language Theory* at `USB`_, and
   he was kind enough to be my tutor in a thesis project on programming
   languages that was more than I could chew. My peers, and then
   teaching advisers **Alberto Torres**, and **Enzo Chiariotti** formed
   a team with **Gustavo** to challenge us with programming languages
   like *LATORTA* and term exams that went well into the eight hours.
   And, of course, there was also the *pirate patch* that should be worn
   on the left or right eye depending on the *LL* or *LR* challenge.
-  **Manuel Rey** led me through another, unfinished, thesis project
   that taught me about what languages (spoken languages in general, and
   programming languages in particular) are about. I learned why
   languages use `declensions`_, and why, although the underlying words
   are in `English`_, the structure of the programs we write is more
   like `Japanese`_.
-  `Marcus Brinkmann`_ has kindly submitted patches that have resolved
   obscure bugs in |TatSu|'s implementation, and that have made the
   tool more user-friendly, specially for newcomers to parsing and
   translation.
-  `Robert Speer`_ cleaned up the nonsense in trying to have Unicode
   handling be compatible with 2.7.x and 3.x, and figured out the
   canonical way of honoring escape sequences in grammar tokens without
   throwing off the encoding.
-  `Basel Shishani`_ has been an incredibly throrough peer-reviewer of
   |TatSu|.
-  `Paul Sargent`_ implemented `Warth et al`_'s algorithm for supporting
   direct and indirect left recursion in `PEG`_ parsers.
-  `Kathryn Long`_ proposed better support for UNICODE in the treatment
   of whitespace and regular expressions (patterns) in general. Her
   other contributions have made |TatSu| more congruent, and more
   user-friendly.
-  `David Röthlisberger`_ provided the definitive patch that allows the
   use of `Python`_ keywords as rule names.
-  `Nicolas Laurent`_ researched, designed, implemented, and published the left recursion algorithm used in |TatSu|.
-  `Vic Nightfall`_  designed and coded an implementation of left recursion that handles all the use cases of interest (see the `Left Recursion`_ topic for details). He was gentle enough to kindly take over management of the |TatSu| project since 2019.

.. _Left Recursion:  left_recursion.html

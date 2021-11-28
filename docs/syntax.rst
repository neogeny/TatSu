.. include:: links.rst

Grammar Syntax
--------------

|TatSu| uses a variant of the standard `EBNF`_ syntax. Syntax
definitions for `VIM`_ and for `Sublime Text`_ can be found under the
``etc/vim`` and ``etc/sublime`` directories in the source code
distribution.

Rules
~~~~~

A grammar consists of a sequence of one or more rules of the form:

.. code::

    name = <expre> ;

If a *name* collides with a `Python`_ keyword, an underscore (``_``)
will be appended to it on the generated parser.

Rule names that start with an uppercase character:

.. code::

    FRAGMENT = /[a-z]+/ ;

*do not* advance over whitespace before beginning to parse. This feature
becomes handy when defining complex lexical elements, as it allows
breaking them into several rules.

The parser returns an `AST`_ value for each rule depending on what was
parsed:

-  A single value
-  A list of `AST`_
-  A dict-like object for rules with named elements
-  An object, when ModelBuilderSemantics is used
-  None

See the `Abstract Syntax Trees`_ and `Building Models`_ sections for more
details.

.. _Abstract Syntax Trees: ast.html
.. _Building Models: models.html

Expressions
~~~~~~~~~~~

The expressions, in reverse order of operator precedence, can be:


``# comment``
^^^^^^^^^^^^^
    `Python`_-style comments are allowed.


``e1 | e2``
^^^^^^^^^^^
    Choice. Match either ``e1`` or ``e2``.

    A `|` be be used before the first option if desired:

.. code::

        choices
            =
            | e1
            | e2
            | e3
            ;


``e1 e2``
^^^^^^^^^
    Sequence. Match ``e1`` and then match ``e2``.


``( e )``
^^^^^^^^^
    Grouping. Match ``e``. For example: ``('a' | 'b')``.


``[ e ]``
^^^^^^^^^
    Optionally match ``e``.


``{ e }`` or ``{ e }*``
^^^^^^^^^^^^^^^^^^^^^^^
    closure. Match ``e`` zero or more times. The `AST`_ returned for a closure is always a ``list``.


``{ e }+``
^^^^^^^^^^
    Positive closure. Match ``e`` one or more times. The `AST`_ is always a ``list``.


``{}``
^^^^^^
    Empty closure. Match nothing and produce an empty ``list`` as `AST`_.


``~``
^^^^^
    The *cut* expression. Commit to the current option and prevent other options from being considered even if what follows fails to parse.

    In this example, other options won't be considered if a
    parenthesis is parsed:

.. code::

        atom
            =
              '(' ~ @:expre ')'
            | int
            | bool
            ;


``s%{ e }+``
^^^^^^^^^^^^
    Positive join. Inspired by `Python`_'s ``str.join()``, it parses the same as this expression:

.. code::

        e {s ~ e}
..

    yet the result is a single list of the form:

.. code::

        [e, s, e, s, e....]

..

    Use grouping if `s` is more complex than a *token* or a *pattern*:

.. code::

        (s t)%{ e }+


``s%{ e }`` or ``s%{ e }*``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
    Join. Parses the list of ``s``-separated expressions, or the empty closure.

    It is equivalent to:

.. code::

        s%{e}+|{}


``op<{ e }+``
^^^^^^^^^^^^^
    Left join. Like the *join expression*, but the result is a left-associative tree built with ``tuple()``, in wich the first element is the separator (``op``), and the other two elements are the operands.

    The expression:

.. code::

        '+'<{/\d+/}+

..

    Will parse this input:

.. code:: python

        1 + 2 + 3 + 4

..

    To this tree:

.. code:: python

        (
            '+',
            (
                '+',
                (
                    '+',
                    '1',
                    '2'
                ),
                '3'
            ),
            '4'
        )


``op>{ e }+``
^^^^^^^^^^^^^
    Right join. Like the *join expression*, but the result is a right-associative tree built with ``tuple()``, in wich the first element is the separator (``op``), and the other two elements are the operands.

    The expression:

.. code::

        '+'>{/\d+/}+
..

    Will parse this input:

.. code:: python

        1 + 2 + 3 + 4
..

    To this tree:

.. code:: python

        (
            '+',
            '1',
            (
                '+',
                '2',
                (
                    '+',
                    '3',
                    '4'
                )
            )
        )


``s.{ e }+``
^^^^^^^^^^^^
    Positive *gather*. Like *positive join*, but the separator is not included in the resulting `AST <https://en.wikipedia.org/wiki/Abstract_syntax_tree>`__.


``s.{ e }`` or ``s.{ e }*``
^^^^^^^^^^^^^^^^^^^^^^^^^^^
    *Gather*. Like the *join*, but the separator is not included in the resulting `AST <https://en.wikipedia.org/wiki/Abstract_syntax_tree>`__.

    It is equivalent to:

.. code::

        s.{e}+|{}


``&e``
^^^^^^
    Positive lookahead. Succeed if ``e`` can be parsed, but do not consume any input.


``!e``
^^^^^^
    Negative lookahead. Fail if ``e`` can be parsed, and do not consume any input.


``'text'`` or ``"text"``
^^^^^^^^^^^^^^^^^^^^^^^^
    Match the token *text* within the quotation marks.

    Note that if *text* is alphanumeric, then |TatSu| will check
    that the character following the token is not alphanumeric. This
    is done to prevent tokens like *IN* matching when the text ahead
    is *INITIALIZE*. This feature can be turned off by passing
    ``nameguard=False`` to the ``Parser`` or the ``Buffer``, or by using a
    pattern expression (see below) instead of a token expression.
    Alternatively, the ``@@nameguard`` or ``@@namechars`` directives may
    be specified in the grammar:

.. code::

        @@nameguard :: False
..

    or to specify additional characters that should also be considered
    part of names:

.. code::

        @@namechars :: '$-.'


``r'text'`` or ``r"text"``
^^^^^^^^^^^^^^^^^^^^^^^^^^
    Match the token *text* within the quotation marks, interpreting *text* like `Python`_'s `raw string literal`_\ s.


``?"regexp"`` or ``?'regexp'`` or ``/regexp/``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    The *pattern* expression. Match the `Python`_ regular expression ``regexp`` at the current text position. Unlike other expressions, this one does not advance over whitespace or comments. For that, place the ``regexp`` as the only term in its own rule.

    The *regex* is interpreted as a Python_'s `raw string literal`_ and passed with ``regexp.MULTILINE | regexp.UNICODE`` options to the Python_ re_ module (or to regex_, if available), using ``match()`` at the current position in the text. The matched text is the AST_ for the expression.

    Consecutive patterns are concatenated to form a single one.

``/./``
^^^^^^^
    The *any* expression, matches the next position in the input. It works exactly like the ``?'.'`` pattern, but is implemented at the lexical level, without regular expressions.


``->e``
^^^^^^^
    The "*skip to*" expression; useful for writing *recovery* rules.

    The parser will advance over input, one character at time, until ``e`` matches. Whitespace and comments will be skipped at each step. Advancing over input is done efficiently, with no regular expressions are involved.

    The expression is equivalent to:

.. code::

    { !e /./ } e
..

    A common form of the expression is ``->&e``, which is equivalent to:

.. code::

    { !e /./ } &e
..

    This is an example of the use of the "*skip to*" expression for recovery:


.. code::

        statement =
            | if_statement
            # ...
            ;

        if_statement
            =
            | 'if' condition 'then' statement ['else' statement]
            | 'if' statement_recovery
            ;

        statement_recovery = ->&statement ;
..


```constant```
^^^^^^^^^^^^^^
    Match nothing, but behave as if ``constant`` had been parsed.

    Constants can be used to inject elements into the concrete and
    abstract syntax trees, perhaps avoiding having to write a
    semantic action. For example:

.. code::

        boolean_option = name ['=' (boolean|`true`) ] ;

``rulename``
^^^^^^^^^^^^
    Invoke the rule named ``rulename``. To help with lexical aspects of grammars, rules with names that begin with an uppercase letter will not advance the input over whitespace or comments.


``>rulename``
^^^^^^^^^^^^^
    The include operator. Include the *right hand side* of rule ``rulename`` at this point.

    The following set of declarations:

.. code::

        includable = exp1 ;

        expanded = exp0 >includable exp2 ;
..

    Has the same effect as defining *expanded* as:

.. code::

        expanded = exp0 exp1 exp2 ;
..

    Note that the included rule must be defined before the rule that
    includes it.


``()``
^^^^^^
    The empty expression. Succeed without advancing over input. Its value is ``None``.


``!()``
^^^^^^^
    The *fail* expression. This is actually ``!`` applied to ``()``, which always fails.


``name:e``
^^^^^^^^^^
    Add the result of ``e`` to the `AST`_ using ``name`` as key. If ``name`` collides with any attribute or method of ``dict``, or is a `Python`_ keyword, an underscore (``_``) will be appended to the name.

    When there are no named items in a rule, the `AST`_ consists of the
    elements parsed by the rule, either a single item or a ``list``. This
    default behavior makes it easier to write simple rules:

.. code::

        number = /[0-9]+/ ;

    Without having to write:

.. code::

        number = number:/[0-9]+/ ;

    When a rule has named elements, the unnamed ones are excluded from the
    `AST`_ (they are ignored).


``name+:e``
^^^^^^^^^^^
    Add the result of ``e`` to the `AST`_ using ``name`` as key. Force the entry to be a ``list`` even if only one element is added. Collisions with ``dict`` attributes or `Python`_ keywords are resolved by appending an underscore to ``name``.


``@:e``
^^^^^^^
    The override operator. Make the `AST`_ for the complete rule be the `AST`_ for ``e``.

    The override operator is useful to recover only part of the right
    hand side of a rule without the need to name it, or add a
    semantic action.

    This is a typical use of the override operator:

.. code::

        subexp = '(' @:expre ')' ;
..

    The [AST][Abstract Syntax Tree] returned for the ``subexp`` rule
    will be the [AST][Abstract Syntax Tree] recovered from invoking
    `expre`.


``@+:e``
^^^^^^^^
    Like ``@:e``, but make the `AST`_ always be a ``list``.

    This operator is convenient in cases such as:

.. code::

        arglist = '(' @+:arg {',' @+:arg}* ')' ;
..

    In which the delimiting tokens are of no interest.


``$``
^^^^^
    The *end of text* symbol. Verify that the end of the input text has been reached.

..
    Deprecated Expressions
    ~~~~~~~~~~~~~~~~~~~~~~

..
    The following expressions are still recognized in grammars, but they are
    considered deprecated, and will be removed in a future version of
    |TatSu|.

..
    ``?/regexp/?``
    ^^^^^^^^^^^^^^
        Another form of the pattern expression that can be used when there are slashes (``/``) in the pattern. Use the ``?"regexp"`` or ``?'regexp'`` forms instead.


..
    ``+?"regexp"`` or ``+?'regexp'`` or ``+/regexp/``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        Concatenate the given pattern with the preceding one.


..
    ``(* comment *)``
    ^^^^^^^^^^^^^^^^^^^^^^^
        Comments may appear anywhere in the text. Use the `Python`_-style comments instead.


Rules with Arguments
~~~~~~~~~~~~~~~~~~~~

|TatSu| allows rules to specify `Python`_-style arguments:

.. code::

    addition(Add, op='+')
        =
        addend '+' addend
        ;

The arguments values are fixed at grammar-compilation time.

An alternative syntax is available if no *keyword parameters* are
required:

.. code::

    addition::Add, '+'
        =
        addend '+' addend
        ;

Semantic methods must be ready to receive any arguments declared in the
corresponding rule:

.. code:: python

    def addition(self, ast, name, op=None):
        ...

When working with rule arguments, it is good to define a ``_default()``
method that is ready to take any combination of standard and keyword
arguments:

.. code:: python

    def _default(self, ast, *args, **kwargs):
        ...

Based Rules
~~~~~~~~~~~

Rules may extend previously defined rules using the ``<`` operator. The
*base rule* must be defined previously in the grammar.

The following set of declarations:

.. code::

    base::Param = exp1 ;

    extended < base = exp2 ;

Has the same effect as defining *extended* as:

.. code::

    extended::Param = exp1 exp2 ;

Parameters from the *base rule* are copied to the new rule if the new
rule doesn't define its own. Repeated inheritance should be possible,
but it *hasn't been tested*.


Memoization
~~~~~~~~~~~

|TatSu| is a packrat parser. The result of parsing a rule at a given position in the input is
cached, so the next time the parser visits the same input position with the same rule the same
result is returned and the input advanced, without repeating the parsing. Memoization allows for
grammars that are clearer and easier to write because there's no fear that repeating
subexpressions will impact performance.

There are rules that should not be memoized. For example, rules that may succeed or not depending on the associated semantic action should not be memoized if sucess depends on more than just the input.

The ``@nomemo`` decorator turns off memoization for a particular rule:

.. code::

    @nomemo
    INDENT = () ;

    @nomemo
    DEDENT = () ;


Rule Overrides
~~~~~~~~~~~~~~

A grammar rule may be redefined by using the ``@override`` decorator:

.. code::

    start = ab $;

    ab = 'xyz' ;

    @override
    ab = @:'a' {@:'b'} ;

When combined with the ``#include`` directive, rule overrides can be
used to create a modified grammar without altering the original.

Grammar Name
~~~~~~~~~~~~

The prefix to be used in classes generated by |TatSu| can be passed to
the command-line tool using the ``-m`` option:

.. code:: bash

    $ tatsu -m MyLanguage mygrammar.ebnf

will generate:

.. code:: python

    class MyLanguageParser(Parser):
        ...

The name can also be specified within the grammar using the
``@@grammar`` directive:

.. code::

    @@grammar :: MyLanguage

Whitespace
~~~~~~~~~~

By default, |TatSu| generated parsers skip the usual whitespace
characters with the regular expression ``r'\s+'`` using the
``re.UNICODE`` flag (or with the ``Pattern_White_Space`` property if the
`regex`_ module is available), but you can change that behavior by
passing a ``whitespace`` parameter to your parser.

For example, the following will skip over *tab* (``\t``) and *space*
characters, but not so with other typical whitespace characters such as
*newline* (``\n``):

.. code:: python

    parser = MyParser(text, whitespace='\t ')

The character string is converted into a regular expression character
set before starting to parse.

You can also provide a regular expression directly instead of a string.
The following is equivalent to the above example:

.. code:: python

    parser = MyParser(text, whitespace=re.compile(r'[\t ]+'))

Note that the regular expression must be pre-compiled to let |TatSu|
distinguish it from plain string.

If you do not define any whitespace characters, then you will have to
handle whitespace in your grammar rules (as it's often done in `PEG`_
parsers):

.. code:: python

    parser = MyParser(text, whitespace='')

Whitespace may also be specified within the grammar using the
``@@whitespace`` directive, although any of the above methods will
overwrite the setting in the grammar:

.. code::

    @@whitespace :: /[\t ]+/

Case Sensitivity
~~~~~~~~~~~~~~~~

If the source language is case insensitive, it can be specified in the
parser by using the ``ignorecase`` parameter:

.. code:: python

    parser = MyParser(text, ignorecase=True)

You may also specify case insensitivity within the grammar using the
``@@ignorecase`` directive:

.. code::

    @@ignorecase :: True

The change will affect token matching, but not pattern matching. Use `(?i)`
in patterns that should ignore case.

Comments
~~~~~~~~

Parsers will skip over comments specified as a regular expression using
the ``comments_re`` parameter:

.. code:: python

    parser = MyParser(text, comments_re="\(\*.*?\*\)")

For more complex comment handling, you can override the
``Buffer.eat_comments()`` method.

For flexibility, it is possible to specify a pattern for end-of-line
comments separately:

.. code:: python

    parser = MyParser(
        text,
        comments_re="\(\*.*?\*\)",
        eol_comments_re="#.*?$"
    )

Both patterns may also be specified within a grammar using the
``@@comments`` and ``@@eol_comments`` directives:

.. code::

    @@comments :: /\(\*.*?\*\)/
    @@eol_comments :: /#.*?$/

Reserved Words and Keywords
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some languages must reserve the use of certain tokens as valid
identifiers because the tokens are used to mark particular constructs in
the language. Those reserved tokens are known as `Reserved Words`_ or
`Keywords`_

|TatSu| provides support for preventing the use of `keywords`_ as
identifiers though the ``@@ keyword`` directive,and the ``@ name``
decorator.

A grammar may specify reserved tokens providing a list of them in one or
more ``@@ keyword`` directives:

.. code::

    @@keyword :: if endif
    @@keyword :: else elseif

The ``@ name`` decorator checks that the result of a grammar rule does
not match a token defined as a `keyword`_:

.. code::

    @name
    identifier = /(?!\d)\w+/ ;

There are situations in which a token is reserved only in a very
specific context. In those cases, a negative lookahead will prevent the
use of the token:

.. code::

    statements = {!'END' statement}+ ;

Include Directive
~~~~~~~~~~~~~~~~~

|TatSu| grammars support file inclusion through the include directive:

.. code::

    #include :: "filename"

The resolution of the *filename* is relative to the directory/folder of
the source. Absolute paths and ``../`` navigations are honored.

The functionality required for implementing includes is available to all
|TatSu|-generated parsers through the ``Buffer`` class; see the
``EBNFBuffer`` class in the ``tatsu.parser`` module for an example.


Left Recursion
~~~~~~~~~~~~~~

|TatSu| supports left recursion in `PEG`_
grammars. The algorithm used is `Warth et al`_'s.

Sometimes, while debugging a grammar, it is useful to turn
left-recursion support on or off:

.. code:: python

    parser = MyParser(
        text,
        left_recursion=True,
    )

Left recursion can also be turned off from within the grammar using the
``@@left_recursion`` directive:

.. code::

    @@left_recursion :: False

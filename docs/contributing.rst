.. include:: links.rst

Contributing
------------

The source code for |TatSu| is posted to it's repository_ on Github. Bug reports, patches,
suggestions, and improvements are welcome.

.. _repository : https://github.com/neogeny/TatSu

If you want to contribute to the development of |TatSu|, follow the
instructions below to create an environment in which |TatSu| can
be tested.

Programing |TatSu|
~~~~~~~~~~~~~~~~~~

prerequisites
^^^^^^^^^^^^^
Before creating an environment for |TatSu| these must be available:

* Python >= 3.12 (use your preferred way of installing it)
* uv_ as project environment manager (see the `uv installation instructions`_).
* make_ to execute the predefined development, testing, and packaging tasks.

.. _uv installation instructions: https://docs.astral.sh/uv/getting-started/installation/

There is support for ``Makefile``'s in several console environments, and also in
popular IDEs lie PyCharm_ and VSCode_. If you don't want to use make_ you can
still read the actiions in the ``Makefile`` and execute them manually.

bootstrap
^^^^^^^^^

Clone the |TatSu| repository and switch to the created directory:

.. code:: bash

    $ git clone git@github.com:neogeny/TatSu.git
    $ cd tatsu

There will be at least these directores under the main project directory:

* **./tatsu/** the top level package for the project
* **./tests/** unit and integration tests
* **./grammar/** grammars used by the project
* **./docs/** the Sphinxs_ documentation
* **./examples/** sample projects
* **./etc/** various configuration file templates


.. code:: console

    .
    ├── docs
    │   └── _static
    │       ├── css
    │       └── images
    ├── etc
    │   ├── sublime
    │   └── vim
    │       ├── ftdetect
    │       └── syntax
    ├── examples
    │   ├── calc
    │   │   └── grammars
    │   └── g2e
    │       └── grammar
    ├── grammar
    ├── media
    ├── scripts
    ├── tatsu
    │   ├── codegen
    │   ├── collections
    │   ├── g2e
    │   ├── mixins
    │   ├── ngcodegen
    │   └── util
    └── tests
        ├── grammar
        └── zzz_bootstrap

environment
^^^^^^^^^^^

Use uv_ to create and configure a Python_ environment with the libraries required
for development and testing:

.. code:: bash

    $ uv sync

testing
^^^^^^^

The ``Makefile`` defines the running of all static analysis, typing, and unit tests
as the default:

.. code:: bash

    $ make
    uv run ruff check -q --preview --fix tatsu tests examples
    uv run ty check --exclude parsers
    All checks passed!
    uv run mypy --install-types --exclude dist --exclude parsers .
    Success: no issues found in 82 source files
    cd docs; uv run make -s html > /dev/null
    find . -name "__pycache__" -delete
    rm -rf tatsu.egg-info dist build .tox
    cd examples/g2e; uv run make -s clean test > /dev/null
    cd examples/g2e; uv run make -s clean > /dev/null
    cd examples/calc; uv run make -s clean test > /dev/null
    uv run pytest --cov -v
    ============================= test session starts ================
    platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
    rootdir: /Users/apalala/art/tatsu
    configfile: pyproject.toml
    testpaths: tests
    plugins: anyio-4.12.1, xdist-3.8.0, rerunfailures-16.1, cov-7.0.0
    collected 144 items
    |
    tests/ast_test.py ......                                     [  4%]
    tests/buffering_test.py .......                              [  9%]
    tests/codegen_test.py .                                      [  9%]
    tests/diagram_test.py .                                      [ 10%]
    tests/grammar/alerts_test.py .                               [ 11%]
    tests/grammar/constants_test.py ....                         [ 13%]
    tests/grammar/defines_test.py ...                            [ 15%]
    tests/grammar/directive_test.py ..........                   [ 22%]
    tests/grammar/error_test.py ..                               [ 24%]
    tests/grammar/firstfollow_test.py ...                        [ 26%]
    tests/grammar/join_test.py ........                          [ 31%]
    tests/grammar/keyword_test.py ........                       [ 37%]
    ...
    tests/walker_test.py ..                                                  [ 99%]
    tests/zzz_bootstrap/bootstrap_test.py .                                  [100%]

    ================================ tests coverage ================================
    _______________ coverage: platform darwin, python 3.14.2 _______________

    Name                                    Stmts   Miss  Cover
    -----------------------------------------------------------
    tatsu/__init__.py                           4      0   100%
    tatsu/_config.py                            2      0   100%
    ...
    tests/grammar/pattern_test.py              41      1    98%
    tests/grammar/pretty_test.py               19      0   100%
    tests/grammar/semantics_test.py            64      1    98%
    tests/grammar/stateful_test.py             41      0   100%
    tests/grammar/syntax_test.py              190      1    99%
    tests/misc_test.py                          7      0   100%
    tests/model_test.py                        30      0   100%
    tests/parser_equivalence_test.py           77      0   100%
    tests/parsing_test.py                      84      3    96%
    tests/pickle_test.py                       22      0   100%
    tests/walker_test.py                       29      0   100%
    tests/zzz_bootstrap/__init__.py             0      0   100%
    tests/zzz_bootstrap/bootstrap_test.py     106      4    96%
    -----------------------------------------------------------
    TOTAL                                    6654   1012    85%
    ======================= 142 passed, 2 skipped in 16.91s ========================



Sponsorship
~~~~~~~~~~~

| |sponsor|
| |paypal|

If you'd like to contribute to the future development of |TatSu|,
please `make a donation`_ to the project.

Among the planned new features a unified intermediate model for parsing and
translating programming languages.

.. |sponsor| image:: https://img.shields.io/badge/Sponsor-EA4AAA?label=TatSu
    :target: https://github.com/sponsors/neogeny

.. |paypal| image:: https://img.shields.io/badge/Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white&label=TatSu
    :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=2TW56SV6WNJV6
    :height: 20

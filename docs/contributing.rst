.. Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
.. SPDX-License-Identifier: BSD-4-Clause

.. include:: links.rst

Contributing
------------

The source code for |TatSu| is posted to it's repository_ on Github. Bug reports, patches,
suggestions, and improvements are welcome.

.. _repository : https://github.com/neogeny/TatSu

If you want to contribute to the development of |TatSu|, follow the
instructions below to create an environment in which |TatSu| can
be tested.

Programming |TatSu|
~~~~~~~~~~~~~~~~~~~

prerequisites
^^^^^^^^^^^^^
Before creating an environment for |TatSu| these must be available:

* Python >= 3.12 (use your preferred way of installing it)
* uv_ as project environment manager (see the `uv installation instructions`_).
* optional installation of Invoke_ on the system's ``python3``

.. _uv installation instructions: https://docs.astral.sh/uv/getting-started/installation/

|TatSu| relies on Invoke_'s ``tasks.py`` to run the tasks for static analysis,
testing, building, documentation, and publishing the project. ``tasks.py`` resides
in ``./tatsu/tasks.py`` and there is a symbolic link to it at the project's repository
root, ``./tasks.py``.

To run the tasks use:

.. code:: bash

    $ uv run inv

Or fun ``inv`` directly if it's installed on the system's ``python3``:

.. code:: bash

    $ inv

bootstrap
^^^^^^^^^

Clone the |TatSu| repository and switch to the created directory:

.. code:: bash

    $ git clone git@github.com:neogeny/TatSu.git
    $ cd tatsu

There will be at least these directories under the main project directory:

* **./tatsu/** the top level package for the project
* **./tests/** unit and integration tests
* **./grammar/** grammars used by the project
* **./docs/** the Sphinx_ documentation
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

The ``tasks.py`` runs all static analysis (linting), typing, unit test,
documentation, and build tasks by default.
as the default:

.. code:: bash

    $ uv run inv
    ────────────────────────────────
    -> clean
    -> ruff
    -> ty
    -> pyright
    ──── ✅ lint ────────────────────
    -> pytest
    ──── ✅ test ────────────────────
    -> docs
    ──── ✅ docs ────────────────────
    -> examples/g2e
    -> examples/calc
    ──── ✅ examples ────────────────
    -> build
    ──── ✅ build ───────────────────
    -> requirements.txt
    -> requirements-dev.txt
    -> requirements-test.txt
    -> requirements-doc.txt
    ──── ✅ requirements ────────────
    ──── ✨ complete! ───────────────


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

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

There will be these directores under the project directory:

* **./tatsu**, the top level package for the project

environment
^^^^^^^^^^^

Use uv_ to create and load the Python environment with the libraries used
for development and testing:

.. code:: bash

    $ uv sync

testing
^^^^^^^

The ``Makefile`` defines running or static analysis, typing, and unit tests
as the default:

.. code:: bash

    $ make


Donations
~~~~~~~~~

|donate|

If you'd like to contribute to the future development of |TatSu|,
please `make a donation`_ to the project.

Some of the planned new features are: grammar expressions for left
and right associativity, new algorithms for left-recursion, a
unified intermediate model for parsing and translating programming
languages, and more...

.. |donate| image:: _static/images/btn_donate_SM.gif
   :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=2TW56SV6WNJV6

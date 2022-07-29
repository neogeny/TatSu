"""Tatsu code generation integration into setuptools."""

import os
import logging

from setuptools.errors import SetupError
from setuptools.extension import Extension
from setuptools.command.build_ext import _build_ext

import tatsu.parser
import tatsu.codegen.python


class Parser(Extension):
    pass


def error(msg):
    raise SetupError(msg)


def parser(dist, attr, value):
    assert attr == 'tatsu_parsers'

    if dist.ext_modules is None:
        dist.ext_modules = []

    for spec in value:
        if not isinstance(spec, str):
            error('argument to tatsu_parsers= must be a list of strings')
        try:
            grammar, module = spec.split(':')
        except ValueError:
            error('arguments to tatsu_parser= must be in the form "path/to/grammar.ebnf:module.name"')
        dist.ext_modules.append(Parser(module, [grammar]))

    build_ext_base = dist.cmdclass.get('build_ext', _build_ext)

    class build_ext(build_ext_base):
        def run(self):
            get_package_dir = self.get_finalized_command('build_py').get_package_dir
            extensions = []
            for ext in self.extensions:  # pylint: disable=access-member-before-definition
                if not isinstance(ext, Parser):
                    extensions.append(ext)
                grammar = ext.sources[0]
                path = ext.name.split('.')
                package = '.'.join(path[:-1])
                filename = os.path.join(get_package_dir(package), path[-1] + '.py')
                if not self.inplace:
                    filename = os.path.join(self.build_lib, filename)
                logging.info('generating TatSu parser %s from grammar %s', filename, grammar)
                generate_parser(grammar, filename)
            self.extensions = extensions
            super().run()

    dist.cmdclass['build_ext'] = build_ext


def generate_parser(grammar, filename):
    with open(grammar, 'r', encoding='utf8') as fd:
        src = fd.read()
    model = tatsu.parser.GrammarGenerator().parse(src)
    code = tatsu.codegen.python.codegen(model)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf8') as fd:
        fd.write(code)

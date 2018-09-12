# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import inspect

from datetime import datetime
from collections import namedtuple

from tatsu.util import (
    compress_seq,
    indent,
    re,
    safe_name,
)
from tatsu.objectmodel import Node
from tatsu.objectmodel import BASE_CLASS_TOKEN
from tatsu.exceptions import CodegenError
from tatsu.rendering import Renderer
from tatsu.codegen.cgbase import ModelRenderer, CodeGenerator
from tatsu.util import PY33


NODE_NAME_PATTERN = r'(?!\d)\w+(' + BASE_CLASS_TOKEN + r'(?!\d)\w+)*'


TypeSpec = namedtuple('TypeSpec', ['class_name', 'base'])

DEFAULT_BASE_TYPE = '''\
class ModelBase(Node):
    pass\
'''


def codegen(model, base_type=None):
    return ObjectModelCodeGenerator().render(model, base_type=base_type)


def _get_node_class_name(rule):
    if not rule.params:
        return None

    typespec = rule.params[0]
    if not re.match(NODE_NAME_PATTERN, typespec):
        return None
    if not typespec[0].isupper():
        return None
    return typespec


def _typespec(rule, default_base=True):
    if not _get_node_class_name(rule):
        return TypeSpec(None, None)

    spec = rule.params[0].split(BASE_CLASS_TOKEN)
    class_name = safe_name(spec[0])
    base = None
    bases = spec[1:]
    if bases:
        base = safe_name(bases[0])
    elif default_base:
        base = 'ModelBase'
    return TypeSpec(class_name, base)


def _get_full_name(cls):
    if not inspect.isclass(cls):
        raise CodegenError("Base type has to be a class")
    module = inspect.getmodule(cls)
    if not module:
        raise CodegenError("Base type has to be inside a module")
    modulename = module.__name__

    if PY33:
        name = cls.__qualname__
    else:
        name = cls.__name__

    # Try to reference the class
    try:
        idents = name.split('.')
        _cls = getattr(module, idents[0])
        for ident in idents[1:]:
            _cls = getattr(_cls, ident)

        assert _cls == cls
    except AttributeError:
        raise CodegenError("Couldn't find base type, it has to be importable")

    return modulename, name


class BaseTypeRenderer(Renderer):
    def __init__(self, base_type):
        self.base_type = base_type

    def render_fields(self, fields):
        module, name = _get_full_name(self.base_type)
        if '.' in name:
            lookup = "\nModelBase = %s" % name
            name = name.split('.')[0]
        else:
            lookup = " as ModelBase"

        fields.update(
            module=module,
            name=name,
            lookup=lookup
        )

    template = '''
        from {module} import {name} {lookup}\
        '''


class BaseClassRenderer(Renderer):
    def __init__(self, class_name):
        self.class_name = class_name

    template = '''
        class {class_name}(ModelBase):
            pass
        '''


class ObjectModelCodeGenerator(CodeGenerator):
    def _find_renderer_class(self, item):
        if not isinstance(item, Node):
            return None

        name = item.__class__.__name__
        renderer = globals().get(name)
        if not renderer or not issubclass(renderer, ModelRenderer):
            raise CodegenError('Renderer for %s not found' % name)
        return renderer


class Rule(ModelRenderer):
    def render_fields(self, fields):
        defs = [safe_name(d) for d, l in compress_seq(self.defines())]
        defs = list(sorted(set(defs)))

        kwargs = '\n'.join('%s = None' % d for d in defs)
        if kwargs:
            kwargs = indent(kwargs)
        else:
            kwargs = indent('pass')

        spec = _typespec(self.node)

        fields.update(
            class_name=spec.class_name,
            base=spec.base,
            kwargs=kwargs,
        )

    template = '''
        class {class_name}({base}):
        {kwargs}\
        '''


class Grammar(ModelRenderer):
    def render_fields(self, fields):
        node_class_names = set()

        bases = []
        model_rules = []
        for rule in self.node.rules:
            spec = _typespec(rule, False)
            if not spec.class_name:
                continue
            if spec.class_name not in node_class_names:
                model_rules.append(rule)
            if spec.base and spec.base not in node_class_names:
                bases.append(spec.base)
            node_class_names.add(spec.class_name)
            node_class_names.add(spec.base)

        base_class_declarations = [
            BaseClassRenderer(base).render()
            for base in bases
        ]

        model_class_declarations = [
            self.get_renderer(rule).render()
            for rule in model_rules
        ]

        base_class_declarations = '\n\n\n'.join(base_class_declarations)
        if base_class_declarations:
            base_class_declarations += '\n\n'
        model_class_declarations = '\n\n\n'.join(model_class_declarations)

        version = datetime.now().strftime('%Y.%m.%d.%H')

        base_type = fields["base_type"]

        fields.update(
            base_class_declarations=base_class_declarations,
            model_class_declarations=model_class_declarations,
            version=version,
            base_type=BaseTypeRenderer(base_type).render() if base_type else DEFAULT_BASE_TYPE
        )

    template = '''\
                #!/usr/bin/env python
                # -*- coding: utf-8 -*-

                # CAVEAT UTILITOR
                #
                # This file was automatically generated by TatSu.
                #
                #    https://pypi.python.org/pypi/tatsu/
                #
                # Any changes you make to it will be overwritten the next time
                # the file is generated.

                from __future__ import print_function, division, absolute_import, unicode_literals

                from tatsu.objectmodel import Node
                from tatsu.semantics import ModelBuilderSemantics


                {base_type}


                class {name}ModelBuilderSemantics(ModelBuilderSemantics):
                    def __init__(self, context=None, types=None):
                        types = [
                            t for t in globals().values()
                            if type(t) is type and issubclass(t, ModelBase)
                        ] + (types or [])
                        super({name}ModelBuilderSemantics, self).__init__(context=context, types=types)


                {base_class_declarations}{model_class_declarations}
                '''

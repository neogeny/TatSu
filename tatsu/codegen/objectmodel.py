import inspect
from collections import namedtuple
from datetime import datetime

from tatsu.util import compress_seq, indent, re, safe_name

from ..codegen.cgbase import CodeGenerator, ModelRenderer
from ..exceptions import CodegenError
from ..objectmodel import BASE_CLASS_TOKEN, Node
from ..rendering import Renderer

NODE_NAME_PATTERN = r'(?!\d)\w+(' + rf'{BASE_CLASS_TOKEN}' + r'(?!\d)\w+)*'


TypeSpec = namedtuple('TypeSpec', ['class_name', 'base'])

DEFAULT_BASE_TYPE = """
@dataclass(eq=False)
class ModelBase(Node):
    pass
"""


def codegen(model, base_type=None):
    return ObjectModelCodeGenerator().render(model, base_type=base_type)


def _get_node_class_name(rule):
    if not rule.params:
        return None

    typespec = rule.params[0]
    if not isinstance(typespec, str):
        return None
    if not re.match(NODE_NAME_PATTERN, typespec):
        return None
    if not typespec[0].isupper():
        return None
    return typespec


def _typespec(rule):
    if not _get_node_class_name(rule):
        return []

    spec = rule.params[0].split(BASE_CLASS_TOKEN)
    class_names = [safe_name(n) for n in spec] + ['ModelBase']

    typespec = []
    for i, class_name in enumerate(class_names[:-1]):
        base = class_names[i + 1]
        typespec.append(TypeSpec(class_name, base))

    return typespec


def _get_full_name(cls):
    if not inspect.isclass(cls):
        raise CodegenError('Base type has to be a class')
    module = inspect.getmodule(cls)
    if not module:
        raise CodegenError('Base type has to be inside a module')
    modulename = module.__name__

    name = cls.__qualname__

    # Try to reference the class
    try:
        idents = name.split('.')
        cls_ = getattr(module, idents[0])
        for ident in idents[1:]:
            cls_ = getattr(cls_, ident)

        assert cls_ == cls
    except AttributeError as e:
        raise CodegenError(
            "Couldn't find base type, it has to be importable",
        ) from e

    return modulename, name


class BaseTypeRenderer(Renderer):
    def __init__(self, base_type):
        super().__init__()
        self.base_type = base_type

    def render_fields(self, fields):
        module, name = _get_full_name(self.base_type)
        if '.' in name:
            lookup = f'\nModelBase = {name}'
            name = name.split('.')[0]
        else:
            lookup = ' as ModelBase'

        fields.update(module=module, name=name, lookup=lookup)

    template = """
        from {module} import {name}{lookup}\
        """


class BaseClassRenderer(Renderer):
    def __init__(self, spec):
        super().__init__()
        self.class_name = spec.class_name
        self.base = spec.base

    template = """
        @dataclass(eq=False)
        class {class_name}({base}):
            pass\
        """


class ObjectModelCodeGenerator(CodeGenerator):
    def _find_renderer_class(self, node):
        if not isinstance(node, Node):
            return None

        name = node.__class__.__name__
        renderer = globals().get(name)
        if not renderer or not issubclass(renderer, ModelRenderer):
            raise CodegenError(f'Renderer for {name} not found')
        return renderer


class Rule(ModelRenderer):
    def render_fields(self, fields):
        defs = [safe_name(d) for d, _ in compress_seq(self.defines())]
        defs = sorted(set(defs))
        spec = fields['spec']

        kwargs = '\n'.join(f'{d}: Any = None' for d in defs)
        kwargs = indent(kwargs) if kwargs else indent('pass')

        fields.update(
            class_name=spec.class_name, base=spec.base, kwargs=kwargs,
        )

    template = """
        @dataclass(eq=False)
        class {class_name}({base}):
        {kwargs}\
        """


class Grammar(ModelRenderer):
    def render_fields(self, fields):
        node_class_names = set()

        bases = []
        model_rules = []
        for rule in self.node.rules:
            specs = _typespec(rule)
            if not specs:
                continue

            node_spec = specs[0]
            base_spec = reversed(specs[1:])

            if node_spec.class_name not in node_class_names:
                model_rules.append((rule, node_spec))

            bases.extend(
                base
                for base in base_spec
                if base.class_name not in node_class_names
            )

            node_class_names.update(s.class_name for s in specs)

        base_class_declarations = [
            BaseClassRenderer(spec).render() for spec in bases
        ]

        model_class_declarations = [
            self.get_renderer(rule).render(spec=spec)
            for rule, spec in model_rules
        ]

        base_class_declarations = '\n\n\n'.join(base_class_declarations)
        if base_class_declarations:
            base_class_declarations += '\n\n'
        model_class_declarations = '\n\n\n'.join(model_class_declarations)

        version = datetime.now().strftime('%Y.%m.%d.%H')

        base_type = fields['base_type']

        fields.update(
            name=self.node.name,
            base_class_declarations=base_class_declarations,
            model_class_declarations=model_class_declarations,
            version=version,
            base_type=BaseTypeRenderer(base_type).render()
            if base_type
            else DEFAULT_BASE_TYPE,
        )

    template = """\
                #!/usr/bin/env python

                # CAVEAT UTILITOR
                #
                # This file was automatically generated by TatSu.
                #
                #    https://pypi.python.org/pypi/tatsu/
                #
                # Any changes you make to it will be overwritten the next time
                # the file is generated.

                from __future__ import annotations

                from typing import Any
                from dataclasses import dataclass

                from tatsu.objectmodel import Node
                from tatsu.semantics import ModelBuilderSemantics

                {base_type}

                class {name}ModelBuilderSemantics(ModelBuilderSemantics):
                    def __init__(self, context=None, types=None):
                        types = [
                            t for t in globals().values()
                            if type(t) is type and issubclass(t, ModelBase)
                        ] + (types or [])
                        super().__init__(context=context, types=types)

                {base_class_declarations}
                {model_class_declarations}
                """

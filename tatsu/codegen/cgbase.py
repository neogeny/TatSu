from __future__ import annotations

from ..exceptions import CodegenError
from ..objectmodel import Node
from ..rendering import Renderer, RenderingFormatter, render

__all__ = [
    'DelegatingRenderingFormatter',
    'ModelRenderer',
    'NullModelRenderer',
    'CodeGenerator',
]


class DelegatingRenderingFormatter(RenderingFormatter):
    def __init__(self, delegate):
        assert hasattr(delegate, 'render')
        super().__init__()
        self.delegate = delegate

    # override
    def render(self, item, join='', **fields):
        result = self.delegate.render(item, join=join, **fields)
        if result is None:
            result = super().render(item, join=join, **fields)
        return result

    def convert_field(self, value, conversion):
        if isinstance(value, Node):
            return self.render(value)
        else:
            return super().convert_field(value, conversion)


class ModelRenderer(Renderer):
    def __init__(self, codegen, node, template=None):
        super().__init__(template=template)
        self._codegen = codegen
        self._node = node

        self.formatter = codegen.formatter

        self.__postinit__()

    def __postinit__(self):
        pass

    def __getattr__(self, name):
        try:
            super().__getattr__(name)
        except AttributeError:
            if name.startswith('_'):
                raise
            return getattr(self.node, name)

    @property
    def node(self):
        return self._node

    @property
    def codegen(self):
        return self._codegen

    @property
    def context(self):
        return self._codegen

    def get_renderer(self, item):
        return self.codegen.get_renderer(item)

    def render(self, **fields):
        template = fields.pop('template', None)
        if isinstance(self.node, Node):
            fields.update(
                {
                    k: v
                    for k, v in vars(self.node).items()
                    if not k.startswith('_')
                },
            )
        else:
            fields.update(value=self.node)
        return super().render(template=template, **fields)


class NullModelRenderer(ModelRenderer):
    """A `ModelRenderer` that generates nothing."""

    template = ''


class CodeGenerator:
    """
    A **CodeGenerator** is an abstract class that finds a
    ``ModelRenderer`` class with the same name as each model's node and
    uses it to render the node.
    """

    def __init__(self, modules=None):
        self.formatter = DelegatingRenderingFormatter(self)
        self._renderers = {}
        if modules is not None:
            self._renderers = self._find_module_renderers(modules)

    def _find_module_renderers(self, modules):
        result = {}

        for module in modules:
            for name, dtype in vars(module).items():
                if not isinstance(dtype, type):
                    continue
                if not issubclass(dtype, ModelRenderer):
                    continue
                if dtype is not ModelRenderer:
                    result[name] = dtype

        return result

    def _find_renderer_class(self, node):
        if not isinstance(node, Node):
            return None

        node_class_name = node.__class__.__name__
        classes = [node.__class__]
        while classes:
            cls = classes.pop()

            name = cls.__name__
            if name in self._renderers:
                renderer = self._renderers[name]
                self._renderers[node_class_name] = renderer
                return renderer

            for base in cls.__bases__:
                if base not in classes:
                    classes.append(base)

        raise CodegenError(f'Renderer for {node_class_name} not found')

    def get_renderer(self, item):
        if not isinstance(item, Node):
            return None

        renderer_class = self._find_renderer_class(item)
        if renderer_class is None:
            raise CodegenError(
                f'Renderer not found for {type(item).__name__}',
            )
        try:
            assert issubclass(renderer_class, ModelRenderer)
            return renderer_class(self, item)
        except Exception as e:
            raise type(e)(str(e), renderer_class.__name__) from e

    def render(self, item, join='', **fields):
        renderer = self.get_renderer(item)
        if renderer is None:
            return render(item, join=join, **fields)
        return str(renderer.render(**fields))

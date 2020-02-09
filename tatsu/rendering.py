# -*- coding: utf-8 -*-
"""
The Renderer class provides the infrastructure for generating template-based
code. It's used by the .grammars module for parser generation.
"""
from __future__ import generator_stop

import itertools
import string

from tatsu.util import indent, isiter, strtype, trim, ustr
from typing import Optional, Dict, Any


def render(item, join='', **fields):
    """ Render the given item
    """
    if item is None:
        return ''
    elif isinstance(item, str):
        return item
    elif isinstance(item, Renderer):
        return item.render(join=join, **fields)
    elif isiter(item):
        return join.join(render(e, **fields) for e in iter(item) if e is not None)
    elif isinstance(item, (int, float)):
        return item
    else:
        return str(item)


class RenderingFormatter(string.Formatter):
    """ Default formatter class for use with `Renderer`
        This class is responsible for the special formatting described
        in :doc:`models`
    """
    def render(self, item, join='', **fields):
        return render(item, join=join, **fields)

    def format_field(self, value, format_spec):
        if ':' not in format_spec:
            return super().format_field(
                self.render(value),
                format_spec
            )

        ind, sep, fmt = format_spec.split(':')
        if sep == '\\n':
            sep = '\n'

        if not ind:
            ind = 0
            mult = 0
        elif '*' in ind:
            ind, mult = ind.split('*')
        else:
            mult = 4
        ind = int(ind)
        mult = int(mult)

        if not fmt:
            fmt = '%s'

        if isiter(value):
            return indent(sep.join(fmt % self.render(v) for v in value), ind, mult)
        else:
            return indent(fmt % self.render(value), ind, mult)


class Renderer(object):
    """ Renders the fileds in the current object using a template
        provided statically, on the constructor, or as a parameter
        to render().

        Fields with a leading underscore are not made available to
        the template. Additional fields may be made available by
        overriding render_fields().
    """
    template = '{__class__}'
    _counter = itertools.count()
    _formatter = RenderingFormatter()

    def __init__(self, template=None):
        if template is not None:
            self.template = template

    @classmethod
    def counter(cls) -> int:
        """ Simple counter. Every call increases it by one.
        """
        return next(cls._counter)

    @classmethod
    def reset_counter(cls):
        Renderer._counter = itertools.count()

    @property
    def formatter(self) -> RenderingFormatter:
        return self._formatter

    @formatter.setter
    def formatter(self, value: RenderingFormatter):
        self._formatter = value

    def rend(self, item, join: str = '', **fields) -> str:
        """ A shortcut for self._formatter.render()
        """
        return self._formatter.render(item, join=join, **fields)

    def indent(self, item, ind=1, multiplier=4) -> str:
        return indent(self.rend(item), indent=ind)

    def trim(self, item, tabwidth: int = 4) -> str:
        return trim(self.rend(item), tabwidth=tabwidth)

    def render_fields(self, fields: Dict[str, Any]) -> Optional[str]:
        """ Pre-render fields before rendering the template.

            :return: An optional string to be used instead of `template`
        """
        return

    def render(self, **fields):
        template = fields.pop('template', None)
        fields.update(__class__=self.__class__.__name__)
        fields.update({k: v for k, v in vars(self).items() if not k.startswith('_')})

        override = self.render_fields(fields)
        if override is not None:
            template = override
        elif template is None:
            template = self.template

        try:
            return self._formatter.format(trim(template), **fields)
        except KeyError:
            # find the missing key
            keys = (p[1] for p in self._formatter.parse(template))
            for key in keys:
                if key and key not in fields:
                    raise KeyError(key, type(self))
            raise

    def __str__(self):
        return self.render()

    def __repr__(self):
        return str(self)

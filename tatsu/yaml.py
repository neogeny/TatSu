# -*- coding: utf-8 -*-
from __future__ import generator_stop

# This code was copied from post from coldfix in Stack Overflow:
#
#    http://stackoverflow.com/a/21912744/545637
#

import yaml
import yaml.resolver

from tatsu.ast import AST


def load(stream, loader_class=yaml.SafeLoader, object_pairs_hook=dict):

    class OrderedLoader(loader_class):
        pass

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: object_pairs_hook(loader.construct_pairs(node)))

    return yaml.load(stream, OrderedLoader)


def ast_dump(data, **kwargs):
    return yaml.dump(data, object_pairs_hook=AST, **kwargs)


def ast_load(stream, **kwargs):
    return load(stream, object_pairs_hook=AST, **kwargs)

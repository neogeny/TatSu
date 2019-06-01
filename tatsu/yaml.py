# -*- coding: utf-8 -*-
from __future__ import generator_stop

# This code was copied from post from coldfix in Stack Overflow:
#
#    http://stackoverflow.com/a/21912744/545637
#

import yaml

from tatsu.ast import AST


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=dict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)


def ast_dump(data, **kwargs):
    return yaml.dump(data, **kwargs)


def ast_load(stream, **kwargs):
    return ordered_load(stream, object_pairs_hook=AST, **kwargs)

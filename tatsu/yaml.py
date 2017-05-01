# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

# This code was copied from post from coldfix in Stack Overflow:
#
#    http://stackoverflow.com/a/21912744/545637
#

import yaml
from collections import OrderedDict

from tatsu.ast import AST


def dump(data, stream=None, dumper_class=yaml.SafeDumper, object_pairs_hook=OrderedDict, **kwds):

    class OrderedDumper(dumper_class):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items()
        )

    OrderedDumper.add_representer(OrderedDict, _dict_representer)

    return yaml.dump(
        data,
        stream,
        OrderedDumper,
        default_flow_style=False,
        **kwds
    )


def load(stream, loader_class=yaml.SafeLoader, object_pairs_hook=OrderedDict):

    class OrderedLoader(loader_class):
        pass

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: object_pairs_hook(loader.construct_pairs(node)))

    return yaml.load(stream, OrderedLoader)


def ast_dump(data, **kwargs):
    return dump(data, object_pairs_hook=AST, **kwargs)


def ast_load(stream, **kwargs):
    return load(stream, object_pairs_hook=AST, **kwargs)

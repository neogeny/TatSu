# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Unit tests for fromjson utility.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import tatsu.grammars as g
from tatsu.util.fromjson import JSONBase, fromjson
from tatsu.util.typetools import is_object


GRAMMAR_DIR = Path() / 'grammar'


def load(name: str) -> dict:
    return json.loads((GRAMMAR_DIR / name).read_text())


TATSU = load('tatsu.json')
JAVA = load('java.json')
CALC = load('calc.json')


# ══════════════════════════════════════════════════════════════════════
# A. Primitives
# ══════════════════════════════════════════════════════════════════════


def test_null():
    assert fromjson(None) is None


def test_int():
    assert fromjson(42) == 42


def test_float():
    assert fromjson(3.14) == 3.14


def test_str():
    assert fromjson("hello") == "hello"


def test_bool():
    assert fromjson(True) is True
    assert fromjson(False) is False


# ══════════════════════════════════════════════════════════════════════
# B. Containers
# ══════════════════════════════════════════════════════════════════════


def test_dict_to_sns():
    r = fromjson({"a": 1})
    assert isinstance(r, SimpleNamespace)
    assert r.a == 1


def test_nested_dict():
    r = fromjson({"a": {"b": 2}})
    assert isinstance(r.a, SimpleNamespace)
    assert r.a.b == 2


def test_list():
    r = fromjson([1, 2, 3])
    assert r == [1, 2, 3]


def test_tuple_to_list():
    r = fromjson((1, 2))
    assert r == [1, 2]
    assert isinstance(r, list)


def test_class_key_stripped():
    r = fromjson({"__class__": "Foo", "x": 1})
    assert isinstance(r, SimpleNamespace)
    assert r.x == 1


def test_empty_dict():
    r = fromjson({})
    assert isinstance(r, SimpleNamespace)


def test_set_to_list():
    r = fromjson({1, 2})
    assert isinstance(r, list)
    assert sorted(r) == [1, 2]


# ══════════════════════════════════════════════════════════════════════
# C. Terminal / meta types (no meaningful or only default= fields)
# ══════════════════════════════════════════════════════════════════════


def test_eof():
    r = fromjson({"__class__": "EOF"})
    assert isinstance(r, g.EOF)


def test_void():
    r = fromjson({"__class__": "Void", "ast": "()"})
    assert isinstance(r, g.Void)


def test_cut():
    r = fromjson({"__class__": "Cut"})
    assert isinstance(r, g.Cut)


def test_nil():
    r = fromjson({"__class__": "NIL"})
    assert isinstance(r, g.NIL)


def test_empty_closure():
    r = fromjson({"__class__": "EmptyClosure"})
    assert isinstance(r, g.EmptyClosure)


def test_name_meta():
    r = fromjson({"__class__": "NameMeta"})
    assert isinstance(r, g.NameMeta)


def test_int_meta():
    r = fromjson({"__class__": "IntMeta"})
    assert isinstance(r, g.IntMeta)


def test_uint_meta():
    r = fromjson({"__class__": "UIntMeta"})
    assert isinstance(r, g.UIntMeta)


def test_float_meta():
    r = fromjson({"__class__": "FloatMeta"})
    assert isinstance(r, g.FloatMeta)


def test_bool_meta():
    r = fromjson({"__class__": "BoolMeta"})
    assert isinstance(r, g.BoolMeta)


def test_eol():
    r = fromjson({"__class__": "EOL"})
    assert isinstance(r, g.EOL)


# ══════════════════════════════════════════════════════════════════════
# D. Leaf expression types (fields use default=, pass hasattr filter)
# ══════════════════════════════════════════════════════════════════════


def test_call():
    r = fromjson({"__class__": "Call", "name": "grammar"})
    assert isinstance(r, g.Call)
    assert r.name == "grammar"


def test_token():
    r = fromjson({"__class__": "Token", "token": "@@"})
    assert isinstance(r, g.Token)
    assert r.token == "@@"


def test_constant():
    r = fromjson({"__class__": "Constant", "literal": "TATSU"})
    assert isinstance(r, g.Constant)
    assert r.literal == "TATSU"


def test_constant_null_literal():
    r = fromjson({"__class__": "Constant", "literal": None})
    assert isinstance(r, g.Constant)
    assert r.literal is None


def test_pattern():
    r = fromjson({"__class__": "Pattern", "pattern": r"\d+"})
    assert isinstance(r, g.Pattern)
    assert r.pattern == r"\d+"


def test_alert():
    r = fromjson({"__class__": "Alert", "literal": "warning", "level": 1})
    assert isinstance(r, g.Alert)
    assert r.literal == "warning"
    assert r.level == 1


# ══════════════════════════════════════════════════════════════════════
# E. Expression partials (some fields pass hasattr, exp is default_factory)
# ══════════════════════════════════════════════════════════════════════


def test_named_name_only():
    r = fromjson({"__class__": "Named", "name": "package"})
    assert isinstance(r, g.Named)
    assert r.name == "package"


def test_named_list_name_only():
    r = fromjson({"__class__": "NamedList", "name": "rules"})
    assert isinstance(r, g.NamedList)
    assert r.name == "rules"


def test_option_name_only():
    r = fromjson({"__class__": "Option", "name": "alt"})
    assert isinstance(r, g.Option)
    assert r.name == "alt"


def test_optional_name_only():
    r = fromjson({"__class__": "Optional", "name": "opt"})
    assert isinstance(r, g.Optional)
    assert r.name == "opt"


def test_closure_name_only():
    r = fromjson({"__class__": "Closure", "name": "lst"})
    assert isinstance(r, g.Closure)
    assert r.name == "lst"


def test_positive_closure_name_only():
    r = fromjson({"__class__": "PositiveClosure", "name": "lst"})
    assert isinstance(r, g.PositiveClosure)
    assert r.name == "lst"


def test_lookahead_name_only():
    r = fromjson({"__class__": "Lookahead", "name": "look"})
    assert isinstance(r, g.Lookahead)
    assert r.name == "look"


def test_negative_lookahead_name_only():
    r = fromjson({"__class__": "NegativeLookahead", "name": "nlook"})
    assert isinstance(r, g.NegativeLookahead)
    assert r.name == "nlook"


def test_group_name_only():
    r = fromjson({"__class__": "Group", "name": "grp"})
    assert isinstance(r, g.Group)
    assert r.name == "grp"


def test_skip_group_name_only():
    r = fromjson({"__class__": "SkipGroup", "name": "skp"})
    assert isinstance(r, g.SkipGroup)
    assert r.name == "skp"


def test_skip_to_name_only():
    r = fromjson({"__class__": "SkipTo", "name": "to"})
    assert isinstance(r, g.SkipTo)
    assert r.name == "to"


def test_override_name_only():
    r = fromjson({"__class__": "Override", "name": "ovr"})
    assert isinstance(r, g.Override)
    assert r.name == "ovr"


def test_override_list_name_only():
    r = fromjson({"__class__": "OverrideList", "name": "ovrl"})
    assert isinstance(r, g.OverrideList)
    assert r.name == "ovrl"


def test_join_with_name_and_sep():
    r = fromjson(
        {
            "__class__": "Join",
            "name": "joined",
            "sep": {"__class__": "Token", "token": ","},
        }
    )
    assert isinstance(r, g.Join)
    assert r.name == "joined"
    assert isinstance(r.sep, g.Token)
    assert r.sep.token == ","


def test_positive_join_with_name_and_sep():
    r = fromjson(
        {
            "__class__": "PositiveJoin",
            "name": "joined",
            "sep": {"__class__": "Token", "token": ","},
        }
    )
    assert isinstance(r, g.PositiveJoin)
    assert r.sep.token == ","


def test_gather_with_name_and_sep():
    r = fromjson(
        {
            "__class__": "Gather",
            "name": "gath",
            "sep": {"__class__": "Token", "token": ","},
        }
    )
    assert isinstance(r, g.Gather)
    assert r.sep.token == ","


def test_positive_gather_with_name_and_sep():
    r = fromjson(
        {
            "__class__": "PositiveGather",
            "name": "gath",
            "sep": {"__class__": "Token", "token": ","},
        }
    )
    assert isinstance(r, g.PositiveGather)
    assert r.sep.token == ","


def test_rule_include_name_only():
    r = fromjson({"__class__": "RuleInclude", "name": "paramdef"})
    assert isinstance(r, g.RuleInclude)
    assert r.name == "paramdef"


# ══════════════════════════════════════════════════════════════════════
# F. Rule partials (only default= fields survive)
# ══════════════════════════════════════════════════════════════════════


def test_rule_with_scalar_fields():
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "start",
            "base": None,
            "is_name": False,
            "is_tokn": True,
            "no_memo": True,
            "no_stak": False,
            "is_memo": False,
            "is_lrec": True,
        }
    )
    assert isinstance(r, g.Rule)
    assert r.name == "start"
    assert r.base is None
    assert r.is_name is False
    assert r.is_tokn is True
    assert r.no_memo is True
    assert r.no_stak is False
    assert r.is_memo is False
    assert r.is_lrec is True


def test_rule_name_from_calc():
    rule_data = {"__class__": "Rule", "name": "start"}
    r = fromjson(rule_data)
    assert r.name == "start"


def test_rule_field_defaults():
    r = fromjson({"__class__": "Rule", "name": "test"})
    assert r.name == "test"
    assert r.base is None
    assert r.is_memo is True
    assert r.is_lrec is False


# ══════════════════════════════════════════════════════════════════════
# G. Grammar partials (only default= fields survive)
# ══════════════════════════════════════════════════════════════════════


def test_grammar_name():
    r = fromjson({"__class__": "Grammar", "name": "CALC"})
    assert isinstance(r, g.Grammar)
    assert r.name == "CALC"


def test_grammar_optimized():
    r = fromjson(
        {
            "__class__": "Grammar",
            "name": "CALC",
            "_optimized": None,
        }
    )
    assert isinstance(r, g.Grammar)
    assert r.name == "CALC"
    assert r._optimized is None


# ══════════════════════════════════════════════════════════════════════
# H. Built-in grammar JSON files (partial — only hasattr-allowed fields)
# ══════════════════════════════════════════════════════════════════════


def test_calc_name():
    r = fromjson(CALC)
    assert isinstance(r, g.Grammar)
    assert r.name == "CALC"


def test_tatsu_name():
    r = fromjson(TATSU)
    assert isinstance(r, g.Grammar)
    assert r.name == "TatSu"


def test_java_name():
    r = fromjson(JAVA)
    assert isinstance(r, g.Grammar)
    assert r.name == "Java"


# ══════════════════════════════════════════════════════════════════════
# I. Roundtrip (asjson -> fromjson) for leaf and terminal types
# ══════════════════════════════════════════════════════════════════════


def test_roundtrip_call():
    original = fromjson({"__class__": "Call", "name": "something"})
    serialized = original.asjson()
    restored = fromjson(serialized)
    assert type(restored) is type(original)
    assert restored.name == original.name


def test_roundtrip_token():
    original = fromjson({"__class__": "Token", "token": "@@"})
    serialized = original.asjson()
    restored = fromjson(serialized)
    assert type(restored) is type(original)
    assert restored.token == original.token


def test_roundtrip_pattern():
    original = fromjson({"__class__": "Pattern", "pattern": r"\d+"})
    serialized = original.asjson()
    restored = fromjson(serialized)
    assert type(restored) is type(original)
    assert restored.pattern == original.pattern


def test_roundtrip_constant():
    original = fromjson({"__class__": "Constant", "literal": "TATSU"})
    serialized = original.asjson()
    restored = fromjson(serialized)
    assert type(restored) is type(original)
    assert restored.literal == original.literal


def test_roundtrip_eof():
    original = fromjson({"__class__": "EOF"})
    serialized = original.asjson()
    restored = fromjson(serialized)
    assert type(restored) is type(original)


def test_roundtrip_named_name():
    original = fromjson({"__class__": "Named", "name": "foo"})
    serialized = original.asjson()
    restored = fromjson(serialized)
    assert type(restored) is type(original)
    assert restored.name == original.name


def test_roundtrip_join_name_sep():
    original = fromjson(
        {
            "__class__": "Join",
            "name": "j",
            "sep": {"__class__": "Token", "token": ","},
        }
    )
    serialized = original.asjson()
    restored = fromjson(serialized)
    assert type(restored) is type(original)
    assert restored.name == original.name
    assert restored.sep.token == original.sep.token


def test_rule_scalar_fields():
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "test",
            "is_memo": True,
            "is_lrec": False,
        }
    )
    assert r.name == "test"
    assert r.is_memo is True
    assert r.is_lrec is False


# ══════════════════════════════════════════════════════════════════════
# J. Error / edge cases
# ══════════════════════════════════════════════════════════════════════


def test_unknown_class_becomes_sns():
    r = fromjson({"__class__": "NoSuchClass", "x": 1})
    assert isinstance(r, SimpleNamespace)
    assert r.x == 1


def test_class_non_jsonbase_becomes_sns():
    r = fromjson({"__class__": "int", "value": 42})
    assert isinstance(r, SimpleNamespace)


# @xfail
def test_extra_fields_on_leaf():
    r = fromjson({"__class__": "Call", "name": "f", "ghost": True})
    assert isinstance(r, g.Call)
    assert r.name == "f"


# @xfail
def test_extra_fields_on_terminal():
    r = fromjson({"__class__": "EOF", "extra": True})
    assert isinstance(r, g.EOF)


def test_deep_nesting_no_exp():
    r = fromjson(
        {
            "__class__": "Named",
            "name": "outer",
        }
    )
    assert isinstance(r, g.Named)
    assert r.name == "outer"


def test_deep_nesting_multiple_calls():
    r = fromjson(
        {
            "__class__": "Sequence",
        }
    )
    assert isinstance(r, g.Sequence)


# ══════════════════════════════════════════════════════════════════════
# K. JSONBase protocol (custom subclasses)
# ══════════════════════════════════════════════════════════════════════


def test_jsonbase_subclass_registration():
    from tatsu.util.fromjson import __from_json__class__

    class TestModel(JSONBase):
        value: str = "default"

    assert TestModel.__name__ in __from_json__class__
    assert __from_json__class__[TestModel.__name__] is TestModel


def test_jsonbase_roundtrip():
    from tatsu.util.fromjson import __from_json__class__

    class Point(JSONBase):
        x: int = 0
        y: int = 0

    data = {"__class__": "Point", "x": 10, "y": 20}
    p = fromjson(data)
    assert isinstance(p, Point)
    assert p.x == 10
    assert p.y == 20


def test_jsonbase_inherits_from_subclass():
    class Shape(JSONBase):
        color: str = "black"

    class Circle(Shape):
        radius: float = 1.0

    data = {"__class__": "Circle", "color": "red", "radius": 5.0}
    c = fromjson(data)
    assert isinstance(c, Circle)
    assert isinstance(c, Shape)
    assert c.color == "red"
    assert c.radius == 5.0


def test_jsonbase_partial_data():
    class Widget(JSONBase):
        name: str = ""
        size: int = 0
        visible: bool = True

    data = {"__class__": "Widget", "name": "button"}
    w = fromjson(data)
    assert w.name == "button"
    assert w.size == 0
    assert w.visible is True


# @xfail
def test_jsonbase_extra_field():
    class WithExtra(JSONBase):
        base_field: str = ""

    data = {"__class__": "WithExtra", "base_field": "a", "extra": 99}
    w = fromjson(data)
    assert w.base_field == "a"


def test_missing_class_key_sns():
    data = {"a": 1, "b": 2}
    r = fromjson(data)
    assert isinstance(r, SimpleNamespace)
    assert r.a == 1
    assert r.b == 2


def test_mixed_containers():
    data = {
        "numbers": [1, 2, 3],
        "nested": {"x": 10},
        "flag": True,
    }
    r = fromjson(data)
    assert isinstance(r, SimpleNamespace)
    assert r.numbers == [1, 2, 3]
    assert isinstance(r.nested, SimpleNamespace)
    assert r.nested.x == 10
    assert r.flag is True


# ══════════════════════════════════════════════════════════════════════
# L. Known limitations (hasattr blocks default_factory fields)
# ══════════════════════════════════════════════════════════════════════


# @xfail
def test_sequence_sequence():
    r = fromjson(
        {
            "__class__": "Sequence",
            "sequence": [{"__class__": "Call", "name": "f"}],
        }
    )
    assert r.sequence[0].name == "f"


# @xfail
def test_grammar_rules():
    r = fromjson(CALC)
    assert len(r.rules) == 9


# @xfail
def test_rule_exp():
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "start",
            "exp": {"__class__": "Call", "name": "grammar"},
        }
    )
    assert isinstance(r.exp, g.Call)


# @xfail
def test_named_exp():
    r = fromjson(
        {
            "__class__": "Named",
            "name": "expr",
            "exp": {"__class__": "Optional", "name": "opt"},
        }
    )
    assert isinstance(r.exp, g.Optional)


# @xfail
def test_choice_options():
    r = fromjson(
        {
            "__class__": "Choice",
            "options": [
                {"__class__": "Option", "name": "first"},
                {"__class__": "Option", "name": "second"},
            ],
        }
    )
    assert len(r.options) == 2


# @xfail
def test_rule_params():
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "with_params",
            "params": ["a", "b"],
        }
    )
    assert r.params == ["a", "b"]


# @xfail
def test_rule_kwparams():
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "with_kw",
            "kwparams": {"opt": "default"},
        }
    )
    assert is_object(r.kwparams)
    assert r.kwparams.opt == 'default'


# @xfail
def test_rule_decorators():
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "decorated",
            "decorators": ["override"],
        }
    )
    assert r.decorators == ["override"]


# @xfail
def test_grammar_directives():
    r = fromjson(CALC)
    assert is_object(r.directives)
    assert r.directives.grammar == 'CALC'


# @xfail
def test_grammar_keywords():
    r = fromjson(JAVA)
    assert "abstract" in r.keywords


# @xfail
def test_full_grammar_roundtrip():
    r = fromjson(CALC)
    serialized = r.asjson()
    restored = fromjson(serialized)
    assert len(restored.rules) == len(CALC["rules"])

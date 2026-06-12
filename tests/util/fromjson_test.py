# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Unit tests for fromjson utility.

All test data payloads are excerpts from grammar/*.json files.
"""

from __future__ import annotations

import json
from pathlib import Path

import tatsu.grammars as g
from tatsu.util.asjson import asjson
from tatsu.util.fromjson import JSONBase, fromjson
from tatsu.util.typetools import is_object


GRAMMAR_DIR = Path() / 'grammar'


def load(name: str) -> dict:
    return json.loads((GRAMMAR_DIR / name).read_text())


TATSU = load('tatsu.json')
JAVA = load('java.json')
CALC = load('calc.json')


def roundtrip(obj):
    return fromjson(asjson(obj))


# ══════════════════════════════════════════════════════════════════════
# A. Primitives
# ══════════════════════════════════════════════════════════════════════


def test_null() -> None:
    assert fromjson(None) is None


def test_int() -> None:
    assert fromjson(42) == 42


def test_float() -> None:
    assert fromjson(3.14) == 3.14


def test_str() -> None:
    assert fromjson("hello") == "hello"


def test_bool() -> None:
    assert fromjson(True) is True
    assert fromjson(False) is False


# ══════════════════════════════════════════════════════════════════════
# B. Containers
# ══════════════════════════════════════════════════════════════════════


def test_dict_stays_dict() -> None:
    r = fromjson({"a": 1})
    assert isinstance(r, dict)
    assert r["a"] == 1


def test_nested_dict() -> None:
    r = fromjson({"a": {"b": 2}})
    assert isinstance(r["a"], dict)
    assert r["a"]["b"] == 2


def test_list() -> None:
    r = fromjson([1, 2, 3])
    assert r == [1, 2, 3]


def test_tuple_to_list() -> None:
    r = fromjson((1, 2))
    assert r == [1, 2]
    assert isinstance(r, list)


def test_class_key_stripped() -> None:
    r = fromjson({"__class__": "ClassKeyStrippedTestOnly", "x": 1})
    assert is_object(r)
    assert r.x == 1


def test_empty_dict() -> None:
    r = fromjson({})
    assert isinstance(r, dict)
    assert r == {}


def test_set_to_list() -> None:
    r = fromjson({1, 2})
    assert isinstance(r, list)
    assert sorted(r) == [1, 2]


# ══════════════════════════════════════════════════════════════════════
# C. Terminal types (excerpts from grammar JSON)
# ══════════════════════════════════════════════════════════════════════

# EOF: {"__class__": "EOF"} — from calc.json, java.json, tatsu.json
# Cut: {"__class__": "Cut"} — from calc.json, java.json, tatsu.json
# Void: {"__class__": "Void", "ast": "()"} — from java.json
# EmptyClosure: {"__class__": "EmptyClosure", "ast": []} — from java.json


def test_eof() -> None:
    r = fromjson({"__class__": "EOF"})
    assert isinstance(r, g.EOF)


def test_cut() -> None:
    r = fromjson({"__class__": "Cut"})
    assert isinstance(r, g.Cut)


def test_void() -> None:
    r = fromjson({"__class__": "Void", "ast": "()"})
    assert isinstance(r, g.Void)


def test_empty_closure() -> None:
    r = fromjson({"__class__": "EmptyClosure", "ast": []})
    assert isinstance(r, g.EmptyClosure)


# ══════════════════════════════════════════════════════════════════════
# D. Leaf expression types (excerpts from grammar JSON)
# ══════════════════════════════════════════════════════════════════════

# Call: {"__class__": "Call", "name": "..."} — from all files
# Token: {"__class__": "Token", "token": "..."} — from all files
# Constant: {"__class__": "Constant", "literal": "..."} — from tatsu.json
# Pattern: {"__class__": "Pattern", "pattern": "..."} — from all files
# RuleInclude: {"__class__": "RuleInclude", "name": "..."} — from tatsu.json


def test_call() -> None:
    r = fromjson({"__class__": "Call", "name": "expression"})
    assert isinstance(r, g.Call)
    assert r.name == "expression"


def test_token() -> None:
    r = fromjson({"__class__": "Token", "token": ";"})
    assert isinstance(r, g.Token)
    assert r.token == ";"  # noqa: S105


def test_constant() -> None:
    r = fromjson({"__class__": "Constant", "literal": "null"})
    assert isinstance(r, g.Constant)
    assert r.literal == "null"


def test_pattern() -> None:
    r = fromjson({"__class__": "Pattern", "pattern": r"\d+"})
    assert isinstance(r, g.Pattern)
    assert r.pattern == r"\d+"


def test_rule_include() -> None:
    r = fromjson({"__class__": "RuleInclude", "name": "method_declaration_mixin"})
    assert isinstance(r, g.RuleInclude)
    assert r.name == "method_declaration_mixin"


# ══════════════════════════════════════════════════════════════════════
# E. Compound expression types (excerpts from grammar JSON)
# ══════════════════════════════════════════════════════════════════════
#
# Box subclasses (Option, Optional, Closure, etc.) have NO "name" field
# in the serialized JSON. Only Named and NamedList carry a "name".


def test_sequence() -> None:
    data = {
        "__class__": "Sequence",
        "sequence": [{"__class__": "Call", "name": "expression"}, {"__class__": "EOF"}],
    }
    r = fromjson(data)
    assert isinstance(r, g.Sequence)
    assert len(r.sequence) == 2


def test_choice() -> None:
    data = {
        "__class__": "Choice",
        "options": [
            {
                "__class__": "Option",
                "exp": {"__class__": "Call", "name": "type_declaration"},
            },
            {"__class__": "Option", "exp": {"__class__": "Token", "token": ";"}},
        ],
    }
    r = fromjson(data)
    assert isinstance(r, g.Choice)
    assert len(r.options) == 2


def test_option() -> None:
    data = {
        "__class__": "Option",
        "exp": {"__class__": "Call", "name": "type_declaration"},
    }
    r = fromjson(data)
    assert isinstance(r, g.Option)


def test_optional() -> None:
    data = {
        "__class__": "Optional",
        "exp": {"__class__": "Call", "name": "package_declaration"},
    }
    r = fromjson(data)
    assert isinstance(r, g.Optional)


def test_closure() -> None:
    data = {"__class__": "Closure", "exp": {"__class__": "Call", "name": "test"}}
    r = fromjson(data)
    assert isinstance(r, g.Closure)


def test_positive_closure() -> None:
    data = {
        "__class__": "PositiveClosure",
        "exp": {"__class__": "Call", "name": "test"},
    }
    r = fromjson(data)
    assert isinstance(r, g.PositiveClosure)


def test_lookahead() -> None:
    data = {"__class__": "Lookahead", "exp": {"__class__": "Token", "token": "}"}}
    r = fromjson(data)
    assert isinstance(r, g.Lookahead)


def test_negative_lookahead() -> None:
    data = {
        "__class__": "NegativeLookahead",
        "exp": {"__class__": "Token", "token": "}"},
    }
    r = fromjson(data)
    assert isinstance(r, g.NegativeLookahead)


def test_group() -> None:
    data = {"__class__": "Group", "exp": {"__class__": "Token", "token": "test"}}
    r = fromjson(data)
    assert isinstance(r, g.Group)


def test_override() -> None:
    data = {"__class__": "Override", "exp": {"__class__": "Call", "name": "type"}}
    r = fromjson(data)
    assert isinstance(r, g.Override)


def test_override_list() -> None:
    data = {
        "__class__": "OverrideList",
        "exp": {"__class__": "Call", "name": "enum_constant_declaration"},
    }
    r = fromjson(data)
    assert isinstance(r, g.OverrideList)


def test_gather() -> None:
    data = {
        "__class__": "Gather",
        "exp": {"__class__": "Call", "name": "type"},
        "sep": {"__class__": "Token", "token": "&"},
    }
    r = fromjson(data)
    assert isinstance(r, g.Gather)
    assert isinstance(r.sep, g.Token)
    assert r.sep.token == "&"  # noqa: S105


def test_positive_gather() -> None:
    data = {
        "__class__": "PositiveGather",
        "exp": {"__class__": "Call", "name": "type"},
        "sep": {"__class__": "Token", "token": "&"},
    }
    r = fromjson(data)
    assert isinstance(r, g.PositiveGather)
    assert isinstance(r.sep, g.Token)
    assert r.sep.token == "&"  # noqa: S105


def test_named() -> None:
    data = {
        "__class__": "Named",
        "name": "package",
        "exp": {
            "__class__": "Optional",
            "exp": {"__class__": "Call", "name": "package_declaration"},
        },
    }
    r = fromjson(data)
    assert isinstance(r, g.Named)
    assert r.name == "package"


def test_named_list() -> None:
    data = {
        "__class__": "NamedList",
        "name": "declarations",
        "exp": {"__class__": "Call", "name": "type_declaration"},
    }
    r = fromjson(data)
    assert isinstance(r, g.NamedList)
    assert r.name == "declarations"


# ══════════════════════════════════════════════════════════════════════
# F. Rule (excerpts from grammar JSON)
# ══════════════════════════════════════════════════════════════════════

# Rule from java.json / tatsu.json:
#   name, base, decorators, exp, is_lrec, is_memo, is_name, is_tokn,
#   kwparams, no_memo, no_stak, params


def test_rule() -> None:
    r = fromjson(CALC['rules'][0])
    assert isinstance(r, g.Rule)
    assert r.name == "start"


def test_rule_with_scalar_fields() -> None:
    data: dict[str, object] = {
        "__class__": "Rule",
        "name": "start",
        "base": None,
        "decorators": [],
        "exp": {"__class__": "Sequence", "sequence": []},
        "is_lrec": False,
        "is_memo": True,
        "is_name": False,
        "is_tokn": False,
        "kwparams": {},
        "no_memo": False,
        "no_stak": False,
        "params": [],
    }
    r = fromjson(data)
    assert isinstance(r, g.Rule)
    assert r.name == "start"
    assert r.base is None
    assert r.is_memo is True
    assert r.is_lrec is False
    assert r.is_name is False
    assert r.is_tokn is False


def test_rule_with_exp() -> None:
    data: dict[str, object] = {
        "__class__": "Rule",
        "name": "start",
        "base": None,
        "decorators": [],
        "exp": {
            "__class__": "Sequence",
            "sequence": [
                {"__class__": "Call", "name": "expression"},
                {"__class__": "EOF"},
            ],
        },
        "is_lrec": False,
        "is_memo": True,
        "is_name": False,
        "is_tokn": False,
        "kwparams": {},
        "no_memo": False,
        "no_stak": False,
        "params": [],
    }
    r = fromjson(data)
    assert isinstance(r.exp, g.Sequence)


# ══════════════════════════════════════════════════════════════════════
# G. Grammar (excerpts from grammar JSON)
# ══════════════════════════════════════════════════════════════════════

# Grammar from java.json / tatsu.json:
#   name, directives, keywords, rules


def test_grammar_from_calc() -> None:
    r = fromjson(CALC)
    assert isinstance(r, g.Grammar)
    assert r.name == "CALC"
    assert len(r.rules) == 9
    assert r.rules[0].name == "start"
    assert isinstance(r.directives, dict)
    assert r.directives == {"grammar": "CALC"}


def test_grammar_with_rules() -> None:
    data = {
        "__class__": "Grammar",
        "name": "CALC",
        "directives": {"grammar": "CALC"},
        "keywords": [],
        "rules": [
            {
                "__class__": "Rule",
                "name": "start",
                "base": None,
                "decorators": [],
                "exp": {"__class__": "EOF"},
                "is_lrec": False,
                "is_memo": True,
                "is_name": False,
                "is_tokn": False,
                "kwparams": {},
                "no_memo": False,
                "no_stak": False,
                "params": [],
            },
        ],
    }
    r = fromjson(data)
    assert isinstance(r, g.Grammar)
    assert r.name == "CALC"
    assert len(r.rules) == 1


# ══════════════════════════════════════════════════════════════════════
# H. Built-in grammar JSON files
# ══════════════════════════════════════════════════════════════════════


def test_calc_name() -> None:
    r = fromjson(CALC)
    assert isinstance(r, g.Grammar)
    assert r.name == "CALC"


def test_tatsu_name() -> None:
    r = fromjson(TATSU)
    assert isinstance(r, g.Grammar)
    assert r.name == "TatSu"


def test_java_name() -> None:
    r = fromjson(JAVA)
    assert isinstance(r, g.Grammar)
    assert r.name == "Java"


# ══════════════════════════════════════════════════════════════════════
# I. Roundtrip (asjson -> fromjson)
# ══════════════════════════════════════════════════════════════════════


def test_roundtrip_call() -> None:
    data = {"__class__": "Call", "name": "expression"}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.name == original.name
    assert asjson(restored) == asjson(original)


def test_roundtrip_token() -> None:
    data = {"__class__": "Token", "token": ";"}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.token == original.token
    assert asjson(restored) == asjson(original)


def test_roundtrip_constant() -> None:
    data = {"__class__": "Constant", "literal": "null"}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.literal == original.literal
    assert asjson(restored) == asjson(original)


def test_roundtrip_pattern() -> None:
    data = {"__class__": "Pattern", "pattern": r"\d+"}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.pattern == original.pattern
    assert asjson(restored) == asjson(original)


def test_roundtrip_eof() -> None:
    data = {"__class__": "EOF"}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert asjson(restored) == asjson(original)


def test_roundtrip_cut() -> None:
    data = {"__class__": "Cut"}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert asjson(restored) == asjson(original)


def test_roundtrip_void() -> None:
    data = {"__class__": "Void", "ast": "()"}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert asjson(restored) == asjson(original)


def test_roundtrip_named() -> None:
    data = {
        "__class__": "Named",
        "name": "package",
        "exp": {"__class__": "Call", "name": "package_declaration"},
    }
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.name == original.name
    assert asjson(restored) == asjson(original)


def test_roundtrip_option() -> None:
    data = {
        "__class__": "Option",
        "exp": {"__class__": "Call", "name": "type_declaration"},
    }
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert asjson(restored) == asjson(original)


def test_roundtrip_optional() -> None:
    data = {
        "__class__": "Optional",
        "exp": {"__class__": "Call", "name": "package_declaration"},
    }
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert asjson(restored) == asjson(original)


def test_roundtrip_lookahead() -> None:
    data = {"__class__": "Lookahead", "exp": {"__class__": "Token", "token": "}"}}
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert asjson(restored) == asjson(original)


def test_roundtrip_sequence() -> None:
    data = {
        "__class__": "Sequence",
        "sequence": [{"__class__": "Call", "name": "expression"}, {"__class__": "EOF"}],
    }
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert asjson(restored) == asjson(original)


def test_roundtrip_gather() -> None:
    data = {
        "__class__": "Gather",
        "exp": {"__class__": "Call", "name": "type"},
        "sep": {"__class__": "Token", "token": "&"},
    }
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.sep.token == original.sep.token
    assert asjson(restored) == asjson(original)


def test_roundtrip_rule() -> None:
    data: dict[str, object] = {
        "__class__": "Rule",
        "name": "start",
        "base": None,
        "decorators": [],
        "exp": {"__class__": "Sequence", "sequence": []},
        "is_lrec": False,
        "is_memo": True,
        "is_name": False,
        "is_tokn": False,
        "kwparams": {},
        "no_memo": False,
        "no_stak": False,
        "params": [],
    }
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.name == original.name
    assert restored.is_memo == original.is_memo
    assert asjson(restored) == asjson(original)


def test_roundtrip_grammar() -> None:
    data = {
        "__class__": "Grammar",
        "name": "CALC",
        "directives": {"grammar": "CALC"},
        "keywords": [],
        "rules": [],
    }
    original = fromjson(data)
    restored = roundtrip(original)
    assert type(restored) is type(original)
    assert restored.name == original.name
    assert asjson(restored) == asjson(original)


# ══════════════════════════════════════════════════════════════════════
# J. Error / edge cases
# ══════════════════════════════════════════════════════════════════════


def test_unknown_class_becomes_object() -> None:
    r = fromjson({"__class__": "NoSuchClass", "x": 1})
    assert is_object(r)
    assert r.x == 1


def test_class_non_jsonbase_becomes_object() -> None:
    r = fromjson({"__class__": "int", "value": 42})
    assert is_object(r)


# @xfail
def test_extra_fields_on_leaf() -> None:
    r = fromjson({"__class__": "Call", "name": "f", "ghost": True})
    assert isinstance(r, g.Call)
    assert r.name == "f"


# @xfail
def test_extra_fields_on_terminal() -> None:
    r = fromjson({"__class__": "EOF", "extra": True})
    assert isinstance(r, g.EOF)


def test_missing_class_key() -> None:
    data = {"a": 1, "b": 2}
    r = fromjson(data)
    assert isinstance(r, dict)
    assert r["a"] == 1
    assert r["b"] == 2


def test_mixed_containers() -> None:
    data = {
        "numbers": [1, 2, 3],
        "nested": {"x": 10},
        "flag": True,
    }
    r = fromjson(data)
    assert isinstance(r, dict)
    assert r["numbers"] == [1, 2, 3]
    assert isinstance(r["nested"], dict)
    assert r["nested"]["x"] == 10
    assert r["flag"] is True


# ══════════════════════════════════════════════════════════════════════
# K. JSONBase protocol (custom subclasses)
# ══════════════════════════════════════════════════════════════════════


def test_jsonbase_subclass_registration() -> None:
    from tatsu.util.fromjson import __from_json__class__

    class TestModel(JSONBase):
        value: str = "default"

    assert TestModel.__name__ in __from_json__class__
    assert __from_json__class__[TestModel.__name__] is TestModel


def test_jsonbase_roundtrip() -> None:
    class Point(JSONBase):
        x: int = 0
        y: int = 0

    data = {"__class__": "Point", "x": 10, "y": 20}
    p = fromjson(data)
    assert isinstance(p, Point)
    assert p.x == 10
    assert p.y == 20


def test_jsonbase_inherits_from_subclass() -> None:
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


def test_jsonbase_partial_data() -> None:
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
def test_jsonbase_extra_field() -> None:
    class WithExtra(JSONBase):
        def __init__(self, base_field: str = ""):
            self.base_field = base_field

    data = {"__class__": "WithExtra", "base_field": "a", "extra": 99}
    w = fromjson(data)
    assert isinstance(w, WithExtra)
    assert w.base_field == "a"


# ══════════════════════════════════════════════════════════════════════
# L. Known limitations (xfail)
# ══════════════════════════════════════════════════════════════════════


# @xfail
def test_sequence_sequence() -> None:
    r = fromjson(
        {
            "__class__": "Sequence",
            "sequence": [{"__class__": "Call", "name": "f"}],
        }
    )
    assert r.sequence[0].name == "f"


# @xfail
def test_grammar_rules() -> None:
    r = fromjson(CALC)
    assert len(r.rules) == 9


# @xfail
def test_rule_exp() -> None:
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "start",
            "exp": {"__class__": "Call", "name": "grammar"},
        }
    )
    assert isinstance(r.exp, g.Call)


# @xfail
def test_named_exp() -> None:
    r = fromjson(
        {
            "__class__": "Named",
            "name": "expr",
            "exp": {"__class__": "Optional", "name": "opt"},
        }
    )
    assert isinstance(r.exp, g.Optional)


# @xfail
def test_choice_options() -> None:
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
def test_rule_params() -> None:
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "with_params",
            "params": ["a", "b"],
        }
    )
    assert r.params == ["a", "b"]


# @xfail
def test_rule_kwparams() -> None:
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "with_kw",
            "kwparams": {"opt": "default"},
        }
    )
    assert isinstance(r.kwparams, dict)
    assert r.kwparams == {"opt": "default"}


# @xfail
def test_rule_decorators() -> None:
    r = fromjson(
        {
            "__class__": "Rule",
            "name": "decorated",
            "decorators": ["override"],
        }
    )
    assert r.decorators == ["override"]


# @xfail
def test_grammar_directives() -> None:
    r = fromjson(CALC)
    assert isinstance(r.directives, dict)
    assert r.directives == {"grammar": "CALC"}


# @xfail
def test_grammar_keywords() -> None:
    r = fromjson(JAVA)
    assert "abstract" in r.keywords


# @xfail
def test_full_grammar_roundtrip() -> None:
    r = fromjson(CALC)
    serialized = r.asjson()
    restored = fromjson(serialized)
    assert len(restored.rules) == len(CALC["rules"])

# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: MIT OR Apache-2.0

"""
json - Direct Value to Grammar translator

This module translates json directly to Grammar,
bypassing the TatSuModel deserializer which fails on modified JSON.
"""

from __future__ import annotations

import json as json_module
from typing import Any

from .. import grammars as g
from ..exceptions import TatSuException
from ..util import typename
from ..util.json import ensure_dict


class JsonError(TatSuException):
    pass


class JsonSerializationHelper:
    def __init__(self, value: Any, path: list[str] | None = None):
        self.value = value
        self.path = path if path is not None else []

    def _push(self, class_name: str) -> JsonSerializationHelper:
        new_path = [*self.path, class_name]
        return JsonSerializationHelper(self.value, new_path)

    def _error(self, msg: str) -> JsonError:
        path_str = " -> ".join(self.path)
        if not path_str:
            return JsonError(msg)
        return JsonError(f"{msg} at {path_str}")

    def _get_obj(self) -> dict[str, Any]:
        if isinstance(self.value, dict):
            return self.value
        raise self._error("Expected object")

    def _get_class(self) -> str:
        obj = self._get_obj()
        class_val = obj.get("__class__")
        if class_val is None:
            raise self._error("Missing __class__")
        if isinstance(class_val, str):
            return class_val
        raise self._error("Expected string for __class__")

    def _get_string(self, field: str) -> str:
        obj = self._get_obj()
        val = obj.get(field)
        if val is None:
            raise self._error(f"Missing field: {field}")
        if isinstance(val, str):
            return val
        raise self._error(f"Expected string for field: {field}")

    def _opt_str(self, field: str) -> str | None:
        obj = self._get_obj()
        val = obj.get(field)
        if val is None:
            return None
        if isinstance(val, str):
            return val
        return None

    def _opt_bool(self, field: str, default: bool) -> bool:
        obj = self._get_obj()
        val = obj.get(field)
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        return default

    def _opt_int(self, field: str) -> int | None:
        obj = self._get_obj()
        val = obj.get(field)
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return int(val)
        return None

    def _get_array(self, field: str) -> list[JsonSerializationHelper]:
        obj = self._get_obj()
        arr_val = obj.get(field)
        if arr_val is None:
            raise self._error(f"Missing or not array: {field}")
        if not isinstance(arr_val, list):
            raise self._error(f"Expected array for field: {field}")

        result = []
        for i, v in enumerate(arr_val):
            if isinstance(v, dict) and "__class__" in v:
                class_name = v["__class__"]  # ty: ignore
                label = f"{field}[{i}]:{class_name}"
            else:
                label = f"{field}[{i}]"
            result.append(self._push(label)._with_value(v))
        return result

    def _get_nested(self, field: str) -> JsonSerializationHelper:
        obj = self._get_obj()
        if field not in obj:
            raise self._error(f"Missing field: {field}")
        value = obj[field]

        if isinstance(value, dict) and "__class__" in value:
            class_name = value["__class__"]
            nested_path = f"{field}:{class_name}"
        else:
            nested_path = field

        return self._push(nested_path)._with_value(value)

    def _with_value(self, value: Any) -> JsonSerializationHelper:
        return JsonSerializationHelper(value, self.path)


def _parse_directives(directives: dict[str, Any] | None) -> dict[str, Any]:
    if directives is None:
        return {}

    result = {}
    for key, val in directives.items():
        if isinstance(val, str):
            result[key] = val
        elif isinstance(val, bool):
            result[key] = str(val)
        elif isinstance(val, (int, float)):
            result[key] = str(val)
        else:
            result[key] = str(val)
    return result


def loads_grammar(json_str: str) -> g.Grammar:
    """Parse JSON string and return a Grammar object."""
    value = json_module.loads(json_str)
    return load_grammar(value)


def load_grammar(value: Any) -> g.Grammar:
    """Parse JSON value and return a Grammar object."""
    value = ensure_dict(value)
    path = JsonSerializationHelper(value)
    class_name = path._get_class()

    if class_name != typename(g.Grammar):
        raise path._error(f"Expected {typename(g.Grammar)} root")

    name = path._get_string("name")

    rules_array = path._get_array("rules")
    rule_list = []
    for i, rule_path in enumerate(rules_array):
        try:
            rule = rule_from_json_path(rule_path)
            rule_list.append(rule)
        except JsonError as e:
            raise JsonError(f"rules[{i}]: {e}") from e

    directives_obj = path._get_obj().get("directives")
    if directives_obj is None:
        directives = {}
    elif isinstance(directives_obj, dict):
        directives = _parse_directives(directives_obj)
    else:
        directives = {}

    keywords: list[str] = []
    if isinstance(path._get_obj().get("keywords"), list):
        keywords = [str(k) for k in path._get_obj()["keywords"]]

    grammar = g.Grammar(rules=rule_list, name=name, directives=directives)
    if keywords:
        grammar.configure(keywords=keywords)
    return grammar


def rule_from_json_value(value: dict[str, Any]) -> g.Rule:
    """Parse JSON value (dict) and return a Rule object."""
    path = JsonSerializationHelper(value)
    return rule_from_json_path(path)


def rule_from_json_path(path: JsonSerializationHelper) -> g.Rule:
    """Parse JSON path and return a Rule object."""
    class_name = path._get_class()

    if class_name != typename(g.Rule):
        raise path._error(f"Expected {typename(g.Rule)}")

    name = path._get_string("name")
    exp_path = path._get_nested("exp")
    rhs = exp_from_json_path(exp_path)

    params: list[str] = []
    if isinstance(path._get_obj().get("params"), list):
        params = [str(p) for p in path._get_obj()["params"]]

    no_memo = path._opt_bool("no_memo", False)
    is_name = path._opt_bool("is_name", False)
    is_tokn = path._opt_bool("is_tokn", False)
    is_memo = path._opt_bool("is_memo", True)
    is_lrec = path._opt_bool("is_lrec", False)

    return g.Rule(
        name=name,
        exp=rhs,
        params=params,
        is_name=is_name,
        is_tokn=is_tokn,
        is_memo=is_memo,
        is_lrec=is_lrec,
        no_memo=no_memo,
    )


def exp_from_json_value(value: dict[str, Any]) -> g.Model:
    """Parse JSON value (dict) and return an expression Model."""
    path = JsonSerializationHelper(value)
    return exp_from_json_path(path)


def exp_from_json_path(path: JsonSerializationHelper) -> g.Model:  # noqa: PLR0912,PLR0911
    """Parse JSON path and return an expression Model."""
    class_name = path._get_class()

    if class_name == typename(g.Sequence):
        items = path._get_array("sequence")
        exprs = [exp_from_json_path(item) for item in items]
        return g.Sequence(sequence=exprs)

    if class_name == typename(g.Choice):
        items = path._get_array("options")
        exprs = [exp_from_json_path(item) for item in items]
        return g.Choice(options=[g.Option(exp=e) for e in exprs])

    if class_name == typename(g.Option):
        exp_path = path._get_nested("exp")
        return g.Option(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.Named):
        name = path._get_string("name")
        exp_path = path._get_nested("exp")
        return g.Named(name=name, exp=exp_from_json_path(exp_path))

    if class_name == typename(g.NamedList):
        name = path._get_string("name")
        exp_path = path._get_nested("exp")
        return g.NamedList(name=name, exp=exp_from_json_path(exp_path))

    if class_name == typename(g.Call):
        name = path._get_string("name")
        return g.Call(name=name)

    if class_name == typename(g.Token):
        token = path._get_string("token")
        return g.Token(token=token)

    if class_name == typename(g.Pattern):
        pattern = path._get_string("pattern")
        return g.Pattern(pattern=pattern)

    if class_name == typename(g.Constant):
        literal = path._opt_str("literal") or ""
        return g.Constant(literal=literal)

    if class_name == typename(g.Alert):
        literal = path._opt_str("literal") or ""
        level = path._opt_int("level") or 0
        return g.Alert(literal=literal, level=level)

    if class_name == typename(g.Group):
        exp_path = path._get_nested("exp")
        return g.Group(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.Optional):
        exp_path = path._get_nested("exp")
        return g.Optional(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.Closure):
        exp_path = path._get_nested("exp")
        return g.Closure(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.PositiveClosure):
        exp_path = path._get_nested("exp")
        return g.PositiveClosure(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.Lookahead):
        exp_path = path._get_nested("exp")
        return g.Lookahead(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.NegativeLookahead):
        exp_path = path._get_nested("exp")
        return g.NegativeLookahead(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.SkipGroup):
        exp_path = path._get_nested("exp")
        return g.SkipGroup(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.SkipTo):
        exp_path = path._get_nested("exp")
        return g.SkipTo(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.Override):
        exp_path = path._get_nested("exp")
        return g.Override(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.OverrideList):
        exp_path = path._get_nested("exp")
        return g.OverrideList(exp=exp_from_json_path(exp_path))

    if class_name == typename(g.Join):
        exp_path = path._get_nested("exp")
        sep_path = path._get_nested("sep")
        return g.Join(
            exp=exp_from_json_path(exp_path),
            sep=exp_from_json_path(sep_path),
        )

    if class_name == typename(g.PositiveJoin):
        exp_path = path._get_nested("exp")
        sep_path = path._get_nested("sep")
        return g.PositiveJoin(
            exp=exp_from_json_path(exp_path),
            sep=exp_from_json_path(sep_path),
        )

    if class_name == typename(g.Gather):
        exp_path = path._get_nested("exp")
        sep_path = path._get_nested("sep")
        return g.Gather(
            exp=exp_from_json_path(exp_path),
            sep=exp_from_json_path(sep_path),
        )

    if class_name == typename(g.PositiveGather):
        exp_path = path._get_nested("exp")
        sep_path = path._get_nested("sep")
        return g.PositiveGather(
            exp=exp_from_json_path(exp_path),
            sep=exp_from_json_path(sep_path),
        )

    if class_name == typename(g.RuleInclude):
        name = path._get_string("name")
        return g.RuleInclude(name=name)

    if class_name == typename(g.Void):
        return g.Void()

    if class_name == typename(g.Cut):
        return g.Cut()

    if class_name == typename(g.EOF):
        return g.EOF()

    if class_name == typename(g.EOL):
        return g.EOL()

    if class_name == typename(g.EmptyClosure):
        return g.EmptyClosure()

    raise path._error(f"Unsupported: {class_name}")

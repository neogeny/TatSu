# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Unit tests for tatsu.util.safeeval
# by Gemini (2026-01-26)
# by [apalala@gmail.com](https://github.com/apalala)
"""
from __future__ import annotations

import pytest

from tatsu.util.safeeval import SecurityError, is_eval_safe, make_hashable, safe_eval


class TestSafeEvalCore:
    """Tests for the primary safe_eval functionality."""

    def test_basic_arithmetic(self):
        assert safe_eval("2 + 2 * 10", {}) == 22

    def test_context_access(self):
        context = {"a": 5, "b": 10}
        assert safe_eval("a * b", context) == 50

    def test_is_eval_safe_boolean(self):
        assert is_eval_safe("1 + 1", {}) is True
        assert is_eval_safe("import os", {}) is False

    def test_unauthorized_name_access(self):
        # Using a name load instead of a call to trigger name access check
        with pytest.raises(SecurityError, match="Unauthorized name access"):
            safe_eval("unauthorized_variable", {})

    def test_unauthorized_function_call(self):
        # Explicitly testing the function call security check
        with pytest.raises(SecurityError, match="Unauthorized function call"):
            safe_eval("print('hello')", {})

    def test_dunder_blocking(self):
        class User:
            __private_field = "hidden_value"

        with pytest.raises(SecurityError, match="Dunder access prohibited"):
            safe_eval("u.__private_field", {"u": User()})

    def test_exception_smuggling_prevention(self):
        with pytest.raises(SecurityError, match="Exception class forbidden"):
            safe_eval("1", {"err": RuntimeError})


class TestMakeHashableMemoization:
    """
    Stress tests for the memoized DFS in make_hashable.
    Verifies O(N) complexity for redundant structures and safety for cycles.
    """

    def test_diamond_reference(self):
        """
        Tests a 'Diamond' structure where two branches point to the same object.
        """
        shared_leaf = {"key": "value"}
        context = {"branch_a": [shared_leaf], "branch_b": [shared_leaf]}

        result = make_hashable(context)

        # Verify both branches resolved the shared leaf identically
        val_a = next(v for k, v in result if k == "branch_a")[0]
        val_b = next(v for k, v in result if k == "branch_b")[0]

        assert val_a == val_b
        assert "value" in str(val_a)

    def test_recursion_cycle_detection(self):
        """Tests that a self-referencing list doesn't cause a StackOverflow."""
        circular = []
        circular.append(circular)

        result = make_hashable(circular)
        assert any("<circular_ref_" in str(item) for item in result)

    def test_complex_graph_cycle(self):
        """Tests A -> B -> C -> A cycle with multiple entry points."""
        a, b, c = {}, {}, {}
        a["next"] = b
        b["next"] = c
        c["next"] = a

        result = make_hashable({"start": a, "middle": b})
        res_str = str(result)

        assert "next" in res_str
        assert "<circular_ref_" in res_str

    def test_tuple_cycle_bridge(self):
        """
        Verifies that tuples correctly detect cycles even if technically hashable.
        """
        mutable_list = []
        t = (mutable_list,)
        mutable_list.append(t)

        result = make_hashable(t)
        assert "<circular_ref_" in str(result)


if __name__ == "__main__":
    pytest.main([__file__])

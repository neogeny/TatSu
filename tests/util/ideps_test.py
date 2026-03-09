# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path

import pytest

from tatsu.util.ideps import Dependency, ModuleImports, findeps, moduledeps, render


def test_moduledeps_collects_absolute_and_relative_imports(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    mod = pkg / "mod.py"
    mod.write_text(
        "from __future__ import annotations\n"
        "import os\n"
        "from collections import defaultdict\n"
        "from . import sibling\n"
        "from .subpkg import child\n"
        "from .. import parent\n"
        "from ..other import thing\n"
    )

    result = moduledeps("pkg.mod", mod)

    assert result.name == "pkg.mod"
    assert result.path == mod

    # `moduledeps` records imported modules/packages, not individual
    # names, and returns them sorted by name.
    assert set(result.imports) == {
        Dependency("collections", is_relative=False),
        Dependency("os", is_relative=False),
        Dependency("parent", is_relative=True),
        Dependency("other", is_relative=True),
        Dependency("pkg.sibling", is_relative=True),
        Dependency("pkg.subpkg", is_relative=True),
    }


def test_findeps_uses_module_names_from_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()

    a = pkg / "a.py"
    b = pkg / "b.py"
    a.write_text("import os\n")
    b.write_text("import sys\n")

    monkeypatch.chdir(tmp_path)

    results = findeps([Path("pkg/a.py"), Path("pkg/b.py")])

    assert [m.name for m in results] == ["pkg.a", "pkg.b"]
    # `findeps` preserves the relative paths it receives; when resolved,
    # they point to the files we created under `tmp_path`.
    assert [m.path.resolve() for m in results] == [a, b]


def test_render_builds_tree_with_internal_and_external_deps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()

    a = pkg / "a.py"
    b = pkg / "b.py"
    a.write_text(
        "from __future__ import annotations\n" "import os\n" "from . import b\n"
    )
    b.write_text("import sys\n")

    monkeypatch.chdir(tmp_path)

    results = findeps([Path("pkg/a.py"), Path("pkg/b.py")])
    tree = render(results)

    # With a single top-level package, render() returns that node directly.
    assert str(tree.label) == "pkg"

    mod_a = next(child for child in tree.children if str(child.label) == "a")
    labels = {str(child.label) for child in mod_a.children}

    # Internal sibling dependency and external import are both shown.
    assert "○ b" in labels
    assert "⟨os⟩" in labels

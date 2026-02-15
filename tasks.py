# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import shutil
from pathlib import Path

from invoke import task

# Metadata
__copyright__ = "Copyright (c) 2017-2026 Juancarlo Añez"
__license__ = "BSD-4-Clause"


def print_line(banner: str = '', add: int = 0):
    cols = shutil.get_terminal_size().columns
    if not banner:
        print("━" * cols)
    else:
        pre = 8
        print("━" * pre, banner, "━" * (cols - pre - add - len(banner) - 2))

last_python = '3.14'

def run_uv(c, cmd, group=None, python=None, **kwargs):
    """
    Helper to wrap uv execution logic.
    Passes any additional keyword arguments (like hide, warn, pty) to c.run.
    """
    global last_python

    base_cmd = "uv run"

    if python:
        last_python = python
    base_cmd += f" --python {last_python}"

    if group:
        base_cmd += f" --group {group}"

    options = {"pty": True}
    options.update(kwargs)

    return c.run(f"{base_cmd} {cmd}", **options)

def set_version(c, python: str, group:str = 'dev'):
    return
    c.run(f"uv python pin {python}", hide='both')
    c.run(f"uv sync -q --python {python} --group {group}")

@task
def version(c):
    """Show python and tatsu versions."""
    c.run("uv run python3 --version")
    c.run("uv run python3 -m tatsu --version")


@task
def clean(c, plus=False):
    """Clean up build and cache artifacts."""
    patterns = ["build", "dist", "tmp", "tatsu.egg-info", ".tox"]
    if plus:
        patterns.extend([".cache", ".pytest_cache", ".ruff_cache", ".mypy_cache"])


    for p in patterns:
        path = Path(p)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


    # Recursive pycache removal
    for p in Path(".").rglob("__pycache__"):
        shutil.rmtree(p)


@task(pre=[version])
def pytest(c):
    """Run pytest suite."""
    clean(c)
    Path("./tmp").mkdir(exist_ok=True)
    Path("./tmp/__init__.py").touch()
    print("-> pytest")
    run_uv(c, "pytest --quiet tests/", group="test")


@task
def ruff(c):
    """Run ruff linting."""
    print("-> ruff")
    run_uv(c, "ruff check -q --preview --fix tatsu tests examples", group="test")


@task
def pyright(c):
    """Run pyright (basedpyright) checks."""
    print("-> pyright")
    run_uv(c, "basedpyright tatsu tests examples", group="test", hide='stdout')


@task
def ty(c):
    """Run ty check and only show output if it fails."""
    print("-> ty")

    # hide='both' stops it from printing to the screen immediately
    # warn=True prevents the script from exiting on a non-zero return code
    res = run_uv(c, "ty check tatsu tests examples", group="test", hide='both', warn=True)

    # If it failed (return code != 0) or doesn't contain the success string
    if res.exited != 0 or "All checks passed!" not in res.stdout:
        # Print the captured stdout/stderr
        if res.stdout.strip():
            print(res.stdout)
        if res.stderr.strip():
            print(res.stderr)


@task(pre=[ruff, ty, pyright])
def lint(c):
    """Run all linters."""
    pass


@task(pre=[lint, pytest])
def test(c):
    """Run all tests and linters."""
    pass


@task
def docs(c):
    """Build sphinx documentation."""
    run_uv(c, "make -s html", group="doc") # Assumes Makefile in /docs or adjust to cd


@task
def build(c):
    """Build package using hatch via uvx."""
    clean(c)
    print("-> build")
    c.run("uvx hatch build")


def run_version(c, ver):
    print_line(f"🐍 Testing Python {ver}", add=1)
    set_version(c, python=ver, group="test")
    version(c)
    run_uv(c, "inv lint", group="test", python=ver)
    # c.run(f"uv run -q --python {ver} --group test inv lint", pty=True)

@task
def py312(c):
    """Run tests on Python 3.12"""
    run_version(c, "3.12")

@task
def py313(c):
    """Run tests on Python 3.13"""
    run_version(c, "3.13")

@task
def py314(c):
    """Run tests on Python 3.14"""
    run_version(c, "3.14")

@task
def py315(c):
    """Run tests on Python 3.15"""
    run_version(c, "3.15")

# 3. Update the main matrix task to use the individuals as dependencies
@task(pre=[py312, py313, py314, py315])
def matrix(c):
    """Run the full multi-version test matrix."""
    print_line("✅ matrix check complete.")


@task
def requirements(c):
    """Export uv.lock to various requirements.txt files."""
    req_map = {
        "requirements.txt": "--no-group dev",
        "requirements-dev.txt": "--dev",
        "requirements-test.txt": "--group test --no-group dev",
        "requirements-doc.txt": "--group doc --no-group dev",
    }
    for file, flags in req_map.items():
        print(f"-> {file}")
        c.run(f"uv export -q --format requirements-txt --no-hashes {flags} > {file}")


@task(pre=[build])
def publish(c, dry_run=True):
    """Run CI workflow via gh CLI."""
    c.run("uv tool install -q gh")
    workflow = "test_publish.yml" if dry_run else "publish.yml"
    c.run(f"gh workflow run {workflow}")
    c.run(f"gh run list --workflow={workflow}")


@task
def g2e(c):
    """Run tests for the g2e example."""
    print("-> examples/g2e")
    # c.cd is a context manager; it handles the 'cd' and 'back' automatically
    with c.cd("examples/g2e"):
        # We use warn=True so one example failure doesn't necessarily
        # kill the entire suite if you don't want it to.
        c.run("uv run make -s clean test", pty=True)
        c.run("uv run make -s clean", pty=True)


@task
def calc(c):
    """Run tests for the calc example."""
    print("-> examples/calc")
    with c.cd("examples/calc"):
        c.run("uv run make -s clean test", pty=True)


@task(pre=[clean, g2e, calc])
def examples(c):
    """Run all example projects tests."""
    pass


@task(pre=[test, docs, examples, build, requirements], default=True)
def all(c):
    """Run all essential tasks: test, docs, examples, build, and requirements."""
    print_line()
    print("✨ All targets completed successfully! ✨")


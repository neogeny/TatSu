# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import math
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from invoke import (  # pyright: ignore[reportMissingImports, reportPrivateImportUsage]
    Context,  # pyright: ignore[reportMissingImports, reportPrivateImportUsage]
    Result,  # pyright: ignore[reportMissingImports, reportPrivateImportUsage]
    Task,  # pyright: ignore[reportMissingImports, reportPrivateImportUsage]
    task,  # pyright: ignore[reportMissingImports, reportPrivateImportUsage]
)

__copyright__: str = 'Copyright (c) 2017-2026 Juancarlo Añez'
__license__: str = 'BSD-4-Clause'

# by Gemini 2026-02-15
# Defeat `ruff --fix` replacing `3.14` with `math.pi`
# and breaking havock on `uv run --python PYTHON`
# Fun using ord of the hidden STX char for '2'
# PYTHON: float = float(f'{math.pi:.{ord('')}f}')
# PYTHON: float = round(math.pi, 2)
PYTHON: float = round(3.15, 2)

LINE_PRE: int = 4
THIN_LINE: str = '─'
THICK_LINE: str = '━'

type TaskFun = Task | Callable[[Context], Result | None] | None


def uv_python_pin(c: Context) -> float:
    result = c.run('uv python pin', pty=True, hide='both')
    if result is None:
        return PYTHON
    return float(result.stdout.strip())


def uv(
    c: Context,
    cmd: str,
    args: str | list[str],
    *,
    quiet: bool = True,
    python: float = PYTHON,
    group: str = 'dev',
    nogroup: str = '',
    **kwargs: Any,
) -> Result:
    uvpython = uv_python_pin(c)
    q = ' --quiet' if quiet else ''
    p = f' --python {python!s}' if python and python != uvpython else ''
    g = f' --group {group}' if group else ''
    n = f' --no-group {nogroup}' if nogroup else ''

    options = kwargs
    args = ' '.join(args) if isinstance(args, list) else args
    return c.run(f'uv {cmd}{q}{p}{g}{n} {args}', **options) or Result()


def uv_run(
    c: Context,
    args: str | list[str],
    *,
    python: float = PYTHON,
    group: str = 'dev',
    quiet: bool = True,
    **kwargs: Any,
) -> Result:
    return uv(c, 'run', args=args, python=python, group=group, quiet=quiet, **kwargs)


def uv_sync(c: Context):
    uv_run(c, 'sync', group='dev', quiet=True)


def version_python(c: Context, python: float = PYTHON) -> str:
    return uv_run(
        c,
        'python3 --version',
        python=python,
        quiet=True,
        hide='both',
    ).stdout.strip()


def version_tatsu(c: Context, python: float = PYTHON) -> str:
    return uv_run(
        c,
        'python3 -m tatsu --version',
        python=python,
        quiet=True,
        hide='both',
    ).stdout.strip()


def boundary_print(banner: str = '', line: str = THIN_LINE):
    cols = shutil.get_terminal_size().columns
    if not banner:
        print(line * cols)
    else:
        pre = LINE_PRE
        add = sum(ord(c) >= 256 for c in banner)
        print(line * pre, banner, line * (cols - 2 - pre - add - len(banner)))


def start_print(task_: TaskFun = None, target: str = ''):
    taskstr = task_.name if task_ else ''  # type: ignore
    print(f'▶ {target}{taskstr}')


def success_print(
    target: str = '',
    *,
    task_: TaskFun = None,
    line: str = THIN_LINE,
    icon: str = '⏏',
):
    taskstr = task_.name if task_ else ''  # type: ignore
    targetstr = ' ' + target if target else ''
    boundary_print(f'{icon} {taskstr}{targetstr}', line=line)


def version_boundary_print(
    c: Context,
    target: str = '',
    python: float = PYTHON,
    line: str = THICK_LINE,
):
    verpython = version_python(c, python=python)
    vertatsu = version_tatsu(c, python=python)
    boundary_print(f'{target} {verpython} {vertatsu}', line=line)


@task
def begin(_c: Context):
    boundary_print()


@task(pre=[begin])
def clean(_c: Context, plus: bool = False):
    start_print(clean)
    patterns = ['build', 'dist', 'tatsu.egg-info', '.tox']
    if plus:
        patterns.extend(['.cache', '.pytest_cache', '.ruff_cache'])

    for pat in patterns:
        path = Path(pat)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    for p in Path().rglob('__pycache__'):
        shutil.rmtree(p)


@task(pre=[clean])
def clobber(_c: Context, _plus: bool = False):
    pass


@task(pre=[begin])
def ruff(c: Context, python: float = PYTHON):
    start_print(ruff)
    uv_run(
        c,
        'ruff check -q --preview tatsu tests examples',
        python=python,
        group='test',
    )


@task(pre=[begin])
def ty(c: Context, python: float = PYTHON):
    start_print(ty)
    res = uv_run(
        c,
        'ty check tatsu tests examples',
        python=python,
        group='test',
        warn=True,
        hide='both',
    )

    if res.exited != 0 or 'All checks passed!' not in res.stdout:
        for r in [res.stdout, res.stderr]:
            if r.strip():
                print(r)


@task(pre=[begin])
def mypy(c: Context, python: float = PYTHON):
    start_print(mypy)
    res = uv_run(
        c,
        [
            'mypy',
            'tatsu',
            'tests',
            'examples',
            '--install-types',
            '--exclude dist',
            '--exclude parsers',
            '--exclude backup',
        ],
        python=python,
        group='test',
        pty=True,
        hide='both',
    )
    if res.exited != 0 or 'Success' not in res.stdout:
        for r in [res.stdout, res.stderr]:
            if r.strip():
                print(r)


@task(pre=[begin])
def pyright(c: Context, python: float = PYTHON):
    start_print(pyright)
    uv_run(
        c,
        'basedpyright tatsu tests examples',
        python=python,
        group='test',
        pty=True,
        hide='both',
    )


@task(pre=[begin])
def pytestfast(c: Context, python: float = PYTHON):
    start_print(pytest, target='fast ')
    Path('./tmp').mkdir(exist_ok=True)
    Path('./tmp/__init__.py').touch()
    uv_run(
        c,
        [
            'pytest',
            '--quiet',
            '-n auto',
            'tests/',
            '--ignore-glob=tests/z*',
        ],
        python=python,
        group='test',
        hide='stdout',
        pty=True,
    )


@task(pre=[begin])
def pytestbootstrap(c: Context, python: float = PYTHON):
    start_print(pytest, target='boot ')
    Path('./tmp').mkdir(exist_ok=True)
    Path('./tmp/__init__.py').touch()
    uv_run(
        c,
        [
            'pytest',
            '--quiet',
            'tests/z_bootstrap_test.py',
        ],
        python=python,
        group='test',
        hide='stdout',
        pty=True,
    )


@task(pre=[begin, pytestfast, pytestbootstrap])
def pytest(_c: Context, _python: float = PYTHON):
    pass


@task(pre=[begin])
def black(c: Context, python: float = PYTHON):
    start_print(black)
    res = uv_run(
        c,
        ["black", "tatsu", "tests", "examples"],
        python=python,
        group='test',
        warn=True,
        hide=True,
        pty=True,
    )
    if res.exited != 0:
        print(res.stdout.splitlines()[-1])
        print('✖ failed!')


@task(pre=[begin, black, ruff, ty, mypy, pyright])
def lint(_c: Context):
    success_print(task_=lint)


@task(pre=[begin, lint, pytest])
def test(_c: Context):
    success_print(task_=test)


@task(pre=[begin])
def doclint(c: Context, _python: float = PYTHON):
    start_print(doclint)
    uv_run(
        c,
        'vale README.rst docs/**/*.rst',
        group='doc',
        hide='stdout',
        pty=True,
    )


@task(pre=[begin, doclint])
def docs(c: Context):
    start_print(docs)
    with c.cd('docs'):
        uv_run(c, 'make -s html', quiet=True, group='doc', hide='stdout')
    success_print(task_=docs)


@task(pre=[clean])
def build(c: Context):
    start_print(build)
    c.run('uvx hatch build', hide='both')
    success_print(task_=build)


def matrix_core(c: Context, python: float = PYTHON):
    version_boundary_print(c, target='ᝰ', python=python)

    ruff(c, python=python)
    ty(c, python=python)
    pyright(c, python=python)

    pytestfast(c, python=python)
    pytestbootstrap(c, python=python)

    success_print(str(python), icon='✓')


@task
def py312(c: Context):
    matrix_core(c, python=3.12)
    uv_sync(c)


@task
def py313(c: Context):
    matrix_core(c, python=3.13)
    uv_sync(c)


@task
def py314(c: Context):
    matrix_core(c, python=round(math.pi, 2))
    uv_sync(c)


@task
def py315(c: Context):
    matrix_core(c, python=3.15)
    uv_sync(c)


@task(pre=[py312, py313, py314, py315])
def matrix(c: Context):
    uv_sync(c)
    success_print(task_=matrix, line=THICK_LINE)


def _export_requirements(c: Context, filename: str, group: str = '', nogroup: str = ''):
    out_file = Path(filename)
    start_print(target=str(out_file))

    # note:
    #   We use pty=True here to ensure the shell redirection behaves
    #   and we see the output immediately if there's an error.
    uv(
        c,
        'export',
        f'--no-hashes --format requirements-txt -o {out_file}',
        group=group,
        nogroup=nogroup,
        quiet=True,
        pty=True,
    )


@task
def req_base(c: Context):
    _export_requirements(c, 'requirements.txt', nogroup='dev')


@task
def req_dev(c: Context):
    _export_requirements(c, 'requirements-dev.txt', group='dev')


@task
def req_test(c: Context):
    _export_requirements(c, 'requirements-test.txt', group='test', nogroup='dev')


@task
def req_doc(c: Context):
    _export_requirements(c, 'requirements-doc.txt', group='doc', nogroup='dev')


@task(pre=[begin, req_base, req_dev, req_test, req_doc])
def requirements(_c: Context):
    success_print(task_=requirements)


@task(pre=[requirements])
def reqs(_c: Context):
    pass


@task(pre=[build])
def testpublish(c: Context):
    start_print(target='test publish')
    workflow = 'test_publish.yml'
    c.run(f'gh workflow run {workflow}')
    c.run(f'gh run list --workflow={workflow}')


@task(pre=[build])
def publish(c: Context, _dry_run: bool = True):
    start_print(publish)
    workflow = 'publish.yml'
    c.run(f'gh workflow run {workflow}')
    c.run(f'gh run list --workflow={workflow}')


@task
def g2e(c: Context):
    start_print(g2e, target='examples/')
    with c.cd('examples/g2e'):
        c.run('uv run make -s clean test', pty=True, hide='both')
        c.run('uv run make -s clean', pty=True, hide='both')


@task
def calc(c: Context):
    start_print(calc, target='examples/')
    with c.cd('examples/calc'):
        c.run('uv run make -s clean test', pty=True, hide='both')


@task(pre=[clean, begin, calc])
def examples(_c: Context):
    success_print(task_=examples)


@task(pre=[test, docs, examples, build, requirements], default=True)
def default(c: Context):
    uv_sync(c)
    boundary_print('✔ all')

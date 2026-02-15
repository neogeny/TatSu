# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import math
import shutil
from pathlib import Path

from invoke import (
    task,  # pyright: ignore[reportMissingImports, reportPrivateImportUsage]
)

__copyright__ = 'Copyright (c) 2017-2026 Juancarlo Añez'
__license__ = 'BSD-4-Clause'


# by Gemini 2026-02-15
# Defeat `ruff --fix` replacing `3.14` with `math.pi`
# and breaking havock on `uv run --python PYTHON`
# Fun using ord of the hidden STX char for '2'
PYTHON = float(f"{math.pi:.{ord('')}f}")

LINE_PRE = 4
THIN_LINE = '─'
THICK_LINE = '━'


def uv_python_pin(c):
    return float(c.run('uv python pin', pty=True, hide='both').stdout.strip())


def uv(c, cmd, args, *, quiet=True, python=PYTHON, group='dev', nogroup='', **kwargs):
    uvpython = uv_python_pin(c)
    q = ' --quiet' if quiet else ''
    p = f' --python {python!s}' if python and python != uvpython else ''
    g = f' --group {group}' if group else ''
    n = f' --no-group {nogroup}' if nogroup else ''

    options = {'pty': True, **kwargs}
    return c.run(f'uv {cmd}{q}{p}{g}{n} {args}', **options)


def uv_run(c, args, *, python=PYTHON, group='dev', quiet=True, **kwargs):
    return uv(c, 'run', args=args, python=python, group=group, quiet=quiet, **kwargs)


def version_python(c, python=PYTHON):
    return uv_run(
        c,
        'python3 --version',
        python=python,
        quiet=True,
        hide='both',
    ).stdout.strip()


def version_tatsu(c, python=PYTHON):
    return uv_run(
        c,
        'python3 -m tatsu --version',
        python=python,
        quiet=True,
        hide='both',
    ).stdout.strip()


def boundary_print(banner: str = '', line=THIN_LINE):
    cols = shutil.get_terminal_size().columns
    if not banner:
        print(line * cols)
    else:
        pre = LINE_PRE
        add = sum(ord(c) >= 256 for c in banner)
        print(line * pre, banner, line * (cols - 2 - pre - add - len(banner)))


def success_print(target='', task=None, line=THIN_LINE):
    target += task.name if task else ''
    boundary_print(f'✅ {target}', line=line)


def version_boundary_print(c, target='', python=PYTHON, line=THICK_LINE):
    verpython = version_python(c, python=python)
    vertatsu = version_tatsu(c, python=python)
    boundary_print(f'{target} {verpython} {vertatsu}', line=line)


@task
def begin(c):
    boundary_print()


@task(pre=[begin])
def clean(c, plus=False):
    print('-> clean')
    patterns = ['build', 'dist', 'tmp', 'tatsu.egg-info', '.tox']
    if plus:
        patterns.extend(['.cache', '.pytest_cache', '.ruff_cache', '.mypy_cache'])

    for p in patterns:
        path = Path(p)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    for p in Path().rglob('__pycache__'):
        shutil.rmtree(p)


@task(pre=[clean])
def ruff(c, python=PYTHON):
    print('-> ruff')
    uv_run(
        c,
        'ruff check -q --preview --fix tatsu tests examples',
        python=python,
        group='test',
    )


@task(pre=[clean])
def ty(c, python=PYTHON):
    print('-> ty')
    res = uv_run(
        c,
        'ty check tatsu tests examples',
        python=python,
        group='test',
        hide='both',
    )

    if res.exited != 0 or 'All checks passed!' not in res.stdout:
        for r in [res.stdout, res.stderr]:
            if r.strip():
                print(r)


@task(pre=[clean])
def pyright(c, python=PYTHON):
    print('-> pyright')
    uv_run(
        c,
        'basedpyright tatsu tests examples',
        python=python,
        group='test',
        hide='stdout',
    )


@task(pre=[clean])
def pytest(c, python=PYTHON):
    print('-> pytest')
    Path('./tmp').mkdir(exist_ok=True)
    Path('./tmp/__init__.py').touch()
    uv_run(c, 'pytest --quiet tests/', python=python, group='test', hide='stdout')


@task(pre=[begin, clean, ruff, ty, pyright])
def lint(c):
    success_print(task=lint)


@task(pre=[begin, lint, pytest])
def test(c):
    success_print(task=test)


@task(pre=[begin])
def docs(c):
    print('-> docs')
    with c.cd('docs'):
        uv_run(
            c,
            'make -s html',
            quiet=True,
            group='doc',
            hide='stdout',
        )
    success_print(task=docs)


@task(pre=[clean])
def build(c):
    print('-> build')
    c.run('uvx hatch build', hide='both')
    success_print(task=build)


def matrix_core(c, python=PYTHON):
    version_boundary_print(c, target='🐍', python=python)
    ruff(c, python=python)
    ty(c, python=python)
    pyright(c, python=python)
    pytest(c, python=python)
    success_print(str(python))


@task
def py312(c):
    matrix_core(c, python=3.12)


@task
def py313(c):
    matrix_core(c, python=3.13)


@task
def py314(c):
    matrix_core(c, python=math.pi)


@task
def py315(c):
    matrix_core(c, python=3.15)


@task(pre=[py312, py313, py314, py315])
def matrix(c):
    success_print(task=matrix, line=THICK_LINE)


def _export_requirements(c, filename, group='', nogroup=''):
    out_file = Path(filename)
    print(f'-> {out_file}')

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
def req_base(c):
    _export_requirements(c, 'requirements.txt', nogroup='dev')


@task
def req_dev(c):
    _export_requirements(c, 'requirements-dev.txt', group='dev')


@task
def req_test(c):
    _export_requirements(c, 'requirements-test.txt', group='test', nogroup='dev')


@task
def req_doc(c):
    _export_requirements(c, 'requirements-doc.txt', group='doc', nogroup='dev')


@task(pre=[begin, req_base, req_dev, req_test, req_doc])
def requirements(c):
    success_print(task=requirements)


@task(pre=[requirements])
def reqs(c):
    pass


@task(pre=[build])
def publish(c, dry_run=True):
    c.run('uv tool install -q gh')
    workflow = 'test_publish.yml' if dry_run else 'publish.yml'
    c.run(f'gh workflow run {workflow}')
    c.run(f'gh run list --workflow={workflow}')


@task
def g2e(c, python=PYTHON):
    print('-> examples/g2e')
    with c.cd('examples/g2e'):
        c.run('uv run make -s clean test', pty=True, hide='both')
        c.run('uv run make -s clean', pty=True, hide='both')


@task
def calc(c, python=PYTHON):
    print('-> examples/calc')
    with c.cd('examples/calc'):
        c.run('uv run make -s clean test', pty=True, hide='both')


@task(pre=[clean, begin, g2e, calc])
def examples(c):
    success_print(task=examples)


@task(pre=[test, docs, examples, build, requirements], default=True)
def all(c, python=PYTHON):
    boundary_print('✨ complete!')

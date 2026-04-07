# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
shell := "xonsh"
set shell := [shell, "-c"]

py := "3.15"

default: test docs examples requirements build
    @echo "✔ all"

@shell:
    {{shell}} --version


# --- Environment Management ---

@sync:
    uv sync --group dev

# --- Requirements Export ---

reqs: requirements

@requirements: req-base req-dev req-test req-doc
    echo "━ requirements ━"

@req-base:
    echo "▶ requirements.txt"
    uv export --quiet --no-hashes --format requirements-txt -o requirements.txt --no-dev

@req-dev:
    echo "▶ requirements-dev.txt"
    uv export --quiet --no-hashes --format requirements-txt -o requirements-dev.txt --group dev

@req-test:
    echo "▶ requirements-test.txt"
    uv export --quiet --no-hashes --format requirements-txt -o requirements-test.txt --group test --no-group dev

@req-doc:
    echo "▶ requirements-doc.txt"
    uv export --quiet --no-hashes --format requirements-txt -o requirements-doc.txt --group doc --no-group dev

# --- Cleaning ---

@clean plus="False":
    echo "▶ clean"
    grm -rf build dist tatsu.egg-info .tox
    if {{plus}} : $[grm -rf .cache .pytest_cache .ruff_cache]
    find tatsu tests examples scripts -type d -name __pycache__ -delete

clobber: (clean "true")

# --- Linting & Formatting ---

@format:
    echo "▶ format {{py}}"
    uv run --quiet --python {{py}} --group test ruff check --select I --fix tatsu tests examples scripts ng
    uv run --quiet --python {{py}} --group test ruff format tatsu tests examples scripts ng

@lint: format ruff ty mypy pyright pyrefly
    echo "━ lint ⏏ ━"

@ruff:
    echo "▶ ruff {{py}}"
    uv run --quiet --python {{py}} --group test ruff check -q --preview tatsu tests examples

@ty:
    echo "▶ ty {{py}}"
    uv run --quiet --python {{py}} --group test ty check tatsu tests examples > /dev/null

@mypy:
    echo "▶ mypy {{py}}"
    uv run --quiet --python {{py}} --group test mypy tatsu tests examples --install-types --exclude "dist|parsers|backup" > /dev/null

@pyright:
    echo "▶ pyrighti {{py}}"
    uv run --quiet --python {{py}} --group test basedpyright tatsu tests examples

@zuban:
    echo "▶ zuban {{py}}"
    uv run --quiet --python {{py}} --group test zuban check tatsu tests examples

@pyrefly:
    echo "▶ pyrefly {{py}}"
    uv run --quiet --python {{py}} --group test pyrefly check tatsu tests examples > /dev/null

# --- Testing ---

@test: lint pytest_fast pytest_boot
    echo "━ test ⏏ ━"

@pytest_fast:
    echo "▶ fast pytest"
    mkdir -p tmp && touch tmp/__init__.py
    uv run --quiet --python {{py}} --group test pytest --quiet -n auto tests/ --ignore-glob=tests/z* > /dev/null

@pytest_boot:
    echo "▶ boot pytest"
    uv run --quiet --python {{py}} --group test pytest --quiet tests/z_bootstrap_test.py > /dev/null

# --- Documentation & Examples ---

@docs: doclint
    echo "▶ docs"
    cd docs && uv run --group doc make -s html > /dev/null

@doclint:
    echo "▶ doclint"
    uv run --group doc vale README.rst docs/**/*.rst > /dev/null

@examples:
    echo "▶ examples/calc"
    cd examples/calc && uv run make -s clean test > /dev/null

# --- Build & Publish ---

@build: clean
    echo "▶ build"
    uvx hatch build

@testpublish: build
    gh workflow run test_publish.yml
    gh run list --workflow=test_publish.yml

@publish: build
    gh workflow run publish.yml
    gh run list --workflow=publish.yml

@matrix: py312 py313 py314 py315 py315t
    echo '⏏ matrix'

@py312:
    just py=3.12 matrix-core

@py313:
    just py=3.13 matrix-core

@py314:
    just py=3.14 matrix-core

@py315:
    just py=3.15 matrix-core

@py315t:
    just py=3.15t matrix-core

@version:
    echo "━ ᝰ {{py}} ━"

@matrix-core: version test

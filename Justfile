# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
shell := "xonsh"
set shell := [shell, "-c"]

py := "3.15"

# Macro-like expansions for consistent uv flag placement
run_test := "uv run --quiet --python " + py + " --group test "
run_doc  := "uv run --quiet --group doc "
export   := "uv export --quiet --no-hashes --format requirements-txt "

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
    {{export}} -o requirements.txt --no-dev

@req-dev:
    echo "▶ requirements-dev.txt"
    {{export}} -o requirements-dev.txt --group dev

@req-test:
    echo "▶ requirements-test.txt"
    {{export}} -o requirements-test.txt --group test --no-group dev

@req-doc:
    echo "▶ requirements-doc.txt"
    {{export}} -o requirements-doc.txt --group doc --no-group dev

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
    {{run_test}} ruff check --select I --fix tatsu tests examples scripts ng > /dev/null
    {{run_test}} ruff format tatsu tests examples scripts ng > /dev/null

@lint: format ruff ty mypy pyright pyrefly
    echo "━ lint ⏏ ━"

@ruff:
    echo "▶ ruff {{py}}"
    {{run_test}} ruff check -q --preview tatsu tests examples > /dev/null

@ty:
    echo "▶ ty {{py}}"
    {{run_test}} ty check tatsu tests examples > /dev/null

@mypy:
    echo "▶ mypy {{py}}"
    {{run_test}} mypy tatsu tests examples --install-types --exclude "dist|parsers|backup" > /dev/null

@pyright:
    echo "▶ pyright {{py}}"
    {{run_test}} basedpyright tatsu tests examples > /dev/null

@pyrefly:
    echo "▶ pyrefly {{py}}"
    {{run_test}} pyrefly check tatsu tests examples 2>&1 > /dev/null

# --- Testing ---

@test: lint pytest_fast pytest_boot
    echo "━ test ⏏ ━"

@pytest_fast:
    echo "▶ fast pytest {{py}}"
    mkdir -p tmp && touch tmp/__init__.py
    {{run_test}} pytest --quiet -n auto tests/ --ignore-glob=tests/z* > /dev/null

@pytest_boot:
    echo "▶ boot pytest {{py}}"
    {{run_test}} pytest --quiet tests/z_bootstrap_test.py > /dev/null

# --- Documentation & Examples ---

@docs: doclint
    echo "▶ docs"
    cd docs && {{run_doc}} make -s html > /dev/null

@doclint:
    echo "▶ doclint"
    {{run_doc}} vale README.rst docs/**/*.rst > /dev/null

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

# --- Matrix Execution ---

@matrix: py312 py313 py314 py315 py315t
    echo '⏏ matrix'

@matrix-core: version test

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

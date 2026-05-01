# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
shell := "xonsh"
set shell := [shell, "-c"]

py := "3.14"

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
    /bin/rm -rf build dist tatsu.egg-info .tox
    if {{plus}} : $[/bin/rm -rf .cache .pytest_cache .ruff_cache]
    find tatsu tests examples scripts -type d -name "__pycache__" -print0 | xargs -0 /bin/rm -rf

clobber: (clean "true")

# --- Linting & Formatting ---

@fmt:
    echo "▶ fmt {{py}}"
    {{run_test}} ruff check \
        --select I --fix \
        tatsu tests examples scripts ng \
        | grep -v "checks passed|left unchanged" | cat

    {{run_test}} ruff format tatsu tests examples scripts ng \
        | grep -v "checks passed|left unchanged" | cat

@lint: fmt ruff ty mypy pyright pyrefly
    echo "━ lint ⏏ ━"

@ruff:
    echo "▶ ruff {{py}}"
    {{run_test}} ruff check -q --preview tatsu tests examples

@ty:
    echo "▶ ty {{py}}"
    {{run_test}} ty check tatsu tests examples | grep --color=always -v r"Checking|All checks passed!" || true

@mypy:
    echo "▶ mypy {{py}}"
    {{run_test}} mypy \
        tatsu tests examples \
        --install-types --exclude "dist|parsers|backup" \
        | grep -v r"Success" || true

@pyright:
    echo "▶ pyright {{py}}"
    {{run_test}} basedpyright tatsu tests examples

@pyrefly:
    echo "▶ pyrefly {{py}}"
    {{run_test}} pyrefly check tatsu tests examples

# --- Testing ---

@test: lint pytest_fast pytest_boot
    echo "━ test ⏏ ━"

@pytest_fast:
    echo "▶ fast pytest {{py}}"
    {{run_test}} pytest \
        --quiet -n auto  \
        --tb=no --no-header --no-summary \
        --ignore-glob=tests/z* \
        tests \
        | grep -v "^.|^$" | cat

@pytest_boot:
    echo "▶ boot pytest {{py}}"
    {{run_test}} pytest \
        --quiet \
        --tb=no --no-header --no-summary \
        tests/z_bootstrap_test.py \
        | grep -v "^." | cat

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

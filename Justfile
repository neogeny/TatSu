# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)

shell := "xonsh"

set shell := [shell, "-c"]

py := "3.14"

# Macro-like expansions for consistent uv flag placement

run_test := "uv run --quiet --python " + py + " --group test "
run_doc := "uv run --quiet --group doc "
export := "uv export --quiet --no-hashes --format requirements-txt "

default: test docs examples requirements build
    @echo "✔ all"

@shell:
    {{ shell }} --version

# --- Environment Management ---

@sync:
    uv sync --group dev

# --- Requirements Export ---

reqs: requirements

@requirements: req-base req-dev req-test req-doc
    echo "━ requirements ━"

@req-base:
    echo "▶ requirements.txt"
    {{ export }} -o requirements.txt --no-dev

@req-dev:
    echo "▶ requirements-dev.txt"
    {{ export }} -o requirements-dev.txt --group dev

@req-test:
    echo "▶ requirements-test.txt"
    {{ export }} -o requirements-test.txt --group test --no-group dev

@req-doc:
    echo "▶ requirements-doc.txt"
    {{ export }} -o requirements-doc.txt --group doc --no-group dev

# --- Cleaning ---

@clean plus="False":
    echo "▶ clean"
    /bin/rm -rf build dist tatsu.egg-info .tox
    if {{ plus }} : $[/bin/rm -rf .cache .pytest_cache .ruff_cache]
    find tatsu tests examples scripts -type d -name "__pycache__" -print0 | xargs -0 /bin/rm -rf

clobber: (clean "true")

# --- Linting & Formatting ---

@testg:
    uv sync --group test

@fmt: testg
    echo "▶ fmt {{ py }}"
    {{ run_test }} ruff check \
        --select I --fix \
        tatsu tests examples scripts ng

    {{ run_test }} ruff format tatsu tests examples scripts ng

@lint: testg fmt ruff ty mypy pyrefly
    echo "━ lint ⏏ ━"

@ruff: testg
    echo "▶ ruff {{ py }}"
    {{ run_test }} ruff check -q --preview tatsu tests examples

@ty: testg
    echo "▶ ty {{ py }}"
    {{ run_test }} ty check tatsu tests examples

@mypy: testg
    echo "▶ mypy {{ py }}"
    {{ run_test }} mypy \
        tatsu tests examples \
        --install-types \
        --exclude "dist|parsers|backup|tatsu/grammars/leftrec" \
        --exclude "bench.py"

@pyright: testg
    echo "▶ pyright {{ py }}"
    {{ run_test }} basedpyright tatsu tests examples

@pyrefly: testg
    echo "▶ pyrefly {{ py }}"
    {{ run_test }} pyrefly check tatsu tests examples \
        --project-excludes=tatsu/grammars/leftrec

# --- Testing ---

@test: lint test-fast test-boot
    echo "━ test ⏏ ━"

@test-fast: testg
    echo "▶ fast test {{ py }}"
    {{ run_test }} pytest \
        -n auto  \
        --tb=no --no-header \
        --ignore-glob=tests/z* \
        tests

@test-boot: testg
    echo "▶ boot test {{ py }}"
    {{ run_test }} pytest \
        --tb=no --no-header \
        tests/z_bootstrap_test.py

# --- Documentation & Examples ---

@docg:
    uv sync --group doc

@docs: docg doclint
    echo "▶ docs"
    cd docs && {{ run_doc }} make -s html > /dev/null

doclint: docg
    # echo "▶ docstring lint"
    # uv run ruff check --select D tatsu
    echo "▶ doclint"
    {{ run_doc }} vale *.rst *.md docs/**/*.rst

@examples:
    echo "▶ examples/calc"
    cd examples/calc && uv run make -s clean test > /dev/null

# --- Build & Publish ---

@build: clean
    echo "▶ build"
    uv build

@parsers:
    echo "▶ parsers"
    python3 -m tatsu tatsu/_tatsu.ebnf \
        -z \
        -m TatSuBootstrap \
        -o tatsu/parser/bootstrap.py
    python3 -m tatsu tatsu/_tatsu.ebnf \
        -z -x \
        -m TatSuBootstrap \
        -o tatsu/parser/bootparser.py

@testpublish: build
    gh workflow run test_publish.yml
    gh run list --workflow=test_publish.yml

@publish: build
    gh workflow run publish.yml
    gh run list --workflow=publish.yml

# --- Matrix Execution ---

@matrix: py312 py313 py314 py315 py314t
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

@py314t:
    just py=3.14t matrix-core

@py315t:
    just py=3.15t matrix-core

@version:
    echo "━ ᝰ {{ py }} ━"

demo:
    echo "▶ demo"
    @uv sync
    vhs media/demo.tape
    vhs publish -q media/demo.gif | media/demo.py > media/demo.rst

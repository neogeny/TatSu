# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause

ifeq ($(OS), Windows_NT)
    PLATFORM := Windows
else
    PLATFORM := $(shell uname -s)
endif


all:  test documentation examples build requirements


test:  lint pytest

test_plus: clean_plus test


__version__:
	@- echo "->" $$(python3 --version) $$(python3 -m tatsu --version)


__line__:
	@- uvx python3 -c "import shutil; print('━' * shutil.get_terminal_size().columns)"


__tests_init__: __line__ __version__
	@- uv sync -q --group test


pytest: __tests_init__ clean
	@- echo "-> $@"
	@- mkdir -p ./tmp
	@- touch ./tmp/__init__.py
	@- uv run pytest --quiet tests/


documentation: sphinx_make


docs: documentation


doc: documentation


sphinx_make:
	@- uv sync -q --group doc
	@  echo "-> docs"
	@- cd docs; uv run make -s html > /dev/null


examples: clean g2e_test calc_test


g2e_test:
	@- echo "-> examples/g2e"
	@- cd examples/g2e && uv run make -s clean test > /dev/null
	@- cd examples/g2e && uv run make -s clean > /dev/null


calc_test:
	@- echo "-> examples/calc"
	@- cd examples/calc && uv run make -s clean test > /dev/null


lint: ruff ty pyright


ruff: __tests_init__ clean
	@- echo "-> $@"
	@- uv run ruff check -q --preview --fix tatsu tests examples


mypy: __tests_init__ clean
	@- echo "-> $@"
	@- uv run mypy tatsu tests examples \
		--install-types \
		--exclude dist \
		--exclude parsers \
		--exclude backup

pyright: basedpyright


basedpyright: __tests_init__ clean
	@- echo "-> $@"
	@- uv run basedpyright tatsu tests examples > /dev/null


ty: __tests_init__ clean
	@- echo "-> $@"
	@- uv run ty check tatsu tests examples > /dev/null


clean:
	@- find tatsu tests examples -name "__pycache__" | xargs /bin/rm -rf
	@- /bin/rm -rf tatsu.egg-info dist tmp build .tox


clean_plus: clean
	@- /bin/rm -rf .cache .pytest_cache .ruff_cache .mypy_cache


checks: matrix

matrix: matrix_run __line__

matrix_run:
	@- uv run -q --python 3.12 make test
	@- uv run -q --python 3.13 make test
	@- uv run -q --python 3.14 make test
	@- uv run -q --python 3.15 make test


build: clean
	@- echo "-> $@"
	@- uvx hatch build


requirements: \
	uv.lock \
	requirements.txt \
	requirements-dev.txt \
	requirements-test.txt \
	requirements-doc.txt


requirements.txt: uv.lock
	@echo "->" $@
	@- uv export -q --format requirements-txt --no-hashes \
		--no-group dev \
		> $@

requirements-dev.txt: uv.lock
	@echo "->" $@
	@- uv export -q --format requirements-txt --no-hashes \
		--dev \
		> $@

requirements-test.txt: uv.lock
	@echo "->" $@
	@- uv export -q --format requirements-txt --no-hashes \
		--group test --no-group dev \
		> $@

requirements-doc.txt: uv.lock
	@echo "->" $@
	@- uv export -q --format requirements-txt --no-hashes \
		--group doc --no-group dev \
		> $@


need_gh:
	@- uv tool install -q gh
	@- gh --version | head -n 1


test_publish: need_gh build
	gh workflow run test_publish.yml
	@- gh run list --workflow="test_publish.yml"


publish: need_gh matrix build
	# CAVEAT: Trusted Publishers are now enabled in pypi.org
	gh workflow run publish.yml
	@- gh run list --workflow="publish.yml"

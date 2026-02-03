# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause

ifeq ($(OS), Windows_NT)
    PLATFORM := Windows
else
    PLATFORM := $(shell uname -s)
endif


all:  lint mypy pytest documentation examples requirements


test:  lint pytest
	@-uv sync -q

test_plus: clean_plus test
	@-uv sync -q


__tests_init__: clean
	@-uv sync -q --group test


pytest: __tests_init__
	@- echo "preparing..."
	@- mkdir -p ./tmp
	@- touch ./tmp/__init__.py
	@- uv run pytest -v tests/


documentation: sphinx_make mkdocs_build


docs: documentation


doc: documentation


sphinx_make:
	@- uv sync -q --group doc
	@  echo "-> docs"
	@- cd docs; uv run make -s html > /dev/null
	@- uv sync -q


mkdocs_build:
	@- uv sync -q --group mkdocs
	@  echo "-> mkdocs"
	@- cd mkdocs; uv run mkdocs build -q 2>&1 > /dev/null
	@- uv sync -q


examples: clean g2e_test calc_test


g2e_test:
	cd examples/g2e && uv run make -s clean test > /dev/null
	@- cd examples/g2e && uv run make -s clean > /dev/null


calc_test:
	cd examples/calc && uv run make -s clean test > /dev/null


lint: ruff ty pyright
	@-uv sync --group test


ruff: __tests_init__
	@- echo $@
	@- uv run ruff check -q --preview --fix tatsu tests examples


mypy: __tests_init__
	@- echo $@
	@- uv run mypy tatsu tests examples \
		--install-types \
		--exclude dist \
		--exclude parsers \
		--exclude backup

pyright: basedpyright


basedpyright: __tests_init__
	@- echo $@
	@- uv run basedpyright tatsu tests examples


ty: __tests_init__
	@- echo $@
	@- uv run ty check --exclude parsers --exclude backups


clean:
	@- echo "cleaning..."
	@- find . -name "__pycache__" | xargs /bin/rm -rf
	@- /bin/rm -rf tatsu.egg-info dist tmp build .tox


clean_plus: clean
	# NOTE: keep the complicated .mypy_cache
	/bin/rm -rf .cache .pytest_cache .ruff_cache


checks: clean_plus __tests_init__
	time uv run hatch run --force-continue test:checks


build: clean
	uvx hatch build


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


publish: need_gh checks build
	# CAVEAT: Trusted Publishers are now enabled in pypi.org
	gh workflow run publish.yml
	@- gh run list --workflow="publish.yml"

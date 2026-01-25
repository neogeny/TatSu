SHELL := /bin/bash

ifeq ($(OS), Windows_NT)
    PLATFORM := Windows
else
    PLATFORM := $(shell uname -s)
endif


all:  prepare test build requirements


test:  prepare lint pytest documentation examples


prepare:
	uv sync -q


pytest: clean
	mkdir -p ./tmp
	touch ./tmp/__init__.py
	uv run pytest -v tests/


documentation: sphinx


docs: documentation


doc: documentation


sphinx:
	cd docs; uv run make -s html > /dev/null


examples: clean g2e_test calc_test


g2e_test:
	cd examples/g2e && uv run make -s clean test > /dev/null
	@- cd examples/g2e && uv run make -s clean > /dev/null


calc_test:
	cd examples/calc && uv run make -s clean test > /dev/null


lint: ruff ty mypy


ruff:
	@- echo ruff
	@- uv run ruff check -q --preview --fix tatsu tests examples


mypy:
	@- echo mypy
	@- uv run mypy . \
		--install-types \
		--exclude dist \
		--exclude parsers \
		--exclude backup


ty:
	@- echo ty
	@- uv run ty check --exclude parsers --exclude backups


clean:
	find . -name "__pycache__" | xargs /bin/rm -rf
	/bin/rm -rf tatsu.egg-info dist tmp build .tox


checks: clean
	time uv run hatch run --force-continue test:checks


build: clean
	uvx hatch build


requirements: uv.lock
	uv export -q --format requirements-txt --no-hashes \
		> requirements.txt
	uv export -q --format requirements-txt --no-hashes \
		--group doc --no-group dev \
		> requirements-doc.txt


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

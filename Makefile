SHELL := /bin/bash


test:  lint pytest documentation examples


pytest: clean
	echo `uv run which pytest`
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


checks: clean documentation
	time uv run hatch run --force-continue test:checks
	@echo version `uv run python -m tatsu --version`


build: clean
	uvx hatch build


need_gh:
	@- uv tool install -q gh
	@- gh --version | head -n 1


test_publish: need_gh build
	gh workflow run test_publish.yml
	@- gh run list --workflow="test_publish.yml"


publish: need_gh checks build
	# WARNING: now Trusted Publishers is enabled on PyPy
	gh workflow run publish.yml
	@- gh run list --workflow="publish.yml"


pygraphviz: graphviz pygraphviz_mac

graphviz:
	brew install -q graphviz

pygraphviz_mac: graphviz
	uv pip install \
		--no-cache-dir \
		--config-settings="--global-option=build_ext" \
		--config-settings="--global-option=-I$(brew --prefix graphviz)/include/" \
		--config-settings="--global-option=-L$(brew --prefix graphviz)/lib/" \
		pygraphviz

pygraphviz_mac_other: graphviz
	CFLAGS="-I$$(brew --prefix graphviz)/include" \
	LDFLAGS="-L$$(brew --prefix graphviz)/lib" \
	uv pip install pygraphviz --no-cache-dir


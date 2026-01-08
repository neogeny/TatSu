test:  lint documentation examples pytest


pytest: clean
	uv run pytest --cov -v


documentation: sphinx


sphinx:
	cd docs; uv run make -s html > /dev/null


examples: clean g2e_test calc_test


g2e_test:
	cd examples/g2e; uv run make -s clean test > /dev/null


calc_test:
	cd examples/calc; uv run make -s clean test > /dev/null


lint: ruff ty mypy


ruff:
	uv run ruff check -q --preview tatsu test examples


mypy:
	uv run mypy --install-types --exclude dist --exclude parsers .


ty:
	uv run ty check -q --exclude parsers


clean:
	find . -name "__pycache__" -delete
	rm -rf tatsu.egg-info dist build .tox


checks: clean documentation
	uv run hatch run --force-continue test:checks
	@echo version `uv run python -m tatsu --version`


build: clean
	uv run hatch build


test_publish: build
	uv run hatch publish --repo test


publish: checks build
	uv run hatch publish

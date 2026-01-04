test:  lint documentation examples pytest


pytest: clean
	pytest -v --cov


documentation: sphinx


sphinx:
	cd docs; make -s html > /dev/null


examples: clean g2e_test calc_test


g2e_test:
	cd examples/g2e; make -s clean; make -s test > /dev/null

calc_test:
	cd examples/calc; make -s clean; make -s test > /dev/null


lint: ruff mypy


ruff:
	-@ pip install -q -U ruff
	ruff check --preview tatsu test examples


mypy:
	-@ pip install -q -U mypy
	mypy   --ignore-missing-imports . --exclude dist


clean:
	find . -name "__pycache__" | xargs rm -rf
	find . -name "*.pyc" | xargs rm -f
	find . -name "*.pyd" | xargs rm -f
	find . -name "*.pyo" | xargs rm -f
	find . -name "*.orig" | xargs rm -f
	rm -rf tatsu.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .tox


checks: clean documentation
	-@ pip install -qU hatch
	hatch run --force-continue test:checks
	@echo version `python -m tatsu --version`


build: cleanhatch
	-@ pip install -qU hatch
	hatch build


test_publish: build
	-@ pip install -qU hatch
	hatch publish --repo test


publish: checks build
	pip install -U hatch
	hatch publish

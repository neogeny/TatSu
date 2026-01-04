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
	-@ pip install -qU ruff
	ruff check --preview tatsu test examples


mypy:
	-@ pip install -qU mypy
	mypy --install-types --exclude dist .


clean:
	find . -name "__pycache__" -delete
	find . -name "*.pyc" -delete
	find . -name "*.pyd" -delete
	find . -name "*.pyo" -delete
	find . -name "*.orig" -delete
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
	-@ pip install -U hatch
	hatch publish

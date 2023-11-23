test:  lint tatsu_test documentation examples


tatsu_test: clean
	pytest


documentation: clean sphinx


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


release_check: clean documentation
	tox
	@echo version `python -m tatsu --version`


build: clean
	pip install -U build
	python -m build


test_upload: build
	pip install -U twine
	twine upload --repository test dist/*


upload: release_check build
	twine upload dist/*

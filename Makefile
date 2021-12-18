test:  lint tatsu_test documentation examples


tatsu_test: clean
	pytest


documentation: clean changelog readme sphinx


changelog:
	rst2html5 CHANGELOG.rst > /dev/null


readme:
	pandoc README.rst -t gfm --wrap=none > README.md


sphinx:
	cd docs; make -s html > /dev/null


examples: clean g2e_test calc_test


g2e_test:
	cd examples/g2e; make -s clean; make -s test > /dev/null

calc_test:
	cd examples/calc; make -s clean; make -s test > /dev/null


lint: flake8 pylint mypy

flake8:
	flake8

pylint:
	pylint --ignore=bootstrap.py,model.py tatsu test examples

mypy:
	mypy   --ignore-missing-imports .


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
	python setup.py sdist --formats=zip
	tox
	@echo version `python -m tatsu --version`


distributions: clean sdist bdist_wheel


sdist:
	python setup.py sdist --formats=zip


bdist_wheel:
	python setup.py bdist_wheel --universal


test_upload: distributions
	twine upload --repository test dist/*


upload: release_check distributions
	twine upload dist/*

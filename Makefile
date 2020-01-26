test:  static_test tatsu_test documentation examples


tatsu_test:
	pytest


documentation:
	pandoc README.rst -o README.md
	cd docs; make -s html > /dev/null


examples: g2e_test calc_test


g2e_test:
	cd examples/g2e; make -s clean; make -s test > /dev/null

calc_test:
	cd examples/calc; make -s clean; make -s test > /dev/null


static_test:
	flake8
	pylint --ignore=bootstrap.py,model.py tatsu test examples
	mypy   --ignore-missing-imports .


cython:
	python setup.py build_ext --inplace
	python3 setup.py build_ext --inplace


clean: clean_cython
	find . -name "__pycache__" | xargs rm -rf
	find . -name "*.pyc" | xargs rm -f
	find . -name "*.pyd" | xargs rm -f
	find . -name "*.pyo" | xargs rm -f
	find . -name "*.orig" | xargs rm -f
	rm -rf tatsu.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .tox


clean_cython:
	find tatsu -name "*.so" | xargs rm -f
	find tatsu -name "*.c" | xargs rm -f


release_check: clean documentation
	rst2html.py CHANGELOG.rst > /dev/null
	python setup.py sdist --formats=zip
	tox
	@echo version `python -m tatsu --version`


distributions: clean release_check
	python setup.py sdist --formats=zip
	python setup.py bdist_wheel --universal


test_distributions:
	python setup.py sdist --formats=zip
	python setup.py bdist_wheel --universal

test_upload: test_distributions
	twine upload --repository test dist/*

upload: distributions
	twine upload dist/*

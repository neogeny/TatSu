test: flake8 mypy tatsu_test documentation examples


tatsu_test:
	py.test


documentation:
	cd docs; make -s html > /dev/null


examples: regex_test g2e_test calc_test


regex_test:
	cd examples/regex; make -s clean; make -s test > /dev/null


g2e_test:
	cd examples/g2e; make -s clean; make -s test > /dev/null

calc_test:
	cd examples/calc; make -s clean; make -s test > /dev/null


flake8:
	flake8


mypy:
	mypy . --ignore-missing-imports


cython:
	python setup.py build_ext --inplace
	python3 setup.py build_ext --inplace


clean: clean_cython
	find -name "__pycache__" | xargs rm -rf
	find -name "*.pyc" | xargs rm -f
	find -name "*.pyd" | xargs rm -f
	find -name "*.pyo" | xargs rm -f
	find -name "*.orig" | xargs rm -f
	rm -rf tatsu.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .tox


clean_cython:
	find tatsu -name "*.so" | xargs rm -f
	find tatsu -name "*.c" | xargs rm -f


release_check: clean
	rst2html.py README.rst > /dev/null
	python setup.py sdist --formats=zip
	tox
	@echo version `python -m tatsu --version`


distributions: clean release_check
	python setup.py sdist --formats=zip
	python setup.py bdist_wheel --universal


upload: distributions
	twine upload dist/*

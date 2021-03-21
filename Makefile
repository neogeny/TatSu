test:  static_test tatsu_test documentation examples


tatsu_test: clean
	pytest


documentation: clean
	rst2html5 CHANGELOG.rst > /dev/null
	pandoc README.rst -t gfm --wrap=none > README.md
	cd docs; make -s html > /dev/null


examples: clean g2e_test calc_test


g2e_test:
	cd examples/g2e; make -s clean; make -s test > /dev/null

calc_test:
	cd examples/calc; make -s clean; make -s test > /dev/null


static_test:
	flake8
	pylint --ignore=bootstrap.py,model.py tatsu test examples
	mypy   --ignore-missing-imports .


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


release_check: clean documentation
	python setup.py sdist --formats=zip
	tox
	@echo version `python -m tatsu --version`


distributions: clean
	python setup.py sdist --formats=zip
	python setup.py bdist_wheel --universal


test_distributions: clean
	python setup.py sdist --formats=zip
	python setup.py bdist_wheel --universal


test_upload: test_distributions
	twine upload --repository test dist/*


upload: release_check distributions
	twine upload dist/*

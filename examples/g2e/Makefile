
start: test

test: clean
	PYTHONPATH=../.. \
		python -m tatsu.g2e grammar/Python.g  \
				> python.ebnf
	PYTHONPATH=../.. \
		python -m tatsu python.ebnf  \
				2>&1

clean:
	:

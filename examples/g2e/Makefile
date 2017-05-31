
start: test

test: clean
	PYTHONPATH=../.. \
		python -m tatsu.g2e grammar/Python.g  \
				> python.ebnf
	PYTHONPATH=../.. \
		python -m tatsu python.ebnf  \
				2>&1
	PYTHONPATH=../.. \
		python -m tatsu.g2e grammar/Python3.g4  \
				> python3.ebnf
	PYTHONPATH=../.. \
		python -m tatsu python3.ebnf  \
				2>&1

clean:
	:

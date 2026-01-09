
start: test

test: clean
	PYTHONPATH=../.. \
		python -m tatsu.g2e grammar/Python3.g4  \
				--name Python \
				--color \
				--trace \
				2>&1 > python3.ebnf
	PYTHONPATH=../.. \
		python -m tatsu python3.ebnf  \
				--name Python \
				2>&1 > python3_parser.py

clean:
	rm -rf python3_parser.py python3.ebnf

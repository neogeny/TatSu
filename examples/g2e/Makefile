
start: test

test: clean parser
	PYTHONPATH=../.. \
		python g2e.py grammar/Python.g  \
				> python.ebnf
	PYTHONPATH=../.. \
		python -m tatsu python.ebnf  \
				2>&1

parser: antlr_parser.py

antlr_parser.py: grammar/antlr.ebnf
	PYTHONPATH=../.. python -m tatsu -m ANTLR -o $@ \
			   $< 2>&1

clean:
	-@rm -f antlr_parser.py

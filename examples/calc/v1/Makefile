start: test

test: clean parser
	PYTHONPATH=../../.. python calc_parser.py ../input.txt

parser: calc_parser.py

calc_parser.py: calc.ebnf
	PYTHONPATH=../../.. python -m tatsu -o $@ $< 2>&1

clean:
	-@rm -f calc/calc_parser.py

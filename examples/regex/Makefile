
start: test
	PYTHONPATH=../..  python genparser.py -l
	PYTHONPATH=../..  python genparser.py data/valid S0

test: parser
	PYTHONPATH=../..  python test.py 2>&1

parser: parser_base.py

parser_base.py: regex.ebnf
	PYTHONPATH=../.. python -m tatsu -m Regex -o parser_base.py regex.ebnf 2>&1

clean:
	-@rm -f parser_base.py
	-@rm -f genparser.py

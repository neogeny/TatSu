# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause

start: test

test: clean
	PYTHONPATH=../.. \
		python -m tatsu.g2e grammar/Python3.g4  \
				--name Python \
				--color \
				2>&1 > python3.tatsu
	PYTHONPATH=../.. \
		python -m tatsu python3.tatsu  \
				--name Python \
				2>&1 > python3_parser.py

clean:
	rm -rf python3_parser.py python3.tatsu

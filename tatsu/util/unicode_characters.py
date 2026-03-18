# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .common import is_posix

U_LARROW = '←'
U_DLARROW = '↙'
U_LDARROW = '⇐'
U_UDARROW = '⇑'
U_RDARROW = '⇒'
U_DDARROW = '⇓'
U_L_TRIPPLE_ARROW = '⇚'

U_WARNING = '⚠'

U_NOT_EQUAL_TO = '≠'
U_IDENTICAL_TO = '≡'
U_NOT_IDENTICAL_TO = '≢'

U_CHECK_MARK = '✓'

U_POWER_SYMBOL = '⏻'
U_POWER_ON_SYMBOL = '⏼'
U_POWER_OFF_SYMBOL = '⏽'

U_GREEK_SMALL_LETTER_EPSILON = 'ε'
U_GREEK_ANO_TELEIA = '·'
U_REGISTERED_SIGN = '®'
U_RIENNMAN = 'ℝ'

U_ANTICLOCKWISE_OPEN_CIRCLE_ARROW = '↺'
U_ANTICLOCKWISE_GAPPED_CIRCLE_ARROW = '⟲'

# Recommendation: Keep spaces as escape sequences to remain visible to the human eye
U_PUNCTUATION_SPACE = '\u2008'
U_FOUR_PER_EM_SPACE = '\u2005'
U_MEDIUM_MATHEMATICAL_SPACE = '\u205f'
U_ZERO_WIDTH_NO_BREAK_SPACE = '\ufeff'

U_BLACK_SCISSORS = '✂'
U_CROSSED_SWORDS = '⚔'


if not is_posix():
    C_DERIVE = '<'
    C_ENTRY = '<'
    C_SUCCESS = '>'
    C_FAILURE = '!'
    C_RECURSION = 'r '
    C_CUT = '~'
    C_DOT = '.'
else:
    C_DERIVE = U_DLARROW
    C_ENTRY = C_DERIVE
    C_SUCCESS = U_IDENTICAL_TO
    C_FAILURE = U_NOT_IDENTICAL_TO
    C_RECURSION = U_ANTICLOCKWISE_GAPPED_CIRCLE_ARROW + U_FOUR_PER_EM_SPACE
    C_CUT = U_CROSSED_SWORDS
    C_DOT = U_GREEK_ANO_TELEIA

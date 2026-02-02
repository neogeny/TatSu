from __future__ import annotations

import codecs
import re


def re_printable(text: Any) -> str:
    """
    Returns the content of a string formatted as an r'...' literal.
    Escapes control characters and internal single quotes.
    """
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-02)

    if isinstance(text, re.Pattern):
        text = text.pattern
    else:
        text = str(text)

    ctrl_map = {
        "\n": r"\n",
        "\r": r"\r",
        "\t": r"\t",
    }

    content = "".join(ctrl_map.get(c, c) for c in text)
    content = content.replace("'", "\\'")

    if content.endswith("\\") and (len(content) - len(content.rstrip("\\"))) % 2 != 0:
        content += "\\"

    return f"r'{content}'"


def eval_escapes(s: str | bytes) -> str | bytes:
    """
    Given a string, evaluate escape sequences starting with backslashes as
    they would be evaluated in Python source code. For a list of these
    sequences, see: https://docs.python.org/3/reference/lexical_analysis.html

    This is not the same as decoding the whole string with the 'unicode-escape'
    codec, because that provides no way to handle non-ASCII characters that are
    literally present in the string.
    """
    # by Rob Speer

    escape_sequence_re: re.Pattern = re.compile(
        r"""(?ux)
        ( \\U........      # 8-digit Unicode escapes
        | \\u....          # 4-digit Unicode escapes
        | \\x..            # 2-digit Unicode escapes
        | \\[0-7]{1,3}     # Octal character escapes
        | \\N\{[^}]+\}     # Unicode characters by name
        | \\[\\'"abfnrtv]  # Single-character escapes
        )""",
    )

    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return escape_sequence_re.sub(decode_match, s)  # type: ignore[no-matching-overload]

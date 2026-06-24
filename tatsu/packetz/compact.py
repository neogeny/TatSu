import re
from typing import Any


def rle_encode(text: str) -> str:
    """Safely encodes runs of characters by doubling existing delimiters and using ~cN~ for runs."""
    # Step 1: Escape existing literal delimiters by doubling them up (~ -> ~~)
    escaped = text.replace("~", "~~")

    # Step 2: Compress runs of 4 or more identical characters
    # Negative-lookahead ensures we don't accidentally compress our newly doubled '~'
    pattern = re.compile(r"([^~])\1{3,}")
    return pattern.sub(lambda m: f"~{m.group(1)}{len(m.group(0))}~", escaped)


def rle_decode(text: str) -> str:
    """Decodes markers and handles escaped literal delimiters properly."""
    # Step 1: Find and expand the RLE tokens (~cN~)
    # Strictly matches one non-tilde character and its count inside ~ delimiters
    rle_pattern = re.compile(r"~([^~])(\d+)~")
    expanded = rle_pattern.sub(lambda m: m.group(1) * int(m.group(2)), text)

    # Step 2: Collapse the doubled literal delimiters back to single ones (~~ -> ~)
    return expanded.replace("~~", "~")


def compact_value(data: Any) -> Any:
    """Recursively targets string data for bulletproof RLE compression."""
    if isinstance(data, str):
        return rle_encode(data)
    if isinstance(data, dict):
        return {k: compact_value(v) for k, v in data.items()}
    if isinstance(data, list):
        return [compact_value(i) for i in data]
    return data


def decompact_value(data: Any) -> Any:
    """Recursively walks the data structure to expand RLE strings back to original."""
    if isinstance(data, str):
        return rle_decode(data)
    if isinstance(data, dict):
        return {k: decompact_value(v) for k, v in data.items()}
    if isinstance(data, list):
        return [decompact_value(i) for i in data]
    return data

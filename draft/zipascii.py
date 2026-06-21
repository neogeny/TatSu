import base64
import textwrap
import zlib


def compress_to_ascii(text: str, width: int = 80) -> str:
    """Compresses a string and encodes it into wrapped printable ASCII."""
    # 1. Convert text to raw UTF-8 bytes
    raw_bytes = text.encode("utf-8")

    # 2. Compress the bytes using zlib (DEFLATE)
    compressed_bytes = zlib.compress(raw_bytes, level=9)

    # 3. Encode binary payload into clean, printable Base85 ASCII characters
    ascii_bytes = base64.b85encode(compressed_bytes)
    ascii_str = ascii_bytes.decode("ascii")

    # 4. Wrap beautifully to the target column width
    return "\n".join(textwrap.wrap(ascii_str, width=width))


def decompress_from_ascii(ascii_block: str) -> str:
    """Reverses the pipeline: unwraps, decodes Base85, and decompresses."""
    # 1. Remove all whitespace and newlines introduced by column wrapping
    cleaned_ascii = "".join(ascii_block.split())

    # 2. Decode the Base85 string back to binary zlib payload
    compressed_bytes = base64.b85decode(cleaned_ascii.encode("ascii"))

    # 3. Decompress the data structure back to standard UTF-8 text
    raw_bytes = zlib.decompress(compressed_bytes)
    return raw_bytes.decode("utf-8")

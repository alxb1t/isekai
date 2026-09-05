"""Build the smallest JPEG and PNG headers that carry a stated size.

The suite is offline and carries no imaging wheel, and the parser under test reads
headers rather than pixels -- so a header with the right shape is a complete input
for it. Building them here rather than tracking binary fixtures keeps the declared
size and the bytes in one place, so a fixture cannot silently disagree with the
dimensions a test asserts against.
"""

import struct


def png_bytes(width: int, height: int) -> bytes:
    """Return a PNG signature and IHDR chunk declaring this size."""
    header = struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", len(header))
        + b"IHDR"
        + header
        + b"\x00\x00\x00\x00"
    )


def jpeg_bytes(width: int, height: int) -> bytes:
    """Return a JPEG with an APP0 segment ahead of the frame header.

    The APP0 is not decoration: it is what makes the frame header's offset a
    variable rather than a constant, which is the property the parser's marker
    walk exists for.
    """
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9
    sof0 = (
        b"\xff\xc0"
        + struct.pack(">H", 17)
        + b"\x08"
        + struct.pack(">HH", height, width)
        + b"\x03"
        + b"\x00" * 9
    )
    return b"\xff\xd8" + app0 + sof0 + b"\xff\xd9"

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


def exif_tiff(orientation: int) -> bytes:
    r"""Return a big-endian TIFF block whose IFD0 declares this Orientation.

    The block itself, without a container: JPEG wraps it in an APP1 segment
    behind an `Exif\x00\x00` marker, and PNG's `eXIf` chunk carries it raw. The
    probe builds both from this one function, so a rotated JPEG and a rotated PNG
    differ only in the container.
    """
    # A single big-endian IFD entry: tag 0x0112, type 3 (SHORT), count 1. A SHORT
    # value is left-justified in the entry's four value bytes, which is why the
    # orientation is packed ahead of the padding rather than after it.
    entry = struct.pack(">HHI", 0x0112, 3, 1) + struct.pack(">HH", orientation, 0)
    return (
        b"MM\x00\x2a"
        + struct.pack(">I", 8)
        + struct.pack(">H", 1)
        + entry
        + struct.pack(">I", 0)
    )


def _exif_app1(orientation: int) -> bytes:
    """Return an APP1 segment whose TIFF IFD0 declares this Orientation."""
    payload = b"Exif\x00\x00" + exif_tiff(orientation)
    return b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload


def _filler_app2(size: int) -> bytes:
    """Return APP2 segments carrying `size` bytes of filler between them.

    A real camera pushes the frame header deep with an embedded thumbnail, an ICC
    profile and XMP. One segment's payload cannot exceed 65533 bytes, so a header
    deeper than that is several segments -- which is the shape being reproduced.
    """
    segments = []
    while size > 0:
        chunk = min(size, 65533 - 2)
        segments.append(b"\xff\xe2" + struct.pack(">H", chunk + 2) + b"\x00" * chunk)
        size -= chunk
    return b"".join(segments)


def jpeg_with_header(
    width: int,
    height: int,
    *,
    orientation: int | None = None,
    header_padding: int = 0,
) -> bytes:
    """Return `jpeg_bytes`, with EXIF orientation and metadata bulk ahead of the SOF.

    Both knobs reproduce properties of an ordinary phone photo that the minimal
    JPEG does not have: an Orientation tag the image loader applies before any
    node sees the pixels, and a header too deep to sit in a short prefix.
    """
    body = jpeg_bytes(width, height)
    prefix = b""
    if orientation is not None:
        prefix += _exif_app1(orientation)
    prefix += _filler_app2(header_padding)
    return body[:2] + prefix + body[2:]

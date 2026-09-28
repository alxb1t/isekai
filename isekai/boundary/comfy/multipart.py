"""A hand-rolled multipart/form-data encoder, so no HTTP client reaches the graph."""

import secrets
from collections.abc import Callable


def _draw() -> str:
    """Return a fresh random boundary."""
    return "isekai-" + secrets.token_hex(16)


def _escaped(name: str) -> str:
    """Return `name` with its quote and line breaks percent-encoded (RFC 7578 §4.2).

    e.g. 'a"b.png' -> 'a%22b.png'
    """
    return name.replace('"', "%22").replace("\r", "%0D").replace("\n", "%0A")


def build_multipart(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
    draw: Callable[[], str] = _draw,
) -> tuple[bytes, str]:
    """Build a multipart/form-data body by hand. Returns (body_bytes, content_type)."""
    parts = [
        (
            f'Content-Disposition: form-data; name="{_escaped(name)}"\r\n\r\n',
            value.encode(),
        )
        for name, value in fields.items()
    ] + [
        (
            f'Content-Disposition: form-data; name="{_escaped(name)}"; '
            f'filename="{_escaped(filename)}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n",
            data,
        )
        for name, (filename, data, ctype) in files.items()
    ]

    # A boundary inside a part would end that part early.
    boundary = draw()
    while any(boundary.encode() in head.encode() + data for head, data in parts):
        boundary = draw()

    body = bytearray()
    for head, data in parts:
        body += f"--{boundary}\r\n{head}".encode() + data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    return bytes(body), f"multipart/form-data; boundary={boundary}"

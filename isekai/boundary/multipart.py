"""A hand-rolled multipart/form-data encoder, so the runtime stays stdlib-only."""


def build_multipart(
    fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]
) -> tuple[bytes, str]:
    """Build a multipart/form-data body by hand. Returns (body_bytes, content_type)."""
    boundary = "---convertpyBoundary7MA4YWxkTrZu0gW"
    body = bytearray()

    for name, value in fields.items():
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    for name, (filename, data, ctype) in files.items():
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode()
        body += data + b"\r\n"

    body += f"--{boundary}--\r\n".encode()

    return bytes(body), f"multipart/form-data; boundary={boundary}"

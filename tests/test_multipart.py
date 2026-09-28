import pytest

from isekai.boundary.comfy.multipart import build_multipart


@pytest.mark.spec("comfy-transport:multipart:content-type-declares-boundary")
def test_multipart_content_type_declares_the_boundary() -> None:
    body, content_type = build_multipart(
        fields={"overwrite": "true"},
        files={"image": ("cat.png", b"\x89PNG", "application/octet-stream")},
    )

    assert content_type.startswith("multipart/form-data; boundary=")
    boundary = content_type.split("boundary=")[1].encode()
    # The declared boundary opens each part, and closes the body.
    assert body.count(b"--" + boundary + b"\r\n") == 2
    assert body.startswith(b"--" + boundary + b"\r\n")
    assert body.endswith(b"--" + boundary + b"--\r\n")


@pytest.mark.spec("comfy-transport:multipart:encodes-fields-and-files")
def test_multipart_encodes_fields_and_files_as_wire_format() -> None:
    body, content_type = build_multipart(
        fields={"overwrite": "true"},
        files={"image": ("cat.png", b"\x89PNG\r\n\x1a\n", "application/octet-stream")},
    )
    boundary = content_type.split("boundary=")[1]

    expected = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="overwrite"\r\n\r\n'
            f"true\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="cat.png"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        + b"\x89PNG\r\n\x1a\n"
        + b"\r\n"
        + f"--{boundary}--\r\n".encode()
    )

    assert body == expected


@pytest.mark.spec("comfy-transport:multipart:preserves-binary-verbatim")
def test_multipart_preserves_binary_file_data_verbatim() -> None:
    raw = bytes(range(256))
    body, _ = build_multipart(
        fields={},
        files={"f": ("x.bin", raw, "application/octet-stream")},
    )

    assert raw in body


@pytest.mark.spec("comfy-transport:multipart:the-boundary-appears-in-no-part")
def test_the_boundary_appears_in_no_part() -> None:
    drawn = iter(["inside", "outside"])
    body, content_type = build_multipart(
        fields={},
        files={"image": ("a.png", b"bytes inside", "application/octet-stream")},
        draw=lambda: next(drawn),
    )

    assert content_type.endswith("boundary=outside")
    assert body.count(b"outside") == 2
    assert b"bytes inside\r\n--outside--\r\n" in body


@pytest.mark.spec("comfy-transport:multipart:names-are-escaped")
def test_names_are_escaped() -> None:
    body, _ = build_multipart(
        fields={},
        files={"image": ('a"b\r\nX: y.png', b"", "application/octet-stream")},
    )

    head = body.split(b"\r\n\r\n", 1)[0]
    assert b'filename="a%22b%0D%0AX: y.png"' in head
    # The encoder's own line breaks are the only ones: the boundary line, the
    # disposition and the content type.
    assert head.count(b"\r\n") == 2

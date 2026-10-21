"""Import: a file read, cleaned, verified and committed into a batch's `sources/`.

Every image is built by Pillow here, except the HEIC, which is a committed fixture
made once by macOS `sips` from a synthetic solid-colour PNG.
"""

import io
import struct
from pathlib import Path

import pytest
from PIL import Image, ImageCms

from isekai.foundation.refusal import Refusal
from isekai.interface.cli import build_parser, dispatch
from isekai.pipeline import importing
from isekai.pipeline.importing import cancel, commit, read, stage, sweep, verify
from isekai.shared.image import metadata_in
from tests.images import jpeg_segment, nef_bytes, photo_jpeg
from tests.stages import bare_wiring

REPO = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sources"
LIMIT = 10 * 1024 * 1024
ORIENTATION = 0x0112
XMP = b"http://ns.adobe.com/xap/1.0/\x00<x:xmpmeta/>"


def _with_xmp(jpeg: bytes) -> bytes:
    """Return `jpeg` with an XMP segment after its SOI."""
    return jpeg[:2] + jpeg_segment(0xE1, XMP) + jpeg[2:]


def _write(folder: Path, name: str, body: bytes) -> Path:
    path = folder / name
    path.write_bytes(body)
    return path


def _camera_exif() -> bytes:
    exif = Image.Exif()
    exif[ORIENTATION] = 6
    exif[0x010F] = "Canon"
    exif[0x0110] = "EOS R5"
    exif[0x0132] = "2026:10:21 09:00:00"
    exif[0x8825] = {1: "N", 2: (51.0, 30.0, 0.0), 3: "W", 4: (0.0, 7.0, 0.0)}
    return exif.tobytes()


def _icc_xyz(x: float, y: float, z: float) -> bytes:
    return b"XYZ \x00\x00\x00\x00" + b"".join(
        struct.pack(">i", round(value * 65536)) for value in (x, y, z)
    )


def _display_p3() -> bytes:
    """Return a Display P3 matrix/TRC profile, D50-adapted, gamma 2.2."""
    text = b"Display P3"
    desc = (
        b"desc\x00\x00\x00\x00"
        + struct.pack(">I", len(text) + 1)
        + text
        + b"\x00"
        + b"\x00" * 8
        + b"\x00" * 3
        + b"\x00" * 67
    )
    curve = b"curv\x00\x00\x00\x00" + struct.pack(">IH", 1, 0x0233) + b"\x00\x00"
    tags = [
        (b"desc", desc),
        (b"wtpt", _icc_xyz(0.9642, 1.0, 0.8249)),
        (b"rXYZ", _icc_xyz(0.5151, 0.2412, -0.0011)),
        (b"gXYZ", _icc_xyz(0.2920, 0.6922, 0.0419)),
        (b"bXYZ", _icc_xyz(0.1571, 0.0666, 0.7841)),
        (b"rTRC", curve),
        (b"gTRC", curve),
        (b"bTRC", curve),
        (b"cprt", b"text\x00\x00\x00\x00none\x00"),
    ]
    offset = 128 + 4 + 12 * len(tags)
    table, data = b"", b""
    for signature, body in tags:
        table += signature + struct.pack(">II", offset + len(data), len(body))
        data += body + b"\x00" * (-len(body) % 4)
    body = struct.pack(">I", len(tags)) + table + data
    header = (
        struct.pack(">I", 128 + len(body))
        + b"\x00" * 4
        + struct.pack(">I", 0x02100000)
        + b"mntrRGB XYZ "
        + b"\x00" * 12
        + b"acsp"
        + b"\x00" * 24
        + struct.pack(">I", 0)
        + _icc_xyz(0.9642, 1.0, 0.8249)[8:]
        + b"\x00" * 48
    )
    return header + body


def _pixels(path: Path | bytes) -> bytes:
    source = io.BytesIO(path) if isinstance(path, bytes) else path
    with Image.open(source) as image:
        return image.convert("RGB").tobytes()


# --- cleaning ----------------------------------------------------------------


@pytest.mark.spec("import:clean:a-jpegs-exif-is-stripped")
def test_a_jpegs_exif_is_stripped_and_its_pixels_kept(tmp_path: Path) -> None:
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    original = photo_jpeg(exif=_camera_exif(), icc_profile=srgb)
    photo = _write(tmp_path, "portrait.jpg", original)
    staging = stage(tmp_path / "library")

    staged = read(photo, staging, LIMIT)

    source = staging / staged.name
    assert (staged.name, staged.state) == ("portrait.jpg", "ready")
    with Image.open(source) as image:
        assert dict(image.getexif()) == {ORIENTATION: 6}
    assert metadata_in(source.read_bytes()) == []
    assert _pixels(source) == _pixels(original)


@pytest.mark.spec("import:clean:another-profile-is-converted-to-srgb")
def test_a_display_p3_jpeg_is_converted_to_srgb(tmp_path: Path) -> None:
    p3 = _display_p3()
    original = photo_jpeg(icc_profile=p3)
    photo = _write(tmp_path, "wide.jpg", original)
    with Image.open(io.BytesIO(original)) as decoded:
        expected = ImageCms.profileToProfile(
            decoded,
            ImageCms.ImageCmsProfile(io.BytesIO(p3)),
            ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")),
        )
    assert expected is not None
    want = expected.getpixel((16, 16))
    assert isinstance(want, tuple)
    unconverted = tuple(_pixels(original)[:3])

    staged = read(photo, stage(tmp_path / "library"), LIMIT)

    source = tmp_path / "library" / ".staging"
    (path,) = source.glob(f"*/{staged.name}")
    assert staged.state == "converted"
    with Image.open(path) as image:
        assert "icc_profile" not in image.info
        got = image.convert("RGB").getpixel((16, 16))
    assert isinstance(got, tuple)
    assert max(abs(a - b) for a, b in zip(got, want, strict=True)) <= 3
    assert max(abs(a - b) for a, b in zip(unconverted, want, strict=True)) > 3

    # A PNG tagged Display P3, as a phone or desktop screenshot is.
    out = io.BytesIO()
    Image.new("RGB", (32, 32), (200, 80, 60)).save(out, "PNG", icc_profile=p3)
    screenshot = _write(tmp_path, "screen.png", out.getvalue())

    png = read(screenshot, stage(tmp_path / "library"), LIMIT)

    (path,) = source.glob(f"*/{png.name}")
    assert (png.name, png.state, png.carries) == ("screen.png", "converted", ())
    with Image.open(path) as image:
        assert "icc_profile" not in image.info
        got = image.convert("RGB").getpixel((16, 16))
    assert isinstance(got, tuple)
    assert max(abs(a - b) for a, b in zip(got, want, strict=True)) <= 3


@pytest.mark.spec("import:clean:a-heic-becomes-a-jpeg")
def test_a_heic_becomes_a_jpeg_with_its_orientation_in_its_pixels(
    tmp_path: Path,
) -> None:
    staging = stage(tmp_path / "library")
    turned = Image.Exif()
    turned[ORIENTATION] = 6
    out = io.BytesIO()
    Image.new("RGB", (40, 20), (10, 120, 200)).save(out, "WEBP", exif=turned.tobytes())
    webp = _write(tmp_path, "turned.webp", out.getvalue())

    heic = read(FIXTURES / "plain.heic", staging, LIMIT)
    rotated = read(webp, staging, LIMIT)

    assert (heic.name, heic.state) == ("plain.jpg", "converted")
    with Image.open(staging / heic.name) as image:
        assert (image.format, image.size) == ("JPEG", (64, 64))
        assert ORIENTATION not in image.getexif()
    with Image.open(staging / rotated.name) as image:
        assert (rotated.name, image.size) == ("turned.jpg", (20, 40))
        assert ORIENTATION not in image.getexif()


@pytest.mark.spec("import:clean:a-transparent-image-becomes-a-png")
def test_a_transparent_webp_becomes_a_png(tmp_path: Path) -> None:
    image = Image.new("RGBA", (32, 32), (200, 80, 60, 255))
    image.paste((0, 0, 0, 0), (0, 0, 16, 32))
    out = io.BytesIO()
    image.save(out, "WEBP", lossless=True)
    photo = _write(tmp_path, "cut-out.webp", out.getvalue())
    staging = stage(tmp_path / "library")

    staged = read(photo, staging, LIMIT)

    assert staged.name == "cut-out.png"
    with Image.open(staging / staged.name) as written:
        assert written.format == "PNG"

    # The same cut-out exported with a Display P3 profile.
    out = io.BytesIO()
    image.save(out, "WEBP", lossless=True, icc_profile=_display_p3())
    profiled = _write(tmp_path, "cut-out-p3.webp", out.getvalue())

    converted = read(profiled, staging, LIMIT)

    assert (converted.name, converted.state) == ("cut-out-p3.png", "converted")
    assert converted.carries == ()
    with Image.open(staging / converted.name) as written:
        assert written.format == "PNG"
        assert "icc_profile" not in written.info


@pytest.mark.spec("import:clean:a-16-bit-image-keeps-its-tones")
def test_a_16_bit_greyscale_tiff_keeps_its_tones(tmp_path: Path) -> None:
    out = io.BytesIO()
    Image.new("I;16", (32, 32), 20000).save(out, "TIFF")
    scan = _write(tmp_path, "film-scan.tiff", out.getvalue())
    staging = stage(tmp_path / "library")

    staged = read(scan, staging, LIMIT)

    assert (staged.name, staged.state) == ("film-scan.jpg", "converted")
    with Image.open(staging / staged.name) as written:
        grey = written.convert("L").getpixel((16, 16))
    assert isinstance(grey, int)
    assert abs(grey - 20000 // 257) <= 2

    # The same scan in Motorola byte order, which Pillow opens as `I;16B`.
    out = io.BytesIO()
    _sixteen_bit("I;16B", 20000).save(out, "TIFF")
    mac = _write(tmp_path, "mac-scan.tiff", out.getvalue())
    staging = stage(tmp_path / "library")

    staged = read(mac, staging, LIMIT)

    assert (staged.name, staged.state) == ("mac-scan.jpg", "converted")
    with Image.open(staging / staged.name) as written:
        grey = written.convert("L").getpixel((16, 16))
    assert isinstance(grey, int)
    assert abs(grey - 20000 // 257) <= 2

    # Every mode Pillow holds 16-bit greyscale in, including the two no file opens as.
    for mode in ("I;16", "I;16L", "I;16B", "I;16N", "I"):
        scaled = importing._eight_bit(_sixteen_bit(mode, 20000))
        grey = scaled.getpixel((16, 16))
        assert (mode, scaled.mode) == (mode, "L")
        assert isinstance(grey, int)
        assert abs(grey - 20000 // 257) <= 1, mode


def _sixteen_bit(mode: str, value: int) -> Image.Image:
    """Return a 32x32 greyscale image in `mode` whose every pixel holds `value`."""
    layout = {"I;16B": ">", "I;16N": "="}.get(mode, "<")
    width = "i" if mode == "I" else "H"
    return Image.frombytes(
        mode, (32, 32), struct.pack(f"{layout}{32 * 32}{width}", *[value] * 32 * 32)
    )


# --- refusing ----------------------------------------------------------------


@pytest.mark.spec("import:refuse:a-raw-photograph-is-refused")
def test_a_raw_photograph_is_refused_and_the_others_import(tmp_path: Path) -> None:
    nef = _write(tmp_path, "DSC_0001.NEF", nef_bytes())
    jpeg = _write(tmp_path, "portrait.jpg", photo_jpeg())
    batch = tmp_path / "library" / "trip"
    err = io.StringIO()
    wired = bare_wiring(err=err)
    args = build_parser().parse_args(
        ["import", "--batch", str(batch), str(nef), str(jpeg)]
    )

    code = dispatch(args, wired)

    assert code == 1
    assert "DSC_0001.NEF: a NEF RAW photograph" in err.getvalue()
    assert "export it as JPEG" in err.getvalue()
    assert [path.name for path in (batch / "sources").iterdir()] == ["portrait.jpg"]


@pytest.mark.spec("import:refuse:an-unconvertible-file-is-refused")
def test_a_file_that_cannot_be_converted_is_refused_and_the_others_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = io.BytesIO()
    _sixteen_bit("I;16B", 20000).save(out, "TIFF")
    scan = _write(tmp_path, "mac-scan.tiff", out.getvalue())
    jpeg = _write(tmp_path, "portrait.jpg", photo_jpeg())
    batch = tmp_path / "library" / "trip"
    args = build_parser().parse_args(
        ["import", "--batch", str(batch), str(scan), str(jpeg)]
    )

    code = dispatch(args, bare_wiring())

    assert code == 0
    assert sorted(path.name for path in (batch / "sources").iterdir()) == [
        "mac-scan.jpg",
        "portrait.jpg",
    ]

    # The same pair, with the scan's conversion failing as Pillow fails on a mode
    # it has no operation for.
    def unsupported(image: Image.Image) -> Image.Image:
        raise ValueError("point operation not supported for this mode")

    monkeypatch.setattr(importing, "_eight_bit", unsupported)
    other = tmp_path / "library" / "other"
    err = io.StringIO()
    args = build_parser().parse_args(
        ["import", "--batch", str(other), str(scan), str(jpeg)]
    )

    code = dispatch(args, bare_wiring(err=err))

    assert code == 1
    assert "refused: mac-scan.tiff: cannot be converted" in err.getvalue()
    assert "export it as an 8-bit JPEG and add it again" in err.getvalue()
    assert [path.name for path in (other / "sources").iterdir()] == ["portrait.jpg"]


@pytest.mark.spec("import:refuse:a-multi-image-file-is-refused")
def test_an_animated_gif_is_refused(tmp_path: Path) -> None:
    frames = [
        Image.new("RGB", (16, 16), colour) for colour in ((255, 0, 0), (0, 0, 255))
    ]
    out = io.BytesIO()
    frames[0].save(out, "GIF", save_all=True, append_images=frames[1:])
    gif = _write(tmp_path, "wave.gif", out.getvalue())

    with pytest.raises(Refusal, match="wave.gif: holds more than one image"):
        read(gif, stage(tmp_path / "library"), LIMIT)


@pytest.mark.spec("import:refuse:a-file-over-the-limit-is-refused")
def test_a_file_over_the_limit_is_refused_before_it_is_read(tmp_path: Path) -> None:
    large = _write(tmp_path, "large.jpg", b"\x00" * (1024 * 1024 + 1))
    staging = stage(tmp_path / "library")

    with pytest.raises(Refusal, match="past the 1 MB limit"):
        read(large, staging, 1024 * 1024)

    assert list(staging.iterdir()) == []


@pytest.mark.spec("import:refuse:what-render-would-refuse-is-refused")
def test_a_photograph_render_would_refuse_is_refused_at_import(
    tmp_path: Path,
) -> None:
    out = io.BytesIO()
    Image.new("RGB", (5000, 1000), (0, 0, 0)).save(out, "PNG")
    banner = _write(tmp_path, "banner.png", out.getvalue())
    staging = stage(tmp_path / "library")

    with pytest.raises(Refusal, match="past the 4096 limit on the long side"):
        read(banner, staging, LIMIT)

    assert list(staging.iterdir()) == []


# --- verifying ---------------------------------------------------------------


def _strip_misses_xmp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the strip hand back what it was given, XMP and all."""
    monkeypatch.setattr(importing, "strip_metadata", lambda photo: photo.read_bytes())


def _reencode_keeps_xmp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importing, "_reencode", lambda body: body)


@pytest.mark.spec("import:verify:a-failing-file-is-re-encoded")
def test_a_file_still_carrying_xmp_is_re_encoded_and_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _strip_misses_xmp(monkeypatch)
    photo = _write(tmp_path, "portrait.jpg", _with_xmp(photo_jpeg()))
    staging = stage(tmp_path / "library")

    staged = read(photo, staging, LIMIT)

    assert staged.state == "converted"
    assert verify(staging / staged.name) == []


@pytest.mark.spec("import:verify:an-uncleanable-file-is-left-out")
def test_a_file_that_cannot_be_cleaned_is_named_and_left_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _strip_misses_xmp(monkeypatch)
    _reencode_keeps_xmp(monkeypatch)
    library = tmp_path / "library"
    staging = stage(library)
    dirty = read(_write(tmp_path, "dirty.jpg", _with_xmp(photo_jpeg())), staging, LIMIT)
    clean = read(_write(tmp_path, "clean.jpg", photo_jpeg((1, 2, 3))), staging, LIMIT)

    done = commit(staging, library, "trip")

    assert (dirty.state, dirty.carries) == ("not cleaned", ("XMP",))
    assert clean.state == "ready"
    assert done.left_out == ("dirty.jpg",)
    assert [path.name for path in (library / "trip" / "sources").iterdir()] == [
        "clean.jpg"
    ]


@pytest.mark.spec("import:verify:an-uncleanable-file-chosen-imports")
def test_an_uncleanable_file_chosen_as_it_is_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _strip_misses_xmp(monkeypatch)
    _reencode_keeps_xmp(monkeypatch)
    library = tmp_path / "library"
    staging = stage(library)
    read(_write(tmp_path, "dirty.jpg", _with_xmp(photo_jpeg())), staging, LIMIT)

    commit(staging, library, "trip", as_is=["dirty.jpg"])

    source = library / "trip" / "sources" / "dirty.jpg"
    assert metadata_in(source.read_bytes()) == ["XMP"]


# --- staging -----------------------------------------------------------------


@pytest.mark.spec("import:stage:a-commit-moves-every-file")
def test_a_commit_moves_every_staged_file_into_the_batch(tmp_path: Path) -> None:
    library = tmp_path / "library"
    staging = stage(library)
    for name, colour in (("a.jpg", (1, 1, 1)), ("b.jpg", (2, 2, 2))):
        read(_write(tmp_path, name, photo_jpeg(colour)), staging, LIMIT)

    done = commit(staging, library, "trip")

    assert done.written == ("a.jpg", "b.jpg")
    assert sorted(p.name for p in (library / "trip" / "sources").iterdir()) == [
        "a.jpg",
        "b.jpg",
    ]
    assert not staging.exists()


@pytest.mark.spec("import:stage:a-cancel-deletes-staging")
def test_a_cancel_deletes_the_staging_folder(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir()
    staging = stage(library)
    read(_write(tmp_path, "a.jpg", photo_jpeg()), staging, LIMIT)

    cancel(staging)

    assert not staging.exists()
    assert list(library.iterdir()) == []


@pytest.mark.spec("import:stage:leftover-staging-is-swept")
def test_staging_left_behind_is_swept_at_start(tmp_path: Path) -> None:
    library = tmp_path / "library"
    left = stage(library)
    _write(left, "a.jpg", photo_jpeg())

    sweep(library)

    assert not left.exists()


@pytest.mark.spec("import:stage:same-bytes-skip-and-a-taken-name-is-renamed")
def test_the_same_bytes_are_skipped_and_a_taken_name_is_renamed(
    tmp_path: Path,
) -> None:
    library = tmp_path / "library"
    sources = library / "trip" / "sources"
    sources.mkdir(parents=True)
    _write(sources, "portrait.jpg", photo_jpeg((5, 5, 5)))
    staging = stage(library)
    read(_write(tmp_path, "again.jpg", photo_jpeg((5, 5, 5))), staging, LIMIT)
    other = tmp_path / "other"
    other.mkdir()
    read(_write(other, "portrait.jpg", photo_jpeg((9, 9, 9))), staging, LIMIT)

    done = commit(staging, library, "trip", add=True)

    assert done.skipped == ("again.jpg",)
    assert done.written == ("portrait-2.jpg",)
    assert sorted(p.name for p in sources.iterdir()) == [
        "portrait-2.jpg",
        "portrait.jpg",
    ]


@pytest.mark.spec("import:stage:an-unusable-name-is-refused")
@pytest.mark.parametrize("name", ["taken", "", "a/b", ".hidden"])
def test_an_unusable_batch_name_is_refused_and_staging_kept(
    tmp_path: Path, name: str
) -> None:
    library = tmp_path / "library"
    (library / "taken").mkdir(parents=True)
    staging = stage(library)
    read(_write(tmp_path, "a.jpg", photo_jpeg()), staging, LIMIT)

    with pytest.raises(Refusal):
        commit(staging, library, name)

    assert (staging / "a.jpg").is_file()


@pytest.mark.spec("import:stage:a-batch-git-can-reach-is-refused")
def test_a_batch_inside_the_working_tree_is_refused_and_nothing_written(
    tmp_path: Path,
) -> None:
    inside = REPO / "batch-in-the-tree"
    photo = _write(tmp_path, "portrait.jpg", photo_jpeg())
    err = io.StringIO()
    args = build_parser().parse_args(
        ["import", "--batch", str(inside / "trip"), str(photo)]
    )

    code = dispatch(args, bare_wiring(err=err))

    assert code == 1
    assert "under .data/ or at a directory outside the repository" in err.getvalue()
    assert not inside.exists()

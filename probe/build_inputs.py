r"""Build the five probe inputs for the v0.11 metered session.

The inputs are **not committed** -- this repository commits `run.json` artifacts
and never inputs, and committing derived faces into a project whose product is
identity preservation invites a confusion the README would then have to disclaim
(design.md D14). This recipe is committed instead, and it takes its sources and
its destination as arguments, so no path outside this repository is tracked.

Four of the five are the render inputs v0.10's CHANGELOG named as untested:

  a  landscape        832x554   -- short-side rounding on the height axis, first time
  b  above the scale  1248x1400 -- an aspect no prior run produced
  c  rotated JPEG     1216x832  -- pixels stored landscape, EXIF Orientation 6
  d  plain JPEG       832x1216  -- the same portrait, no EXIF at all

`d` is the control: without it, a failure on `c` is not attributable to the tag
rather than to the codec, which this project has never fed to a pod.

The fifth is not a render input. `e` is a PNG carrying an `eXIf` chunk, and it
exists for the loader probe: it is what decides whether ComfyUI's `LoadImage`
transposes PNGs the way it transposes JPEGs (design.md D11, D12).

Pixels move through ImageMagick's `convert`, because a crop needs an exact
origin and `sips --cropOffset` is measured from the centre. The EXIF blocks are
built by `tests/images.exif_tiff` -- the suite's own helper, so the tag is
written by code the gate already holds.

    python probe/build_inputs.py --portrait <832x1216.png> \
        --tall <1248x1824.png> --out <dir>
"""

import argparse
import hashlib
import shutil
import struct
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.images import exif_tiff, png_chunk  # noqa: E402

# The face sits in the upper third of the source portrait, so the landscape band
# is taken from y=110 rather than from the centre: a centred crop of a standing
# figure is a crop of its chest, and a probe input with no face in it measures
# the scale node while proving nothing about the rest of the graph.
LANDSCAPE_CROP = (832, 554, 0, 110)

# The tall source is a full-height figure with the head near the top, so the
# crop that changes its aspect is taken from the top edge.
ABOVE_SCALE_CROP = (1248, 1400, 0, 0)

ORIENTATION_ROTATED = 6

# Every APPn marker. A JPEG written by an encoder carries its own metadata, and
# the probe needs to state exactly one thing about orientation -- so the control
# is stripped to nothing and the rotated file carries a single segment this
# script wrote.
_APPN = range(0xE0, 0xF0)
_STANDALONE = {0x01, *range(0xD0, 0xD8)}
_START_OF_SCAN = 0xDA

# The SOFn markers that carry a frame's dimensions. 0xC4, 0xC8 and 0xCC are DHT,
# JPG and DAC, which are not frame headers and whose payloads would decode to
# nonsense sizes if read as one.
_SOF_MARKERS = frozenset(set(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC})


# ImageMagick stamps a PNG with the time it wrote it, so two runs of an identical
# recipe produce different bytes and the SHA-256 in `README.md` verifies nothing.
# Excluding the date chunks and stripping profiles makes the recipe reproducible,
# which is the only reason to record a digest for a file that is not committed.
_DETERMINISTIC = ("-strip", "-define", "png:exclude-chunks=date,time")


def _convert(*args: str) -> None:
    """Run ImageMagick, failing loudly rather than leaving a half-built input.

    The determinism flags are spliced in ahead of the output path, because
    ImageMagick reads its arguments as a pipeline and takes the last one as the
    destination.
    """
    if shutil.which("convert") is None:
        sys.exit("ImageMagick's `convert` is not on PATH; cannot build the inputs.")
    *pipeline, destination = args
    subprocess.run(["convert", *pipeline, *_DETERMINISTIC, destination], check=True)


def _crop(source: Path, out: Path, box: tuple[int, int, int, int]) -> None:
    """Write `source` cropped to an exact width, height and origin."""
    width, height, x, y = box
    _convert(str(source), "-crop", f"{width}x{height}+{x}+{y}", "+repage", str(out))


def segments(jpeg: bytes) -> Iterator[tuple[int, int, int]]:
    """Yield `(marker code, offset, whole-segment length)` for each segment.

    One walk, because both consumers below need the same one: the marker byte, and
    how far to step. It stops at the scan -- past which there are no segments,
    only entropy-coded data that would decode to nonsense if read as one -- and
    reports the scan itself last so a caller can copy the remainder.
    """
    i = 2
    while i < len(jpeg) and jpeg[i] == 0xFF:
        code = jpeg[i + 1]
        if code in _STANDALONE:
            yield code, i, 2
            i += 2
            continue
        if code == _START_OF_SCAN:
            yield code, i, len(jpeg) - i
            return
        (length,) = struct.unpack(">H", jpeg[i + 2 : i + 4])
        yield code, i, 2 + length
        i += 2 + length


def strip_app_segments(jpeg: bytes) -> bytes:
    """Return the JPEG with every APPn segment removed."""
    out = bytearray(jpeg[:2])
    for code, offset, length in segments(jpeg):
        if code not in _APPN:
            out += jpeg[offset : offset + length]
    return bytes(out)


def jpeg_with_orientation(jpeg: bytes, orientation: int | None) -> bytes:
    """Return the JPEG carrying exactly this Orientation, or none at all."""
    body = strip_app_segments(jpeg)
    if orientation is None:
        return body
    payload = b"Exif\x00\x00" + exif_tiff(orientation)
    app1 = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    return body[:2] + app1 + body[2:]


def png_with_exif(png: bytes, orientation: int) -> bytes:
    r"""Return the PNG with an `eXIf` chunk declaring this Orientation.

    The chunk carries the TIFF block raw, with no `Exif\x00\x00` marker -- that
    marker is JPEG's, and PNG's own spec defines the chunk as the TIFF stream
    itself. Inserted straight after IHDR, which is where a writer puts it and
    where a reader will find it before any pixel data.
    """
    # Signature, then IHDR's length word, type, payload and CRC.
    ihdr_end = 8 + 8 + struct.unpack(">I", png[8:12])[0] + 4
    return png[:ihdr_end] + png_chunk(b"eXIf", exif_tiff(orientation)) + png[ihdr_end:]


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Return the width and height a PNG's IHDR declares."""
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_stored_size(jpeg: bytes) -> tuple[int, int]:
    """Return the dimensions the JPEG's frame header states, the tag ignored.

    The stored size on purpose: the probe's whole question is what a reader does
    with the orientation beside it, so applying it here would erase the thing
    being measured. `isekai.workflow.image_dimensions` is therefore not the helper
    to call -- it answers the opposite question.
    """
    for code, offset, _ in segments(jpeg):
        if code in _SOF_MARKERS:
            height, width = struct.unpack(">HH", jpeg[offset + 5 : offset + 9])
            return width, height
    raise SystemExit("no frame header in the built JPEG")


def main() -> int:
    """Build all five inputs and print the table `probe/README.md` records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portrait", required=True, help="an 832x1216 PNG portrait")
    parser.add_argument("--tall", required=True, help="a 1248x1824 PNG portrait")
    parser.add_argument("--out", required=True, help="destination directory")
    args = parser.parse_args()

    portrait, tall = Path(args.portrait), Path(args.tall)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    built: list[Path] = []

    landscape = out / "a_landscape.png"
    _crop(portrait, landscape, LANDSCAPE_CROP)
    built.append(landscape)

    above = out / "b_above_scale.png"
    _crop(tall, above, ABOVE_SCALE_CROP)
    built.append(above)

    # Rotated 90 degrees clockwise, so the pixels are stored landscape and the
    # tag is the only thing saying otherwise -- byte for byte what a phone
    # writes, and `LoadImage` cannot tell who wrote it.
    rotated_raw = out / "c_rotated.raw.jpg"
    _convert(str(portrait), "-rotate", "90", "-quality", "95", str(rotated_raw))
    rotated = out / "c_rotated.jpg"
    rotated.write_bytes(
        jpeg_with_orientation(rotated_raw.read_bytes(), ORIENTATION_ROTATED)
    )
    rotated_raw.unlink()
    built.append(rotated)

    control_raw = out / "d_control.raw.jpg"
    _convert(str(portrait), "-quality", "95", str(control_raw))
    control = out / "d_control.jpg"
    control.write_bytes(jpeg_with_orientation(control_raw.read_bytes(), None))
    control_raw.unlink()
    built.append(control)

    exif_png = out / "e_png_exif.png"
    exif_png.write_bytes(png_with_exif(portrait.read_bytes(), ORIENTATION_ROTATED))
    built.append(exif_png)

    print(f"{'file':<20} {'stored':>11}  sha256")
    for path in built:
        data = path.read_bytes()
        if path.suffix == ".png":
            width, height = png_dimensions(data)
        else:
            # The stored size of a JPEG is what the frame header says; the probe
            # is about what a reader does with the tag beside it.
            width, height = jpeg_stored_size(data)
        digest = hashlib.sha256(data).hexdigest()
        print(f"{path.name:<20} {f'{width}x{height}':>11}  {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

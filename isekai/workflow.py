"""Locate nodes in a ComfyUI graph, and wire the photo into one."""

import struct
import sys
from pathlib import Path
from typing import BinaryIO, NamedTuple

from isekai.comfy_types import Workflow

# The one graph, anchored to the repository rather than to the working
# directory: `convert.py` is run in place, and a CWD-relative path would make
# the product's only workflow unloadable from anywhere but the repo root. The
# suite loads the same constant, so the filename is spelled once.
PIPELINE_PATH = Path(__file__).parent.parent / "workflows" / "pipeline.json"

# The short side every render is normalised to, and the step both dimensions are
# rounded to. 1024 is the SDXL family's trained scale and the floor MistoLine's
# card names; 64 is the latent stride, so an off-step dimension is padded by the
# encoder rather than honoured. The rule -- short side, aspect preserved, both
# dimensions on the step -- is the spec's; this is the number it left open.
WORKING_SCALE = 1024
DIMENSION_STEP = 64

# Three stated ceilings (design.md D8). A short-side rule places no bound on the
# other axis, and a header field is an unverified number until something bounds
# it. Each refuses rather than clamping: a clamped target no longer preserves the
# aspect ratio, and would squash the photo the way the orientation rule exists to
# prevent.
#
#   4096 is 4:1 at a 1024 short side -- past any real photo, and 1024x4096 is
#   already a heavy SDXL allocation.
#   65535 is what JPEG's two-byte frame field already enforces, so both codecs
#   refuse the same input.
#   4 MiB is generous for a camera's EXIF, thumbnail, ICC and XMP together --
#   a few hundred KiB -- without being unbounded.
MAX_TARGET_LONG_SIDE = 4096
MAX_HEADER_DIMENSION = 65535
MAX_HEADER_BYTES = 4 * 1024 * 1024

# The SOFn markers that carry a JPEG frame's dimensions. The gaps are deliberate:
# 0xC4, 0xC8 and 0xCC are DHT, JPG and DAC, which are not frame headers and whose
# payloads would decode to nonsense sizes if read as one.
_JPEG_SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)

# Markers with no length word: TEM and the eight restart markers.
_JPEG_STANDALONE_MARKERS = frozenset(
    {0x01, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7}
)
_JPEG_START_OF_SCAN = 0xDA
_JPEG_APP1 = 0xE1

# EXIF Orientation, and the four of its eight values that transpose the image.
# ComfyUI's LoadImage applies the tag before any node sees the pixels, so on these
# four the frame header's dimensions are not the ones the graph is handed.
_EXIF_ORIENTATION_TAG = 0x0112
_EXIF_TRANSPOSING_ORIENTATIONS = frozenset({5, 6, 7, 8})

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# PNG carries the same EXIF payload JPEG does, in an `eXIf` chunk holding the TIFF
# stream raw -- the `Exif\x00\x00` marker is JPEG's container, not this one. The
# walk stops at the pixel data, past which a writer may not put it.
_PNG_EXIF_CHUNK = b"eXIf"
_PNG_PIXEL_CHUNKS = frozenset({b"IDAT", b"IEND"})


class _HeaderTooDeep(Exception):
    """The marker walk passed `MAX_HEADER_BYTES` without reaching a frame header."""


class _Header(NamedTuple):
    """What an image's header states: the stored size, and the loader's correction.

    Both codec parsers report this rather than each applying the correction, so
    the loader's behaviour -- that it transposes on four of the eight orientation
    values before any node sees the pixels -- is stated once, in
    `image_dimensions`, instead of once per codec. A third codec would inherit it.
    """

    width: int
    height: int
    orientation: int


def find_nodes(workflow: Workflow, *, class_type: str) -> list[str]:
    """Return every node ID with this class_type, in the graph's own order."""
    return [
        nid for nid, node in workflow.items() if node.get("class_type") == class_type
    ]


def find_node(workflow: Workflow, *, class_type: str) -> str:
    """Return the single node ID with this class_type.

    Fail if the match is not exactly one node: an injection that edits the wrong
    node produces a silently wrong render rather than an error.
    """
    matches = find_nodes(workflow, class_type=class_type)

    if len(matches) != 1:
        sys.exit(
            f"find_node(class_type={class_type!r}): "
            f"expected exactly 1 match, found {len(matches)}"
        )

    return matches[0]


def _png_dimensions(handle: BinaryIO) -> _Header | None:
    """Return what a PNG's header states, or None if the file is not one.

    IHDR states the stored size; an `eXIf` chunk may then declare an orientation.
    Both are read, because the phase-6 loader probe measured the pinned build and
    found `LoadImage` applies the orientation to a PNG exactly as it applies it to
    a tagged JPEG -- and every input this project has ever rendered is a PNG.

    The chunk walk reads each chunk's header and seeks over its payload, so this
    stays a header parse: a writer may put `eXIf` anywhere before the pixel data,
    and looking only straight after IHDR would report the untransposed pair.
    """
    handle.seek(0)
    header = handle.read(24)
    if (
        len(header) < 24
        or not header.startswith(_PNG_SIGNATURE)
        or header[12:16] != b"IHDR"
    ):
        return None
    width, height = struct.unpack(">II", header[16:24])

    # Past IHDR, whose length word is already in hand: signature, length, type,
    # payload, CRC.
    (ihdr_length,) = struct.unpack(">I", header[8:12])
    handle.seek(len(_PNG_SIGNATURE) + 8 + ihdr_length + 4)
    while True:
        if handle.tell() > MAX_HEADER_BYTES:
            raise _HeaderTooDeep
        chunk = handle.read(8)
        if len(chunk) < 8:
            break
        (length,) = struct.unpack(">I", chunk[:4])
        kind = chunk[4:8]
        if kind in _PNG_PIXEL_CHUNKS:
            break
        if kind == _PNG_EXIF_CHUNK:
            return _Header(width, height, _tiff_orientation(handle.read(length)))
        # payload, then the chunk's own four-byte CRC
        handle.seek(length + 4, 1)

    return _Header(width, height, 1)


def _exif_orientation(segment: bytes) -> int:
    """Return the Orientation tag in a JPEG APP1 segment, or 1 if it declares none."""
    if not segment.startswith(b"Exif\x00\x00"):
        return 1
    return _tiff_orientation(segment[6:])


def _tiff_orientation(tiff: bytes) -> int:
    """Return the Orientation tag in a TIFF block, or 1 if it declares none.

    1 is the identity, and is what an absent tag or an unreadable IFD both mean:
    orientation is a correction, so the safe reading of "not stated" is "no
    correction". The block is the payload of JPEG's APP1 and of PNG's `eXIf`
    alike, which is why the two codecs share this walk rather than each having
    one.
    """
    if len(tiff) < 8:
        return 1
    if tiff[:2] == b"II":
        endian = "<"
    elif tiff[:2] == b"MM":
        endian = ">"
    else:
        return 1

    (offset,) = struct.unpack(endian + "I", tiff[4:8])
    if offset + 2 > len(tiff):
        return 1
    (count,) = struct.unpack(endian + "H", tiff[offset : offset + 2])

    for n in range(count):
        entry = offset + 2 + n * 12
        if entry + 12 > len(tiff):
            return 1
        (tag,) = struct.unpack(endian + "H", tiff[entry : entry + 2])
        if tag == _EXIF_ORIENTATION_TAG:
            # A SHORT is left-justified in the entry's four value bytes, so the
            # value is the first two of them under either byte order.
            (value,) = struct.unpack(endian + "H", tiff[entry + 8 : entry + 10])
            return value

    return 1


def _jpeg_dimensions(handle: BinaryIO) -> _Header | None:
    """Return what a JPEG's header states, or None if it is unreadable.

    Walks the marker segments against the open file rather than over a fixed
    prefix: an EXIF segment carrying an embedded thumbnail is alone allowed to be
    65 533 bytes, and a camera writes ICC and XMP segments besides, so the frame
    header's offset is bounded by nothing in particular. Only each segment's
    header is read; the payloads are seeked over, so this stays a header parse.
    """
    handle.seek(0)
    if handle.read(2) != b"\xff\xd8":
        return None

    orientation = 1
    while True:
        # Bounded by a stated number rather than by the file, which is not a
        # bound: a 100 MB file walked to its end takes seconds to refuse.
        if handle.tell() > MAX_HEADER_BYTES:
            raise _HeaderTooDeep
        byte = handle.read(1)
        if byte != b"\xff":
            return None
        # Fill bytes between segments are written as repeated 0xFF.
        marker = handle.read(1)
        while marker == b"\xff":
            marker = handle.read(1)
        if not marker:
            return None
        code = marker[0]

        # Standalone markers carry no length word; reading one as length-bearing
        # would step the walk into entropy-coded data and read it as a header.
        if code in _JPEG_STANDALONE_MARKERS:
            continue
        # The scan is where the header ends: past it there is no frame header to
        # find, only compressed data that would decode to nonsense as one.
        if code == _JPEG_START_OF_SCAN:
            return None

        raw = handle.read(2)
        if len(raw) < 2:
            return None
        (length,) = struct.unpack(">H", raw)
        # The length field counts itself, so anything below 2 is malformed.
        if length < 2:
            return None
        payload_start = handle.tell()

        if code in _JPEG_SOF_MARKERS:
            frame = handle.read(5)
            if len(frame) < 5:
                return None
            height, width = struct.unpack(">HH", frame[1:5])
            return _Header(width, height, orientation)

        if code == _JPEG_APP1 and orientation == 1:
            orientation = _exif_orientation(handle.read(length - 2))

        handle.seek(payload_start + length - 2)


def image_dimensions(path: str) -> tuple[int, int]:
    """Return the pixel dimensions a JPEG or PNG will be loaded at.

    Stdlib only, by parsing the header directly: the runtime carries no imaging
    wheel and this is on `convert.py`'s import graph.

    An unreadable or truncated header stops the run naming the file. There is no
    default size, because a silently wrong resolution is a wrong render rather
    than an error (design.md D2).

    A header that declares a dimension past `MAX_HEADER_DIMENSION`, and a marker
    walk that passes `MAX_HEADER_BYTES` without reaching a frame header, are each
    refused the same way and for the same reason: the header states a number, and
    a number nothing bounds is not a measurement.
    """
    try:
        with open(path, "rb") as handle:
            # Both are chunk or segment walks against the open file rather than
            # over a prefix guessed to be long enough: PNG's orientation chunk and
            # JPEG's frame header alike sit after however much metadata the writer
            # put in front of them.
            header = _png_dimensions(handle) or _jpeg_dimensions(handle)
    except OSError as e:
        sys.exit(f"{path}: cannot be read ({e.strerror})")
    except _HeaderTooDeep:
        sys.exit(
            f"{path}: no frame header in the first {MAX_HEADER_BYTES} bytes; "
            f"refusing to walk further"
        )

    if header is None or 0 in (header.width, header.height):
        sys.exit(f"{path}: cannot read the image dimensions from its header")

    if max(header.width, header.height) > MAX_HEADER_DIMENSION:
        sys.exit(
            f"{path}: header declares {header.width}x{header.height}, past the "
            f"{MAX_HEADER_DIMENSION} limit either dimension may state"
        )

    # The one statement of what the loader does with the tag, for every codec.
    if header.orientation in _EXIF_TRANSPOSING_ORIENTATIONS:
        return header.height, header.width
    return header.width, header.height


def working_resolution(width: int, height: int) -> tuple[int, int]:
    """Return the render target for a photo of this size.

    Aspect preserved, short side at `WORKING_SCALE`, both dimensions on
    `DIMENSION_STEP`. Applied in both directions, so a photo below the working
    scale is scaled up as well as a larger one down: scaling is a normalisation,
    not a ceiling.

    Expressed as a short side rather than a pixel budget on purpose. At a fixed
    megapixel count the short side moves with the aspect ratio, so a wide photo
    lands below the line-art ControlNet's floor while a squarer one clears it --
    a failure that varies by input and reports nothing (design.md D2).
    """
    scale = WORKING_SCALE / min(width, height)
    long_side = round(max(width, height) * scale / DIMENSION_STEP) * DIMENSION_STEP
    return (long_side, WORKING_SCALE) if width >= height else (WORKING_SCALE, long_side)


def inject(workflow: Workflow, image_name: str, image_path: str) -> None:
    """Wire the uploaded photo into the pipeline graph.

    Mutates `workflow` in place. The positive prompt is committed to the graph,
    so the photo -- its uploaded name, and the render target derived from its own
    dimensions -- is the only thing injection wires.

    `image_path` is the photo on local disk, which the graph cannot read: no node
    available to this pipeline derives a target from the image it is given, so
    the dimensions are computed here and written in. It stays an argument, passed
    from the `input_path` `pipeline.run` already holds, rather than becoming state.
    """
    load_id = find_node(workflow, class_type="LoadImage")
    workflow[load_id]["inputs"]["image"] = image_name

    scale_id = find_node(workflow, class_type="ImageScale")
    width, height = working_resolution(*image_dimensions(image_path))
    if max(width, height) > MAX_TARGET_LONG_SIDE:
        sys.exit(
            f"{image_path}: a {width}x{height} target is past the "
            f"{MAX_TARGET_LONG_SIDE} limit on the long side; the short-side rule "
            f"bounds one axis and this photo's aspect ratio is extreme"
        )
    workflow[scale_id]["inputs"]["width"] = width
    workflow[scale_id]["inputs"]["height"] = height

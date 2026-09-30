"""What a photograph is, and what render target it implies.

Reads a JPEG or PNG header -- dimensions and the orientation tag the loader will
apply -- and turns the answer into the target the render is normalised to. It
touches no ComfyUI graph: the flow's manifest names the node that takes the
target, and the caller writes it there.

Also strips a photograph's metadata for upload: a byte walk over the same
segments and chunks, keeping what decodes and never re-encoding.
"""

import io
import re
import struct
import sys
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO, NamedTuple

from isekai.foundation.refusal import Refusal

# The short side every render is normalised to, and the step both dimensions are
# rounded to. 1024 is the SDXL family's trained scale; 64 is the latent stride, so
# an off-step dimension is padded by the encoder rather than honoured. The rule --
# short side, aspect preserved, both dimensions on the step -- is the spec's; this
# is the number it left open.
WORKING_SCALE = 1024
DIMENSION_STEP = 64

# Three stated ceilings. A short-side rule places no bound on the
# other axis, and a header field is an unverified number until something bounds
# it. Each refuses rather than clamping: a clamped target no longer preserves the
# aspect ratio, and would squash the photo the way the orientation rule exists to
# prevent.
#
# Two of the three are enforced here, where the header is read. The third bounds
# a *computed target* rather than a header field, so it is enforced where a target
# is computed for a render -- `generate.photo_resolution`, which is also the only
# caller that can turn it into a per-photograph refusal instead of a dead batch.
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
    """A header walk passed `MAX_HEADER_BYTES` without reaching what it sought.

    Carries the codec, because both walks raise it: a PNG's chunk walk and a
    JPEG's marker walk look for different structures, and a refusal that names
    the wrong one tells an operator their file lacks something it never had.
    """

    def __init__(self, codec: str) -> None:
        super().__init__(codec)
        self.codec = codec


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
            raise _HeaderTooDeep("PNG")
        chunk = handle.read(8)
        if len(chunk) < 8:
            break
        (length,) = struct.unpack(">I", chunk[:4])
        kind = chunk[4:8]
        if kind in _PNG_PIXEL_CHUNKS:
            break
        if kind == _PNG_EXIF_CHUNK:
            # The one payload this walk materialises instead of seeking over, so
            # the one place a header-declared length is bounded before it is
            # read rather than after: a chunk header may state 4 GiB, and a read
            # on that word alone is a `MemoryError` that escapes as a traceback
            # instead of the refusal that names the file and the budget.
            if handle.tell() + length > MAX_HEADER_BYTES:
                raise _HeaderTooDeep("PNG")
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
            raise _HeaderTooDeep("JPEG")
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

    Stdlib only, by parsing the header directly: this is on `python -m isekai`'s
    import graph, which reaches no wheel.

    An unreadable or truncated header stops the run naming the file. There is no
    default size, because a silently wrong resolution is a wrong render rather
    than an error.

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
    except _HeaderTooDeep as deep:
        sys.exit(
            f"{path}: its {deep.codec} header is not resolved within the first "
            f"{MAX_HEADER_BYTES} bytes; refusing to walk further"
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
    lands below the base family's own trained scale while a squarer one clears it
    -- a failure that varies by input and reports nothing.
    """
    scale = WORKING_SCALE / min(width, height)
    long_side = round(max(width, height) * scale / DIMENSION_STEP) * DIMENSION_STEP
    return (long_side, WORKING_SCALE) if width >= height else (WORKING_SCALE, long_side)


def dimensions_or_refuse(photo: Path, remedy: str) -> tuple[int, int]:
    """Return a photograph's dimensions as a `Refusal` rather than an exit.

    `image_dimensions` stops the process with `sys.exit`, which is correct for
    the single-photograph command it was written for and wrong for every batch:
    a `SystemExit` is a `BaseException`, so `across` walks straight past it and
    the remaining photographs die with it.

    **One wrap, for `generate.photo_resolution` and `ui/batch.py` alike**, so the
    identical failure has one wording. It lives here rather than at either caller
    because the hazard is a property of `image_dimensions` and every future caller
    inherits it; `remedy` is a parameter because what to do about it is not --
    the render path says *open the run again* and the review surface says *start
    the surface again*.
    """
    try:
        return image_dimensions(str(photo))
    except SystemExit as unreadable:
        raise Refusal(f"{unreadable}; {remedy}") from unreadable


# What a stripped photograph keeps. An allowlist rather than a
# list of metadata to drop: a block nobody named -- an appended video, a depth
# map, a provenance record -- goes without anyone having to name it.
_JPEG_KEPT_TABLES = _JPEG_SOF_MARKERS | {0xC4, 0xCC, 0xDB, 0xDD}  # DHT DAC DQT DRI
_JPEG_KEPT_APPS = {0xE0: b"JFIF\x00", 0xEE: b"Adobe"}
# JFIF's and Adobe's fixed fields, by payload length. Past them a JFIF header
# carries a thumbnail and an Adobe one whatever a writer appended, so each is cut
# to its fields -- JFIF's thumbnail size zeroed -- rather than copied whole; one
# too short to hold them is what a decoder ignores, and is dropped.
_JPEG_FIXED_FIELDS = {0xE0: 14, 0xEE: 12}
_JPEG_DROPPED = frozenset(range(0xE0, 0xF0)) | {0xFE}  # every APPn, and COM
_JPEG_END_OF_IMAGE = 0xD9
# Inside a scan, 0xFF is followed by a stuffed 0x00 or a restart marker; any
# other byte after it starts the next segment.
_JPEG_SCAN_END = re.compile(rb"\xff[^\x00\xd0-\xd7]")
# No colour chunk is kept: the endpoint decodes without them.
_PNG_KEPT_CHUNKS = frozenset({b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS"})


class _Unwalkable(Exception):
    """A photograph's blocks cannot be read to the image's end."""


def strip_metadata(photo: Path) -> bytes:
    """Return the photograph's bytes with every block decoding does not need removed.

    The pixel data and the orientation are kept -- the orientation as a minimal
    EXIF of its own -- and anything after the image's end goes. A photograph the
    walk cannot read to its end is refused rather than sent whole.
    """
    try:
        data = photo.read_bytes()
        if data.startswith(_PNG_SIGNATURE):
            return _strip_png(data)
        if data.startswith(b"\xff\xd8"):
            return _strip_jpeg(data)
        reason = "it is neither a JPEG nor a PNG"
    except OSError as unreadable:
        reason = f"it cannot be read ({unreadable.strerror})"
    except _Unwalkable as unwalkable:
        reason = str(unwalkable)
    raise Refusal(
        f"{photo.name}: its metadata cannot be stripped for upload -- {reason}; "
        "re-export the photograph as a JPEG or PNG and open the run again"
    )


def _strip_jpeg(data: bytes) -> bytes:
    """Return a JPEG's kept segments and scans, ending at its first EOI."""
    kept = [data[:2]]
    at = 2
    while at < len(data):
        if data[at] != 0xFF:
            raise _Unwalkable(f"byte {at} is not a marker")
        # Fill bytes before a marker are written as repeated 0xFF.
        while at + 1 < len(data) and data[at + 1] == 0xFF:
            at += 1
        if at + 1 >= len(data):
            raise _Unwalkable("it ends inside a marker")
        code, start, at = data[at + 1], at, at + 2
        if code == _JPEG_END_OF_IMAGE:
            kept.append(data[start:at])
            break
        if code in _JPEG_STANDALONE_MARKERS:
            continue
        # A length word cut short by the file's end reads short, and is refused.
        end = at + int.from_bytes(data[at : at + 2], "big")
        if end < at + 2 or end > len(data):
            raise _Unwalkable(f"the segment at byte {start} runs past the file")
        if code == _JPEG_START_OF_SCAN:
            scan = _JPEG_SCAN_END.search(data, end)
            if scan is None:
                raise _Unwalkable("a scan runs past the end of the file")
            kept += [data[start:end], data[end : scan.start()]]
            end = scan.start()
        elif code in _JPEG_KEPT_TABLES or (
            code in _JPEG_KEPT_APPS
            and data.startswith(_JPEG_KEPT_APPS[code], at + 2, end)
        ):
            fixed = _JPEG_FIXED_FIELDS.get(code)
            if fixed is None:
                kept.append(data[start:end])
            elif end - at - 2 >= fixed:
                fields = data[at + 2 : at + 2 + fixed]
                if code == 0xE0:
                    fields = fields[:-2] + b"\x00\x00"
                kept.append(data[start:at] + struct.pack(">H", fixed + 2) + fields)
        elif code not in _JPEG_DROPPED:
            # Dropping a marker the walk does not know could change the pixels.
            raise _Unwalkable(f"it carries marker 0x{code:02X}, which is not known")
        at = end

    tiff = _orientation_tiff(_jpeg_dimensions, data)
    if tiff:
        exif = b"Exif\x00\x00" + tiff
        # JFIF must stay first, so the orientation goes in behind it.
        exif_at = 2 if kept[1:2] and kept[1][1] == 0xE0 else 1
        kept.insert(exif_at, b"\xff\xe1" + struct.pack(">H", len(exif) + 2) + exif)
    return b"".join(kept)


def _strip_png(data: bytes) -> bytes:
    """Return a PNG's kept chunks, ending at IEND. CRCs are copied, never checked."""
    kept = [_PNG_SIGNATURE]
    at = len(_PNG_SIGNATURE)
    while at < len(data):
        # A length word cut short by the file's end reads short, and is refused.
        end = at + 8 + int.from_bytes(data[at : at + 4], "big") + 4
        if end > len(data):
            raise _Unwalkable(f"the chunk at byte {at} runs past the file")
        kind = data[at + 4 : at + 8]
        if len(kept) == 1 and kind != b"IHDR":
            raise _Unwalkable("its first chunk is not IHDR")
        if kind in _PNG_KEPT_CHUNKS:
            kept.append(data[at:end])
        elif not kind[0] & 0x20:
            # An uppercase first letter marks a chunk the decoder cannot skip.
            raise _Unwalkable(f"it carries critical chunk {kind!r}, which is not known")
        at = end
        if kind == b"IEND":
            break

    tiff = _orientation_tiff(_png_dimensions, data)
    if tiff:
        chunk = struct.pack(">I", len(tiff)) + _PNG_EXIF_CHUNK + tiff
        kept.insert(2, chunk + struct.pack(">I", zlib.crc32(chunk[4:])))
    return b"".join(kept)


def _orientation_tiff(
    parse: Callable[[BinaryIO], _Header | None], data: bytes
) -> bytes:
    """Return a big-endian TIFF holding the orientation alone; b"" if upright.

    The header reader reads the orientation, so the upload turns as the render
    target was sized. An unreadable value is upright, as that reader treats it.
    """
    try:
        header = parse(io.BytesIO(data))
    except _HeaderTooDeep as deep:
        raise _Unwalkable(
            f"its {deep.codec} header is not resolved within the first "
            f"{MAX_HEADER_BYTES} bytes"
        ) from deep
    orientation = header.orientation if header else 1
    if not 2 <= orientation <= 8:
        return b""
    entry = struct.pack(">HHIHH", _EXIF_ORIENTATION_TAG, 3, 1, orientation, 0)
    return b"MM\x00\x2a" + struct.pack(">IH", 8, 1) + entry + struct.pack(">I", 0)

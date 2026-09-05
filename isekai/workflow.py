"""Locate nodes in a ComfyUI graph, and wire the photo into one."""

import struct
import sys
from pathlib import Path

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

# The SOFn markers that carry a JPEG frame's dimensions. The gaps are deliberate:
# 0xC4, 0xC8 and 0xCC are DHT, JPG and DAC, which are not frame headers and whose
# payloads would decode to nonsense sizes if read as one.
_JPEG_SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


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


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return the width and height in a PNG's IHDR, or None if it is not readable."""
    if not data.startswith(_PNG_SIGNATURE) or data[12:16] != b"IHDR":
        return None
    if len(data) < 24:
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return the width and height in a JPEG's frame header, or None if unreadable.

    Walks the marker segments rather than seeking to a fixed offset: the frame
    header sits after however many application and quantisation segments the
    encoder wrote, and its position is not a constant.
    """
    if not data.startswith(b"\xff\xd8"):
        return None

    i = 2
    while i + 3 < len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        # Padding between segments is written as repeated 0xFF; skip one at a time.
        if marker == 0xFF:
            i += 1
            continue
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if marker in _JPEG_SOF_MARKERS:
            if i + 9 > len(data):
                return None
            height, width = struct.unpack(">HH", data[i + 5 : i + 9])
            return width, height
        i += 2 + length

    return None


def image_dimensions(path: str) -> tuple[int, int]:
    """Return the pixel dimensions in a JPEG or PNG file's header.

    Stdlib only, by parsing the header directly: the runtime carries no imaging
    wheel and this is on `convert.py`'s import graph.

    An unreadable or truncated header stops the run naming the file. There is no
    default size, because a silently wrong resolution is a wrong render rather
    than an error (design.md D2).
    """
    try:
        # The frame header is near the front of both formats, and a photo is
        # megabytes; reading a prefix keeps this a header parse, not a file load.
        with open(path, "rb") as handle:
            data = handle.read(65536)
    except OSError as e:
        sys.exit(f"{path}: cannot be read ({e.strerror})")

    size = _png_dimensions(data) or _jpeg_dimensions(data)
    if size is None or 0 in size:
        sys.exit(f"{path}: cannot read the image dimensions from its header")

    return size


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
    long_side = max(long_side, WORKING_SCALE)
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
    workflow[scale_id]["inputs"]["width"] = width
    workflow[scale_id]["inputs"]["height"] = height

from collections.abc import Callable
from pathlib import Path

import pytest

from isekai.boundary.comfy_types import Workflow
from isekai.foundation.flow import load_flow
from isekai.shared.image import (
    DIMENSION_STEP,
    MAX_HEADER_BYTES,
    MAX_HEADER_DIMENSION,
    WORKING_SCALE,
    image_dimensions,
    working_resolution,
)
from tests.images import jpeg_bytes, jpeg_with_header, png_bytes, png_with_exif


@pytest.mark.spec("image-generation:working-resolution:scale-precedes-every-consumer")
def test_a_scale_node_sits_between_the_loader_and_every_consumer(
    workflow: Workflow,
) -> None:
    # By role, not by class: `summon-anime-wai` has two `ImageScale` nodes -- one
    # on the photograph and one on the hires pass -- so a class lookup is ambiguous
    # against it, and the flow's manifest is what names the photograph's.
    flow = load_flow("summon-anime-wai")
    load_id = flow.node("photo")
    scale_id = flow.node("scale")
    assert workflow[scale_id]["inputs"]["image"] == [load_id, 0]

    # The two nodes that read the photograph: the identity node's embedding and
    # keypoints, and the pose preprocessor's control hint.
    assert workflow[flow.node("identity")]["inputs"]["image"] == [scale_id, 0]
    pose_id = next(
        nid for nid, node in workflow.items() if node["class_type"] == "DWPreprocessor"
    )
    assert workflow[pose_id]["inputs"]["image"] == [scale_id, 0]

    # And nothing else reaches the loader, so there is exactly one pixel grid in
    # the graph and no control hint is registered against a different one.
    readers = {
        node_id
        for node_id, node in workflow.items()
        for value in node["inputs"].values()
        if isinstance(value, list) and value[0] == load_id
    }
    assert readers == {scale_id}


def _write(directory: Path, name: str, data: bytes) -> str:
    """Write `data` to `directory/name` and return the path as the reader takes it."""
    path = directory / name
    path.write_bytes(data)
    return str(path)


@pytest.mark.spec("image-generation:working-resolution:short-side-at-the-working-scale")
@pytest.mark.parametrize(
    ("width", "height"),
    [(4032, 3024), (3024, 4032), (2000, 2000), (1920, 1080), (1080, 1920)],
)
def test_the_target_preserves_aspect_with_the_short_side_at_the_working_scale(
    width: int, height: int
) -> None:
    out_width, out_height = working_resolution(width, height)

    assert min(out_width, out_height) == WORKING_SCALE
    assert out_width % DIMENSION_STEP == 0
    assert out_height % DIMENSION_STEP == 0

    # Aspect to within one rounding step: the long side is snapped to the step,
    # so the ratio may move by at most half a step over the short side.
    exact = max(width, height) / min(width, height)
    got = max(out_width, out_height) / WORKING_SCALE
    assert abs(got - exact) <= DIMENSION_STEP / WORKING_SCALE

    # Orientation survives: a landscape photo does not come back portrait.
    assert (out_width >= out_height) == (width >= height)


@pytest.mark.spec("image-generation:working-resolution:small-photos-are-scaled-up")
def test_a_photo_below_the_working_scale_is_scaled_up() -> None:
    width, height = 640, 480
    out_width, out_height = working_resolution(width, height)

    assert out_width > width
    assert out_height > height
    assert min(out_width, out_height) == WORKING_SCALE


@pytest.mark.spec("image-generation:working-resolution:dimensions-come-from-the-header")
@pytest.mark.parametrize("builder", [png_bytes, jpeg_bytes])
@pytest.mark.parametrize(("width", "height"), [(1600, 1200), (1200, 1600), (900, 900)])
def test_dimensions_are_read_from_landscape_portrait_and_square_headers(
    builder: Callable[[int, int], bytes], width: int, height: int, tmp_path: Path
) -> None:
    path = _write(tmp_path, "photo.bin", builder(width, height))
    assert image_dimensions(path) == (width, height)


@pytest.mark.spec("image-generation:working-resolution:orientation-is-honoured")
@pytest.mark.parametrize("orientation", [5, 6, 7, 8])
def test_a_rotated_photo_reports_the_dimensions_the_loader_will_present(
    orientation: int, tmp_path: Path
) -> None:
    # The loader transposes on these four values, so the frame header's landscape
    # dimensions are not the ones the graph will see. Reporting the header's own
    # would scale a portrait photo into a landscape frame with crop disabled --
    # a non-uniform squash, silently, since every node still succeeds.
    path = _write(
        tmp_path, "rotated.jpg", jpeg_with_header(4032, 3024, orientation=orientation)
    )
    assert image_dimensions(path) == (3024, 4032)


@pytest.mark.spec("image-generation:working-resolution:orientation-is-honoured")
@pytest.mark.parametrize("orientation", [1, 2, 3, 4])
def test_an_upright_orientation_leaves_the_header_dimensions_alone(
    orientation: int, tmp_path: Path
) -> None:
    # 1-4 are the identity and the flips and the half turn: none transposes, so
    # the header's dimensions are already the ones the loader will present.
    path = _write(
        tmp_path, "upright.jpg", jpeg_with_header(4032, 3024, orientation=orientation)
    )
    assert image_dimensions(path) == (4032, 3024)


@pytest.mark.spec("image-generation:working-resolution:a-deep-header-is-still-read")
def test_dimensions_are_read_past_a_metadata_block_larger_than_a_prefix(
    tmp_path: Path,
) -> None:
    data = jpeg_with_header(4032, 3024, orientation=6, header_padding=200_000)
    # The premise of the test: the frame header is past any short prefix, which is
    # ordinary for a camera JPEG carrying a thumbnail, an ICC profile and XMP.
    assert len(data) > 65536
    path = _write(tmp_path, "deep-header.jpg", data)

    assert image_dimensions(path) == (3024, 4032)


@pytest.mark.spec(
    "image-generation:working-resolution:unreadable-dimensions-are-refused"
)
@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("truncated.png", png_bytes(1600, 1200)[:20]),
        ("truncated.jpg", jpeg_bytes(1600, 1200)[:8]),
        # A segment length below 2 is malformed -- the field counts itself -- and
        # walking past it lands inside a payload, where arbitrary bytes would be
        # read as a frame header and returned as dimensions.
        ("zero-length-segment.jpg", b"\xff\xd8\xff\xe0\x00\x00" + b"\xff" * 64),
        ("not-an-image.txt", b"this is not a photo"),
        ("empty.jpg", b""),
    ],
)
def test_a_photo_whose_dimensions_cannot_be_read_stops_the_run(
    name: str, data: bytes, tmp_path: Path
) -> None:
    path = _write(tmp_path, name, data)

    with pytest.raises(SystemExit) as excinfo:
        image_dimensions(path)

    # The message names the file, and there is no fallback size: a silently wrong
    # resolution is a wrong render rather than an error.
    assert path in str(excinfo.value)


# The two header ceilings. A header field is an unverified number until something
# bounds it (design.md D8). The third stated ceiling is the target's long side,
# enforced where the target is computed for a render -- see `tests/test_generate.py`.


@pytest.mark.spec(
    "image-generation:working-resolution:an-out-of-range-header-dimension-is-refused"
)
def test_a_header_dimension_past_the_ceiling_is_refused(tmp_path: Path) -> None:
    # JPEG's own two-byte frame field enforces this already, so a PNG is the only
    # codec that can declare it — and both refuse the same input.
    path = _write(tmp_path, "absurd.png", png_bytes(70_000, 1_000))

    with pytest.raises(SystemExit) as excinfo:
        image_dimensions(path)

    message = str(excinfo.value)
    assert path in message
    assert str(MAX_HEADER_DIMENSION) in message


@pytest.mark.spec(
    "image-generation:working-resolution:an-out-of-range-header-dimension-is-refused"
)
def test_a_header_dimension_at_the_ceiling_is_read(tmp_path: Path) -> None:
    path = _write(tmp_path, "at-the-limit.png", png_bytes(MAX_HEADER_DIMENSION, 1_000))
    assert image_dimensions(path) == (MAX_HEADER_DIMENSION, 1_000)


@pytest.mark.spec(
    "image-generation:working-resolution:an-unbounded-header-walk-is-refused"
)
def test_a_header_walk_past_the_byte_ceiling_is_refused(tmp_path: Path) -> None:
    # The walk is bounded by the file, which is not a bound: a camera's EXIF,
    # thumbnail, ICC and XMP together are a few hundred KiB, so a frame header
    # this deep is a file being used to make the parser read the whole of it.
    data = jpeg_with_header(4032, 3024, header_padding=MAX_HEADER_BYTES + 1024)
    path = _write(tmp_path, "unbounded.jpg", data)

    with pytest.raises(SystemExit) as excinfo:
        image_dimensions(path)

    message = str(excinfo.value)
    assert path in message
    assert str(MAX_HEADER_BYTES) in message


# The PNG half of the orientation rule. v0.10 closed the JPEG branch and left this
# one open; the phase-6 loader probe measured the pod and found `LoadImage`
# transposes a PNG carrying an `eXIf` chunk exactly as it transposes a tagged
# JPEG -- and every input this project has ever rendered is a PNG.


@pytest.mark.spec("image-generation:working-resolution:orientation-is-honoured")
@pytest.mark.parametrize("orientation", [5, 6, 7, 8])
def test_a_rotated_png_reports_the_dimensions_the_loader_will_present(
    orientation: int, tmp_path: Path
) -> None:
    path = _write(tmp_path, "rotated.png", png_with_exif(4032, 3024, orientation))
    assert image_dimensions(path) == (3024, 4032)


@pytest.mark.spec("image-generation:working-resolution:orientation-is-honoured")
@pytest.mark.parametrize("orientation", [1, 2, 3, 4])
def test_an_upright_png_orientation_leaves_the_header_dimensions_alone(
    orientation: int, tmp_path: Path
) -> None:
    path = _write(tmp_path, "upright.png", png_with_exif(4032, 3024, orientation))
    assert image_dimensions(path) == (4032, 3024)


@pytest.mark.spec("image-generation:working-resolution:orientation-is-honoured")
def test_a_png_with_no_exif_chunk_is_measured_as_its_header_states(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path, "plain.png", png_bytes(4032, 3024))
    assert image_dimensions(path) == (4032, 3024)


@pytest.mark.spec("image-generation:working-resolution:orientation-is-honoured")
def test_the_exif_chunk_is_found_wherever_the_writer_put_it(tmp_path: Path) -> None:
    # A writer may put `eXIf` anywhere before the pixel data, so a parser that
    # looks only straight after IHDR would report the untransposed pair.
    path = _write(tmp_path, "late.png", png_with_exif(4032, 3024, 6, chunks_before=5))
    assert image_dimensions(path) == (3024, 4032)


@pytest.mark.spec("image-generation:working-resolution:orientation-is-honoured")
def test_both_codecs_agree_on_the_same_rotation(tmp_path: Path) -> None:
    # The mismatch this rule prevents is a property of the loader, not of the
    # container: the phase-6 probe measured both and both transposed.
    as_jpeg = _write(tmp_path, "r.jpg", jpeg_with_header(4032, 3024, orientation=6))
    as_png = _write(tmp_path, "r.png", png_with_exif(4032, 3024, 6))
    assert image_dimensions(as_jpeg) == image_dimensions(as_png) == (3024, 4032)


@pytest.mark.spec(
    "image-generation:working-resolution:an-unbounded-header-walk-is-refused"
)
def test_a_png_declaring_an_unbounded_exif_chunk_is_refused(tmp_path: Path) -> None:
    # The `eXIf` payload is the one thing the walk reads rather than seeks over,
    # so it is the one place a header-declared length is materialised. A chunk
    # header may state up to 4 GiB; reading it on the header's word alone is a
    # `MemoryError` no refusal names.
    data = bytearray(png_with_exif(4032, 3024, 6))
    at = data.index(b"eXIf")
    data[at - 4 : at] = b"\xff\xff\xff\xff"
    path = _write(tmp_path, "unbounded-chunk.png", bytes(data))

    with pytest.raises(SystemExit) as excinfo:
        image_dimensions(path)

    message = str(excinfo.value)
    assert path in message
    assert str(MAX_HEADER_BYTES) in message
    # and it says which walk gave up: this refusal is reachable from the PNG
    # chunk walk as well as the JPEG marker walk, so a message naming only a
    # JPEG's frame header tells an operator handed a corrupt PNG that the file
    # lacks a structure PNG does not have.
    assert "PNG" in message
    assert "frame header" not in message

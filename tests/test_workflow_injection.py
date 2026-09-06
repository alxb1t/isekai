import inspect
from collections.abc import Callable
from pathlib import Path

import pytest

from isekai import cli
from isekai.comfy_types import Workflow
from isekai.workflow import (
    DIMENSION_STEP,
    MAX_HEADER_BYTES,
    MAX_HEADER_DIMENSION,
    MAX_TARGET_LONG_SIDE,
    WORKING_SCALE,
    find_node,
    find_nodes,
    image_dimensions,
    inject,
    working_resolution,
)
from tests.images import jpeg_bytes, jpeg_with_header, png_bytes, png_with_exif


@pytest.mark.spec("workflow-injection:node-location:locates-by-class-type")
def test_find_node_locates_a_node_by_class_type() -> None:
    wf = {
        "7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}},
        "9": {"class_type": "KSampler", "_meta": {"title": "KSampler"}},
    }

    assert find_node(wf, class_type="LoadImage") == "7"


@pytest.mark.spec("workflow-injection:node-location:exits-when-no-node-matches")
def test_find_node_exits_when_no_node_matches() -> None:
    wf = {"7": {"class_type": "LoadImage", "_meta": {"title": "Load Image"}}}

    with pytest.raises(SystemExit):
        find_node(wf, class_type="KSampler")


@pytest.mark.spec("workflow-injection:node-location:exits-when-ambiguous")
def test_find_node_exits_when_the_match_is_ambiguous() -> None:
    wf = {
        "1": {"class_type": "CLIPTextEncode", "_meta": {"title": "Positive"}},
        "2": {"class_type": "CLIPTextEncode", "_meta": {"title": "Negative"}},
    }

    with pytest.raises(SystemExit):
        find_node(wf, class_type="CLIPTextEncode")


@pytest.mark.spec("workflow-injection:node-location:single-load-image-in-real-workflow")
def test_find_node_locates_the_single_load_image_in_the_real_workflow(
    workflow: Workflow,
) -> None:
    assert find_node(workflow, class_type="LoadImage") == "2"


@pytest.mark.spec("workflow-injection:node-location:text-encoders-are-ambiguous")
def test_find_node_is_ambiguous_for_the_two_text_encoders(
    workflow: Workflow,
) -> None:
    # The shipped graph carries a positive and a negative CLIPTextEncode, so a
    # class-type lookup cannot name either — which is why the positive string is
    # committed to the graph rather than reached by lookup.
    with pytest.raises(SystemExit):
        find_node(workflow, class_type="CLIPTextEncode")


@pytest.mark.spec("workflow-injection:latent-init:inits-from-photo-below-one")
def test_graph_inits_the_latent_from_the_photo_at_denoise_below_one(
    workflow: Workflow,
) -> None:
    # One LoadImage feeds VAEEncode through the scale node, which seeds the
    # KSampler latent at denoise < 1 (from-photo, not from-noise).
    load_id = find_node(workflow, class_type="LoadImage")
    scale_id = find_node(workflow, class_type="ImageScale")
    vae_id = find_node(workflow, class_type="VAEEncode")
    sampler_id = find_node(workflow, class_type="KSampler")
    assert workflow[scale_id]["inputs"]["image"][0] == load_id
    assert workflow[vae_id]["inputs"]["pixels"][0] == scale_id
    assert workflow[sampler_id]["inputs"]["latent_image"][0] == vae_id
    assert workflow[sampler_id]["inputs"]["denoise"] < 1


@pytest.mark.spec("workflow-injection:photo-wiring:single-loader-fans-out")
def test_inject_wires_the_single_load_image_across_the_stack(
    workflow: Workflow, photo: str
) -> None:
    # One LoadImage fans out, through the scale node, to VAEEncode + InstantID +
    # all three CN preprocessors, so find_node stays unique and the
    # exactly-one-LoadImage rule holds.
    inject(workflow, image_name="face.png", image_path=photo)
    load_id = find_node(workflow, class_type="LoadImage")
    assert workflow[load_id]["inputs"]["image"] == "face.png"


# --- v0.8: the positive prompt is graph configuration -----------------------

# The committed prompts, pinned by equality rather than by a blacklist: "the
# string holds no subject text" has no mechanical form, and a test asserting
# `"arms crossed" not in text` is defeated silently by any rewrite. Equality
# makes every future prompt edit a deliberate test edit, which is what makes
# "not typeable" a property rather than a convention (0008's design.md D7).
#
# v0.10 rewrote both to WAI's register: the content tags with the publisher's own
# ladder appended last, and the publisher's own short negative. `1girl` is gone --
# `solo` is what does the mode-selection work, while `1girl` additionally asserted
# a gender the identity node's embedding already carries, so that axis now belongs
# to a mechanism in the graph rather than to a tag (0010's design.md D5). That
# closes the defect v0.8 recorded; v0.9 changed no base and decided no register.
COMMITTED_POSITIVE = (
    "solo, anime screencap, detailed eyes, soft lighting, "
    "masterpiece, best quality, amazing quality"
)

# The publisher's short form, plus the `nsfw` tag the same model page instructs
# users to add. Deliberately short: WAI's page warns that over-long negatives
# reduce image quality, so taking its positive while keeping v0.8's eighteen-token
# negative would have taken half the guidance and ignored the half stated as a
# warning. One consequence is recorded rather than absorbed -- `realistic,
# photorealistic` is gone, which removes a push away from the photograph on a
# product whose whole subject is a photograph (design.md D4).
COMMITTED_NEGATIVE = "bad quality, worst quality, worst detail, sketch, censor, nsfw"

# Tags that name the subject's gender. The register must select the single-subject
# mode without deciding who the photo is of.
GENDER_TAGS = ("1girl", "1boy", "girl", "boy", "male", "female", "woman", "man")

# Clip skip 2, in ComfyUI's negative-index spelling. Every published WAI v17 sample
# generates at it and none of the publisher's prose mentions it, so a graph that
# does not set it ships a configuration the publisher never tested while looking
# identical to one that does (design.md D6).
COMMITTED_CLIP_LAYER = -2


@pytest.mark.spec("workflow-injection:committed-prompt:string-is-pinned")
def test_the_committed_positive_string_is_pinned(workflow: Workflow) -> None:
    assert workflow["3"]["inputs"]["text"] == COMMITTED_POSITIVE


@pytest.mark.spec("workflow-injection:committed-prompt:asserts-no-gender")
def test_the_committed_positive_asserts_no_gender(workflow: Workflow) -> None:
    # Read the shipped graph, not the literal above. `solo` is the mode selector
    # and names no gender; the axis `1girl` used to fix is carried by the face
    # embedding the identity node computes, which is documented as holding it.
    tags = [tag.strip() for tag in workflow["3"]["inputs"]["text"].split(",")]
    assert "solo" in tags
    assert not [tag for tag in tags if tag in GENDER_TAGS]


@pytest.mark.spec("workflow-injection:committed-prompt:carries-no-pose-tag")
def test_the_committed_positive_carries_no_pose_tag(workflow: Workflow) -> None:
    # Pose is the OpenPose ControlNet's axis. A pose tag in the prompt competes
    # with the mechanism that owns it, so it is removed on that argument alone --
    # no render is needed to justify it. Read the shipped graph, not the literal
    # above: a test asserting against its own constant can only fail if someone
    # edits the test.
    assert "arms crossed" not in workflow["3"]["inputs"]["text"]


@pytest.mark.spec("workflow-injection:committed-prompt:not-settable-from-the-cli")
def test_no_command_line_path_sets_the_positive_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two halves, both needed: no flag carries a prompt, AND injection takes no
    # prompt argument -- so there is no path by which typed text reaches the
    # encoder even if a flag were added back.
    monkeypatch.setattr("sys.argv", ["convert.py", "photo.jpg", "--prompt", "anime"])
    with pytest.raises(SystemExit):
        cli.parse_args()

    assert list(inspect.signature(inject).parameters) == [
        "workflow",
        "image_name",
        "image_path",
    ]


@pytest.mark.spec("workflow-injection:committed-prompt:negative-is-untouched")
def test_injection_leaves_the_negative_encoder_as_the_graph_committed_it(
    workflow: Workflow, photo: str
) -> None:
    before = workflow["4"]["inputs"]["text"]
    inject(workflow, image_name="face.png", image_path=photo)
    assert workflow["4"]["inputs"]["text"] == before
    assert before == COMMITTED_NEGATIVE


# --- v0.10: the photo is scaled to a working resolution ---------------------


def _write(directory: Path, name: str, data: bytes) -> str:
    """Write `data` to `directory/name` and return the path as injection takes it."""
    path = directory / name
    path.write_bytes(data)
    return str(path)


# Every node that reads the photo, by the input that carries it. Named rather
# than discovered: the scenario is that *these* consumers read one pixel grid,
# and a check that derives its own list from the graph would pass an empty one.
PHOTO_CONSUMERS = (
    ("8", "image"),  # ApplyInstantIDAdvanced
    ("9", "pixels"),  # VAEEncode
    ("13", "image"),  # TilePreprocessor
    ("16", "image"),  # DWPreprocessor
    ("19", "image"),  # LineArtPreprocessor
)


@pytest.mark.spec("workflow-injection:working-resolution:scale-precedes-every-consumer")
def test_a_scale_node_sits_between_the_loader_and_every_consumer(
    workflow: Workflow,
) -> None:
    load_id = find_node(workflow, class_type="LoadImage")
    scale_id = find_node(workflow, class_type="ImageScale")
    assert workflow[scale_id]["inputs"]["image"] == [load_id, 0]

    for node_id, key in PHOTO_CONSUMERS:
        assert workflow[node_id]["inputs"][key] == [scale_id, 0]

    # And nothing else reaches the loader, so there is exactly one pixel grid in
    # the graph and no control hint is registered against a different one.
    readers = {
        node_id
        for node_id, node in workflow.items()
        for value in node["inputs"].values()
        if isinstance(value, list) and value[0] == load_id
    }
    assert readers == {scale_id}


@pytest.mark.spec(
    "workflow-injection:working-resolution:short-side-at-the-working-scale"
)
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


@pytest.mark.spec("workflow-injection:working-resolution:small-photos-are-scaled-up")
def test_a_photo_below_the_working_scale_is_scaled_up() -> None:
    width, height = 640, 480
    out_width, out_height = working_resolution(width, height)

    assert out_width > width
    assert out_height > height
    assert min(out_width, out_height) == WORKING_SCALE


@pytest.mark.spec(
    "workflow-injection:working-resolution:dimensions-are-written-by-injection"
)
def test_injection_writes_the_computed_dimensions_into_the_scale_node(
    workflow: Workflow, tmp_path: Path
) -> None:
    path = _write(tmp_path, "portrait.png", png_bytes(3024, 4032))
    inject(workflow, image_name="face.png", image_path=path)

    scale_id = find_node(workflow, class_type="ImageScale")
    expected_width, expected_height = working_resolution(3024, 4032)
    assert workflow[scale_id]["inputs"]["width"] == expected_width
    assert workflow[scale_id]["inputs"]["height"] == expected_height


@pytest.mark.spec(
    "workflow-injection:working-resolution:dimensions-are-written-by-injection"
)
@pytest.mark.parametrize("builder", [png_bytes, jpeg_bytes])
@pytest.mark.parametrize(("width", "height"), [(1600, 1200), (1200, 1600), (900, 900)])
def test_dimensions_are_read_from_landscape_portrait_and_square_headers(
    builder: Callable[[int, int], bytes], width: int, height: int, tmp_path: Path
) -> None:
    path = _write(tmp_path, "photo.bin", builder(width, height))
    assert image_dimensions(path) == (width, height)


@pytest.mark.spec("workflow-injection:working-resolution:orientation-is-honoured")
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


@pytest.mark.spec("workflow-injection:working-resolution:orientation-is-honoured")
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


@pytest.mark.spec("workflow-injection:working-resolution:a-deep-header-is-still-read")
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
    "workflow-injection:working-resolution:unreadable-dimensions-are-refused"
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


@pytest.mark.spec(
    "workflow-injection:working-resolution:unreadable-dimensions-are-refused"
)
def test_injection_stops_when_the_photo_is_not_on_disk(
    workflow: Workflow, tmp_path: Path
) -> None:
    missing = str(tmp_path / "absent.jpg")

    with pytest.raises(SystemExit) as excinfo:
        inject(workflow, image_name="face.png", image_path=missing)

    assert missing in str(excinfo.value)


@pytest.mark.spec(
    "workflow-injection:clip-layer:conditioning-stops-at-the-expected-layer"
)
def test_both_encoders_take_their_clip_through_the_committed_layer(
    workflow: Workflow,
) -> None:
    loader_id = find_node(workflow, class_type="CheckpointLoaderSimple")
    clip_id = find_node(workflow, class_type="CLIPSetLastLayer")

    assert workflow[clip_id]["inputs"]["clip"] == [loader_id, 1]
    assert workflow[clip_id]["inputs"]["stop_at_clip_layer"] == COMMITTED_CLIP_LAYER

    # Both encoders, not one: a graph where only the positive is routed through
    # the layer node conditions the two halves against different text towers.
    for encoder_id in ("3", "4"):
        assert workflow[encoder_id]["inputs"]["clip"] == [clip_id, 0]


# --- v0.10: what the phase-5 probe settled, held in place -------------------

# The dials the probe chose, by eye, against one photo at a fixed seed. They are
# the values that were already in the graph -- tuned on Animagine, with no reason
# to expect they would transfer, so this is a real search with a null result
# rather than a decision skipped. Pinned so the evaluator version inherits a
# baseline it can measure against, and so a silent re-tune is a test edit.
# `probe/README.md` records what they were chosen against. Chosen is not best.
PROBE_DENOISE = 0.65
PROBE_IP_WEIGHT = 0.9


@pytest.mark.spec_exempt(
    "preference, not a scenario: holds the dials design.md D9 records as by-eye"
)
def test_the_graph_carries_the_dials_the_probe_chose(workflow: Workflow) -> None:
    sampler_id = find_node(workflow, class_type="KSampler")
    apply_id = find_node(workflow, class_type="ApplyInstantIDAdvanced")
    assert workflow[sampler_id]["inputs"]["denoise"] == PROBE_DENOISE
    assert workflow[apply_id]["inputs"]["ip_weight"] == PROBE_IP_WEIGHT


@pytest.mark.spec_exempt(
    "structural: the sampler must reach the encoder through whatever stack remains"
)
def test_the_samplers_positive_input_reaches_the_encoder_through_the_stack(
    workflow: Workflow,
) -> None:
    # The non-obvious property this graph has always had: `KSampler.positive` may
    # point at `ApplyInstantIDAdvanced` directly OR through a stack of
    # `ControlNetApplyAdvanced` nodes, so the encoder is found by following the
    # link, never by class lookup. A shortened stack -- which the phase-5 probe
    # could have produced, had a ControlNet come back indistinguishable from
    # absent -- is exactly when that would break unnoticed.
    sampler_id = find_node(workflow, class_type="KSampler")
    identity_id = find_node(workflow, class_type="ApplyInstantIDAdvanced")

    node_id = workflow[sampler_id]["inputs"]["positive"][0]
    hops = 0
    while workflow[node_id]["class_type"] == "ControlNetApplyAdvanced":
        node_id = workflow[node_id]["inputs"]["positive"][0]
        hops += 1

    assert node_id == identity_id
    assert workflow[identity_id]["inputs"]["positive"] == ["3", 0]
    assert workflow["3"]["inputs"]["text"] == COMMITTED_POSITIVE

    # The probe kept all three ControlNets, so the walk is three hops long. If a
    # later version deletes one, this number moves and the walk above still holds.
    assert hops == len(find_nodes(workflow, class_type="ControlNetApplyAdvanced"))
    assert hops == 3


# Three stated ceilings. A short-side rule places no bound on the other axis, and
# a header field is an unverified number until something bounds it (design.md D8).
# Each refuses rather than clamping: a clamped target no longer preserves the
# aspect ratio, and would squash the photo the way the orientation rule exists to
# prevent.


@pytest.mark.spec(
    "workflow-injection:working-resolution:an-extreme-aspect-ratio-is-refused"
)
def test_a_photo_whose_target_long_side_exceeds_the_ceiling_is_refused(
    workflow: Workflow, tmp_path: Path
) -> None:
    # 1:8 at a 1024 short side computes to 8192 on the long axis — already a
    # heavy SDXL allocation at 4096, and past any real photo.
    path = _write(tmp_path, "panorama.png", png_bytes(1024, 8192))

    with pytest.raises(SystemExit) as excinfo:
        inject(workflow, image_name="face.png", image_path=path)

    message = str(excinfo.value)
    assert path in message
    assert str(MAX_TARGET_LONG_SIDE) in message


@pytest.mark.spec(
    "workflow-injection:working-resolution:an-extreme-aspect-ratio-is-refused"
)
def test_an_aspect_ratio_at_the_ceiling_is_still_rendered(
    workflow: Workflow, tmp_path: Path
) -> None:
    path = _write(tmp_path, "wide.png", png_bytes(4096, 1024))
    inject(workflow, image_name="face.png", image_path=path)

    scale_id = find_node(workflow, class_type="ImageScale")
    assert workflow[scale_id]["inputs"]["width"] == MAX_TARGET_LONG_SIDE


@pytest.mark.spec(
    "workflow-injection:working-resolution:an-out-of-range-header-dimension-is-refused"
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
    "workflow-injection:working-resolution:an-out-of-range-header-dimension-is-refused"
)
def test_a_header_dimension_at_the_ceiling_is_read(tmp_path: Path) -> None:
    path = _write(tmp_path, "at-the-limit.png", png_bytes(MAX_HEADER_DIMENSION, 1_000))
    assert image_dimensions(path) == (MAX_HEADER_DIMENSION, 1_000)


@pytest.mark.spec(
    "workflow-injection:working-resolution:an-unbounded-header-walk-is-refused"
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


@pytest.mark.spec("workflow-injection:working-resolution:orientation-is-honoured")
@pytest.mark.parametrize("orientation", [5, 6, 7, 8])
def test_a_rotated_png_reports_the_dimensions_the_loader_will_present(
    orientation: int, tmp_path: Path
) -> None:
    path = _write(tmp_path, "rotated.png", png_with_exif(4032, 3024, orientation))
    assert image_dimensions(path) == (3024, 4032)


@pytest.mark.spec("workflow-injection:working-resolution:orientation-is-honoured")
@pytest.mark.parametrize("orientation", [1, 2, 3, 4])
def test_an_upright_png_orientation_leaves_the_header_dimensions_alone(
    orientation: int, tmp_path: Path
) -> None:
    path = _write(tmp_path, "upright.png", png_with_exif(4032, 3024, orientation))
    assert image_dimensions(path) == (4032, 3024)


@pytest.mark.spec("workflow-injection:working-resolution:orientation-is-honoured")
def test_a_png_with_no_exif_chunk_is_measured_as_its_header_states(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path, "plain.png", png_bytes(4032, 3024))
    assert image_dimensions(path) == (4032, 3024)


@pytest.mark.spec("workflow-injection:working-resolution:orientation-is-honoured")
def test_the_exif_chunk_is_found_wherever_the_writer_put_it(tmp_path: Path) -> None:
    # A writer may put `eXIf` anywhere before the pixel data, so a parser that
    # looks only straight after IHDR would report the untransposed pair.
    path = _write(tmp_path, "late.png", png_with_exif(4032, 3024, 6, chunks_before=5))
    assert image_dimensions(path) == (3024, 4032)


@pytest.mark.spec("workflow-injection:working-resolution:orientation-is-honoured")
def test_both_codecs_agree_on_the_same_rotation(tmp_path: Path) -> None:
    # The mismatch this rule prevents is a property of the loader, not of the
    # container: the phase-6 probe measured both and both transposed.
    as_jpeg = _write(tmp_path, "r.jpg", jpeg_with_header(4032, 3024, orientation=6))
    as_png = _write(tmp_path, "r.png", png_with_exif(4032, 3024, 6))
    assert image_dimensions(as_jpeg) == image_dimensions(as_png) == (3024, 4032)


@pytest.mark.spec(
    "workflow-injection:working-resolution:an-unbounded-header-walk-is-refused"
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

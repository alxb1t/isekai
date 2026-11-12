"""The edit's request: its file names, the maths of its derivation, its refusals.

Each image is built here from flat colour, so what the derivation must read is known
before it runs.
"""

import io
import json
import random
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import isekai.pipeline.edit as edit_module
from isekai.boundary.comfy import TransportFailure, read_runtime
from isekai.foundation.artifacts import EDIT_FILE, VERSIONS, read, write
from isekai.foundation.edit import load_edit
from isekai.foundation.flow import graph_digest
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    FRAME_NAME,
    digest_of,
    edit_at,
    edit_files,
    edit_numbers,
    edit_stem,
    next_edit,
)
from isekai.interface.cli import build_parser, dispatch
from isekai.pipeline.edit import Requested, check, pending, records, request, sample
from isekai.shared.tattoo import (
    MASK_FLOOR,
    decode_composite,
    decode_render,
    derive,
    ink_of,
    plan_crop,
    stitch,
)
from tests.fakes import FakeComfyClient, RecordingComfyClient
from tests.stages import bare_wiring

DIALS = load_edit("tattoo-wai").dials
SKIN = (200, 150, 120)
SIDE = 200
# The square a tattoo covers, as rows and columns.
INKED = slice(80, 120)


def _group(tmp_path: Path, flow: str = "summon-anime-wai") -> Path:
    """Return an outputs group inside a run that has a frame."""
    run = tmp_path / "runs" / "0123456789ab_a"
    group = run / flow / "outputs" / "001"
    group.mkdir(parents=True)
    (run / FRAME_NAME).write_text("{}\n")
    return group


@pytest.mark.spec_exempt(
    "structural: the edit kind is declared once, at its first version"
)
def test_edit_names_the_kind_is_declared_and_versioned() -> None:
    assert EDIT_FILE.schema == {"name": "edit", "version": 1}
    assert VERSIONS["edit"] == 1


@pytest.mark.spec_exempt(
    "structural: an edit's files are named for its seed and number"
)
def test_edit_names_the_files_of_an_edit_share_its_stem(tmp_path: Path) -> None:
    group = tmp_path / "outputs" / "001"

    assert edit_stem(42, 2) == "42.edit-2"
    assert [path.name for path in edit_files(group, 42, 2)] == [
        "42.edit-2.png",
        "42.edit-2.json",
        "42.edit-2.composite.png",
    ]


@pytest.mark.spec_exempt("structural: the next number is read from the listing")
def test_edit_names_the_next_number_follows_the_highest_file_of_the_seed(
    tmp_path: Path,
) -> None:
    group = _group(tmp_path)
    assert next_edit(group, 42) == 1

    (group / "42.edit-1.json").write_text("{}\n")
    (group / "42.edit-3.composite.png").write_bytes(b"png")
    (group / "7.edit-9.png").write_bytes(b"png")
    (group / "42.png").write_bytes(b"png")

    assert edit_numbers(group, 42) == [1, 3]
    assert next_edit(group, 42) == 4


@pytest.mark.spec_exempt("structural: a missing group lists no edit")
def test_edit_names_a_group_that_is_not_there_holds_no_edit(tmp_path: Path) -> None:
    assert edit_numbers(tmp_path / "gone", 42) == []
    assert next_edit(tmp_path / "gone", 42) == 1


@pytest.mark.spec_exempt("structural: an edit image's path names its run and chain")
def test_edit_names_an_image_path_names_its_run_flow_approval_seed_and_number(
    tmp_path: Path,
) -> None:
    group = _group(tmp_path)
    image = group / "42.edit-2.png"
    image.write_bytes(b"png")

    run, flow, version, seed, number = edit_at(image)

    assert (run.id, flow, version, seed, number) == (
        "0123456789ab_a",
        "summon-anime-wai",
        1,
        42,
        2,
    )
    assert run.path == tmp_path / "runs" / "0123456789ab_a"


@pytest.mark.spec_exempt("structural: a path that is no edit image is refused by name")
@pytest.mark.parametrize(
    "name",
    [
        "42.png",
        "42.edit-0.png",
        "42.edit-1.json",
        "x.edit-1.png",
        "42.edit-1.composite.png",
    ],
)
def test_edit_names_a_path_that_is_no_edit_image_is_refused(
    name: str, tmp_path: Path
) -> None:
    group = _group(tmp_path)
    (group / name).write_bytes(b"png")

    with pytest.raises(Refusal, match=r"is not an edit's image.*<seed>\.edit-<k>\.png"):
        edit_at(group / name)


@pytest.mark.spec_exempt("structural: an edit image that is not on disk is refused")
def test_edit_names_an_image_that_is_not_there_is_refused(tmp_path: Path) -> None:
    group = _group(tmp_path)

    with pytest.raises(Refusal, match="is not an edit's image"):
        edit_at(group / "42.edit-1.png")


def _render(side: int = SIDE, colour: tuple[int, int, int] = SKIN) -> "np.ndarray":
    """Return a flat render of one colour."""
    return np.full((side, side, 3), colour, dtype=np.uint8)


def _multiplied(render: "np.ndarray", factor: float = 0.5) -> "np.ndarray":
    """Return `render` with the tattoo's square multiplied by `factor`."""
    composite = render.copy()
    square = composite[INKED, INKED].astype(np.float32) * factor
    composite[INKED, INKED] = (square + 0.5).astype(np.uint8)
    return composite


def _png(array: "np.ndarray", mode: str | None = None) -> bytes:
    """Return `array` encoded as a PNG."""
    body = io.BytesIO()
    Image.fromarray(array, mode).save(body, "PNG")
    return body.getvalue()


@pytest.mark.spec_exempt("structural: the ink is the composite over the render")
def test_edit_derive_the_ink_is_the_composite_divided_by_the_render() -> None:
    render = _render()

    derived = derive(render, _multiplied(render), DIALS)

    assert derived.ink[100, 100] == pytest.approx([0.5, 0.5, 0.5], abs=0.01)
    assert (derived.ink[10, 10] == 1.0).all()
    assert derived.darkness[100, 100] == pytest.approx(0.5, abs=0.01)
    assert derived.darkness[10, 10] == 0.0


@pytest.mark.spec_exempt("structural: darkness is one minus the least channel")
def test_edit_derive_darkness_follows_the_darkest_channel() -> None:
    render = _render()
    composite = render.copy()
    composite[INKED, INKED, 0] = render[0, 0, 0] // 4

    derived = derive(render, composite, DIALS)

    assert derived.ink[100, 100, 1] == 1.0
    assert derived.darkness[100, 100] == pytest.approx(0.75, abs=0.01)


@pytest.mark.spec_exempt("structural: the mask is the ink grown and feathered")
def test_edit_derive_the_mask_covers_the_ink_and_reaches_past_its_edge() -> None:
    render = _render()

    mask = derive(render, _multiplied(render), DIALS).mask

    assert mask.dtype == np.uint8
    assert mask[100, 100] == 255
    # Three pixels past the edge is inside the growth, which the feather softens.
    assert mask[100, 80 - 3] > 128
    assert mask[100, 80 - 3] < 255
    assert mask[100, 80 - 40] == 0
    assert mask[5, 5] == 0


@pytest.mark.spec_exempt("structural: the mask's feather leaves levels between")
def test_edit_derive_a_feather_of_nothing_leaves_a_hard_edge() -> None:
    render = _render()
    hard = {**DIALS, "feather": 0, "grow": 0}

    mask = derive(render, _multiplied(render), hard).mask

    assert set(np.unique(mask)) == {0, 255}
    assert (mask > MASK_FLOOR).sum() == 40 * 40


@pytest.mark.spec_exempt("structural: the control is darkness times its gain")
def test_edit_derive_the_control_is_darkness_times_the_gain_clipped() -> None:
    render = _render()

    half = derive(render, _multiplied(render, 0.5), DIALS).control
    deep = derive(render, _multiplied(render, 0.1), DIALS).control

    assert half[100, 100] == round(0.5 * DIALS["control_gain"] * 255)
    assert deep[100, 100] == 255
    assert half[10, 10] == 0


@pytest.mark.spec("edit:refusals:a-composite-of-another-size-is-refused")
def test_edit_refuse_a_composite_of_another_size_names_both_sizes() -> None:
    render = _render()
    smaller = _render(SIDE - 10)

    with pytest.raises(
        Refusal, match=r"composite is 190x190 and the render is 200x200"
    ):
        ink_of(render, smaller, DIALS)


@pytest.mark.spec("edit:refusals:a-composite-with-no-ink-is-refused")
def test_edit_refuse_a_composite_that_is_the_render_carries_no_ink() -> None:
    render = _render()

    with pytest.raises(Refusal, match="carries no ink"):
        derive(render, render.copy(), DIALS)


@pytest.mark.spec("edit:refusals:a-composite-with-no-ink-is-refused")
def test_edit_refuse_a_darkening_past_the_threshold_is_ink() -> None:
    render = _render()
    faint = _multiplied(render, 1.0 - 2 * DIALS["ink_threshold"])

    assert derive(render, faint, DIALS).mask.max() == 255


@pytest.mark.spec("edit:refusals:a-lighter-composite-is-refused")
def test_edit_refuse_a_lighter_composite_names_the_pixel_and_the_blend_mode() -> None:
    render = _render()
    composite = _multiplied(render)
    composite[10, 20, 1] = render[10, 20, 1] + DIALS["rounding"] + 1

    with pytest.raises(
        Refusal, match=r"lighter than the render at \(20, 10\).*Multiply"
    ):
        derive(render, composite, DIALS)


@pytest.mark.spec("edit:refusals:a-lighter-composite-is-refused")
def test_edit_refuse_a_lightening_within_rounding_is_read_as_no_lighter() -> None:
    render = _render()
    composite = _multiplied(render)
    composite[10, 20, 1] = render[10, 20, 1] + DIALS["rounding"]

    assert derive(render, composite, DIALS).darkness[10, 20] == 0.0


@pytest.mark.spec("edit:refusals:a-composite-with-transparency-is-refused")
def test_edit_refuse_a_composite_with_a_transparent_pixel_names_the_flattening() -> (
    None
):
    rgba = np.full((8, 8, 4), 255, dtype=np.uint8)
    rgba[3, 3, 3] = 0

    with pytest.raises(Refusal, match="transparency.*flatten its layers"):
        decode_composite(_png(rgba))


@pytest.mark.spec("edit:refusals:a-composite-with-transparency-is-refused")
def test_edit_refuse_a_composite_with_an_opaque_alpha_channel_is_read() -> None:
    rgba = np.full((8, 8, 4), 255, dtype=np.uint8)
    rgba[..., :3] = SKIN

    assert (decode_composite(_png(rgba)) == _render(8)).all()


@pytest.mark.spec_exempt("structural: bytes that are no image are refused with the fix")
def test_edit_refuse_a_composite_that_does_not_decode_names_the_export() -> None:
    with pytest.raises(
        Refusal, match="cannot be read as an image.*export the composite"
    ):
        decode_composite(b"not a png")


@pytest.mark.spec("edit:refusals:a-near-black-render-reads-no-ink")
def test_edit_refuse_a_difference_only_where_the_render_is_near_black_is_no_ink() -> (
    None
):
    render = _render()
    render[INKED, INKED] = DIALS["lit_floor"]
    composite = render.copy()
    composite[INKED, INKED] = 0

    with pytest.raises(Refusal, match="carries no ink"):
        derive(render, composite, DIALS)
    assert (ink_of(render, composite, DIALS) == 1.0).all()


@pytest.mark.spec("edit:refusals:a-near-black-render-reads-no-ink")
def test_edit_refuse_the_same_difference_one_level_above_the_floor_is_ink() -> None:
    render = _render()
    render[INKED, INKED] = DIALS["lit_floor"] + 1
    composite = render.copy()
    composite[INKED, INKED] = 0

    assert derive(render, composite, DIALS).darkness[100, 100] == 1.0


def _mask(side: int, x0: int, y0: int, x1: int, y1: int) -> "np.ndarray":
    """Return a mask of `side` squared, white from (x0, y0) up to (x1, y1)."""
    mask = np.zeros((side, side), dtype=np.uint8)
    mask[y0:y1, x0:x1] = 255
    return mask


@pytest.mark.spec("edit:crop:the-box-is-the-masks-plus-the-margin")
def test_edit_crop_the_box_is_the_masks_grown_by_the_margin() -> None:
    crop = plan_crop(_mask(1000, 300, 300, 700, 600), DIALS)

    assert crop.box == (252, 252, 748, 648)
    assert (crop.widened, crop.grown) == (False, False)
    # 496 px scaled to 1216 on the long side; the 396 px side lands on a multiple of 8.
    assert crop.size == (1216, 968)


@pytest.mark.spec("edit:crop:the-box-is-the-masks-plus-the-margin")
def test_edit_crop_the_margin_stops_at_the_image_edge() -> None:
    crop = plan_crop(_mask(1000, 0, 300, 400, 700), DIALS)

    assert crop.box == (0, 252, 448, 748)


@pytest.mark.spec("edit:crop:a-thin-strip-is-widened")
def test_edit_crop_a_thin_strip_is_widened_to_one_to_two_and_recorded() -> None:
    crop = plan_crop(_mask(1000, 300, 400, 700, 440), DIALS)

    assert crop.box == (252, 296, 748, 544)
    assert (crop.widened, crop.grown) == (True, False)
    left, top, right, bottom = crop.box
    assert (bottom - top) / (right - left) >= DIALS["min_aspect"]


@pytest.mark.spec("edit:crop:a-thin-strip-is-widened")
def test_edit_crop_a_strip_at_one_to_two_is_left_as_it_is() -> None:
    crop = plan_crop(_mask(1000, 300, 400, 700, 560), DIALS)

    assert (crop.box, crop.widened) == ((252, 352, 748, 608), False)


@pytest.mark.spec("edit:crop:a-thin-strip-is-widened")
def test_edit_crop_an_image_too_narrow_to_widen_the_box_is_refused_naming_the_fix() -> (
    None
):
    tall = np.zeros((1200, 400), dtype=np.uint8)
    tall[100:1100, 180:220] = 255

    with pytest.raises(
        Refusal, match=r"400x1200 render cannot widen it to the 548 px.*larger"
    ):
        plan_crop(tall, DIALS)


@pytest.mark.spec("edit:crop:a-tiny-tattoo-is-grown")
def test_edit_crop_a_tiny_tattoo_is_grown_until_the_upscale_is_allowed() -> None:
    crop = plan_crop(_mask(1000, 500, 500, 540, 540), DIALS)

    assert crop.box == (368, 368, 672, 672)
    assert (crop.widened, crop.grown) == (False, True)
    assert crop.size == (DIALS["long_side"], DIALS["long_side"])
    assert DIALS["long_side"] / 304 <= DIALS["max_upscale"]


@pytest.mark.spec("edit:crop:a-tiny-tattoo-is-grown")
def test_edit_crop_a_grown_box_is_moved_inside_the_image() -> None:
    crop = plan_crop(_mask(1000, 0, 0, 40, 40), DIALS)

    assert crop.box == (0, 0, 304, 304)
    assert crop.grown


@pytest.mark.spec("edit:crop:a-tiny-tattoo-is-grown")
def test_edit_crop_an_image_too_small_to_grow_the_box_is_refused_naming_the_fix() -> (
    None
):
    with pytest.raises(
        Refusal, match=r"200x200 render cannot grow it to the 304 px.*larger"
    ):
        plan_crop(_mask(200, 80, 80, 120, 120), DIALS)


@pytest.mark.spec("edit:crop:a-tiny-tattoo-is-grown")
def test_edit_crop_an_image_just_big_enough_takes_the_whole_image() -> None:
    crop = plan_crop(_mask(304, 132, 132, 172, 172), DIALS)

    assert crop.box == (0, 0, 304, 304)


@pytest.mark.spec_exempt(
    "structural: every sampled side is a multiple of the VAE's eight"
)
@pytest.mark.parametrize("top", [300, 301, 303])
def test_edit_crop_the_sampling_size_is_a_multiple_of_eight_on_its_long_side(
    top: int,
) -> None:
    crop = plan_crop(_mask(1000, 300, top, 713, top + 307), DIALS)

    assert all(side % 8 == 0 for side in crop.size)
    assert max(crop.size) == DIALS["long_side"]


@pytest.mark.spec("edit:refusals:a-composite-with-no-ink-is-refused")
def test_edit_crop_a_mask_with_no_tattoo_is_refused() -> None:
    faint = np.full((300, 300), MASK_FLOOR, dtype=np.uint8)

    with pytest.raises(Refusal, match="carries no ink"):
        plan_crop(faint, DIALS)


@pytest.mark.spec_exempt("structural: a PNG decodes as its pixels, whatever its mode")
def test_edit_derive_a_png_decodes_to_the_pixels_it_holds() -> None:
    render = _render(8)

    assert (decode_render(_png(render), "7.png") == render).all()
    assert (decode_composite(_png(render)) == render).all()
    grey = np.full((8, 8), 90, dtype=np.uint8)
    assert (decode_composite(_png(grey)) == 90).all()


# --- the request ---------------------------------------------------------------

EDIT = load_edit("tattoo-wai")
REQUEST_SIDE = 400
RENDER_SEED = 42


def _scene(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Return a group, the path of a render in it, and a Multiply composite of it."""
    group = _group(tmp_path)
    render = _render(REQUEST_SIDE)
    image = group / f"{RENDER_SEED}.png"
    image.write_bytes(_png(render))
    composite = tmp_path / "composite.png"
    composite.write_bytes(_png(_multiplied(render)))
    return group, image, composite


def _ask(
    source: Path,
    composite: Path,
    *,
    overrides: dict[str, float | None] | None = None,
    seed: int | None = None,
    rng: random.Random | None = None,
) -> Requested:
    """Request the edit of `source` from `composite`, with the dials as they are."""
    return request(
        EDIT,
        source,
        composite,
        overrides=overrides or {},
        seed=seed,
        rng=rng or random.Random(1),
    )


def _listing(group: Path) -> list[str]:
    """Return the names a group holds."""
    return sorted(path.name for path in group.iterdir())


@pytest.mark.spec("edit:request:a-request-writes-a-pending-record")
def test_edit_request_writes_the_composite_then_a_pending_record(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)

    asked = _ask(image, composite, rng=random.Random(1))

    assert _listing(group) == ["42.edit-1.composite.png", "42.edit-1.json", "42.png"]
    assert (asked.composite, asked.record, asked.number) == (
        group / "42.edit-1.composite.png",
        group / "42.edit-1.json",
        1,
    )
    record = read(asked.record, EDIT_FILE)
    assert record["edit"] == "tattoo-wai"
    assert record["edit_digest"] == EDIT.digest
    assert record["source"] == "42.png"
    assert record["source_sha256"] == digest_of(image.read_bytes())
    assert record["composite_sha256"] == digest_of(asked.composite.read_bytes())
    assert record["seed"] == random.Random(1).getrandbits(64) == asked.seed
    assert record["dials"] == EDIT.dials
    assert record["crop"]["box"] == [0, 0, 304, 304]
    assert record["crop"]["size"] == [1216, 1216]
    assert (record["crop"]["widened"], record["crop"]["grown"]) == (False, True)


@pytest.mark.spec("edit:request:a-repeated-seed-repeats-the-draw")
def test_edit_request_a_repeated_seed_is_held_by_both_records(tmp_path: Path) -> None:
    _, image, composite = _scene(tmp_path)

    first = _ask(image, composite, seed=77)
    second = _ask(image, composite, seed=77, rng=random.Random(2))

    assert [read(it.record, EDIT_FILE)["seed"] for it in (first, second)] == [77, 77]
    assert (first.number, second.number) == (1, 2)


@pytest.mark.spec("edit:request:a-request-writes-a-pending-record")
def test_edit_request_a_number_taken_after_its_choice_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    group, image, composite = _scene(tmp_path)
    chosen = edit_module.next_edit
    calls: list[int] = []

    def raced(where: Path, seed: int) -> int:
        number = chosen(where, seed)
        calls.append(number)
        if len(calls) == 1:
            # Another request takes the number after this one has chosen it.
            _ask(image, composite, seed=88)
        return number

    monkeypatch.setattr(edit_module, "next_edit", raced)

    mine = _ask(image, composite, seed=77)

    # The other request's own choice sits between this one's two.
    assert calls == [1, 1, 2]
    assert mine.number == 2
    assert [read(group / f"42.edit-{k}.json", EDIT_FILE)["seed"] for k in (1, 2)] == [
        88,
        77,
    ]


@pytest.mark.spec("edit:request:a-repeated-seed-repeats-the-draw")
def test_edit_request_without_a_seed_two_draws_differ(tmp_path: Path) -> None:
    _, image, composite = _scene(tmp_path)
    rng = random.Random(3)

    assert _ask(image, composite, rng=rng).seed != _ask(image, composite, rng=rng).seed


@pytest.mark.spec("edit:request:an-override-is-recorded-and-marked")
def test_edit_request_an_override_is_recorded_marked_and_leaves_the_manifest(
    tmp_path: Path,
) -> None:
    _, image, composite = _scene(tmp_path)
    manifest = (EDIT.path / "edit.json").read_bytes()

    asked = _ask(image, composite, overrides={"denoise": 0.3, "lines": None})

    record = read(asked.record, EDIT_FILE)
    assert record["dials"]["denoise"] == 0.3
    assert record["overridden"] == ["denoise"]
    assert record["dials"] == {**EDIT.dials, "denoise": 0.3}
    assert (EDIT.path / "edit.json").read_bytes() == manifest
    assert load_edit("tattoo-wai").dials["denoise"] == EDIT.dials["denoise"]


@pytest.mark.spec("edit:request:an-override-is-recorded-and-marked")
def test_edit_request_every_override_is_listed_in_the_dials_order(
    tmp_path: Path,
) -> None:
    _, image, composite = _scene(tmp_path)

    asked = _ask(
        image, composite, overrides={"lines": 0.7, "strength": 0.8, "denoise": 0.25}
    )

    assert read(asked.record, EDIT_FILE)["overridden"] == [
        "denoise",
        "strength",
        "lines",
    ]


@pytest.mark.spec("edit:request:an-override-is-recorded-and-marked")
@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("denoise", 0.0),
        ("denoise", 1.5),
        ("lines", 1.1),
        ("lines", -0.1),
        ("strength", -1.0),
    ],
)
def test_edit_request_an_override_outside_its_range_is_refused_and_writes_nothing(
    name: str, value: float, tmp_path: Path
) -> None:
    group, image, composite = _scene(tmp_path)
    before = _listing(group)

    with pytest.raises(Refusal, match=rf"--{name} {value} is outside the range"):
        _ask(image, composite, overrides={name: value})

    assert _listing(group) == before


@pytest.mark.spec("edit:request:an-override-is-recorded-and-marked")
@pytest.mark.parametrize(
    ("name", "value"),
    [("denoise", 1.0), ("lines", 0.0), ("lines", 1.0), ("strength", 0.0)],
)
def test_edit_request_an_override_at_the_end_of_its_range_is_taken(
    name: str, value: float, tmp_path: Path
) -> None:
    _, image, composite = _scene(tmp_path)

    asked = _ask(image, composite, overrides={name: value})

    assert read(asked.record, EDIT_FILE)["dials"][name] == value


@pytest.mark.spec("edit:request:an-edits-image-chains")
def test_edit_request_an_edits_image_chains_to_the_next_number(tmp_path: Path) -> None:
    group, image, composite = _scene(tmp_path)
    _ask(image, composite)
    edited = group / "42.edit-1.png"
    edited.write_bytes(_png(_multiplied(_render(REQUEST_SIDE), 0.9)))
    again = tmp_path / "again.png"
    again.write_bytes(_png(_multiplied(_multiplied(_render(REQUEST_SIDE), 0.9), 0.5)))

    chained = _ask(edited, again)

    assert chained.number == 2
    assert _listing(group) == [
        "42.edit-1.composite.png",
        "42.edit-1.json",
        "42.edit-1.png",
        "42.edit-2.composite.png",
        "42.edit-2.json",
        "42.png",
    ]
    record = read(chained.record, EDIT_FILE)
    assert record["source"] == "42.edit-1.png"
    assert record["source_sha256"] == digest_of(edited.read_bytes())


@pytest.mark.spec("edit:request:the-composite-is-kept-as-pixels-only")
def test_edit_request_the_kept_composite_carries_no_profile_and_no_text(
    tmp_path: Path,
) -> None:
    _, image, composite = _scene(tmp_path)
    pixels = _multiplied(_render(REQUEST_SIDE))
    notes = PngInfo()
    notes.add_text("note", "a tattoo")
    Image.fromarray(pixels).save(
        composite, "PNG", icc_profile=b"a profile", pnginfo=notes
    )
    assert Image.open(composite).info["note"] == "a tattoo"
    assert "icc_profile" in Image.open(composite).info

    asked = _ask(image, composite)

    with Image.open(asked.composite) as kept:
        assert kept.mode == "RGB"
        assert "icc_profile" not in kept.info
        assert "note" not in kept.info
        assert (np.asarray(kept) == pixels).all()


@pytest.mark.spec("edit:request:the-composite-is-kept-as-pixels-only")
def test_edit_request_an_opaque_alpha_composite_is_kept_as_rgb(tmp_path: Path) -> None:
    _, image, composite = _scene(tmp_path)
    pixels = _multiplied(_render(REQUEST_SIDE))
    Image.fromarray(pixels).convert("RGBA").save(composite, "PNG")

    asked = _ask(image, composite)

    with Image.open(asked.composite) as kept:
        assert kept.mode == "RGB"
        assert (np.asarray(kept) == pixels).all()


@pytest.mark.spec("edit:refusals:a-composite-of-another-size-is-refused")
def test_edit_request_a_composite_of_another_size_is_refused_and_writes_nothing(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    composite.write_bytes(_png(_multiplied(_render(REQUEST_SIDE - 10))))
    before = _listing(group)

    with pytest.raises(Refusal, match="composite is 390x390 and the render is 400x400"):
        _ask(image, composite)

    assert _listing(group) == before


@pytest.mark.spec("edit:refusals:a-composite-with-no-ink-is-refused")
def test_edit_request_a_composite_with_no_ink_writes_nothing(tmp_path: Path) -> None:
    group, image, composite = _scene(tmp_path)
    composite.write_bytes(image.read_bytes())
    before = _listing(group)

    with pytest.raises(Refusal, match="carries no ink"):
        _ask(image, composite)

    assert _listing(group) == before


@pytest.mark.spec_exempt("structural: a composite that is not on disk is refused")
def test_edit_request_a_composite_that_is_missing_is_refused_and_writes_nothing(
    tmp_path: Path,
) -> None:
    group, image, _ = _scene(tmp_path)
    before = _listing(group)

    with pytest.raises(Refusal, match=r"the composite gone\.png: cannot be read"):
        _ask(image, tmp_path / "gone.png")

    assert _listing(group) == before


@pytest.mark.spec_exempt(
    "structural: a source outside the run layout is refused by name"
)
def test_edit_request_a_source_that_is_no_render_is_refused(tmp_path: Path) -> None:
    _, _, composite = _scene(tmp_path)
    stray = tmp_path / "42.png"
    stray.write_bytes(_png(_render(REQUEST_SIDE)))

    with pytest.raises(Refusal, match="is not an image a render wrote"):
        _ask(stray, composite)


# --- the verb ------------------------------------------------------------------


def _verb(
    image: Path, composite: Path, *flags: str, edit: str = "tattoo-wai"
) -> tuple[int, str, str, Path]:
    """Run `edit` on a wiring with no endpoint; return its exit, streams and group."""
    wired = bare_wiring(rng=random.Random(1))
    args = build_parser().parse_args(
        ["edit", edit, str(image), "--composite", str(composite), *flags]
    )
    assert isinstance(wired.out, io.StringIO)
    assert isinstance(wired.err, io.StringIO)
    code = dispatch(args, wired)
    return code, wired.out.getvalue(), wired.err.getvalue(), image.parent


@pytest.mark.spec("edit:request:a-request-rents-nothing")
def test_edit_verb_succeeds_on_a_wiring_with_no_endpoint_and_opens_no_session(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)

    code, out, err, _ = _verb(image, composite)

    # `bare_wiring` has no client and a gpunit that fails the test when it is called.
    assert (code, err) == (0, "")
    assert _listing(group) == ["42.edit-1.composite.png", "42.edit-1.json", "42.png"]
    assert (
        "edit wrote 0123456789ab_a/summon-anime-wai/outputs/001/42.edit-1.json" in out
    )
    assert "edit pending: run `python -m isekai render " in out


@pytest.mark.spec("edit:request:a-repeated-seed-repeats-the-draw")
def test_edit_verb_a_seed_and_the_dials_reach_the_record(tmp_path: Path) -> None:
    group, image, composite = _scene(tmp_path)

    code, _, _, _ = _verb(
        image,
        composite,
        "--seed",
        "5",
        "--denoise",
        "0.3",
        "--strength",
        "0.9",
        "--lines",
        "0.5",
    )

    record = read(group / "42.edit-1.json", EDIT_FILE)
    assert code == 0
    assert record["seed"] == 5
    assert record["overridden"] == ["denoise", "strength", "lines"]
    assert [record["dials"][name] for name in ("denoise", "strength", "lines")] == [
        0.3,
        0.9,
        0.5,
    ]


@pytest.mark.spec_exempt(
    "structural: an untracked edit is refused, naming the tracked ones"
)
@pytest.mark.parametrize("name", ["tattoo-v1", "../flows", "", "edit.json"])
def test_edit_verb_an_untracked_edit_is_refused_naming_the_tracked_ones(
    name: str, tmp_path: Path
) -> None:
    group, image, composite = _scene(tmp_path)

    code, out, err, _ = _verb(image, composite, edit=name)

    assert code == 1
    assert out == ""
    assert f"refused: {name}: not an edit this build tracks; " in err
    assert "the edits it carries are tattoo-wai" in err
    assert _listing(group) == ["42.png"]


@pytest.mark.spec("edit:refusals:a-composite-with-no-ink-is-refused")
def test_edit_verb_a_refused_request_exits_one_and_writes_nothing(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    composite.write_bytes(image.read_bytes())

    code, out, err, _ = _verb(image, composite)

    assert (code, out) == (1, "")
    assert "refused: the composite carries no ink" in err
    assert _listing(group) == ["42.png"]


@pytest.mark.spec_exempt("structural: the composite is required at parse time")
def test_edit_verb_a_request_without_a_composite_is_refused_at_parse_time(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as refused:
        build_parser().parse_args(["edit", "tattoo-wai", "outputs/001/42.png"])

    assert refused.value.code == 2
    assert "--composite" in capsys.readouterr().err


@pytest.mark.spec_exempt(
    "structural: a seed outside the sampler's range is refused at parse time"
)
def test_edit_verb_a_seed_past_the_sampler_is_refused_at_parse_time(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "edit",
                "tattoo-wai",
                "a.png",
                "--composite",
                "c.png",
                "--seed",
                str(2**64),
            ]
        )

    assert "unsigned 64-bit range" in capsys.readouterr().err


# --- the sampling --------------------------------------------------------------

SAMPLED = (10, 200, 30)
# The crop of the request scene: the whole top-left 304 px, sampled at 1216 px.
CROP_SIZE = 1216


def _pod(rejects: TransportFailure | None = None) -> RecordingComfyClient:
    """Return a client whose pod answers with a flat sampled crop."""
    flat = np.full((CROP_SIZE, CROP_SIZE, 3), SAMPLED, dtype=np.uint8)
    return RecordingComfyClient(rejects=rejects, view_bytes=_png(flat))


def _sampled(
    tmp_path: Path, pod: RecordingComfyClient | None = None, **overrides: float | None
) -> tuple[Path, Path, RecordingComfyClient]:
    """Request an edit in a scene and sample it; return the group, record and pod."""
    group, image, composite = _scene(tmp_path)
    asked = _ask(image, composite, overrides=overrides, seed=77)
    pod = pod or _pod()
    sample(pod, asked.record, runtime=lambda: read_runtime(pod))
    return group, asked.record, pod


@pytest.mark.spec("edit:session:the-pod-receives-only-crops")
def test_edit_sample_uploads_the_crop_its_mask_and_its_control_and_no_other_image(
    tmp_path: Path,
) -> None:
    _, _, pod = _sampled(tmp_path)

    assert [name for name, _ in pod.uploads] == [
        "42.edit-1.crop.png",
        "42.edit-1.mask.png",
        "42.edit-1.control.png",
    ]
    for _, body in pod.uploads:
        with Image.open(io.BytesIO(body)) as sent:
            assert sent.size == (CROP_SIZE, CROP_SIZE)
    # The tattoo's square, at (100, 100) of a 304 px box, lands at (400, 400).
    with Image.open(io.BytesIO(pod.uploads[0][1])) as crop:
        assert np.asarray(crop.convert("RGB"))[400, 400].tolist() == [100, 75, 60]


@pytest.mark.spec("edit:session:the-pod-receives-only-crops")
def test_edit_sample_the_graph_is_patched_from_the_manifest_and_the_record(
    tmp_path: Path,
) -> None:
    _, _, pod = _sampled(tmp_path, denoise=0.3, strength=0.9)

    (graph,) = pod.submissions
    nodes = EDIT.nodes
    assert graph[nodes["image"]]["inputs"]["image"] == "stored-42.edit-1.crop.png"
    assert graph[nodes["mask"]]["inputs"]["image"] == "stored-42.edit-1.mask.png"
    assert graph[nodes["control"]]["inputs"]["image"] == "stored-42.edit-1.control.png"
    sampler = graph[nodes["sampler"]]["inputs"]
    assert (sampler["seed"], sampler["denoise"], sampler["steps"]) == (77, 0.3, 28)
    assert graph[nodes["apply"]]["inputs"]["strength"] == 0.9
    assert graph[nodes["positive"]]["inputs"]["text"] == EDIT.prompt["positive"]
    assert graph[nodes["controlnet"]]["inputs"]["control_net_name"] == EDIT.controlnet
    assert graph[nodes["union"]]["inputs"]["type"] == EDIT.union_type
    assert EDIT.graph()[nodes["sampler"]]["inputs"]["seed"] == 0


@pytest.mark.spec("edit:session:a-pending-edit-runs-beside-the-renders")
def test_edit_sample_completes_the_record_and_writes_the_image_beside_the_source(
    tmp_path: Path,
) -> None:
    group, record, pod = _sampled(tmp_path)

    body = read(record, EDIT_FILE)
    assert body["graph_sha256"] == graph_digest(pod.submissions[0])
    assert body["runtime"] == read_runtime(FakeComfyClient())
    assert isinstance(body["duration"], float)
    assert _listing(group) == [
        "42.edit-1.composite.png",
        "42.edit-1.json",
        "42.edit-1.png",
        "42.png",
    ]
    assert pending(group) == []


@pytest.mark.spec("edit:session:a-failed-sampling-leaves-the-request-pending")
def test_edit_sample_a_rejected_graph_leaves_the_request_pending_and_names_the_discard(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    asked = _ask(image, composite)
    before = asked.record.read_bytes()
    pod = _pod(TransportFailure("permanent", "the endpoint rejected the graph"))

    with pytest.raises(Refusal) as refused:
        sample(pod, asked.record, runtime=lambda: read_runtime(pod))

    assert "the sampling failed (permanent) -- the endpoint rejected the graph" in str(
        refused.value
    )
    assert f"python -m isekai discard {group / '42.edit-1.png'}" in str(refused.value)
    assert asked.record.read_bytes() == before
    assert pending(group) == [asked.record]
    assert _listing(group) == ["42.edit-1.composite.png", "42.edit-1.json", "42.png"]


@pytest.mark.spec("edit:session:a-changed-source-refuses-before-the-pod")
def test_edit_sample_a_source_that_changed_is_refused_before_anything_is_sent(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    asked = _ask(image, composite)
    image.write_bytes(_png(_render(REQUEST_SIDE, (190, 150, 120))))
    pod = _pod()

    with pytest.raises(
        Refusal, match=r"42\.edit-1\.json: its source 42\.png has changed"
    ):
        check(asked.record)
    with pytest.raises(Refusal, match="its source 42.png has changed"):
        sample(pod, asked.record, runtime=lambda: read_runtime(pod))

    assert (pod.uploads, pod.submissions, pod.stats_calls) == ([], [], 0)


@pytest.mark.spec("edit:session:a-changed-source-refuses-before-the-pod")
def test_edit_sample_a_changed_composite_or_edit_is_refused_naming_the_discard(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    asked = _ask(image, composite)
    asked.composite.write_bytes(_png(_multiplied(_render(REQUEST_SIDE), 0.4)))

    with pytest.raises(Refusal, match=r"its composite 42\.edit-1\.composite\.png has"):
        check(asked.record)

    other = _ask(image, composite)
    body = read(other.record, EDIT_FILE)
    body["edit_digest"] = "0" * 64
    write(other.record, EDIT_FILE, body)
    with pytest.raises(Refusal, match="edit tattoo-wai has changed since"):
        check(other.record)
    assert "python -m isekai discard" in _refusal(lambda: check(other.record))


def _refusal(act: "Callable[[], object]") -> str:
    """Return the text of the refusal `act` raises."""
    with pytest.raises(Refusal) as refused:
        act()
    return str(refused.value)


@pytest.mark.spec("edit:session:a-changed-source-refuses-before-the-pod")
def test_edit_sample_a_source_another_edit_will_write_is_not_yet_checked(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    _ask(image, composite)
    first = group / "42.edit-1.png"
    first.write_bytes(_png(_multiplied(_render(REQUEST_SIDE), 0.9)))
    again = tmp_path / "again.png"
    again.write_bytes(_png(_multiplied(_multiplied(_render(REQUEST_SIDE), 0.9), 0.5)))
    chained = _ask(first, again)
    first.unlink()

    check(chained.record, waiting=[first])
    with pytest.raises(Refusal, match=r"its source 42\.edit-1\.png cannot be read"):
        check(chained.record)


@pytest.mark.spec_exempt(
    "structural: pending lists the records with no image, in order"
)
def test_edit_sample_pending_lists_the_requests_with_no_image_in_chain_order(
    tmp_path: Path,
) -> None:
    group = _group(tmp_path)
    for name in ("9.edit-2.json", "9.edit-1.json", "7.edit-1.json", "7.edit-1.png"):
        (group / name).write_bytes(b"{}")
    (group / "9.edit-1.composite.png").write_bytes(b"png")
    (group / "notes.json").write_bytes(b"{}")

    assert [path.name for path in pending(group)] == ["9.edit-1.json", "9.edit-2.json"]
    assert [path.name for path in records(group)] == [
        "7.edit-1.json",
        "9.edit-1.json",
        "9.edit-2.json",
    ]
    assert pending(tmp_path / "gone") == []


# --- the stitch ----------------------------------------------------------------


def _stitched(lines: float = 0.4) -> "np.ndarray":
    """Return the stitch of a flat sampled crop into the request scene's composite."""
    render = _render(REQUEST_SIDE)
    composite = _multiplied(render)
    derived = derive(render, composite, DIALS)
    crop = plan_crop(derived.mask, DIALS)
    flat = np.full((CROP_SIZE, CROP_SIZE, 3), SAMPLED, dtype=np.uint8)
    return stitch(composite, _png(flat), derived, crop, lines)


@pytest.mark.spec("edit:session:a-pending-edit-runs-beside-the-renders")
def test_edit_stitch_the_crop_replaces_the_composite_where_the_mask_is_full() -> None:
    stitched = _stitched(lines=0.0)

    assert stitched[100, 100].tolist() == list(SAMPLED)
    # Far from the tattoo the composite stands, whatever the crop held.
    assert stitched[300, 300].tolist() == list(SKIN)
    assert stitched[5, 5].tolist() == list(SKIN)


@pytest.mark.spec("edit:session:a-pending-edit-runs-beside-the-renders")
def test_edit_stitch_the_feather_blends_the_crop_with_the_composite() -> None:
    render = _render(REQUEST_SIDE)
    derived = derive(render, _multiplied(render), DIALS)
    weight = derived.mask[100, 80 - 3] / 255
    assert 0.5 < weight < 1.0

    edge = _stitched(lines=0.0)[100, 80 - 3]

    for now, skin, sampled in zip(edge, SKIN, SAMPLED, strict=True):
        assert abs(int(now) - (skin * (1 - weight) + sampled * weight)) <= 1


@pytest.mark.spec("edit:session:a-pending-edit-runs-beside-the-renders")
def test_edit_stitch_the_lines_are_multiplied_by_one_minus_lines_of_the_darkness() -> (
    None
):
    held = _stitched(lines=0.4)
    none = _stitched(lines=0.0)

    # Darkness 0.5 under the ink: the sampled colour times 1 - 0.4 * 0.5.
    assert held[100, 100].tolist() == [round(level * 0.8) for level in SAMPLED]
    assert none[100, 100].tolist() == list(SAMPLED)
    assert (held[300, 300] == none[300, 300]).all()
    full = _stitched(lines=1.0)
    assert full[100, 100].tolist() == [round(level * 0.5) for level in SAMPLED]


@pytest.mark.spec("edit:session:a-pending-edit-runs-beside-the-renders")
def test_edit_stitch_the_written_image_is_the_stitch_of_the_samplers_answer(
    tmp_path: Path,
) -> None:
    group, _, _ = _sampled(tmp_path)

    with Image.open(group / "42.edit-1.png") as written:
        assert written.mode == "RGB"
        assert written.size == (REQUEST_SIDE, REQUEST_SIDE)
        pixels = np.asarray(written)
    assert pixels[100, 100].tolist() == [round(level * 0.8) for level in SAMPLED]
    assert pixels[300, 300].tolist() == list(SKIN)


@pytest.mark.spec("edit:session:a-failed-sampling-leaves-the-request-pending")
def test_edit_stitch_a_crash_before_the_image_leaves_a_completed_record_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    group, image, composite = _scene(tmp_path)
    asked = _ask(image, composite)

    def crashed(path: Path, body: bytes) -> None:
        raise OSError("disk gone")

    monkeypatch.setattr(edit_module, "write_atomically", crashed)
    pod = _pod()
    with pytest.raises(OSError, match="disk gone"):
        sample(pod, asked.record, runtime=lambda: read_runtime(pod))

    assert "duration" in read(asked.record, EDIT_FILE)
    assert not (group / "42.edit-1.png").exists()
    assert pending(group) == [asked.record]


@pytest.mark.spec_exempt("structural: bytes the endpoint sent that are no image refuse")
def test_edit_stitch_an_answer_that_is_no_image_is_refused() -> None:
    render = _render(REQUEST_SIDE)
    composite = _multiplied(render)
    derived = derive(render, composite, DIALS)

    with pytest.raises(Refusal, match="sampled crop cannot be read; check the pod"):
        stitch(composite, b"not a png", derived, plan_crop(derived.mask, DIALS), 0.4)


# --- the verb's pending form ---------------------------------------------------

CELL = "0123456789ab_a/summon-anime-wai"


def _pending(
    tmp_path: Path, *flags: str, client: RecordingComfyClient | None = None
) -> tuple[int, str, str]:
    """Run `edit --pending` over the scene's cell; return its exit and streams."""
    wired = bare_wiring(runs_root=tmp_path / "runs", client=client)
    args = build_parser().parse_args(["edit", "--pending", CELL, *flags])
    assert isinstance(wired.out, io.StringIO)
    assert isinstance(wired.err, io.StringIO)
    return dispatch(args, wired), wired.out.getvalue(), wired.err.getvalue()


@pytest.mark.spec("edit:session:a-changed-source-refuses-before-the-pod")
def test_edit_pending_without_a_client_derives_and_checks_and_rents_nothing(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    _ask(image, composite)
    before = _listing(group)

    code, out, err = _pending(tmp_path)

    assert (code, err) == (0, "")
    assert "0123456789ab_a: summon-anime-wai/42.edit-1.json is ready to sample" in out
    assert _listing(group) == before


@pytest.mark.spec("edit:session:a-changed-source-refuses-before-the-pod")
def test_edit_pending_a_changed_source_refuses_naming_the_edit_and_the_discard(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    _ask(image, composite)
    image.write_bytes(_png(_render(REQUEST_SIDE, (190, 150, 120))))
    pod = _pod()

    code, out, err = _pending(tmp_path, client=pod)

    assert (code, out) == (1, "")
    assert "refused: 42.edit-1.json: its source 42.png has changed" in err
    assert "python -m isekai discard" in err
    assert (pod.uploads, pod.submissions, pod.stats_calls) == ([], [], 0)


@pytest.mark.spec("edit:session:a-pending-edit-runs-beside-the-renders")
def test_edit_pending_with_a_client_samples_each_pending_edit_in_chain_order(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    _ask(image, composite, seed=5)
    _ask(image, composite, seed=6)
    pod = _pod()

    code, out, err = _pending(tmp_path, client=pod)

    assert (code, err) == (0, "")
    assert (group / "42.edit-1.png").is_file()
    assert (group / "42.edit-2.png").is_file()
    assert [
        graph[EDIT.nodes["sampler"]]["inputs"]["seed"] for graph in pod.submissions
    ] == [5, 6]
    assert out.splitlines() == [
        "0123456789ab_a: edited summon-anime-wai/42.edit-1.png",
        "0123456789ab_a: edited summon-anime-wai/42.edit-2.png",
    ]
    assert pod.stats_calls == 1


@pytest.mark.spec("edit:session:a-failed-sampling-leaves-the-request-pending")
def test_edit_pending_a_failed_sampling_does_not_cost_the_next_its_turn(
    tmp_path: Path,
) -> None:
    group, image, composite = _scene(tmp_path)
    _ask(image, composite)
    pod = _pod(TransportFailure("permanent", "rejected"))

    code, out, err = _pending(tmp_path, client=pod)

    assert (code, out) == (1, "")
    assert "refused: 42.edit-1.json: the sampling failed (permanent) -- rejected" in err
    assert [path.name for path in pending(group)] == ["42.edit-1.json"]


@pytest.mark.spec_exempt("structural: --progress json prints one line per sampled edit")
def test_edit_pending_progress_json_prints_a_line_per_sampled_edit(
    tmp_path: Path,
) -> None:
    _, image, composite = _scene(tmp_path)
    _ask(image, composite)

    code, out, err = _pending(tmp_path, "--progress", "json", client=_pod())

    (line,) = [json.loads(text) for text in out.splitlines()]
    assert code == 0
    assert line["run"] == "0123456789ab_a"
    assert (line["flow"], line["stage"], line["state"]) == (
        "summon-anime-wai",
        "edit",
        "done",
    )
    assert (line["version"], line["file"]) == (1, "42.edit-1.png")
    assert "edited summon-anime-wai/42.edit-1.png" in err


@pytest.mark.spec_exempt("structural: a cell is named as <run-id>/<flow>")
@pytest.mark.parametrize(
    ("cell", "message"),
    [
        ("nowhere", "not a cell"),
        ("0123456789ab_b/summon-anime-wai", "no run 0123456789ab_b under"),
        ("0123456789ab_a/not-a-flow", "not-a-flow: not a flow this build tracks"),
    ],
)
def test_edit_pending_a_bad_cell_is_refused_before_any_check(
    cell: str, message: str, tmp_path: Path
) -> None:
    _scene(tmp_path)
    wired = bare_wiring(runs_root=tmp_path / "runs")
    args = build_parser().parse_args(["edit", "--pending", cell])

    assert dispatch(args, wired) == 1
    assert isinstance(wired.err, io.StringIO)
    assert message in wired.err.getvalue()


@pytest.mark.spec_exempt(
    "structural: a request and --pending are two forms, never both"
)
def test_edit_pending_takes_cells_alone_and_a_request_takes_its_names(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    wired = bare_wiring(runs_root=tmp_path / "runs")
    assert isinstance(wired.err, io.StringIO)
    mixed = build_parser().parse_args(["edit", "tattoo-wai", "--pending", CELL])
    assert dispatch(mixed, wired) == 1
    assert "--pending takes cells alone" in wired.err.getvalue()

    bare = build_parser().parse_args(["edit", "--composite", "c.png"])
    assert dispatch(bare, wired) == 1
    assert "a request names its edit and its render" in wired.err.getvalue()

    with pytest.raises(SystemExit):
        build_parser().parse_args(
            ["edit", "tattoo-wai", "a.png", "--composite", "c.png", "--pending", CELL]
        )
    assert "not allowed with argument" in capsys.readouterr().err

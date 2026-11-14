"""The chain: thin-plate splines, the lookup, the clip, the Multiply and the crop box.

Every image is a small array built here, so what each function must carry is known.
"""

import math

import numpy as np
import pytest

from isekai.foundation.refusal import Refusal
from isekai.shared import chain
from isekai.shared.chain import (
    MIN_PAIRS,
    Spline,
    clip,
    crop_box,
    lookup,
    multiply,
    polygon_mask,
)

SCATTER = np.array(
    [(0, 0), (40, 3), (5, 38), (42, 40), (20, 18), (31, 9), (12, 25)], dtype=float
)


def _bent() -> np.ndarray:
    """Return `SCATTER` moved by an offset that differs from point to point."""
    return SCATTER + np.array(
        [(2, -1), (-3, 4), (5, 5), (0, -6), (1, 1), (-2, 3), (4, 0)]
    )


@pytest.mark.spec("tattoo:chain:a-spline-is-exact-at-its-pairs")
def test_chain_spline_is_exact_at_its_pairs() -> None:
    target = _bent()

    mapped = Spline(SCATTER, target)(SCATTER)

    assert np.abs(mapped - target).max() < 1e-6


@pytest.mark.spec("tattoo:chain:a-spline-refuses-too-few-pairs")
def test_chain_spline_refuses_too_few_pairs_naming_the_floor_and_the_pairs_given() -> (
    None
):
    with pytest.raises(Refusal, match=rf"at least {MIN_PAIRS} pairs, got 2"):
        Spline(SCATTER[:2], _bent()[:2])


@pytest.mark.spec("tattoo:chain:a-spline-refuses-pairs-on-a-line")
def test_chain_spline_refuses_pairs_on_a_line_as_it_refuses_too_few() -> None:
    online = np.array([(0, 0), (10, 10), (20, 20)], dtype=float)

    with pytest.raises(Refusal, match="lie on a line"):
        Spline(online, online + 3)
    assert len(online) == MIN_PAIRS


@pytest.mark.spec("tattoo:chain:a-spline-refuses-pairs-on-a-line")
def test_chain_spline_takes_the_floors_pairs_off_a_line() -> None:
    triangle = np.array([(0, 0), (10, 0), (0, 10)], dtype=float)

    assert Spline(triangle, triangle + 3)(triangle[:1]).shape == (1, 2)


@pytest.mark.spec_exempt(
    "structural: a repeated source point leaves no system to solve"
)
def test_chain_spline_refuses_two_pairs_at_one_source_point() -> None:
    repeated = SCATTER.copy()
    repeated[1] = repeated[0]

    with pytest.raises(Refusal, match="share a source point"):
        Spline(repeated, _bent())


@pytest.mark.spec_exempt("structural: a source point has one target point")
def test_chain_spline_refuses_a_target_for_each_source_point_that_is_missing() -> None:
    with pytest.raises(Refusal, match="one target point for each source point"):
        Spline(SCATTER, _bent()[:-1])


@pytest.mark.spec("tattoo:chain:a-translation-is-carried")
def test_chain_spline_carries_a_translation_as_a_translation() -> None:
    offset = np.array([5.0, -2.0])
    spline = Spline(SCATTER, SCATTER + offset)
    away = np.array([(100.0, 7.0), (-30.0, 55.0), (21.5, 19.25)])

    assert np.abs(spline(away) - (away + offset)).max() < 1e-6


@pytest.mark.spec_exempt("structural: a chunked call is the whole call")
def test_chain_spline_chunks_a_large_grid_without_changing_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spline = Spline(SCATTER, _bent())
    grid = np.random.default_rng(3).uniform(-10, 60, size=(50, 2))
    whole = spline(grid)

    monkeypatch.setattr(chain, "CHUNK", 7)
    kernel = chain._kernel
    calls: list[int] = []

    def counted(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        calls.append(len(a))
        return kernel(a, b)

    monkeypatch.setattr(chain, "_kernel", counted)

    np.testing.assert_allclose(spline(grid), whole, rtol=0, atol=1e-9)
    assert len(calls) == math.ceil(len(grid) / 7)


def _ink(width: int, height: int) -> np.ndarray:
    """Return opaque black ink of the given size, RGBA in 0..1."""
    ink = np.zeros((height, width, 4))
    ink[..., 3] = 1.0
    return ink


def _shift(dx: float, dy: float) -> Spline:
    """Return the stage that moves every point by (dx, dy)."""
    corners = np.array([(0, 0), (60, 0), (0, 60), (60, 60)], dtype=float)
    return Spline(corners, corners + np.array([dx, dy]))


@pytest.mark.spec("tattoo:chain:the-lookup-is-backwards-and-leaves-no-hole")
def test_chain_lookup_runs_each_stage_and_leaves_no_hole() -> None:
    layer = lookup(_ink(20, 20), [_shift(10, 10), _shift(5, 0)], (30, 30))

    assert layer.shape == (30, 30, 4)
    assert np.isfinite(layer).all()
    assert layer[0, 0].tolist() == pytest.approx([0.0, 0.0, 0.0, 1.0])
    assert layer[4, 4].tolist() == pytest.approx([0.0, 0.0, 0.0, 1.0])
    assert layer[29, 29].tolist() == pytest.approx([1.0, 1.0, 1.0, 0.0])
    assert layer[0, 29].tolist() == pytest.approx([1.0, 1.0, 1.0, 0.0])


@pytest.mark.spec("tattoo:chain:the-lookup-is-backwards-and-leaves-no-hole")
def test_chain_lookup_samples_between_pixels_bilinearly() -> None:
    ink = np.zeros((4, 4, 4))
    ink[:, 2:, :3] = 1.0
    ink[..., 3] = 1.0

    layer = lookup(ink, [_shift(1.5, 0)], (2, 2))

    assert layer[0, 0, 0] == pytest.approx(0.5)
    assert layer[1, 1, 0] == pytest.approx(1.0)


@pytest.mark.spec("tattoo:chain:a-point-a-hair-past-the-edge-is-on-it")
def test_chain_lookup_takes_a_point_a_hair_past_the_edge_as_on_it() -> None:
    ink = np.zeros((4, 4, 4))
    ink[:, 2:, :3] = 1.0
    ink[..., 3] = 1.0

    for dx, dy in [(-1e-12, 1), (1, -1e-12), (3 + 1e-12, 1), (1, 3 + 1e-12)]:
        layer = lookup(ink, [_shift(dx, dy)], (1, 1))
        assert layer[0, 0, 3] == pytest.approx(1.0)

    for dx, dy in [(-1e-6, 1), (1, -1e-6), (3 + 1e-6, 1), (1, 3 + 1e-6)]:
        layer = lookup(ink, [_shift(dx, dy)], (1, 1))
        assert layer[0, 0].tolist() == pytest.approx([1, 1, 1, 0])


def _filled(width: int, height: int) -> np.ndarray:
    """Return fully opaque white ink, RGBA in 0..1."""
    ink = np.ones((height, width, 4))
    return ink


@pytest.mark.spec("tattoo:chain:the-outline-clips-and-an-exclusion-removes")
def test_chain_composite_the_limb_clips_and_an_exclusion_removes() -> None:
    limb = [(10, 10), (30, 10), (30, 30), (10, 30)]
    hole = [(18, 18), (22, 18), (22, 22), (18, 22)]

    clipped = clip(_filled(40, 40), limb, [hole])
    alpha = clipped[..., 3]

    assert alpha[5, 5] == 0.0
    assert alpha[35, 35] == 0.0
    assert alpha[14, 26] == pytest.approx(1.0, abs=0.01)
    assert alpha[20, 20] == 0.0
    assert 0.0 < alpha[20, 10] < 1.0
    assert np.array_equal(clipped[..., :3], _filled(40, 40)[..., :3])


@pytest.mark.spec("tattoo:chain:the-outline-clips-and-an-exclusion-removes")
def test_chain_composite_clip_leaves_the_ink_it_was_given_as_it_was() -> None:
    ink = _filled(40, 40)

    clip(ink, [(10, 10), (30, 10), (30, 30)])

    assert (ink == 1.0).all()


@pytest.mark.spec("tattoo:chain:the-outline-clips-and-an-exclusion-removes")
def test_chain_composite_a_polygon_mask_is_filled_inside_and_empty_outside() -> None:
    mask = polygon_mask([(2, 2), (8, 2), (8, 8), (2, 8)], (12, 10))

    assert mask.shape == (10, 12)
    assert mask[5, 5] == 255
    assert mask[0, 0] == 0
    assert mask[5, 10] == 0


SLANT = [(2, 2), (30, 2), (2, 30)]


@pytest.mark.spec("tattoo:chain:a-polygon-mask-is-antialiased")
def test_chain_composite_a_polygon_mask_is_antialiased_at_its_edge() -> None:
    mask = polygon_mask(SLANT, (34, 34))
    edge = [mask[32 - x, x] for x in range(4, 26)]

    assert mask[5, 5] == 255
    assert mask[28, 28] == 0
    assert all(0 < value < 255 for value in edge)

    alpha = clip(_filled(34, 34), SLANT)[..., 3]

    assert alpha[5, 5] == pytest.approx(1.0, abs=0.01)
    assert all(0.0 < alpha[32 - x, x] < 1.0 for x in range(4, 26))


@pytest.mark.spec("tattoo:chain:an-exclusions-edge-is-partly-removed")
def test_chain_composite_an_exclusions_edge_is_partly_removed() -> None:
    limb = [(-2, -2), (42, -2), (42, 42), (-2, 42)]

    alpha = clip(_filled(34, 34), limb, [SLANT])[..., 3]

    assert alpha[5, 5] == 0.0
    assert alpha[28, 28] == pytest.approx(1.0, abs=0.01)
    assert alpha[32 - 17, 17] == pytest.approx(1.0 - 96 / 255, abs=0.01)


CORNERS = [(0.0, 0.0), (60.0, 0.0), (0.0, 60.0), (60.0, 60.0)]


def _moved(dx: float, dy: float) -> list[tuple[float, float]]:
    """Return `CORNERS` moved by (dx, dy)."""
    return [(x + dx, y + dy) for x, y in CORNERS]


@pytest.mark.spec_exempt("structural: place reads the pairs, the box and the origin")
def test_chain_place_a_target_pixel_shows_the_ink_pixel_its_pairs_name() -> None:
    ink = np.zeros((20, 20, 4))
    ink[..., 3] = 1.0
    ink[2, 3, :3] = 0.5

    layer = chain.place(ink, (0, 0), [(CORNERS, _moved(3, 2))], (0, 0, 10, 10))

    assert layer.shape == (10, 10, 4)
    assert layer[0, 0].tolist() == pytest.approx([0.5, 0.5, 0.5, 1.0], abs=0.01)
    assert layer[1, 1].tolist() == pytest.approx([0.0, 0.0, 0.0, 1.0], abs=0.01)


@pytest.mark.spec_exempt("structural: the box and the origin shift one side each")
def test_chain_place_the_box_shifts_the_target_and_the_origin_the_source() -> None:
    ink = np.zeros((20, 20, 4))
    ink[..., 3] = 1.0
    ink[5, 6, :3] = 0.5

    layer = chain.place(ink, (10, 10), [(_moved(4, 4), _moved(16, 15))], (4, 4, 8, 8))

    assert layer[0, 0].tolist() == pytest.approx([0.5, 0.5, 0.5, 1.0], abs=0.01)
    assert layer[3, 3].tolist() == pytest.approx([0.0, 0.0, 0.0, 1.0], abs=0.01)


@pytest.mark.spec_exempt("structural: stages chain from the target back to the ink")
def test_chain_place_two_stages_are_carried_one_after_the_other() -> None:
    ink = np.zeros((20, 20, 4))
    ink[..., 3] = 1.0
    ink[4, 5, :3] = 0.5
    stages = [(CORNERS, _moved(2, 0)), (_moved(2, 0), _moved(5, 3))]

    layer = chain.place(ink, (0, 0), stages, (0, 0, 10, 10))

    assert layer[1, 0].tolist() == pytest.approx([0.5, 0.5, 0.5, 1.0], abs=0.01)


@pytest.mark.spec_exempt(
    "structural: the limb and an exclusion are in the box's pixels"
)
def test_chain_place_clips_to_the_limb_and_removes_each_exclusion() -> None:
    ink = np.zeros((40, 40, 4))
    ink[..., 3] = 1.0
    limb = [(14, 14), (30, 14), (30, 30), (14, 30)]
    hole = [(20, 20), (24, 20), (24, 24), (20, 24)]

    layer = chain.place(
        ink, (0, 0), [(CORNERS, CORNERS)], (10, 10, 30, 30), limb, [hole]
    )

    assert layer[2, 2, 3] == 0.0
    assert layer[16, 16, 3] == pytest.approx(1.0, abs=0.01)
    assert layer[12, 12, 3] == 0.0
    assert layer[25, 25, 3] == 0.0


@pytest.mark.spec_exempt("structural: no limb keeps the whole box")
def test_chain_place_with_no_limb_keeps_the_ink_to_the_edge_of_the_box() -> None:
    ink = np.zeros((40, 40, 4))
    ink[..., 3] = 1.0

    layer = chain.place(ink, (0, 0), [(CORNERS, CORNERS)], (0, 0, 30, 30))

    assert layer[1, 1, 3] == pytest.approx(1.0, abs=0.01)
    assert layer[28, 28, 3] == pytest.approx(1.0, abs=0.01)


@pytest.mark.spec_exempt("structural: flatten lays a layer on white as 8-bit RGB")
def test_chain_place_flatten_lays_the_layer_on_white() -> None:
    layer = np.zeros((1, 3, 4))
    layer[0, 0] = (0.0, 0.0, 0.0, 1.0)
    layer[0, 1] = (0.0, 0.0, 0.0, 0.5)
    layer[0, 2] = (0.2, 0.2, 0.2, 0.0)

    flat = chain.flatten(layer)

    assert flat.dtype == np.uint8
    assert flat.shape == (1, 3, 3)
    assert flat[0, 0].tolist() == [0, 0, 0]
    assert flat[0, 1].tolist() == [128, 128, 128]
    assert flat[0, 2].tolist() == [255, 255, 255]


@pytest.mark.spec("tattoo:chain:the-composite-is-a-multiply")
def test_chain_composite_a_dark_pixel_darkens_the_render_there_alone() -> None:
    render = np.full((4, 4, 3), 0.8)
    layer = np.ones((4, 4, 4))
    layer[1, 2, :3] = 0.5

    composite = multiply(render, layer)

    assert composite[1, 2].tolist() == pytest.approx([0.4, 0.4, 0.4])
    untouched = np.ones((4, 4), dtype=bool)
    untouched[1, 2] = False
    assert np.array_equal(composite[untouched], render[untouched])


@pytest.mark.spec("tattoo:chain:the-composite-is-a-multiply")
def test_chain_composite_a_transparent_dark_pixel_leaves_the_render_as_it_was() -> None:
    render = np.full((2, 2, 3), 0.8)
    layer = np.zeros((2, 2, 4))

    assert np.array_equal(multiply(render, layer), render)


@pytest.mark.spec("tattoo:chain:the-crop-box-is-the-points-box")
def test_chain_crop_is_the_points_box_grown_by_the_margin() -> None:
    points = [(10.5, 20.2), (30.7, 40.9), (15.0, 25.0)]

    assert crop_box(points, 5, (100, 100)) == (5, 15, 36, 46)


@pytest.mark.spec("tattoo:chain:the-crop-box-is-the-points-box")
def test_chain_crop_is_clipped_to_the_image() -> None:
    points = [(10.5, 20.2), (30.7, 40.9)]

    assert crop_box(points, 500, (100, 80)) == (0, 0, 100, 80)


@pytest.mark.spec_exempt("structural: a box has points to be the box of")
def test_chain_crop_refuses_no_points() -> None:
    with pytest.raises(Refusal, match="at least one point"):
        crop_box([], 5, (100, 100))

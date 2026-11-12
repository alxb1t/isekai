"""The proposal's geometry over synthetic masks: edges, pairs, joints, the arm."""

import numpy as np
import pytest
from numpy.typing import NDArray

from isekai.shared.proposal import (
    BAND,
    DARK_AFTER,
    FRACTIONS,
    PROMPTS,
    SCORE_CUT,
    bone_pairs,
    bones_of,
    edge_pair,
    joint_pairs,
    nearest_side,
    prompt_points,
    usable_bone,
)

SIZE = (200, 300)


def _rows(top: int, bottom: int) -> NDArray[np.bool_]:
    """Return a mask of the rows `top` to `bottom` inclusive."""
    mask = np.zeros(SIZE, dtype=bool)
    mask[top : bottom + 1] = True
    return mask


def _light() -> NDArray[np.float32]:
    """Return a luminance of white."""
    return np.ones(SIZE, dtype=np.float32)


def _near(found: tuple[float, float] | None, wanted: tuple[float, float]) -> None:
    assert found is not None
    assert found == pytest.approx(wanted)


# --- the edge search ---------------------------------------------------------------


@pytest.mark.spec("placement-proposal:pairs:an-edge-stops-at-the-band-round-the-bone")
def test_propose_edges_stop_at_the_band_and_at_the_masks_own_end() -> None:
    spilled = _rows(95, 199)

    found = edge_pair(spilled, (100, 100), (0, 1), BAND * 40)

    assert found is not None
    _near(found[0], (100, 112))
    _near(found[1], (100, 95))


@pytest.mark.spec("placement-proposal:pairs:an-edge-stops-at-the-band-round-the-bone")
def test_propose_edges_an_image_border_ends_the_walk() -> None:
    found = edge_pair(np.ones(SIZE, dtype=bool), (100, 2), (0, 1), 30)

    assert found is not None
    _near(found[1], (100, 0))


@pytest.mark.spec_exempt("structural: a side with no first pixel gives no pair")
def test_propose_edges_a_side_whose_first_pixel_is_dropped_gives_none() -> None:
    mask = _rows(100, 130)
    mask[101] = False

    assert edge_pair(mask, (100, 100), (0, 1), 20) is None
    assert edge_pair(_rows(0, 99), (100, 100), (0, 1), 20) is None


@pytest.mark.spec("placement-proposal:pairs:a-render-edge-stops-at-the-first-dark-line")
def test_propose_edges_a_dark_line_stops_the_render_and_not_the_photograph() -> None:
    mask = np.ones(SIZE, dtype=bool)
    luminance = _light()
    luminance[108] = 0.0

    render = edge_pair(mask, (100, 100), (0, 1), 20, luminance)
    photograph = edge_pair(mask, (100, 100), (0, 1), 20)

    assert render is not None and photograph is not None
    _near(render[0], (100, 107))
    _near(photograph[0], (100, 120))
    _near(render[1], (100, 80))


@pytest.mark.spec("placement-proposal:pairs:a-dark-line-at-the-bone-stops-nothing")
def test_propose_edges_a_dark_line_within_the_distance_of_the_bone_stops_nothing() -> (
    None
):
    mask = np.ones(SIZE, dtype=bool)
    luminance = _light()
    luminance[100 - DARK_AFTER : 100 + DARK_AFTER + 1] = 0.0

    found = edge_pair(mask, (100, 100), (0, 1), 20, luminance)

    assert found is not None
    _near(found[0], (100, 120))
    _near(found[1], (100, 80))


@pytest.mark.spec("placement-proposal:pairs:a-dark-line-at-the-bone-stops-nothing")
def test_propose_edges_twin_a_dark_line_just_past_the_distance_stops_the_edge() -> None:
    mask = np.ones(SIZE, dtype=bool)
    luminance = _light()
    luminance[100 + DARK_AFTER + 1] = 0.0

    found = edge_pair(mask, (100, 100), (0, 1), 20, luminance)

    assert found is not None
    _near(found[0], (100, 100 + DARK_AFTER))


# --- the pairs of a bone and of an arm ---------------------------------------------

LIMB = ((50.0, 100.0), (150.0, 100.0))


@pytest.mark.spec(
    "placement-proposal:pairs:a-bone-gives-two-edges-and-a-middle-at-each-fraction"
)
def test_propose_pairs_a_bone_gives_two_edges_and_a_middle_at_each_fraction() -> None:
    mask = _rows(90, 110)

    pairs = bone_pairs(LIMB, mask, LIMB, mask, _light())

    assert len(pairs) == 3 * len(FRACTIONS)
    for step, fraction in enumerate(FRACTIONS):
        x = 50 + 100 * fraction
        first, second, middle = pairs[3 * step : 3 * step + 3]
        _near(first[0], (x, 110))
        _near(second[0], (x, 90))
        _near(middle[0], (x, 100))
        assert [pair[1] for pair in (first, second, middle)] == [
            pair[0] for pair in (first, second, middle)
        ]


@pytest.mark.spec(
    "placement-proposal:pairs:a-pair-is-the-same-fraction-and-side-in-both-images"
)
def test_propose_pairs_a_scaled_and_moved_limb_pairs_each_point_with_its_image() -> (
    None
):
    seen = _rows(90, 110)
    drawn = _rows(65, 75)
    moved = ((35.0, 70.0), (85.0, 70.0))

    pairs = bone_pairs(LIMB, seen, moved, drawn, _light())

    assert pairs
    for photograph, render in pairs:
        _near(render, (photograph[0] * 0.5 + 10, photograph[1] * 0.5 + 20))


@pytest.mark.spec_exempt("structural: a fraction short of an edge gives no pair")
def test_propose_pairs_a_fraction_with_no_edge_in_one_image_gives_none() -> None:
    seen = _rows(90, 110)
    drawn = _rows(90, 110)
    drawn[:, : 35 + 1] = False
    drawn[:, 80:] = False

    pairs = bone_pairs(LIMB, seen, LIMB, drawn, _light())

    assert 0 < len(pairs) < 3 * len(FRACTIONS)
    assert len(pairs) % 3 == 0


@pytest.mark.spec_exempt("structural: a bone of no length proposes nothing")
def test_propose_pairs_a_bone_of_no_length_gives_none() -> None:
    point = (50.0, 100.0)
    mask = _rows(90, 110)

    assert bone_pairs((point, point), mask, LIMB, mask, _light()) == []


def _body(scores: float = 0.9) -> tuple[list[tuple[float, float]], list[float]]:
    """Return 17 keypoints on a diagonal, and one score for each."""
    return [(float(10 * index), float(7 * index)) for index in range(17)], [scores] * 17


@pytest.mark.spec("placement-proposal:pairs:the-joints-are-pairs-after-the-bones")
def test_propose_pairs_the_joints_are_the_shoulder_the_elbow_and_the_wrist() -> None:
    seen, seen_scores = _body()
    drawn = [(x + 1, y + 2) for x, y in seen]

    joints = joint_pairs(seen, seen_scores, drawn, [0.9] * 17, "left")

    assert joints == [(seen[5], drawn[5]), (seen[7], drawn[7]), (seen[9], drawn[9])]
    assert [
        pair[0] for pair in joint_pairs(seen, seen_scores, drawn, seen_scores, "right")
    ] == [
        seen[6],
        seen[8],
        seen[10],
    ]


@pytest.mark.spec(
    "placement-proposal:pairs:a-keypoint-under-the-cut-proposes-nothing-for-its-bone"
)
def test_propose_pairs_a_wrist_under_the_cut_drops_its_bone_and_its_joint() -> None:
    seen, seen_scores = _body()
    drawn_scores = [0.9] * 17
    seen_scores[9] = 0.23

    forearm, upper = bones_of("left")[1], bones_of("left")[0]

    assert not usable_bone(forearm, seen_scores, drawn_scores)
    assert usable_bone(upper, seen_scores, drawn_scores)
    assert usable_bone(forearm, drawn_scores, drawn_scores)
    joints = joint_pairs(seen, seen_scores, seen, drawn_scores, "left")
    assert [pair[0] for pair in joints] == [seen[5], seen[7]]


@pytest.mark.spec_exempt("structural: the cut is inclusive")
def test_propose_pairs_a_score_at_the_cut_is_usable() -> None:
    scores = [SCORE_CUT] * 17

    assert usable_bone((5, 7), scores, scores)
    assert not usable_bone((5, 7), scores, [SCORE_CUT - 0.01] * 17)


@pytest.mark.spec_exempt(
    "structural: the prompts are along the bone, the negatives off it"
)
def test_propose_pairs_prompts_lie_along_the_bone_and_negatives_off_it() -> None:
    points, scores = _body()

    positive, negative = prompt_points(points, scores, (5, 7), (7, 9))

    start, end = points[5], points[7]
    assert positive == [
        pytest.approx(
            (start[0] + (end[0] - start[0]) * f, start[1] + (end[1] - start[1]) * f)
        )
        for f in PROMPTS
    ]
    middle = ((points[7][0] + points[9][0]) / 2, (points[7][1] + points[9][1]) / 2)
    torso = [points[index] for index in (5, 6, 11, 12)]
    assert negative == [
        pytest.approx(middle),
        pytest.approx((sum(x for x, _ in torso) / 4, sum(y for _, y in torso) / 4)),
    ]


@pytest.mark.spec_exempt(
    "structural: the torso is the corners that score, and may be none"
)
def test_propose_pairs_the_torso_takes_the_corners_over_the_cut_alone() -> None:
    points, scores = _body()
    scores[6] = scores[11] = 0.1

    _, kept = prompt_points(points, scores, (5, 7), None)
    _, none = prompt_points(points, [0.0] * 17, (5, 7), None)

    assert kept == [
        pytest.approx(
            ((points[5][0] + points[12][0]) / 2, (points[5][1] + points[12][1]) / 2)
        )
    ]
    assert none == []


# --- the arm -----------------------------------------------------------------------


def _arms() -> list[tuple[float, float]]:
    """Return 17 keypoints with the left arm along x=100 and the right along x=300."""
    points = [(200.0, 0.0)] * 17
    for left, right, y in ((5, 6, 100.0), (7, 8, 200.0), (9, 10, 300.0)):
        points[left] = (100.0, y)
        points[right] = (300.0, y)
    return points


@pytest.mark.spec("placement-proposal:pairs:the-arm-nearest-the-tattoo-is-proposed")
def test_propose_side_the_arm_nearest_the_points_is_chosen() -> None:
    arms, good = _arms(), [0.9] * 17

    assert nearest_side([(110.0, 150.0), (95.0, 220.0)], arms, good, good) == "left"
    assert nearest_side([(290.0, 150.0), (310.0, 220.0)], arms, good, good) == "right"


@pytest.mark.spec_exempt(
    "structural: a tie is the left, an arm with no usable bone is out"
)
def test_propose_side_a_tie_is_the_left_and_an_unusable_arm_is_never_chosen() -> None:
    arms, good = _arms(), [0.9] * 17
    low = list(good)
    low[7] = 0.1

    assert nearest_side([(200.0, 150.0)], arms, good, good) == "left"
    assert nearest_side([(110.0, 150.0)], arms, low, good) == "right"
    assert nearest_side([(110.0, 150.0)], arms, good, low) == "right"
    assert nearest_side([(110.0, 150.0)], arms, [0.0] * 17, good) is None


@pytest.mark.spec_exempt("structural: no points name no arm")
def test_propose_side_no_points_name_no_arm() -> None:
    assert nearest_side([], _arms(), [0.9] * 17, [0.9] * 17) is None

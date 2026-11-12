"""The pairs a pose and two silhouettes propose: geometry over arrays, no model.

A limb's bones are walked at fixed fractions; at each, the silhouette's two edges and
its middle are paired between the photograph and the render, and the joints follow.
The arm proposed is the one nearest the tattoo's points in the photograph.

numpy is imported inside the functions that use it (D20), so `python -m isekai`
loads no wheel.
"""

import math
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

# A keypoint scoring under the cut proposes nothing for its bone or joint.
SCORE_CUT = 0.3

# Positive prompts along a bone, as fractions of it.
PROMPTS = (0.25, 0.5, 0.75)

# Fractions along a bone where edges are searched, evenly from 0.1 to 0.9.
STEPS = 6
FRACTIONS = tuple(0.1 + 0.8 * step / (STEPS - 1) for step in range(STEPS))

# The furthest an edge may lie from its bone, as a fraction of the bone's length.
BAND = 0.3

# The render's luminance under which a line stops an edge, and the distance from the
# bone within which none does: the bone's own line may be dark.
DARK = 0.42
DARK_AFTER = 3

Point = tuple[float, float]
Pair = tuple[Point, Point]
Bone = tuple[int, int]
Side = Literal["left", "right"]

# COCO's body keypoints: each arm's shoulder, elbow and wrist, and the torso's corners.
ARMS: Mapping[Side, tuple[int, int, int]] = {"left": (5, 7, 9), "right": (6, 8, 10)}
TORSO = (5, 6, 11, 12)


def bones_of(side: Side) -> tuple[Bone, Bone]:
    """Return the arm's upper arm then forearm, each as its two keypoint indices.

    e.g. "left" -> ((5, 7), (7, 9))
    """
    shoulder, elbow, wrist = ARMS[side]
    return (shoulder, elbow), (elbow, wrist)


def _usable(
    keypoints: Sequence[int], photograph: Sequence[float], render: Sequence[float]
) -> bool:
    """Return whether every keypoint scores at least the cut in both images."""
    return all(
        scores[keypoint] >= SCORE_CUT
        for keypoint in keypoints
        for scores in (photograph, render)
    )


def usable_bone(
    bone: Bone, photograph: Sequence[float], render: Sequence[float]
) -> bool:
    """Return whether both keypoints of `bone` score at least the cut in both images.

    `photograph` and `render` are each image's keypoint scores.
    """
    return _usable(bone, photograph, render)


def _along(start: Point, end: Point, fraction: float) -> Point:
    """Return the point `fraction` of the way from `start` to `end`."""
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )


def prompt_points(
    points: Sequence[Point],
    scores: Sequence[float],
    bone: Bone,
    other: Bone | None,
) -> tuple[list[Point], list[Point]]:
    """Return the segmenter's positive and negative points for `bone` in one image.

    The positives lie along the bone at `PROMPTS`. The negatives are the middle of
    `other`, the arm's other bone, when it is usable and so given, and the torso: the
    mean of the shoulders and hips that score at least the cut, when any does.
    """
    start, end = points[bone[0]], points[bone[1]]
    positive = [_along(start, end, fraction) for fraction in PROMPTS]
    negative: list[Point] = []
    if other is not None:
        negative.append(_along(points[other[0]], points[other[1]], 0.5))
    corners = [points[index] for index in TORSO if scores[index] >= SCORE_CUT]
    if corners:
        negative.append(
            (
                sum(x for x, _ in corners) / len(corners),
                sum(y for _, y in corners) / len(corners),
            )
        )
    return positive, negative


def _reach(
    mask: "NDArray[np.bool_]",
    centre: Point,
    direction: Point,
    reach: float,
    luminance: "NDArray[np.float32] | None",
) -> int:
    """Return how many whole pixels from `centre` along `direction` are kept.

    A pixel is kept while it lies in the image and the mask, within `reach` of the
    centre, and, with a luminance, is not a dark one past `DARK_AFTER`.
    """
    import numpy as np

    height, width = mask.shape
    steps = np.arange(1, int(reach) + 1)
    across = np.rint(centre[0] + direction[0] * steps).astype(int)
    down = np.rint(centre[1] + direction[1] * steps).astype(int)
    inside = (across >= 0) & (across < width) & (down >= 0) & (down < height)
    kept = np.zeros(len(steps), dtype=bool)
    kept[inside] = mask[down[inside], across[inside]]
    if luminance is not None:
        dark = np.zeros(len(steps), dtype=bool)
        dark[inside] = luminance[down[inside], across[inside]] < DARK
        kept &= ~(dark & (steps > DARK_AFTER))
    stopped = np.flatnonzero(~kept)
    return int(stopped[0]) if len(stopped) else len(steps)


def edge_pair(
    mask: "NDArray[np.bool_]",
    centre: Point,
    normal: Point,
    reach: float,
    luminance: "NDArray[np.float32] | None" = None,
) -> tuple[Point, Point] | None:
    """Return the mask's edge on each side of `centre` along `normal`, or None.

    The search walks one pixel at a time from `centre`, first along `normal`, then
    against it, until the mask ends, `reach` is passed or, with a `luminance`, a pixel
    past `DARK_AFTER` is under `DARK`. The edge is the last pixel kept; a side whose
    first pixel is not kept gives none, and so does the pair.
    e.g. a mask of rows 40 to 59, centre (50, 50), normal (0, 1) -> ((50, 59), (50, 40))
    """
    edges: list[Point] = []
    for sign in (1.0, -1.0):
        direction = (normal[0] * sign, normal[1] * sign)
        distance = _reach(mask, centre, direction, reach, luminance)
        if distance == 0:
            return None
        edges.append(
            (centre[0] + direction[0] * distance, centre[1] + direction[1] * distance)
        )
    return edges[0], edges[1]


def _edges_at(
    bone: tuple[Point, Point],
    mask: "NDArray[np.bool_]",
    fraction: float,
    luminance: "NDArray[np.float32] | None",
) -> tuple[Point, Point] | None:
    """Return the mask's two edges across `bone` at `fraction` of its length, or None.

    The first edge lies on the side the bone's direction turned a quarter round, the
    same side in every image.
    """
    start, end = bone
    length = math.dist(start, end)
    normal = (-(end[1] - start[1]) / length, (end[0] - start[0]) / length)
    return edge_pair(
        mask, _along(start, end, fraction), normal, BAND * length, luminance
    )


def bone_pairs(
    photograph: tuple[Point, Point],
    photograph_mask: "NDArray[np.bool_]",
    render: tuple[Point, Point],
    render_mask: "NDArray[np.bool_]",
    luminance: "NDArray[np.float32]",
) -> list[Pair]:
    """Return one bone's pairs: at each fraction the first edge, the second, the middle.

    `photograph` and `render` are the bone's two keypoints in each image. A fraction
    where either image has no edge on both sides gives no pair. The photograph's point
    is first, and the same side of the bone is first in both images.
    """
    if min(math.dist(*bone) for bone in (photograph, render)) == 0:
        return []
    pairs: list[Pair] = []
    for fraction in FRACTIONS:
        seen = _edges_at(photograph, photograph_mask, fraction, None)
        drawn = _edges_at(render, render_mask, fraction, luminance)
        if seen is None or drawn is None:
            continue
        pairs.append((seen[0], drawn[0]))
        pairs.append((seen[1], drawn[1]))
        pairs.append((_along(seen[0], seen[1], 0.5), _along(drawn[0], drawn[1], 0.5)))
    return pairs


def joint_pairs(
    photograph: Sequence[Point],
    photograph_scores: Sequence[float],
    render: Sequence[Point],
    render_scores: Sequence[float],
    side: Side,
) -> list[Pair]:
    """Return the arm's shoulder, elbow and wrist as pairs, each when it is usable."""
    return [
        (photograph[joint], render[joint])
        for joint in ARMS[side]
        if _usable((joint,), photograph_scores, render_scores)
    ]


def _distance_to_segment(point: Point, start: Point, end: Point) -> float:
    """Return the distance from `point` to the segment `start` to `end`."""
    run = (end[0] - start[0], end[1] - start[1])
    length = run[0] ** 2 + run[1] ** 2
    if length == 0:
        return math.dist(point, start)
    along = ((point[0] - start[0]) * run[0] + (point[1] - start[1]) * run[1]) / length
    return math.dist(point, _along(start, end, min(1.0, max(0.0, along))))


def nearest_side(
    points: Sequence[Point],
    keypoints: Sequence[Point],
    photograph_scores: Sequence[float],
    render_scores: Sequence[float],
) -> Side | None:
    """Return the usable arm whose polyline lies nearest the points, or None.

    `points` are the tattoo's on the photograph, `keypoints` the photograph's. An arm
    is usable when a bone of it is, in both images; its polyline runs shoulder, elbow,
    wrist, and the distance is from the points' mean to it. The left wins a tie.
    """
    if not points:
        return None
    mean = (
        sum(x for x, _ in points) / len(points),
        sum(y for _, y in points) / len(points),
    )
    best: tuple[float, Side] | None = None
    for side, joints in ARMS.items():
        if not any(
            usable_bone(bone, photograph_scores, render_scores)
            for bone in bones_of(side)
        ):
            continue
        shoulder, elbow, wrist = (keypoints[joint] for joint in joints)
        distance = min(
            _distance_to_segment(mean, shoulder, elbow),
            _distance_to_segment(mean, elbow, wrist),
        )
        if best is None or distance < best[0]:
            best = (distance, side)
    return None if best is None else best[1]


__all__: Sequence[str] = (
    "ARMS",
    "BAND",
    "DARK",
    "DARK_AFTER",
    "FRACTIONS",
    "PROMPTS",
    "SCORE_CUT",
    "STEPS",
    "Bone",
    "Pair",
    "Point",
    "Side",
    "bone_pairs",
    "bones_of",
    "edge_pair",
    "joint_pairs",
    "nearest_side",
    "prompt_points",
    "usable_bone",
)

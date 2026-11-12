"""Proposed stage-2 pairs: one arm found in two images, segmented and paired.

`propose` reads a person's pose in the photograph and in the render, takes the arm
nearest the tattoo's points, segments each of its bones in both images and pairs
their edges and the joints. It reads no file and keeps nothing; the pose and the
segmenter are passed in, so the suite needs no model.

Stdlib only at module scope: numpy is imported inside `propose` (D20).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from isekai.boundary.pose import PoseFinder
from isekai.boundary.sam2 import Segmenter
from isekai.shared.proposal import (
    Pair,
    Point,
    Side,
    bone_pairs,
    bones_of,
    joint_pairs,
    nearest_side,
    prompt_points,
    usable_bone,
)

if TYPE_CHECKING:
    from PIL.Image import Image


@dataclass(frozen=True)
class Proposal:
    """The arm proposed and its pairs, the photograph's point first.

    `NOTHING` holds no arm and no pair; a chosen arm always holds its joints.
    """

    arm: Side | None
    pairs: tuple[Pair, ...]


NOTHING = Proposal(None, ())


@dataclass(frozen=True)
class Proposer:
    """The models a proposal runs on: a pose finder and a segmenter."""

    pose: PoseFinder
    segmenter: Segmenter

    def propose(
        self, photograph: "Image", render: "Image", points: Sequence[Point]
    ) -> Proposal:
        """Return the proposal for `render` and the tattoo's `points`."""
        return propose(photograph, render, points, self.pose, self.segmenter)


def propose(
    photograph: "Image",
    render: "Image",
    points: Sequence[Point],
    pose: PoseFinder,
    segmenter: Segmenter,
) -> Proposal:
    """Return the pairs of the arm nearest `points`, or `NOTHING`.

    The images are RGB, the photograph upright. `points` are the tattoo's on the
    photograph. No person in either image, or no usable bone, gives `NOTHING`. Each
    image is embedded once, and each usable bone is prompted once in each.
    e.g. a left arm with both bones usable -> bone pairs, then three joint pairs
    """
    import numpy as np

    seen, drawn = pose.find(photograph), pose.find(render)
    if seen is None or drawn is None:
        return NOTHING
    side = nearest_side(points, seen.points, seen.scores, drawn.scores)
    if side is None:
        return NOTHING
    upper, forearm = bones_of(side)
    embedded = segmenter.embed(photograph), segmenter.embed(render)
    luminance = np.asarray(render.convert("L"), dtype=np.float32) / 255.0
    pairs: list[Pair] = []
    for bone, other in ((upper, forearm), (forearm, upper)):
        if not usable_bone(bone, seen.scores, drawn.scores):
            continue
        beside = other if usable_bone(other, seen.scores, drawn.scores) else None
        masks = [
            embedding.mask(*prompt_points(found.points, found.scores, bone, beside))
            for embedding, found in zip(embedded, (seen, drawn), strict=True)
        ]
        pairs += bone_pairs(
            (seen.points[bone[0]], seen.points[bone[1]]),
            masks[0],
            (drawn.points[bone[0]], drawn.points[bone[1]]),
            masks[1],
            luminance,
        )
    pairs += joint_pairs(seen.points, seen.scores, drawn.points, drawn.scores, side)
    return Proposal(side, tuple(pairs))


__all__: Sequence[str] = ("NOTHING", "Proposal", "Proposer", "propose")

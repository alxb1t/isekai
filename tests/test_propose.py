"""`propose` over the fakes, and the wiring seam that opens the models once."""

from collections.abc import Iterator, Sequence
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image, ImageDraw

from isekai.boundary import pose as pose_boundary
from isekai.boundary.pose import Pose
from isekai.boundary.unpack import PLACEMENT_REMEDY
from isekai.foundation.refusal import Refusal
from isekai.interface import wiring
from isekai.interface.wiring import Wiring, proposer_for, proposer_of, wiring_from
from isekai.pipeline.proposing import NOTHING, Proposer, propose
from isekai.shared.proposal import FRACTIONS, PROMPTS
from isekai.shared.vocabulary import Vocabulary
from tests.fakes import FakePoseFinder, FakeSegmenter
from tests.stages import FIELD_MAP, NO_GPUNIT

SIZE = (300, 200)
HALF = 10

Point = tuple[float, float]

# The left arm along y=100, the right along y=180; hips and shoulders give the torso.
LEFT = {5: (50.0, 100.0), 7: (150.0, 100.0), 9: (250.0, 100.0)}
RIGHT = {6: (50.0, 180.0), 8: (150.0, 180.0), 10: (250.0, 180.0)}
HIPS = {11: (60.0, 150.0), 12: (60.0, 170.0)}
TORSO = (55.0, 150.0)


def _pose(**scores: float) -> Pose:
    """Return a pose of both arms and the hips, every score 0.9 unless `kN` says."""
    placed = {**LEFT, **RIGHT, **HIPS}
    points = tuple(placed.get(index, (10.0, 10.0)) for index in range(17))
    marks = [scores.get(f"k{index}", 0.9) for index in range(17)]
    return Pose((0.0, 0.0, 300.0, 200.0), points, tuple(marks))


def _images() -> tuple[Image.Image, Image.Image]:
    """Return a photograph and a render, both light, so no dark line stops an edge."""
    return (
        Image.new("RGB", SIZE, (230, 230, 230)),
        Image.new("RGB", SIZE, (220, 220, 220)),
    )


def _band(
    size: tuple[int, int], positive: Sequence[Point], negative: Sequence[Point]
) -> NDArray[np.bool_]:
    """Paint the rows within `HALF` of the positives' mean height."""
    width, height = size
    middle = sum(y for _, y in positive) / len(positive)
    mask = np.zeros((height, width), dtype=bool)
    mask[round(middle) - HALF : round(middle) + HALF + 1] = True
    return mask


def _empty(
    size: tuple[int, int], positive: Sequence[Point], negative: Sequence[Point]
) -> NDArray[np.bool_]:
    """Paint nothing."""
    return np.zeros((size[1], size[0]), dtype=bool)


def _edges(start: float, end: float, y: float) -> list[Point]:
    """Return a bone's expected points: at each fraction two edges and a middle."""
    found: list[Point] = []
    for fraction in FRACTIONS:
        x = start + (end - start) * fraction
        found += [(x, y + HALF), (x, y - HALF), (x, y)]
    return found


def _approx(points: Sequence[Point]) -> list[object]:
    return [pytest.approx(point) for point in points]


@pytest.mark.spec(
    "placement-proposal:pairs:a-bone-gives-two-edges-and-a-middle-at-each-fraction"
)
@pytest.mark.spec("placement-proposal:pairs:the-joints-are-pairs-after-the-bones")
@pytest.mark.spec("placement-proposal:pairs:the-arm-nearest-the-tattoo-is-proposed")
def test_propose_pipeline_the_nearest_arm_gives_its_bones_then_its_joints() -> None:
    photograph, render = _images()
    pose, segmenter = FakePoseFinder(_pose(), _pose()), FakeSegmenter(_band)

    answer = propose(photograph, render, [(100.0, 105.0)], pose, segmenter)

    assert answer.arm == "left"
    expected = [*_edges(50, 150, 100), *_edges(150, 250, 100), *LEFT.values()]
    assert [pair[0] for pair in answer.pairs] == _approx(expected)
    assert [pair[1] for pair in answer.pairs] == _approx(expected)
    assert max(pair[0][1] for pair in answer.pairs) <= 110
    assert pose.seen[0] is photograph and pose.seen[1] is render


@pytest.mark.spec("placement-proposal:pairs:the-arm-nearest-the-tattoo-is-proposed")
def test_propose_pipeline_the_right_arm_is_proposed_when_the_points_lie_along_it() -> (
    None
):
    photograph, render = _images()
    pose, segmenter = FakePoseFinder(_pose(), _pose()), FakeSegmenter(_band)

    answer = propose(photograph, render, [(100.0, 175.0)], pose, segmenter)

    assert answer.arm == "right"
    assert min(pair[0][1] for pair in answer.pairs) >= 170
    assert [pair[0] for pair in answer.pairs[-3:]] == _approx(list(RIGHT.values()))


@pytest.mark.spec_exempt("structural: an image is embedded once, a bone prompted once")
def test_propose_pipeline_each_image_is_embedded_once_and_each_bone_prompted_once() -> (
    None
):
    photograph, render = _images()
    segmenter = FakeSegmenter(_band)

    propose(
        photograph,
        render,
        [(100.0, 105.0)],
        FakePoseFinder(_pose(), _pose()),
        segmenter,
    )

    assert segmenter.embedded[0] is photograph and segmenter.embedded[1] is render
    assert len(segmenter.embedded) == 2
    assert [number for number, _ in segmenter.prompts] == [0, 1, 0, 1]
    upper, _, forearm, _ = (prompt for _, prompt in segmenter.prompts)
    along = [(50 + 100 * f, 100.0) for f in PROMPTS]
    assert upper[0] == _approx(along)
    assert upper[1] == _approx([(200.0, 100.0), TORSO])
    assert forearm[0] == _approx([(150 + 100 * f, 100.0) for f in PROMPTS])
    assert forearm[1] == _approx([(100.0, 100.0), TORSO])


@pytest.mark.spec(
    "placement-proposal:pairs:a-keypoint-under-the-cut-proposes-nothing-for-its-bone"
)
def test_propose_pipeline_a_wrist_under_the_cut_drops_the_forearm_and_its_joint() -> (
    None
):
    photograph, render = _images()
    segmenter = FakeSegmenter(_band)

    answer = propose(
        photograph,
        render,
        [(100.0, 105.0)],
        FakePoseFinder(_pose(k9=0.23), _pose()),
        segmenter,
    )

    expected = [*_edges(50, 150, 100), LEFT[5], LEFT[7]]
    assert [pair[0] for pair in answer.pairs] == _approx(expected)
    assert [number for number, _ in segmenter.prompts] == [0, 1]
    assert segmenter.prompts[0][1][1] == _approx([TORSO])


@pytest.mark.spec(
    "placement-proposal:pairs:no-person-or-no-usable-bone-proposes-nothing"
)
def test_propose_pipeline_no_person_in_either_image_proposes_nothing() -> None:
    photograph, render = _images()
    for poses in ((_pose(), None), (None, _pose()), (None, None)):
        segmenter = FakeSegmenter(_band)

        answer = propose(
            photograph, render, [(100.0, 105.0)], FakePoseFinder(*poses), segmenter
        )

        assert answer == NOTHING
        assert segmenter.embedded == []


@pytest.mark.spec(
    "placement-proposal:pairs:no-person-or-no-usable-bone-proposes-nothing"
)
def test_propose_pipeline_no_usable_bone_proposes_nothing_and_embeds_nothing() -> None:
    photograph, render = _images()
    scores = {f"k{index}": 0.1 for index in (5, 6, 7, 8, 9, 10)}
    segmenter = FakeSegmenter(_band)

    answer = propose(
        photograph,
        render,
        [(100.0, 105.0)],
        FakePoseFinder(_pose(**scores), _pose()),
        segmenter,
    )

    assert answer == NOTHING
    assert segmenter.embedded == []


@pytest.mark.spec_exempt("structural: a mask with no edge leaves the joints alone")
def test_propose_pipeline_masks_with_no_edge_leave_the_joints() -> None:
    photograph, render = _images()

    answer = propose(
        photograph,
        render,
        [(100.0, 105.0)],
        FakePoseFinder(_pose(), _pose()),
        FakeSegmenter(_empty),
    )

    assert answer.arm == "left"
    assert [pair[0] for pair in answer.pairs] == _approx(list(LEFT.values()))


@pytest.mark.spec_exempt("structural: a render's dark line is read from its luminance")
def test_propose_pipeline_the_renders_luminance_stops_its_edge() -> None:
    photograph, render = _images()
    ImageDraw.Draw(render).line([(0, 107), (SIZE[0] - 1, 107)], fill=(0, 0, 0))

    answer = propose(
        photograph,
        render,
        [(100.0, 105.0)],
        FakePoseFinder(_pose(), _pose()),
        FakeSegmenter(_band),
    )

    seen, drawn = answer.pairs[0]
    assert seen[1] == pytest.approx(100 + HALF)
    assert drawn[1] == pytest.approx(106)


@pytest.mark.spec_exempt("structural: a proposer is the two models and `propose`")
def test_propose_pipeline_a_proposer_answers_as_propose_does() -> None:
    photograph, render = _images()
    points = [(100.0, 105.0)]

    through = Proposer(FakePoseFinder(_pose(), _pose()), FakeSegmenter(_band))
    direct = propose(
        photograph,
        render,
        points,
        FakePoseFinder(_pose(), _pose()),
        FakeSegmenter(_band),
    )

    assert through.propose(photograph, render, points) == direct


# --- the wiring seam ---------------------------------------------------------------


@pytest.fixture(autouse=True)
def _unopened() -> Iterator[None]:
    """Forget the models a test opened, so no test sees another's."""
    proposer_for.cache_clear()
    yield
    proposer_for.cache_clear()


def _opening(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace the two openers with fakes, and return the names opened, in order."""
    opened: list[str] = []

    def pose() -> FakePoseFinder:
        opened.append("pose")
        return FakePoseFinder()

    def segmenter() -> FakeSegmenter:
        opened.append("segmenter")
        return FakeSegmenter(_band)

    monkeypatch.setattr(wiring, "open_pose", pose)
    monkeypatch.setattr(wiring, "open_segmenter", segmenter)
    monkeypatch.delenv("ISEKAI_WIRING", raising=False)
    return opened


@pytest.mark.spec("placement-proposal:models:the-sessions-are-opened-once")
def test_propose_wiring_the_models_open_once_for_two_proposals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened = _opening(monkeypatch)
    wired = wiring_from(runs=tmp_path / "runs")

    assert wired.proposer is proposer_for
    assert opened == []
    first = proposer_of(wired)
    second = proposer_of(replace(wired, runs_root=tmp_path / "other"))

    assert first is second
    assert opened == ["pose", "segmenter"]


@pytest.mark.spec_exempt("structural: a wiring built by hand proposes nothing")
def test_propose_wiring_a_wiring_with_none_refuses_saying_so(
    vocabulary: Vocabulary,
) -> None:
    bare = Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=lambda: vocabulary,
        field_map=lambda _: FIELD_MAP,
        volume=NO_GPUNIT,
    )

    assert bare.proposer is None
    with pytest.raises(Refusal, match="no proposer"):
        proposer_of(bare)


@pytest.mark.spec("placement-proposal:pairs:a-missing-model-refuses-naming-the-fetch")
def test_propose_wiring_a_missing_model_refuses_naming_the_fetch_and_is_not_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    asked: list[str] = []

    def absent() -> object:
        asked.append("pose")
        return pose_boundary.open_pose(tmp_path / "models")

    monkeypatch.setattr(wiring, "open_pose", absent)
    monkeypatch.delenv("ISEKAI_WIRING", raising=False)
    wired = wiring_from(runs=tmp_path / "runs")

    for _ in range(2):
        with pytest.raises(Refusal) as refused:
            proposer_of(wired)
        assert PLACEMENT_REMEDY in str(refused.value)

    assert asked == ["pose", "pose"]

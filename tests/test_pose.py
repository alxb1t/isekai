"""The pose boundary: the detector's and the estimator's reading, and their opening.

The sessions are a recording runtime's, so the suite needs no model file. One check
reads the real models and skips only under `ISEKAI_PLACEMENT=absent`.
"""

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image

from isekai.boundary import pose, unpack
from isekai.boundary.pose import (
    DETECTOR_DEST,
    ESTIMATOR_DEST,
    OnnxPoseFinder,
    Pose,
    crop_for,
    fit,
    open_pose,
    person_box,
    read_keypoints,
    verified_paths,
)
from isekai.boundary.provision import DEFAULT_MODELS_DIR, DigestMismatch
from isekai.boundary.unpack import PLACEMENT_REMEDY
from isekai.foundation.refusal import Refusal
from tests.conftest import require_placement

DETECTOR_BYTES = b"the detector's bytes"
ESTIMATOR_BYTES = b"the estimator's bytes"

PIN = "https://huggingface.co/yzd-v/DWPose/resolve/" + "a" * 40 + "/"


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _provisioned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write both files and a manifest declaring them; return the models directory."""
    models = tmp_path / "models"
    (models / "dwpose").mkdir(parents=True)
    (models / DETECTOR_DEST).write_bytes(DETECTOR_BYTES)
    (models / ESTIMATOR_DEST).write_bytes(ESTIMATOR_BYTES)
    manifest = tmp_path / "placement.json"
    manifest.write_text(
        json.dumps(
            {
                "pinned": "2026-11-11",
                "publishers": ["yzd-v"],
                "entries": [
                    {
                        "dest": dest,
                        "sha256": _digest(body),
                        "bytes": len(body),
                        "sources": [PIN + dest.rsplit("/", 1)[1]],
                    }
                    for dest, body in (
                        (DETECTOR_DEST, DETECTOR_BYTES),
                        (ESTIMATOR_DEST, ESTIMATOR_BYTES),
                    )
                ],
            }
        )
    )
    monkeypatch.setattr(unpack, "PLACEMENT_MANIFEST_PATH", manifest)
    return models


@dataclass
class _Input:
    name: str


@dataclass
class _Session:
    """A session that answers what it was given and records what it was fed."""

    answers: Sequence[NDArray[np.float32]]
    name: str
    fed: list[Mapping[str, NDArray[np.float32]]] = field(default_factory=list)

    def get_inputs(self) -> list[_Input]:
        return [_Input(self.name)]

    def run(
        self, outputs: None, feed: Mapping[str, NDArray[np.float32]]
    ) -> Sequence[NDArray[np.float32]]:
        self.fed.append(feed)
        return self.answers


class _Runtime:
    """A runtime that records each session's path and providers, and fakes it."""

    def __init__(self, detector_rows: int = 8400) -> None:
        self.opened: list[tuple[str, list[str]]] = []
        self.sessions: dict[str, _Session] = {}
        self._rows = detector_rows

    def InferenceSession(  # noqa: N802 - the runtime's own name
        self, path: str, providers: Sequence[str]
    ) -> _Session:
        self.opened.append((path, list(providers)))
        if path.endswith("yolox_l.onnx"):
            session = _Session([_detector_rows(self._rows)], "images")
        else:
            session = _Session([_peak(576, 288, 0.9), _peak(768, 384, 0.6)], "input")
        self.sessions[Path(path).name] = session
        return session


def _detector_rows(count: int) -> NDArray[np.float32]:
    """Return the detector's answer: one strong person row at stride 8, cell (10, 5)."""
    rows = np.zeros((1, count, 85), dtype=np.float32)
    if count:
        row = 5 * 80 + 10
        rows[0, row, :4] = (0.5, 0.5, math.log(5), math.log(10))
        rows[0, row, 4] = 0.9
        rows[0, row, 5] = 0.8
    return rows


def _peak(bins: int, at: int, value: float) -> NDArray[np.float32]:
    """Return an estimator answer whose every keypoint peaks at bin `at`."""
    answer = np.zeros((1, 133, bins), dtype=np.float32)
    answer[0, :, at] = value
    return answer


# --- the files, verified before a session ------------------------------------------


@pytest.mark.spec(
    "placement-proposal:models:a-stale-pin-refuses-before-a-session-opens"
)
def test_pose_verified_returns_the_detectors_and_the_estimators_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = _provisioned(tmp_path, monkeypatch)

    assert verified_paths(models) == (
        models / DETECTOR_DEST,
        models / ESTIMATOR_DEST,
    )


@pytest.mark.spec("placement-proposal:models:an-absent-file-refuses-naming-the-fetch")
@pytest.mark.parametrize("gone", [DETECTOR_DEST, ESTIMATOR_DEST])
def test_pose_verified_an_absent_file_refuses_naming_the_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gone: str
) -> None:
    models = _provisioned(tmp_path, monkeypatch)
    (models / gone).unlink()

    with pytest.raises(Refusal) as refused:
        verified_paths(models)

    assert gone in str(refused.value)
    assert PLACEMENT_REMEDY in str(refused.value)


@pytest.mark.spec(
    "placement-proposal:models:a-stale-pin-refuses-before-a-session-opens"
)
def test_pose_verified_a_stale_pin_refuses_naming_both_digests_and_opens_no_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = _provisioned(tmp_path, monkeypatch)
    (models / ESTIMATOR_DEST).write_bytes(b"other bytes")
    runtime = _Runtime()

    with pytest.raises(DigestMismatch) as refused:
        open_pose(models, runtime)

    message = str(refused.value)
    assert str(models / ESTIMATOR_DEST) in message
    assert _digest(ESTIMATOR_BYTES) in message
    assert _digest(b"other bytes") in message
    assert runtime.opened == []


# --- the detector ------------------------------------------------------------------


@pytest.mark.spec(
    "placement-proposal:pose:the-detector-sees-the-image-fitted-and-padded"
)
def test_pose_box_fits_a_wide_image_in_the_corner_and_pads_the_rest() -> None:
    image = Image.new("RGB", (200, 100), (200, 100, 50))

    array, ratio = fit(image, 64)

    assert array.shape == (1, 3, 64, 64)
    assert ratio == pytest.approx(0.32)
    assert array[0, :, :32, :].min(axis=(1, 2)).tolist() == [200.0, 100.0, 50.0]
    assert array[0, :, :32, :].max(axis=(1, 2)).tolist() == [200.0, 100.0, 50.0]
    assert (array[0, :, 32:, :] == 114.0).all()


@pytest.mark.spec(
    "placement-proposal:pose:the-detector-sees-the-image-fitted-and-padded"
)
def test_pose_box_a_tall_image_is_padded_on_the_right() -> None:
    array, _ = fit(Image.new("RGB", (50, 100), (10, 20, 30)), 64)

    assert (array[0, :, :, 32:] == 114.0).all()
    assert (array[0, 0, :, :32] == 10.0).all()


@pytest.mark.spec("placement-proposal:pose:the-highest-scoring-person-is-the-one")
def test_pose_box_the_higher_row_is_the_person_in_the_images_pixels() -> None:
    rows = _detector_rows(8400)[0]
    # A weaker row on stride 32, cell (3, 2): the strides' blocks hold 6400, 1600, 400.
    weaker = 6400 + 1600 + 2 * 20 + 3
    rows[weaker, :4] = (0.5, 0.5, math.log(2), math.log(2))
    rows[weaker, 4] = 0.5
    rows[weaker, 5] = 0.5

    assert person_box(rows, 0.5) == pytest.approx((128.0, 8.0, 208.0, 168.0))


@pytest.mark.spec("placement-proposal:pose:the-highest-scoring-person-is-the-one")
def test_pose_box_a_higher_row_on_a_coarser_stride_wins() -> None:
    rows = _detector_rows(8400)[0]
    stronger = 6400 + 1600 + 2 * 20 + 3
    rows[stronger, :4] = (0.5, 0.5, math.log(2), math.log(2))
    rows[stronger, 4] = 0.99
    rows[stronger, 5] = 0.99

    # centre (3.5, 2.5) * 32 = (112, 80), size 64 by 64, scale 1.
    assert person_box(rows, 1.0) == pytest.approx((80.0, 48.0, 144.0, 112.0))


@pytest.mark.spec("placement-proposal:pose:the-highest-scoring-person-is-the-one")
def test_pose_box_no_row_is_no_person() -> None:
    assert person_box(np.zeros((0, 85), dtype=np.float32), 1.0) is None


# --- the estimator -----------------------------------------------------------------


@pytest.mark.spec(
    "placement-proposal:pose:the-estimator-reads-a-crop-grown-by-a-quarter"
)
def test_pose_keypoints_the_crop_is_the_box_grown_by_a_quarter() -> None:
    assert crop_for((100, 100, 200, 300)) == pytest.approx((56.25, 75.0, 243.75, 325.0))


@pytest.mark.spec(
    "placement-proposal:pose:the-estimator-reads-a-crop-grown-by-a-quarter"
)
def test_pose_keypoints_a_wide_box_grows_in_height_to_the_aspect() -> None:
    left, top, right, bottom = crop_for((0, 0, 400, 100))

    assert (right - left) / (bottom - top) == pytest.approx(288 / 384)
    assert (right - left) == pytest.approx(500.0)
    assert (left + right) / 2 == pytest.approx(200.0)
    assert (top + bottom) / 2 == pytest.approx(50.0)


@pytest.mark.spec(
    "placement-proposal:pose:a-keypoint-is-the-highest-value-on-each-axis-mapped-back"
)
def test_pose_keypoints_are_the_peaks_mapped_back_and_scored_by_the_lower() -> None:
    across = _peak(576, 288, 0.9)[0]
    down = _peak(768, 384, 0.6)[0]
    across[3, 288], across[3, 100] = 0.0, 0.7
    down[3, 384], down[3, 60] = 0.0, 0.8

    points, scores = read_keypoints(across, down, (100.0, 200.0, 388.0, 584.0))

    assert len(points) == len(scores) == 17
    assert points[0] == pytest.approx((244.0, 392.0))
    assert scores[0] == pytest.approx(0.6)
    # bins 100 and 60, over the split ratio of 2, at the crop's scale of 1.
    assert points[3] == pytest.approx((150.0, 230.0))
    assert scores[3] == pytest.approx(0.7)


# --- the finder --------------------------------------------------------------------


def _finder(runtime: _Runtime, tmp_path: Path) -> OnnxPoseFinder:
    return OnnxPoseFinder(tmp_path / "yolox_l.onnx", tmp_path / "dw.onnx", runtime)


@pytest.mark.spec("placement-proposal:pose:the-highest-scoring-person-is-the-one")
def test_pose_find_returns_the_pose_from_the_detectors_box_and_the_estimators_peaks(
    tmp_path: Path,
) -> None:
    runtime = _Runtime()

    found = _finder(runtime, tmp_path).find(Image.new("RGB", (1280, 640), "gray"))

    assert isinstance(found, Pose)
    # the image is 1280 by 640, fitted at 0.5.
    assert found.box == pytest.approx((128.0, 8.0, 208.0, 168.0))
    assert len(found.points) == len(found.scores) == 17
    assert found.scores[0] == pytest.approx(0.6)
    detector = runtime.sessions["yolox_l.onnx"]
    assert detector.fed[0]["images"].shape == (1, 3, 640, 640)
    estimator = runtime.sessions["dw.onnx"]
    assert estimator.fed[0]["input"].shape == (1, 3, 384, 288)


@pytest.mark.spec("placement-proposal:pose:the-highest-scoring-person-is-the-one")
def test_pose_find_no_row_is_none_and_the_estimator_is_not_run(tmp_path: Path) -> None:
    runtime = _Runtime(detector_rows=0)

    assert _finder(runtime, tmp_path).find(Image.new("RGB", (64, 64))) is None
    assert runtime.sessions["dw.onnx"].fed == []


@pytest.mark.spec("placement-proposal:models:the-sessions-use-the-cpu-provider-alone")
def test_pose_cpu_each_session_is_made_with_the_cpu_provider_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = _provisioned(tmp_path, monkeypatch)
    runtime = _Runtime()

    open_pose(models, runtime)

    assert runtime.opened == [
        (str(models / DETECTOR_DEST), ["CPUExecutionProvider"]),
        (str(models / ESTIMATOR_DEST), ["CPUExecutionProvider"]),
    ]


# --- the real models ---------------------------------------------------------------


@pytest.mark.spec_exempt(
    "structural: reads the provisioned models, skipped where absent"
)
def test_pose_real_reads_a_synthetic_image_into_finite_points_of_one_length() -> None:
    require_placement(DEFAULT_MODELS_DIR / DETECTOR_DEST)
    require_placement(DEFAULT_MODELS_DIR / ESTIMATOR_DEST)
    pixels = np.add.outer(np.arange(480), np.arange(320)) % 256
    image = Image.fromarray(np.stack([pixels] * 3, axis=2).astype(np.uint8))

    found = open_pose().find(image)

    assert found is not None
    assert len(found.points) == len(found.scores) == pose.BODY
    assert all(math.isfinite(v) for point in found.points for v in point)
    assert all(math.isfinite(score) for score in found.scores)

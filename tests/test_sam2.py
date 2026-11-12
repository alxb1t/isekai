"""The segmenter boundary: the preparation, the prompts, the choice, the opening.

The sessions are a recording runtime's, so the suite needs no model file. One check
reads the real models and skips only under `ISEKAI_PLACEMENT=absent`.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image

from isekai.boundary import sam2, unpack
from isekai.boundary.provision import DEFAULT_MODELS_DIR, DigestMismatch
from isekai.boundary.sam2 import (
    DECODER_DEST,
    ENCODER_DEST,
    OnnxSegmenter,
    open_segmenter,
    prepare,
)
from isekai.boundary.unpack import PLACEMENT_REMEDY
from isekai.foundation.refusal import Refusal
from tests.conftest import require_placement

ENCODER_BYTES = b"the encoder's bytes"
DECODER_BYTES = b"the decoder's bytes"

ARCHIVE = "https://huggingface.co/vietanhdev/x/resolve/" + "b" * 40 + "/sam.zip"

DECODER_INPUTS = (
    "image_embed",
    "high_res_feats_0",
    "high_res_feats_1",
    "point_coords",
    "point_labels",
    "mask_input",
    "has_mask_input",
)


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _provisioned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write both members and a manifest declaring them; return the models directory."""
    models = tmp_path / "models"
    (models / "sam2").mkdir(parents=True)
    (models / ENCODER_DEST).write_bytes(ENCODER_BYTES)
    (models / DECODER_DEST).write_bytes(DECODER_BYTES)
    manifest = tmp_path / "placement.json"
    manifest.write_text(
        json.dumps(
            {
                "pinned": "2026-11-11",
                "publishers": ["vietanhdev"],
                "entries": [
                    {
                        "dest": "sam2/sam.zip",
                        "sha256": "c" * 64,
                        "bytes": 1,
                        "sources": [ARCHIVE],
                        "unpack": [
                            {
                                "member": f"sam.{dest.rsplit('/', 1)[1]}",
                                "dest": dest,
                                "sha256": _digest(body),
                                "bytes": len(body),
                            }
                            for dest, body in (
                                (ENCODER_DEST, ENCODER_BYTES),
                                (DECODER_DEST, DECODER_BYTES),
                            )
                        ],
                    }
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
    """A session that answers each output by name and records what it was fed."""

    inputs: Sequence[str]
    answers: Mapping[str, NDArray[np.float32]]
    fed: list[Mapping[str, NDArray[np.float32]]] = field(default_factory=list)
    asked: list[Sequence[str] | None] = field(default_factory=list)

    def get_inputs(self) -> list[_Input]:
        return [_Input(name) for name in self.inputs]

    def run(
        self, outputs: Sequence[str] | None, feed: Mapping[str, NDArray[np.float32]]
    ) -> Sequence[NDArray[np.float32]]:
        assert outputs is not None
        self.fed.append(feed)
        self.asked.append(outputs)
        return [self.answers[name] for name in outputs]


def _features() -> dict[str, NDArray[np.float32]]:
    return {
        "image_embed": np.full((1, 256, 64, 64), 1.0, dtype=np.float32),
        "high_res_feats_0": np.full((1, 32, 256, 256), 2.0, dtype=np.float32),
        "high_res_feats_1": np.full((1, 64, 128, 128), 3.0, dtype=np.float32),
    }


def _masks(
    candidates: Sequence[NDArray[np.float32]], scores: Sequence[float]
) -> dict[str, NDArray[np.float32]]:
    """Return the decoder's answer: candidates at 256 by 256 and their scores."""
    return {
        "masks": np.stack(candidates)[None].astype(np.float32),
        "iou_predictions": np.array([scores], dtype=np.float32),
    }


def _flat(value: float) -> NDArray[np.float32]:
    return np.full((256, 256), value, dtype=np.float32)


class _Runtime:
    """A runtime that records each session's path and providers, and fakes it."""

    def __init__(
        self,
        decoder_inputs: Sequence[str] = DECODER_INPUTS,
        decoder_answers: Mapping[str, NDArray[np.float32]] | None = None,
    ) -> None:
        self.opened: list[tuple[str, list[str]]] = []
        self.sessions: dict[str, _Session] = {}
        self._decoder_inputs = decoder_inputs
        self._decoder_answers = decoder_answers or _masks(
            [_flat(-1.0), _flat(1.0), _flat(-1.0)], [0.1, 0.9, 0.2]
        )

    def InferenceSession(  # noqa: N802 - the runtime's own name
        self, path: str, providers: Sequence[str]
    ) -> _Session:
        self.opened.append((path, list(providers)))
        if path.endswith("encoder.onnx"):
            session = _Session(["image"], _features())
        else:
            session = _Session(self._decoder_inputs, self._decoder_answers)
        self.sessions[Path(path).name] = session
        return session


def _segmenter(runtime: _Runtime, tmp_path: Path) -> OnnxSegmenter:
    return OnnxSegmenter(tmp_path / "encoder.onnx", tmp_path / "decoder.onnx", runtime)


# --- the preparation ---------------------------------------------------------------


@pytest.mark.spec(
    "placement-proposal:segment:the-image-is-scaled-and-normalised-for-the-encoder"
)
def test_sam_prepare_is_the_square_three_channels_first_and_normalised() -> None:
    array = prepare(Image.new("RGB", (40, 20), (255, 0, 51)))

    assert array.shape == (1, 3, 1024, 1024)
    assert array.dtype == np.float32
    expected = [(1.0 - 0.485) / 0.229, (0.0 - 0.456) / 0.224, (0.2 - 0.406) / 0.225]
    assert array[0].min(axis=(1, 2)) == pytest.approx(expected, abs=1e-4)
    assert array[0].max(axis=(1, 2)) == pytest.approx(expected, abs=1e-4)


@pytest.mark.spec(
    "placement-proposal:segment:the-image-is-scaled-and-normalised-for-the-encoder"
)
def test_sam_prepare_keeps_the_images_left_and_right_in_the_squares() -> None:
    wide = Image.new("RGB", (30, 10), (0, 0, 0))
    wide.paste((255, 255, 255), (15, 0, 30, 10))

    array = prepare(wide)

    assert array[0, 0, 512, 10] < array[0, 0, 512, 1000]


@pytest.mark.spec(
    "placement-proposal:segment:the-image-is-scaled-and-normalised-for-the-encoder"
)
def test_sam_prepare_reads_a_grey_image_as_three_channels() -> None:
    assert prepare(Image.new("L", (8, 8), 255)).shape == (1, 3, 1024, 1024)


# --- the embedding -----------------------------------------------------------------


@pytest.mark.spec(
    "placement-proposal:segment:an-image-is-embedded-once-for-all-its-bones"
)
def test_sam_embed_runs_the_encoder_once_and_keeps_the_features_and_the_size(
    tmp_path: Path,
) -> None:
    runtime = _Runtime()

    embedding = _segmenter(runtime, tmp_path).embed(Image.new("RGB", (300, 200)))

    encoder = runtime.sessions["encoder.onnx"]
    assert len(encoder.fed) == 1
    assert encoder.fed[0]["image"].shape == (1, 3, 1024, 1024)
    assert set(encoder.asked[0] or []) == {
        "image_embed",
        "high_res_feats_0",
        "high_res_feats_1",
    }
    assert embedding.size == (300, 200)
    assert set(embedding.features) == {
        "image_embed",
        "high_res_feats_0",
        "high_res_feats_1",
    }


@pytest.mark.spec(
    "placement-proposal:segment:an-image-is-embedded-once-for-all-its-bones"
)
def test_sam_embed_two_bones_cost_one_encoder_run_and_two_decoder_runs(
    tmp_path: Path,
) -> None:
    runtime = _Runtime()
    embedding = _segmenter(runtime, tmp_path).embed(Image.new("RGB", (300, 200)))

    embedding.mask([(10.0, 10.0)], [(200.0, 100.0)])
    embedding.mask([(20.0, 20.0)], [(250.0, 150.0)])

    assert len(runtime.sessions["encoder.onnx"].fed) == 1
    assert len(runtime.sessions["decoder.onnx"].fed) == 2


@pytest.mark.spec(
    "placement-proposal:segment:an-image-is-embedded-once-for-all-its-bones"
)
def test_sam_embed_gives_the_decoder_the_encoders_features(tmp_path: Path) -> None:
    runtime = _Runtime()
    embedding = _segmenter(runtime, tmp_path).embed(Image.new("RGB", (64, 64)))

    embedding.mask([(1.0, 1.0)], [])

    fed = runtime.sessions["decoder.onnx"].fed[0]
    assert fed["image_embed"] is embedding.features["image_embed"]
    assert fed["high_res_feats_0"] is embedding.features["high_res_feats_0"]
    assert fed["high_res_feats_1"] is embedding.features["high_res_feats_1"]


# --- the prompt --------------------------------------------------------------------


@pytest.mark.spec(
    "placement-proposal:segment:a-mask-is-prompted-by-positive-and-negative-points"
)
def test_sam_prompt_scales_the_points_to_the_input_and_labels_them(
    tmp_path: Path,
) -> None:
    runtime = _Runtime()
    embedding = _segmenter(runtime, tmp_path).embed(Image.new("RGB", (512, 256)))

    embedding.mask(
        [(0.0, 0.0), (256.0, 128.0), (512.0, 256.0)], [(128.0, 64.0), (384.0, 192.0)]
    )

    fed = runtime.sessions["decoder.onnx"].fed[0]
    assert fed["point_coords"].shape == (1, 5, 2)
    assert fed["point_coords"][0].tolist() == [
        [0.0, 0.0],
        [512.0, 512.0],
        [1024.0, 1024.0],
        [256.0, 256.0],
        [768.0, 768.0],
    ]
    assert fed["point_labels"].shape == (1, 5)
    assert fed["point_labels"][0].tolist() == [1.0, 1.0, 1.0, 0.0, 0.0]
    assert fed["point_coords"].dtype == fed["point_labels"].dtype == np.float32


@pytest.mark.spec(
    "placement-proposal:segment:a-mask-is-prompted-by-positive-and-negative-points"
)
def test_sam_prompt_gives_no_earlier_mask(tmp_path: Path) -> None:
    runtime = _Runtime()
    embedding = _segmenter(runtime, tmp_path).embed(Image.new("RGB", (64, 64)))

    embedding.mask([(1.0, 1.0)], [])

    fed = runtime.sessions["decoder.onnx"].fed[0]
    assert fed["mask_input"].shape == (1, 1, 256, 256)
    assert not fed["mask_input"].any()
    assert fed["has_mask_input"].tolist() == [0.0]


# --- the inputs the decoder declares -----------------------------------------------


@pytest.mark.spec(
    "placement-proposal:segment:a-declared-input-with-no-value-is-refused"
)
def test_sam_inputs_one_the_table_lacks_is_refused_by_name(tmp_path: Path) -> None:
    runtime = _Runtime(decoder_inputs=(*DECODER_INPUTS, "orig_im_size"))
    embedding = _segmenter(runtime, tmp_path).embed(Image.new("RGB", (64, 64)))

    with pytest.raises(Refusal) as refused:
        embedding.mask([(1.0, 1.0)], [])

    assert "orig_im_size" in str(refused.value)
    assert runtime.sessions["decoder.onnx"].fed == []


@pytest.mark.spec(
    "placement-proposal:segment:a-declared-input-with-no-value-is-refused"
)
def test_sam_inputs_the_decoder_is_given_only_what_it_declares(tmp_path: Path) -> None:
    runtime = _Runtime(decoder_inputs=("image_embed", "point_coords", "point_labels"))
    embedding = _segmenter(runtime, tmp_path).embed(Image.new("RGB", (64, 64)))

    embedding.mask([(1.0, 1.0)], [])

    assert set(runtime.sessions["decoder.onnx"].fed[0]) == {
        "image_embed",
        "point_coords",
        "point_labels",
    }


# --- the choice --------------------------------------------------------------------


def _step() -> NDArray[np.float32]:
    """Return logits that are -1 left of column 128 and 7 from it."""
    logits = _flat(-1.0)
    logits[:, 128:] = 7.0
    return logits


@pytest.mark.spec("placement-proposal:segment:the-mask-is-the-candidate-scored-highest")
def test_sam_choice_the_mask_is_the_candidate_the_decoder_scores_highest(
    tmp_path: Path,
) -> None:
    answers = _masks([_flat(5.0), _step(), _flat(5.0)], [0.2, 0.8, 0.5])
    embedding = _segmenter(_Runtime(decoder_answers=answers), tmp_path).embed(
        Image.new("RGB", (256, 256))
    )

    mask = embedding.mask([(1.0, 1.0)], [])

    assert mask.dtype == np.bool_
    assert not mask[:, :128].any()
    assert mask[:, 128:].all()


@pytest.mark.spec("placement-proposal:segment:the-mask-is-the-candidate-scored-highest")
def test_sam_choice_the_mask_has_the_images_size(tmp_path: Path) -> None:
    embedding = _segmenter(_Runtime(), tmp_path).embed(Image.new("RGB", (300, 200)))

    assert embedding.mask([(1.0, 1.0)], []).shape == (200, 300)


@pytest.mark.spec("placement-proposal:segment:the-mask-is-the-candidate-scored-highest")
def test_sam_choice_the_logits_are_resized_and_then_taken_above_zero(
    tmp_path: Path,
) -> None:
    answers = _masks([_flat(-1.0), _step(), _flat(-1.0)], [0.0, 1.0, 0.0])
    embedding = _segmenter(_Runtime(decoder_answers=answers), tmp_path).embed(
        Image.new("RGB", (512, 512))
    )

    mask = embedding.mask([(1.0, 1.0)], [])

    # Bilinear logits cross 0 a quarter of the way from column 127 to column 128, which
    # is output column 255 of 512; a resized threshold would put the edge at 256.
    assert not mask[:, 254].any()
    assert mask[:, 255].all()


# --- the opening -------------------------------------------------------------------


@pytest.mark.spec("placement-proposal:models:the-sessions-use-the-cpu-provider-alone")
def test_sam_open_each_session_is_made_with_the_cpu_provider_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = _provisioned(tmp_path, monkeypatch)
    runtime = _Runtime()

    open_segmenter(models, runtime)

    assert runtime.opened == [
        (str(models / ENCODER_DEST), ["CPUExecutionProvider"]),
        (str(models / DECODER_DEST), ["CPUExecutionProvider"]),
    ]


@pytest.mark.spec("placement-proposal:models:an-absent-file-refuses-naming-the-fetch")
@pytest.mark.parametrize("gone", [ENCODER_DEST, DECODER_DEST])
def test_sam_open_an_absent_file_refuses_naming_the_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gone: str
) -> None:
    models = _provisioned(tmp_path, monkeypatch)
    (models / gone).unlink()
    runtime = _Runtime()

    with pytest.raises(Refusal) as refused:
        open_segmenter(models, runtime)

    assert gone in str(refused.value)
    assert PLACEMENT_REMEDY in str(refused.value)
    assert runtime.opened == []


@pytest.mark.spec(
    "placement-proposal:models:a-stale-pin-refuses-before-a-session-opens"
)
def test_sam_open_a_stale_pin_refuses_naming_both_digests_and_opens_no_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = _provisioned(tmp_path, monkeypatch)
    (models / DECODER_DEST).write_bytes(b"other bytes")
    runtime = _Runtime()

    with pytest.raises(DigestMismatch) as refused:
        open_segmenter(models, runtime)

    message = str(refused.value)
    assert str(models / DECODER_DEST) in message
    assert _digest(DECODER_BYTES) in message
    assert _digest(b"other bytes") in message
    assert runtime.opened == []


# --- the real models ---------------------------------------------------------------


@pytest.mark.spec_exempt(
    "structural: reads the provisioned models, skipped where absent"
)
def test_sam_real_prompts_a_point_into_a_boolean_mask_of_the_images_size() -> None:
    require_placement(DEFAULT_MODELS_DIR / ENCODER_DEST)
    require_placement(DEFAULT_MODELS_DIR / DECODER_DEST)
    pixels = np.add.outer(np.arange(240), np.arange(320)) % 256
    image = Image.fromarray(np.stack([pixels] * 3, axis=2).astype(np.uint8))

    mask = sam2.open_segmenter().embed(image).mask([(160.0, 120.0)], [])

    assert mask.dtype == np.bool_
    assert mask.shape == (240, 320)

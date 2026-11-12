"""The placement manifest, read as the tracked file, and the helper checks over it use.

The manifest is committed, so these read it directly. The model files it names are
fetched by `make setup` and gitignored, so a check that reads one goes through
`require_placement`, which skips only under `ISEKAI_PLACEMENT=absent`.
"""

import re
from pathlib import Path

import pytest

from isekai.boundary.provision import DIGEST, Manifest, load_manifest
from isekai.boundary.unpack import (
    PLACEMENT_MANIFEST_PATH,
    PLACEMENT_REMEDY,
    ZipEntry,
    member_for,
)
from tests.conftest import require_placement

REVISION = re.compile(r"/resolve/[0-9a-f]{40}/")

DETECTOR = "dwpose/yolox_l.onnx"
ARCHIVE = "sam2/sam2.1_hiera_small_20260221.zip"
ENCODER = "sam2/encoder.onnx"
DECODER = "sam2/decoder.onnx"

# The render manifest's name for the detector the pod runs.
PODS_DETECTOR = "annotator_ckpts/yzd-v/DWPose/yolox_l.onnx"


def _placement() -> Manifest:
    return load_manifest(PLACEMENT_MANIFEST_PATH)


@pytest.mark.spec(
    "model-provisioning:placement:a-check-that-reads-the-models-skips-only-under-the-declaration"
)
def test_placement_require_returns_when_the_file_is_there(tmp_path: Path) -> None:
    present = tmp_path / "model.onnx"
    present.write_bytes(b"x")

    require_placement(present)


@pytest.mark.spec(
    "model-provisioning:placement:a-check-that-reads-the-models-skips-only-under-the-declaration"
)
def test_placement_require_skips_an_absent_file_under_the_declaration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ISEKAI_PLACEMENT", "absent")

    with pytest.raises(pytest.skip.Exception):
        require_placement(tmp_path / "gone.onnx")


@pytest.mark.spec(
    "model-provisioning:placement:a-check-that-reads-the-models-skips-only-under-the-declaration"
)
@pytest.mark.parametrize("declared", [None, "", "present", "ABSENT"])
def test_placement_require_fails_an_absent_file_naming_the_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, declared: str | None
) -> None:
    if declared is None:
        monkeypatch.delenv("ISEKAI_PLACEMENT", raising=False)
    else:
        monkeypatch.setenv("ISEKAI_PLACEMENT", declared)

    with pytest.raises(pytest.fail.Exception) as failed:
        require_placement(tmp_path / "gone.onnx")

    assert PLACEMENT_REMEDY in str(failed.value)


@pytest.mark.spec(
    "model-provisioning:placement:every-source-is-pinned-and-every-entry-digested"
)
def test_placement_pins_every_source_revision_and_every_digest() -> None:
    manifest = _placement()
    assert manifest["pinned"]
    assert [entry["dest"] for entry in manifest["entries"]] == [
        DETECTOR,
        "dwpose/dw-ll_ucoco_384.onnx",
        ARCHIVE,
    ]
    for entry in manifest["entries"]:
        assert entry["sources"], entry["dest"]
        for source in entry["sources"]:
            assert REVISION.search(source), f"{entry['dest']}: {source}"
        assert DIGEST.match(entry["sha256"]), entry["dest"]
        assert entry["bytes"] > 0, entry["dest"]
    archive = _zip_entry(_placement())
    for member in archive["unpack"]:
        assert member["member"], member["dest"]
        assert DIGEST.match(member["sha256"]), member["dest"]
        assert member["bytes"] > 0, member["dest"]


@pytest.mark.spec(
    "model-provisioning:placement:every-source-is-pinned-and-every-entry-digested"
)
def test_placement_pins_twin_a_branch_source_fails_the_revision_check() -> None:
    assert not REVISION.search(
        "https://huggingface.co/yzd-v/DWPose/resolve/main/yolox_l.onnx"
    )


@pytest.mark.spec("model-provisioning:placement:the-detector-is-the-pods-pin")
def test_placement_detector_equals_the_pods_pin() -> None:
    (pods,) = [
        entry for entry in load_manifest()["entries"] if entry["dest"] == PODS_DETECTOR
    ]
    (ours,) = [entry for entry in _placement()["entries"] if entry["dest"] == DETECTOR]

    assert ours["sha256"] == pods["sha256"]
    assert ours["bytes"] == pods["bytes"]
    assert ours["sources"][0] == pods["sources"][0]


@pytest.mark.spec("model-provisioning:placement:the-detector-is-the-pods-pin")
def test_placement_detector_twin_a_moved_digest_is_not_equal() -> None:
    (pods,) = [
        entry for entry in load_manifest()["entries"] if entry["dest"] == PODS_DETECTOR
    ]

    assert pods["sha256"] != "0" * 64


def _zip_entry(manifest: Manifest) -> ZipEntry:
    entry, _ = member_for(manifest, ENCODER)
    return entry


@pytest.mark.spec(
    "model-provisioning:placement:the-archive-declares-its-encoder-and-decoder"
)
def test_placement_members_land_the_encoder_and_decoder_inside_the_models_dir() -> None:
    entry = _zip_entry(_placement())

    assert entry["dest"] == ARCHIVE
    assert [member["dest"] for member in entry["unpack"]] == [ENCODER, DECODER]
    for member in entry["unpack"]:
        assert not Path(member["dest"]).is_absolute()
        assert ".." not in Path(member["dest"]).parts

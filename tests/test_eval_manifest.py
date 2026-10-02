import copy
import hashlib
import re
from pathlib import Path
from typing import Any, cast

import pytest

import evaluation.__main__ as entry_point
from evaluation import eval_models
from evaluation.eval_models import ENCODER, load_eval_manifest, shared_with_the_graph
from isekai.boundary.provision import (
    DigestMismatch,
    EscapingDestination,
    Manifest,
    UnknownArtifact,
    UnpinnedArtifact,
    entries_with_missing_keys,
    entries_without_a_digest,
    entry_for,
    load_manifest,
    mirror_entries_without_an_alternate,
    resolve,
    sources_on_a_mutable_ref,
)
from isekai.foundation.refusal import Refusal


@pytest.fixture
def eval_manifest() -> Manifest:
    """Return a private copy of the tracked eval manifest, free to be malformed.

    The tracked file itself, like every other manifest fixture here -- a
    byte-identical copy with no drift check is a second thing to keep in step.
    """
    return copy.deepcopy(load_eval_manifest())


def _land(models_dir: Path, entry: dict[str, Any], body: bytes) -> Path:
    """Write `body` at the entry's destination under `models_dir`, and return it."""
    path = models_dir / entry["dest"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


@pytest.mark.spec_exempt("structural: the eval manifest is data the other checks read")
def test_the_tracked_eval_manifest_parses_and_declares_entries(
    eval_manifest: Manifest,
) -> None:
    assert eval_manifest["entries"]
    assert eval_manifest["pinned"]
    assert eval_manifest["publishers"]


@pytest.mark.spec_exempt("structural: shape, not a scenario about pins or digests")
def test_every_eval_entry_declares_the_required_keys(eval_manifest: Manifest) -> None:
    assert entries_with_missing_keys(eval_manifest) == []


@pytest.mark.spec("evaluation:pinned-artifacts:unpinned-source-is-refused")
def test_no_source_in_the_eval_manifest_resolves_a_mutable_ref(
    eval_manifest: Manifest,
) -> None:
    assert sources_on_a_mutable_ref(eval_manifest) == []


@pytest.mark.spec("evaluation:pinned-artifacts:unpinned-source-is-refused")
def test_an_unpinned_entry_is_refused_rather_than_loaded(
    eval_manifest: Manifest, tmp_path: Path
) -> None:
    entry = cast(dict[str, Any], entry_for(eval_manifest, ENCODER))
    body = b"whatever the bytes are, the pin is what says they are the right ones"
    entry["sha256"] = hashlib.sha256(body).hexdigest()
    entry["sources"] = [
        "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx"
    ]
    _land(tmp_path, entry, body)

    # The digest on disk matches: the refusal is about the pin, not the bytes.
    with pytest.raises(UnpinnedArtifact) as refused:
        resolve(ENCODER, tmp_path, eval_manifest)
    assert "resolve/main" in str(refused.value)


@pytest.mark.spec_exempt(
    "structural: a digest's presence, not the mismatch the scenario describes"
)
def test_every_eval_entry_carries_a_digest(eval_manifest: Manifest) -> None:
    assert entries_without_a_digest(eval_manifest) == []


@pytest.mark.spec_exempt("structural: availability, the rule models.json is under")
def test_every_mirror_primary_in_the_eval_manifest_declares_an_alternate(
    eval_manifest: Manifest,
) -> None:
    assert mirror_entries_without_an_alternate(eval_manifest) == []


@pytest.mark.spec("evaluation:pinned-artifacts:digest-mismatch-is-refused")
def test_bytes_matching_the_pin_resolve_to_their_path(
    eval_manifest: Manifest, tmp_path: Path
) -> None:
    entry = cast(dict[str, Any], entry_for(eval_manifest, ENCODER))
    body = b"the encoder's bytes, as far as this test is concerned"
    entry["sha256"] = hashlib.sha256(body).hexdigest()
    expected = _land(tmp_path, entry, body)

    assert resolve(ENCODER, tmp_path, eval_manifest) == expected


@pytest.mark.spec("evaluation:pinned-artifacts:digest-mismatch-is-refused")
def test_a_digest_mismatch_refuses_naming_the_artifact_and_both_digests(
    eval_manifest: Manifest, tmp_path: Path
) -> None:
    entry = cast(dict[str, Any], entry_for(eval_manifest, ENCODER))
    landed = _land(tmp_path, entry, b"not the bytes the manifest pins")
    computed = hashlib.sha256(b"not the bytes the manifest pins").hexdigest()

    with pytest.raises(DigestMismatch) as refused:
        resolve(ENCODER, tmp_path, eval_manifest)

    message = str(refused.value)
    assert str(landed) in message
    assert entry["sha256"] in message
    assert computed in message


@pytest.mark.spec("evaluation:pinned-artifacts:digest-mismatch-is-refused")
def test_an_artifact_the_manifest_does_not_declare_is_refused(
    eval_manifest: Manifest, tmp_path: Path
) -> None:
    with pytest.raises(UnknownArtifact):
        resolve("opencv_face/a_model_nobody_pinned.onnx", tmp_path, eval_manifest)


# The two shapes `isekai.boundary.provision.resolve_dest` refuses, mirroring
# `tests/test_provision.py`'s: a relative destination that climbs out, and one
# that is absolute and would win the join outright.
ESCAPES = "../../etc/cron.d/payload"
ABSOLUTE = "/etc/cron.d/payload"


@pytest.mark.spec("evaluation:pinned-artifacts:escaping-destination-is-refused")
@pytest.mark.parametrize("dest", [ESCAPES, ABSOLUTE])
def test_a_destination_outside_the_models_root_is_refused_rather_than_loaded(
    eval_manifest: Manifest, tmp_path: Path, dest: str
) -> None:
    # The scorer's join goes through the provisioner's containment check, so the
    # rule has one enforcement site rather than two. Nothing is landed on disk:
    # the refusal must come before any byte is read, not from a missing file.
    entry = cast(dict[str, Any], entry_for(eval_manifest, ENCODER))
    entry["dest"] = dest

    with pytest.raises(EscapingDestination) as refused:
        resolve(dest, tmp_path, eval_manifest)
    assert dest in str(refused.value)


@pytest.mark.spec("evaluation:encoder:shares-no-pin-with-the-generator")
def test_a_destination_the_generator_also_pins_refuses_the_scoring_naming_it(
    eval_manifest: Manifest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    graph = load_manifest()
    borrowed = graph["entries"][0]
    eval_manifest["entries"].append(borrowed)
    monkeypatch.setattr(eval_models, "load_eval_manifest", lambda: eval_manifest)

    assert shared_with_the_graph(load_eval_manifest(), graph) == []
    assert shared_with_the_graph(eval_manifest, graph) == [borrowed["dest"]]
    with pytest.raises(Refusal, match=re.escape(borrowed["dest"])):
        entry_point._embedder(tmp_path)


@pytest.mark.spec("evaluation:encoder:shares-no-bytes-with-the-generator")
def test_the_generators_bytes_under_another_destination_refuse_the_scoring(
    eval_manifest: Manifest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    graph = load_manifest()
    renamed = {**graph["entries"][0], "dest": "opencv_face/renamed.onnx"}
    eval_manifest["entries"].append(cast(Any, renamed))
    monkeypatch.setattr(eval_models, "load_eval_manifest", lambda: eval_manifest)

    assert shared_with_the_graph(eval_manifest, graph) == [renamed["dest"]]
    with pytest.raises(Refusal, match=re.escape(renamed["dest"])):
        entry_point._embedder(tmp_path)

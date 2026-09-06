import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from isekai.eval_models import (
    RECOGNIZER,
    SHARED_WITH_THE_GRAPH,
    UnknownArtifact,
    UnpinnedArtifact,
    entry_for,
    load_eval_manifest,
    resolve,
    shared_entries_that_differ,
)
from isekai.provision import (
    DigestMismatch,
    Manifest,
    entries_with_missing_keys,
    entries_without_a_digest,
    mirror_entries_without_an_alternate,
    sources_on_a_mutable_ref,
)


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
    entry = cast(dict[str, Any], entry_for(eval_manifest, RECOGNIZER))
    body = b"whatever the bytes are, the pin is what says they are the right ones"
    entry["sha256"] = hashlib.sha256(body).hexdigest()
    entry["sources"] = [
        "https://huggingface.co/DIAMONIK7777/antelopev2/resolve/main/glintr100.onnx"
    ]
    _land(tmp_path, entry, body)

    # The digest on disk matches: the refusal is about the pin, not the bytes.
    with pytest.raises(UnpinnedArtifact) as refused:
        resolve(RECOGNIZER, tmp_path, eval_manifest)
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
    entry = cast(dict[str, Any], entry_for(eval_manifest, RECOGNIZER))
    body = b"the recognizer's bytes, as far as this test is concerned"
    entry["sha256"] = hashlib.sha256(body).hexdigest()
    expected = _land(tmp_path, entry, body)

    assert resolve(RECOGNIZER, tmp_path, eval_manifest) == expected


@pytest.mark.spec("evaluation:pinned-artifacts:digest-mismatch-is-refused")
def test_a_digest_mismatch_refuses_naming_the_artifact_and_both_digests(
    eval_manifest: Manifest, tmp_path: Path
) -> None:
    entry = cast(dict[str, Any], entry_for(eval_manifest, RECOGNIZER))
    landed = _land(tmp_path, entry, b"not the bytes the manifest pins")
    computed = hashlib.sha256(b"not the bytes the manifest pins").hexdigest()

    with pytest.raises(DigestMismatch) as refused:
        resolve(RECOGNIZER, tmp_path, eval_manifest)

    message = str(refused.value)
    assert str(landed) in message
    assert entry["sha256"] in message
    assert computed in message


@pytest.mark.spec("evaluation:pinned-artifacts:digest-mismatch-is-refused")
def test_an_artifact_the_manifest_does_not_declare_is_refused(
    eval_manifest: Manifest, tmp_path: Path
) -> None:
    with pytest.raises(UnknownArtifact):
        resolve("styleid/a_model_nobody_pinned.safetensors", tmp_path, eval_manifest)


@pytest.mark.spec("evaluation:pinned-artifacts:recognizer-matches-the-generators-pin")
def test_the_recognizer_is_the_pin_the_graphs_own_manifest_carries() -> None:
    assert shared_entries_that_differ() == []


@pytest.mark.spec("evaluation:pinned-artifacts:recognizer-matches-the-generators-pin")
def test_the_recognizer_is_one_of_the_shared_entries() -> None:
    assert RECOGNIZER in SHARED_WITH_THE_GRAPH


@pytest.mark.spec("evaluation:pinned-artifacts:recognizer-matches-the-generators-pin")
def test_a_recognizer_that_drifted_from_the_graphs_pin_is_reported(
    eval_manifest: Manifest,
) -> None:
    # A different build of ArcFace, pinned only in the scorer's manifest. Nothing
    # about the file's shape is wrong; only the two files no longer agree.
    entry = cast(dict[str, Any], entry_for(eval_manifest, RECOGNIZER))
    entry["sha256"] = "0" * 64

    assert shared_entries_that_differ(eval_manifest) == [RECOGNIZER]


@pytest.mark.spec("evaluation:pinned-artifacts:recognizer-matches-the-generators-pin")
def test_a_shared_entry_dropped_from_the_graphs_manifest_is_reported(
    eval_manifest: Manifest, tmp_path: Path
) -> None:
    graph: dict[str, Any] = json.loads(
        (Path(__file__).resolve().parent.parent / "scripts" / "models.json").read_text()
    )
    graph["entries"] = [
        entry for entry in graph["entries"] if entry["dest"] != RECOGNIZER
    ]
    thinned = tmp_path / "models.json"
    thinned.write_text(json.dumps(graph))

    assert shared_entries_that_differ(eval_manifest, thinned) == [RECOGNIZER]

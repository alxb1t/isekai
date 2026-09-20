"""The vocabulary's manifest, held to the same rules as the graph's and the scorer's.

Two entries, and one artifact split in two: `selected_tags.csv` is the output
layer of the `model.onnx` beside it, row N naming neuron N, so a pair at two
revisions mislabels every tag with nothing downstream able to notice. That is why
the revision the two share is asserted here rather than assumed (design.md D18,
D24). Both are pinned to an immutable revision; the CSV's digest is obtained by
fetching and hashing, because at roughly 300 KB it is not stored as a large file
and so publishes none, and the graph's is read from its LFS object id.

The manifest exists at all so that a fresh clone can fill a sheet: the CSV used to
arrive as a side effect of downloading a tagger this repository did not load
(design.md D9). It now loads it.
"""

import copy
import re
from pathlib import Path

import pytest

from isekai.boundary.provision import (
    DIGEST,
    MANIFEST_PATH,
    VOCABULARY_MANIFEST_PATH,
    Manifest,
    entries_with_missing_keys,
    entries_without_a_digest,
    load_manifest,
    mirror_entries_without_an_alternate,
    sources_on_a_mutable_ref,
)
from isekai.evaluation.eval_models import load_eval_manifest
from isekai.foundation.refusal import Refusal
from isekai.shared.vocabulary import load as load_vocabulary
from tests.fakes import FakeFetcher

VOCABULARY = "wd14/selected_tags.csv"
TAGGER = "wd14/model.onnx"

# The immutable revision both halves resolve, and the repository that publishes
# them. Written out rather than read back off the manifest, so the assertion is
# against a value a human pinned and not against whatever the file happens to say.
REVISION = "627aef95638667ddcaa3ac8ae625e88ea5b02f51"
REPOSITORY = "SmilingWolf/wd-swinv2-tagger-v3"

# The tracked note that sits beside the manifests. It is one record for every
# artifact this repository pins, rather than one per manifest: a licence is a
# property of the artifact, and three notes would be three places to forget.
LICENCES_PATH = Path(__file__).resolve().parent.parent / "scripts" / "eval_licences.md"

# The one command that provisions anything in this repository. The vocabulary is
# fetched by pointing it at the vocabulary's manifest rather than by a second
# driver that would have to be kept in step with this one.
DRIVER_PATH = Path(__file__).resolve().parent.parent / "scripts" / "download_models.sh"

# Extensions a model's weights arrive under. Exactly one entry here carries one,
# and which one is asserted: the graph the tag list is the output layer of. A
# second would mean this manifest had started answering somebody else's question.
WEIGHT_SUFFIXES = (".onnx", ".safetensors", ".pt", ".pth", ".bin")


@pytest.fixture
def vocabulary_manifest() -> Manifest:
    """Return a private copy of the vocabulary manifest, free to be malformed."""
    return copy.deepcopy(load_manifest(VOCABULARY_MANIFEST_PATH))


@pytest.mark.spec_exempt("structural: the manifest is data the other checks read")
def test_the_tracked_vocabulary_manifest_parses_and_declares_entries(
    vocabulary_manifest: Manifest,
) -> None:
    assert vocabulary_manifest["pinned"]
    assert vocabulary_manifest["publishers"]
    assert vocabulary_manifest["entries"]


@pytest.mark.spec("model-provisioning:vocabulary:entry-is-pinned-and-digested")
def test_the_vocabulary_entry_declares_every_required_key(
    vocabulary_manifest: Manifest,
) -> None:
    assert entries_with_missing_keys(vocabulary_manifest) == []


@pytest.mark.spec("model-provisioning:vocabulary:entry-is-pinned-and-digested")
def test_the_vocabulary_entry_carries_a_destination_a_digest_and_a_byte_count(
    vocabulary_manifest: Manifest,
) -> None:
    (entry,) = [e for e in vocabulary_manifest["entries"] if e["dest"] == VOCABULARY]
    assert DIGEST.match(entry["sha256"])
    assert entry["bytes"] > 0
    assert len(entry["sources"]) >= 1


@pytest.mark.spec("model-provisioning:vocabulary:entry-is-pinned-and-digested")
def test_every_vocabulary_entry_carries_a_digest(
    vocabulary_manifest: Manifest,
) -> None:
    assert entries_without_a_digest(vocabulary_manifest) == []


@pytest.mark.spec("model-provisioning:vocabulary:entry-is-pinned-and-digested")
def test_no_source_in_the_vocabulary_manifest_resolves_a_mutable_ref(
    vocabulary_manifest: Manifest,
) -> None:
    assert sources_on_a_mutable_ref(vocabulary_manifest) == []


@pytest.mark.spec("model-provisioning:vocabulary:entry-is-pinned-and-digested")
def test_a_vocabulary_source_naming_a_branch_fails_the_same_check(
    vocabulary_manifest: Manifest,
) -> None:
    entry = vocabulary_manifest["entries"][0]
    entry["sources"] = [
        "https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3"
        "/resolve/main/selected_tags.csv"
    ]
    assert sources_on_a_mutable_ref(vocabulary_manifest) == entry["sources"]


@pytest.mark.spec("model-provisioning:vocabulary:entry-is-pinned-and-digested")
def test_the_vocabularys_primary_publishes_the_artifact_it_serves(
    vocabulary_manifest: Manifest,
) -> None:
    assert mirror_entries_without_an_alternate(vocabulary_manifest) == []


@pytest.mark.spec("model-provisioning:vocabulary:manifest-is-its-own-file")
def test_the_vocabulary_appears_only_in_its_own_manifest() -> None:
    vocabulary = {e["dest"] for e in load_manifest(VOCABULARY_MANIFEST_PATH)["entries"]}
    graph = {e["dest"] for e in load_manifest()["entries"]}
    scorer = {e["dest"] for e in load_eval_manifest()["entries"]}
    assert VOCABULARY in vocabulary
    assert vocabulary & graph == set()
    assert vocabulary & scorer == set()


@pytest.mark.spec("model-provisioning:vocabulary:manifest-is-its-own-file")
def test_the_vocabulary_manifest_answers_one_question(
    vocabulary_manifest: Manifest,
) -> None:
    assert [e["dest"] for e in vocabulary_manifest["entries"]] == [VOCABULARY, TAGGER]


@pytest.mark.spec(
    "model-provisioning:vocabulary:label-index-and-model-share-a-revision"
)
def test_the_label_index_and_the_model_it_indexes_are_both_declared(
    vocabulary_manifest: Manifest,
) -> None:
    weights = [
        entry["dest"]
        for entry in vocabulary_manifest["entries"]
        if entry["dest"].endswith(WEIGHT_SUFFIXES)
    ]
    assert weights == [TAGGER]


@pytest.mark.spec(
    "model-provisioning:vocabulary:label-index-and-model-share-a-revision"
)
def test_every_vocabulary_source_resolves_one_revision_of_one_repository(
    vocabulary_manifest: Manifest,
) -> None:
    for entry in vocabulary_manifest["entries"]:
        for source in entry["sources"]:
            assert source.startswith(
                f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/"
            ), f"{entry['dest']} is not pinned to {REVISION}"


@pytest.mark.spec(
    "model-provisioning:vocabulary:label-index-and-model-share-a-revision"
)
def test_a_label_index_and_a_model_at_two_revisions_fail_the_check(
    vocabulary_manifest: Manifest,
) -> None:
    (tagger,) = [e for e in vocabulary_manifest["entries"] if e["dest"] == TAGGER]
    tagger["sources"] = [
        source.replace(REVISION, "0" * 40) for source in tagger["sources"]
    ]

    with pytest.raises(AssertionError):
        test_every_vocabulary_source_resolves_one_revision_of_one_repository(
            vocabulary_manifest
        )


@pytest.mark.spec("model-provisioning:licences:vocabulary-terms-are-recorded")
def test_every_vocabulary_artifact_is_named_in_the_licence_record(
    vocabulary_manifest: Manifest,
) -> None:
    record = LICENCES_PATH.read_text()
    for entry in vocabulary_manifest["entries"]:
        assert entry["dest"] in record, f"{entry['dest']} carries no recorded licence"


@pytest.mark.spec("model-provisioning:licences:vocabulary-terms-are-recorded")
@pytest.mark.parametrize("artifact", [VOCABULARY, TAGGER])
def test_each_vocabulary_row_names_its_terms_its_source_and_the_date_read(
    artifact: str,
) -> None:
    section = _section_naming(LICENCES_PATH.read_text(), artifact)
    terms = re.search(r"- \*\*Licence:\*\* (?P<terms>\S.*)", section)
    assert terms is not None and terms.group("terms").strip()
    read_at = re.search(
        r"- \*\*Read at:\*\* .*<(?P<url>https://\S+)>.*?(?P<date>\d{4}-\d{2}-\d{2})",
        section,
        re.DOTALL,
    )
    assert read_at is not None
    assert read_at.group("url")
    assert read_at.group("date")


def _section_naming(record: str, artifact: str) -> str:
    """Return the one `###` section of the licence record that names `artifact`.

    The closing summary table is excluded rather than searched. It names every
    artifact by design -- it is the index over the records, not a record -- so
    leaving it in would make "recorded in exactly one section" unsatisfiable for
    all of them the moment a second artifact was added under the last heading.
    """
    body = record.split("\n## Summary", 1)[0]
    sections = re.split(r"^### ", body, flags=re.MULTILINE)[1:]
    naming = [section for section in sections if artifact in section]
    assert len(naming) == 1, f"{artifact} is recorded in {len(naming)} sections"
    return naming[0]


# --- provisioning -------------------------------------------------------------


def _targets(captured: str) -> list[str]:
    """Return the destination each plan line names, whatever it decided about it."""
    return [line.split("\t")[1] for line in captured.splitlines()]


@pytest.mark.spec("model-provisioning:vocabulary:driver-provisions-the-manifest")
def test_the_provisioner_plans_the_vocabulary_when_pointed_at_its_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import isekai.boundary.provision as provision

    # The pre-flight is the only network call in the module; the fake is what the
    # rest of this suite already drives it with.
    monkeypatch.setattr(provision, "HuggingFaceFetcher", FakeFetcher)

    assert provision.main(["plan", str(tmp_path), str(VOCABULARY_MANIFEST_PATH)]) == 0

    assert _targets(capsys.readouterr().out) == [
        str(tmp_path / VOCABULARY),
        str(tmp_path / TAGGER),
    ]


@pytest.mark.spec("model-provisioning:vocabulary:driver-provisions-the-manifest")
def test_the_provisioner_still_plans_the_graphs_stack_when_told_no_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import isekai.boundary.provision as provision

    monkeypatch.setattr(provision, "HuggingFaceFetcher", FakeFetcher)

    assert provision.main(["plan", str(tmp_path)]) == 0

    planned = _targets(capsys.readouterr().out)
    assert planned == [
        str(tmp_path / entry["dest"])
        for entry in load_manifest(MANIFEST_PATH)["entries"]
    ]
    assert str(tmp_path / VOCABULARY) not in planned


@pytest.mark.spec("model-provisioning:vocabulary:driver-provisions-the-manifest")
def test_the_shell_driver_forwards_the_manifest_to_every_invocation() -> None:
    script = DRIVER_PATH.read_text()
    invocations = [line for line in script.splitlines() if '"$PROVISION"' in line]

    assert invocations
    assert all("MANIFEST" in line for line in invocations)
    assert "scripts/vocabulary.json" in script


@pytest.mark.spec("model-provisioning:vocabulary:absent-vocabulary-names-the-command")
def test_an_unprovisioned_vocabulary_refuses_naming_the_command(
    tmp_path: Path,
) -> None:
    with pytest.raises(Refusal) as refused:
        load_vocabulary(tmp_path)

    message = str(refused.value)
    assert VOCABULARY in message
    assert "scripts/download_models.sh scripts/vocabulary.json" in message

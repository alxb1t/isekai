"""The vocabulary's manifest, held to the same rules as the graph's and the scorer's.

One entry, pinned to an immutable revision and digested by fetching, because at
roughly 300 KB the artifact is not stored as a large file and so publishes no
digest to read. It reaches the tree through a manifest at all so that a fresh
clone can fill a sheet: it used to arrive as a side effect of downloading a
tagger this repository does not load (design.md D9).
"""

import copy
import re
from pathlib import Path

import pytest

from isekai.eval_models import load_eval_manifest
from isekai.provision import (
    DIGEST,
    Manifest,
    entries_with_missing_keys,
    entries_without_a_digest,
    load_manifest,
    load_vocabulary_manifest,
    mirror_entries_without_an_alternate,
    sources_on_a_mutable_ref,
)

VOCABULARY = "wd14/selected_tags.csv"

# The tracked note that sits beside the manifests. It is one record for every
# artifact this repository pins, rather than one per manifest: a licence is a
# property of the artifact, and three notes would be three places to forget.
LICENCES_PATH = Path(__file__).resolve().parent.parent / "scripts" / "eval_licences.md"

# Extensions a model's weights arrive under. The vocabulary is published beside
# one; the point of this manifest is that it declares the list and not the model.
WEIGHT_SUFFIXES = (".onnx", ".safetensors", ".pt", ".pth", ".bin")


@pytest.fixture
def vocabulary_manifest() -> Manifest:
    """Return a private copy of the vocabulary manifest, free to be malformed."""
    return copy.deepcopy(load_vocabulary_manifest())


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
    vocabulary = {e["dest"] for e in load_vocabulary_manifest()["entries"]}
    graph = {e["dest"] for e in load_manifest()["entries"]}
    scorer = {e["dest"] for e in load_eval_manifest()["entries"]}
    assert VOCABULARY in vocabulary
    assert vocabulary & graph == set()
    assert vocabulary & scorer == set()


@pytest.mark.spec("model-provisioning:vocabulary:manifest-is-its-own-file")
def test_the_vocabulary_manifest_answers_one_question(
    vocabulary_manifest: Manifest,
) -> None:
    assert [e["dest"] for e in vocabulary_manifest["entries"]] == [VOCABULARY]


@pytest.mark.spec("model-provisioning:vocabulary:tagger-model-is-not-included")
def test_the_vocabulary_manifest_declares_no_model_weights(
    vocabulary_manifest: Manifest,
) -> None:
    weights = [
        entry["dest"]
        for entry in vocabulary_manifest["entries"]
        if entry["dest"].endswith(WEIGHT_SUFFIXES)
    ]
    assert weights == []


@pytest.mark.spec("model-provisioning:vocabulary:tagger-model-is-not-included")
def test_no_source_in_the_vocabulary_manifest_fetches_a_model_file(
    vocabulary_manifest: Manifest,
) -> None:
    weights = [
        source
        for entry in vocabulary_manifest["entries"]
        for source in entry["sources"]
        if source.endswith(WEIGHT_SUFFIXES)
    ]
    assert weights == []


@pytest.mark.spec("model-provisioning:licences:vocabulary-terms-are-recorded")
def test_every_vocabulary_artifact_is_named_in_the_licence_record(
    vocabulary_manifest: Manifest,
) -> None:
    record = LICENCES_PATH.read_text()
    for entry in vocabulary_manifest["entries"]:
        assert entry["dest"] in record, f"{entry['dest']} carries no recorded licence"


@pytest.mark.spec("model-provisioning:licences:vocabulary-terms-are-recorded")
def test_the_vocabularys_row_names_its_terms_its_source_and_the_date_read() -> None:
    section = _section_naming(LICENCES_PATH.read_text(), VOCABULARY)
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
    """Return the one `###` section of the licence record that names `artifact`."""
    sections = re.split(r"^### ", record, flags=re.MULTILINE)[1:]
    naming = [section for section in sections if artifact in section]
    assert len(naming) == 1, f"{artifact} is recorded in {len(naming)} sections"
    return naming[0]

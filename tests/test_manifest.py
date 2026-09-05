from typing import Any, cast

import pytest

from isekai.provision import (
    SOURCE_ORG,
    Entry,
    Manifest,
    entries_with_missing_keys,
    entries_without_a_digest,
    mirror_entries_without_an_alternate,
    sources_on_a_mutable_ref,
)


def _org_of(source: str) -> str | None:
    """Return the org a source URL belongs to, exactly as the module reads it."""
    match = SOURCE_ORG.match(source)
    return match.group("org") if match else None


def _first_mirror_entry(manifest: Manifest) -> Entry:
    """Return the first entry whose primary source is a mirror, not a publisher."""
    publishers = set(manifest["publishers"])
    for entry in manifest["entries"]:
        if _org_of(entry["sources"][0]) not in publishers:
            return entry
    raise AssertionError("the manifest declares no mirror-primary entry")


@pytest.mark.spec_exempt("structural: the manifest is data the other checks read")
def test_the_tracked_manifest_parses_and_declares_entries(manifest: Manifest) -> None:
    assert manifest["entries"]
    assert manifest["pinned"]
    assert manifest["publishers"]


@pytest.mark.spec_exempt("structural: shape, not a scenario about pins or digests")
def test_every_entry_declares_the_required_keys(manifest: Manifest) -> None:
    assert entries_with_missing_keys(manifest) == []


@pytest.mark.spec_exempt("structural: shape, not a scenario about pins or digests")
def test_an_entry_missing_a_key_is_reported(manifest: Manifest) -> None:
    # Deliberately off-type: an entry with no `sha256` is exactly what an `Entry`
    # is not, which is why the check exists and why the cast is here.
    entry = cast(dict[str, Any], manifest["entries"][0])
    del entry["sha256"]
    assert entries_with_missing_keys(manifest) == [entry["dest"]]


@pytest.mark.spec("model-provisioning:immutable-pins:no-source-resolves-a-mutable-ref")
def test_no_source_in_the_manifest_resolves_a_mutable_ref(manifest: Manifest) -> None:
    assert sources_on_a_mutable_ref(manifest) == []


@pytest.mark.spec("model-provisioning:immutable-pins:no-source-resolves-a-mutable-ref")
def test_a_source_naming_a_branch_rather_than_a_revision_fails_the_check(
    manifest: Manifest,
) -> None:
    entry = manifest["entries"][0]
    entry["sources"][0] = "https://huggingface.co/an/org/resolve/main/model.safetensors"
    assert sources_on_a_mutable_ref(manifest) == [entry["sources"][0]]


@pytest.mark.spec("model-provisioning:immutable-pins:every-entry-carries-a-digest")
def test_every_entry_carries_a_well_formed_sha256(manifest: Manifest) -> None:
    assert entries_without_a_digest(manifest) == []


@pytest.mark.spec("model-provisioning:immutable-pins:every-entry-carries-a-digest")
def test_an_entry_with_a_malformed_digest_fails_the_check(manifest: Manifest) -> None:
    entry = manifest["entries"][0]
    entry["sha256"] = "not-a-digest"
    assert entries_without_a_digest(manifest) == [entry["dest"]]


@pytest.mark.spec("model-provisioning:immutable-pins:every-entry-carries-a-digest")
def test_an_entry_with_no_digest_at_all_fails_the_check(manifest: Manifest) -> None:
    entry = cast(dict[str, Any], manifest["entries"][0])
    del entry["sha256"]
    assert entries_without_a_digest(manifest) == [entry["dest"]]


@pytest.mark.spec(
    "model-provisioning:immutable-pins:third-party-artifact-carries-an-alternate"
)
def test_every_mirror_primary_entry_declares_an_alternate(manifest: Manifest) -> None:
    assert mirror_entries_without_an_alternate(manifest) == []


@pytest.mark.spec(
    "model-provisioning:immutable-pins:third-party-artifact-carries-an-alternate"
)
def test_a_mirror_primary_entry_with_no_alternate_fails_the_check(
    manifest: Manifest,
) -> None:
    entry = _first_mirror_entry(manifest)
    del entry["sources"][1:]
    assert mirror_entries_without_an_alternate(manifest) == [entry["dest"]]


@pytest.mark.spec(
    "model-provisioning:immutable-pins:third-party-artifact-carries-an-alternate"
)
def test_a_publisher_primary_entry_needs_no_alternate(manifest: Manifest) -> None:
    publishers = set(manifest["publishers"])
    single = [
        entry
        for entry in manifest["entries"]
        if len(entry["sources"]) == 1 and _org_of(entry["sources"][0]) in publishers
    ]
    assert single
    assert mirror_entries_without_an_alternate(manifest) == []


@pytest.mark.spec_exempt("structural: every alternate must serve the declared digest")
def test_every_entry_declares_at_least_one_source(manifest: Manifest) -> None:
    assert all(entry["sources"] for entry in manifest["entries"])

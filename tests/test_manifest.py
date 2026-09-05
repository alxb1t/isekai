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


# The SHA-256 Civitai publishes for WAI-illustrious-SDXL v17.0 (model 827184,
# version 2883731). WAI has no first-party Hugging Face repo, so every source the
# manifest declares for it is a mirror and this digest is the acceptance test:
# any host serving matching bytes is equally acceptable, and one serving anything
# else is rejected whoever it is (design.md D1).
#
# `derive_manifest.py` asserts the same equality when it re-derives, but that runs
# only when a human points it at the network. Pinned here as well so the tie
# between the shipped bytes and the publisher's own digest is checked by the gate,
# and so changing it is a deliberate test edit -- the same idiom the prompts, the
# clip layer and the probe's dials are held by.
#
# It is a cross-check, not a signature: Civitai computes it after upload, so it
# attests the mirrors agree with the publisher's copy, not that the author signed
# anything.
WAI_PUBLISHED_SHA256 = (
    "f116b0c78ff441467b0cdc8f1936e1ed18ea31e9997c7b132b1b8db533f0bd04"
)


def _checkpoints(manifest: Manifest) -> list[Entry]:
    """Return every entry the manifest lands on the checkpoints tree."""
    return [
        entry
        for entry in manifest["entries"]
        if entry["dest"].startswith("checkpoints/")
    ]


@pytest.mark.spec_exempt(
    "the one-path rule, not a provisioning scenario: design.md D3 admits one base"
)
def test_the_manifest_declares_exactly_one_base_checkpoint(manifest: Manifest) -> None:
    # A second declared checkpoint would be a second path in everything but name.
    assert len(_checkpoints(manifest)) == 1


@pytest.mark.spec(
    "model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest"
)
def test_the_base_checkpoint_carries_the_digest_its_publisher_states(
    manifest: Manifest,
) -> None:
    (checkpoint,) = _checkpoints(manifest)
    assert checkpoint["sha256"] == WAI_PUBLISHED_SHA256

    # Every source is a mirror, which is why the digest above is load-bearing.
    publishers = set(manifest["publishers"])
    assert all(_org_of(source) not in publishers for source in checkpoint["sources"])

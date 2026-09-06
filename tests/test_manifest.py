import json
from typing import Any, cast

import pytest

# `scripts/` is declared a source root in `pyproject.toml` -- operator tooling, not
# a package. It is not on `convert.py`'s import graph, so the stdlib-only runtime
# rule is untouched either way.
from derive_manifest import civitai_file

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
# `derive_manifest.py` now *fetches* this value from Civitai's own record and holds
# the mirrors against it, so no human transcribes it into the derivation. But that
# runs only when a human points the tool at the network. Pinned here as well, by
# hand and on purpose: this copy is the offline anchor, and an anchor that fetches
# is not one. It is what makes the tie
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


# --- the trust root, derived rather than transcribed ---
#
# `derive_manifest.py` claimed the manifest is "derived, never transcribed", and
# then read the one digest that matters most -- the base checkpoint's, which is
# the whole trust root for an artifact no publisher hosts -- out of a constant a
# human typed. Three copies of one transcription cross-check the copying, not the
# value. The parse is a pure function so the suite can hold it offline; only the
# fetch around it touches the network.

CIVITAI_PAYLOAD = {
    "name": "v17.0",
    "files": [
        {
            "name": "waiIllustriousSDXL_v170.safetensors",
            "sizeKB": 6775430.353515625,
            "hashes": {
                "AutoV2": "F116B0C78F",
                "SHA256": (
                    "F116B0C78FF441467B0CDC8F1936E1ED18EA31E9997C7B132B1B8DB533F0BD04"
                ),
                "BLAKE3": (
                    "1762AFDFBC3F22A1BB34C6AA85405414FE838828F771CA444776DEEA141F8BE8"
                ),
            },
        }
    ],
}


@pytest.mark.spec(
    "model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest"
)
def test_the_published_digest_is_read_from_the_publishers_own_record() -> None:
    digest = civitai_file(CIVITAI_PAYLOAD, "waiIllustriousSDXL_v170.safetensors")
    # lowercased, because the manifest's own `DIGEST` pattern is lowercase and a
    # digest that differs only in case would fail a check it should pass
    assert digest == WAI_PUBLISHED_SHA256


@pytest.mark.spec(
    "model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest"
)
def test_a_version_not_serving_that_file_is_refused() -> None:
    with pytest.raises(SystemExit):
        civitai_file(CIVITAI_PAYLOAD, "somebodyElsesCheckpoint.safetensors")


@pytest.mark.spec(
    "model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest"
)
def test_a_file_publishing_no_sha256_is_refused_rather_than_downgraded() -> None:
    payload = {
        "files": [
            {
                "name": "waiIllustriousSDXL_v170.safetensors",
                "sizeKB": 1.0,
                "hashes": {"AutoV2": "F116B0C78F", "CRC32": "BBAEFE08"},
            }
        ]
    }
    # AutoV2 is a truncation and CRC32 is not a digest of anything; degrading to
    # either would put a value in a SHA-256 field that verifies nothing.
    with pytest.raises(SystemExit):
        civitai_file(payload, "waiIllustriousSDXL_v170.safetensors")


@pytest.mark.spec_exempt(
    "structural: BLAKE3 is published and deliberately not recorded (design.md D13)"
)
def test_the_derived_manifest_records_no_blake3(manifest: Manifest) -> None:
    # Verifying it would need a wheel the runtime rule forbids, and a field
    # nothing reads is the same smell as a one-entry registry.
    assert "BLAKE3" not in json.dumps(manifest)
    assert "blake3" not in json.dumps(manifest)


@pytest.mark.spec(
    "model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest"
)
def test_a_record_omitting_its_size_still_yields_the_digest() -> None:
    # The size was read with a subscript where every sibling read uses `.get` with
    # a `SystemExit`, and no caller consumed it -- so an omitted `sizeKB` aborted
    # derivation with a raw `KeyError` for a number nobody wanted. What this
    # function is for is the digest.
    payload = {
        "files": [
            {
                "name": "waiIllustriousSDXL_v170.safetensors",
                "hashes": {"SHA256": WAI_PUBLISHED_SHA256},
            }
        ]
    }
    assert civitai_file(payload, "waiIllustriousSDXL_v170.safetensors") == (
        WAI_PUBLISHED_SHA256
    )

"""The reader's manifest: the files each alias is built from, pinned like any other.

A flow names its reader by an alias `ollama create` builds from
`config/joycaption.Modelfile`. `config/reader.json` pins the files behind it and
says which is the model and which the projector, so the check in
`isekai/boundary/ollama.py` has one place to read them from (0033 design D4).
"""

import copy
from pathlib import Path

import pytest

from isekai.boundary.provision import (
    DIGEST,
    READER_MANIFEST_PATH,
    Manifest,
    entries_with_missing_keys,
    load_manifest,
    mirror_entries_without_an_alternate,
    sources_on_a_mutable_ref,
)
from isekai.foundation.flow import load_flow, tracked_flows
from tests.fakes import FakeFetcher


@pytest.fixture
def reader_manifest() -> Manifest:
    """Return a private copy of the reader's manifest, free to be malformed."""
    return copy.deepcopy(load_manifest(READER_MANIFEST_PATH))


def aliases_off_the_entries(manifest: Manifest) -> list[str]:
    """Return each `alias.role` whose file is not exactly one of the entries."""
    dests = [entry["dest"] for entry in manifest["entries"]]
    return [
        f"{alias}.{role}"
        for alias, built in manifest.get("aliases", {}).items()
        for role, dest in (("model", built["model"]), ("projector", built["projector"]))
        if dests.count(dest) != 1
    ]


@pytest.mark.spec("model-provisioning:reader:each-model-names-its-model-and-projector")
def test_each_alias_names_a_pinned_model_and_projector(
    reader_manifest: Manifest,
) -> None:
    assert reader_manifest["aliases"]
    assert entries_with_missing_keys(reader_manifest) == []
    assert sources_on_a_mutable_ref(reader_manifest) == []
    assert mirror_entries_without_an_alternate(reader_manifest) == []
    for entry in reader_manifest["entries"]:
        assert DIGEST.match(entry["sha256"])
        assert entry["bytes"] > 0
    assert aliases_off_the_entries(reader_manifest) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_each_alias_names_a_pinned_model_and_projector"
)
def test_the_check_catches_an_alias_naming_a_file_no_entry_pins(
    reader_manifest: Manifest,
) -> None:
    alias = next(iter(reader_manifest["aliases"]))
    reader_manifest["aliases"][alias]["projector"] = "joycaption/elsewhere.gguf"
    assert aliases_off_the_entries(reader_manifest) == [f"{alias}.projector"]


@pytest.mark.spec("model-provisioning:reader:every-flow-model-is-pinned")
def test_every_model_a_tracked_flow_declares_is_pinned(
    reader_manifest: Manifest,
) -> None:
    flows = tracked_flows()
    assert flows
    for flow in flows:
        assert load_flow(flow).model in reader_manifest["aliases"], flow


@pytest.mark.spec("model-provisioning:reader:driver-provisions-the-manifest")
def test_the_provisioner_plans_the_readers_files_when_pointed_at_its_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import isekai.boundary.provision as provision

    monkeypatch.setattr(provision, "HuggingFaceFetcher", FakeFetcher)

    assert provision.main(["plan", str(tmp_path), str(READER_MANIFEST_PATH)]) == 0

    planned = [line.split("\t")[1] for line in capsys.readouterr().out.splitlines()]
    assert planned == [
        str(tmp_path / entry["dest"])
        for entry in load_manifest(READER_MANIFEST_PATH)["entries"]
    ]

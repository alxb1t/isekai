import pytest

from isekai.comfy_types import Workflow
from isekai.provision import (
    Manifest,
    graph_model_files,
    preprocessor_model_files,
    undeclared_files,
    unmapped_preprocessors,
)


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:graph-filename-has-an-entry"
)
def test_every_model_file_the_graph_names_has_a_manifest_entry(
    workflow: Workflow, manifest: Manifest
) -> None:
    assert undeclared_files(graph_model_files(workflow), manifest) == []


@pytest.mark.spec_exempt(
    "structural: guards the completeness check against passing vacuously"
)
def test_the_shipped_graph_names_model_files_at_all(workflow: Workflow) -> None:
    named = graph_model_files(workflow)
    assert "animagine-xl-4.0.safetensors" in named
    assert "ip-adapter.bin" in named
    assert len(named) >= 7


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:graph-filename-has-an-entry"
)
def test_a_graph_naming_a_file_the_manifest_does_not_carry_fails_the_check(
    workflow: Workflow, manifest: Manifest
) -> None:
    workflow["1"]["inputs"]["ckpt_name"] = "some-other-base.safetensors"
    assert undeclared_files(graph_model_files(workflow), manifest) == [
        "some-other-base.safetensors"
    ]


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:preprocessor-models-are-declared"
)
def test_every_preprocessor_in_the_graph_is_present_in_the_mapping(
    workflow: Workflow,
) -> None:
    assert unmapped_preprocessors(workflow) == []


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:preprocessor-models-are-declared"
)
def test_a_preprocessor_absent_from_the_mapping_fails_the_check(
    workflow: Workflow,
) -> None:
    workflow["99"] = {"class_type": "SomeNewPreprocessor", "inputs": {}}
    assert unmapped_preprocessors(workflow) == ["SomeNewPreprocessor"]


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:preprocessor-models-are-declared"
)
def test_the_files_a_preprocessor_fetches_for_itself_have_manifest_entries(
    workflow: Workflow, manifest: Manifest
) -> None:
    assert undeclared_files(preprocessor_model_files(workflow), manifest) == []


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:preprocessor-models-are-declared"
)
def test_the_lineart_files_are_declared_although_the_graph_names_neither(
    workflow: Workflow, manifest: Manifest
) -> None:
    named = graph_model_files(workflow)
    assert "sk_model.pth" not in named
    assert "sk_model2.pth" not in named
    fetched = preprocessor_model_files(workflow)
    assert "sk_model.pth" in fetched
    assert "sk_model2.pth" in fetched
    assert undeclared_files(["sk_model.pth", "sk_model2.pth"], manifest) == []


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:preprocessor-models-are-declared"
)
def test_dropping_a_mapped_file_from_the_manifest_fails_the_check(
    workflow: Workflow, manifest: Manifest
) -> None:
    manifest["entries"] = [
        entry
        for entry in manifest["entries"]
        if not entry["dest"].endswith("/sk_model2.pth")
    ]
    assert undeclared_files(preprocessor_model_files(workflow), manifest) == [
        "sk_model2.pth"
    ]


@pytest.mark.spec_exempt("structural: the mapping is tracked data the checks read")
def test_the_mapping_covers_every_preprocessor_the_shipped_graph_uses(
    workflow: Workflow,
) -> None:
    used = {
        node["class_type"]
        for node in workflow.values()
        if node["class_type"].endswith("Preprocessor")
    }
    assert used == {"TilePreprocessor", "DWPreprocessor", "LineArtPreprocessor"}

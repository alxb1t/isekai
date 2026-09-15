import pytest

from isekai.comfy_types import Workflow
from isekai.provision import (
    Manifest,
    graph_model_files,
    self_fetched_model_files,
    unclassified_node_classes,
    undeclared_files,
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
    assert "waiIllustriousSDXL_v170.safetensors" in named
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
def test_the_files_a_preprocessor_fetches_for_itself_have_manifest_entries(
    workflow: Workflow, manifest: Manifest
) -> None:
    assert undeclared_files(self_fetched_model_files(workflow), manifest) == []


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:preprocessor-models-are-declared"
)
def test_the_pose_preprocessor_names_its_own_files_rather_than_fetching_them(
    workflow: Workflow, manifest: Manifest
) -> None:
    # The other half of the binding. `DWPreprocessor` is the shipped graph's only
    # preprocessor and it names both checkpoints in its own inputs, so the graph
    # half already covers them and the self-fetching half must claim neither --
    # a node counted twice would hide a missing entry behind a present one.
    named = graph_model_files(workflow)
    assert "yolox_l.onnx" in named
    assert "dw-ll_ucoco_384_bs5.torchscript.pt" in named
    fetched = self_fetched_model_files(workflow)
    assert "yolox_l.onnx" not in fetched
    assert "dw-ll_ucoco_384_bs5.torchscript.pt" not in fetched
    assert undeclared_files(named, manifest) == []


@pytest.mark.spec(
    "model-provisioning:manifest-completeness:preprocessor-models-are-declared"
)
def test_dropping_a_preprocessors_file_from_the_manifest_fails_the_check(
    workflow: Workflow, manifest: Manifest
) -> None:
    manifest["entries"] = [
        entry
        for entry in manifest["entries"]
        if not entry["dest"].endswith("/dw-ll_ucoco_384_bs5.torchscript.pt")
    ]
    assert undeclared_files(graph_model_files(workflow), manifest) == [
        "dw-ll_ucoco_384_bs5.torchscript.pt"
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
    assert used == {"DWPreprocessor"}


ANTELOPEV2 = (
    "1k3d68.onnx",
    "2d106det.onnx",
    "genderage.onnx",
    "glintr100.onnx",
    "scrfd_10g_bnkps.onnx",
)


@pytest.mark.spec("model-provisioning:namespace:self-fetching-nodes-are-bound-by-name")
def test_every_class_the_graph_uses_is_classified_by_name(workflow: Workflow) -> None:
    assert unclassified_node_classes(workflow) == []


@pytest.mark.spec("model-provisioning:namespace:self-fetching-nodes-are-bound-by-name")
def test_a_class_absent_from_the_mapping_fails_the_check(workflow: Workflow) -> None:
    # It does not end in `Preprocessor`, so a suffix rule would have passed it.
    workflow["99"] = {"class_type": "SomeNewIdentityLoader", "inputs": {}}
    assert unclassified_node_classes(workflow) == ["SomeNewIdentityLoader"]


@pytest.mark.spec("model-provisioning:namespace:self-fetching-nodes-are-bound-by-name")
def test_the_identity_node_fetches_antelopev2_and_the_manifest_declares_it(
    workflow: Workflow, manifest: Manifest
) -> None:
    fetched = self_fetched_model_files(workflow)
    for filename in ANTELOPEV2:
        assert filename in fetched
    assert undeclared_files(list(ANTELOPEV2), manifest) == []


@pytest.mark.spec("model-provisioning:namespace:self-fetching-nodes-are-bound-by-name")
def test_the_identity_node_names_none_of_the_files_it_fetches(
    workflow: Workflow,
) -> None:
    named = graph_model_files(workflow)
    for filename in ANTELOPEV2:
        assert filename not in named


@pytest.mark.spec("model-provisioning:namespace:self-fetching-nodes-are-bound-by-name")
def test_dropping_an_antelopev2_entry_from_the_manifest_fails_the_check(
    workflow: Workflow, manifest: Manifest
) -> None:
    manifest["entries"] = [
        entry
        for entry in manifest["entries"]
        if not entry["dest"].endswith("/genderage.onnx")
    ]
    assert undeclared_files(self_fetched_model_files(workflow), manifest) == [
        "genderage.onnx"
    ]

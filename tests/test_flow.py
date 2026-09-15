"""The flow manifest: what it declares, what it refuses, and that it cannot drift.

The immutability test is the load-bearing one. An output's path identifies a
configuration only if a flow identifier never silently means something else, so a
changed dial has to fail here rather than change what an existing identifier
renders.
"""

import json
from pathlib import Path

import pytest

from isekai.flow import (
    FLOW_SCHEMA_VERSION,
    MANIFEST_NAME,
    REQUIRED,
    Flow,
    assemble,
    load_flow,
    manifest_digest,
    tracked_flows,
)
from isekai.refusal import Refusal
from isekai.sheet import load_schema

# The digest of every tracked flow's whole directory, committed here.
#
# **Changing a dial does not edit a flow; it creates a new one.** A tuned dial is
# not a variant of a flow, it is an untested flow -- so editing `summon-v1` fails
# this test naming it, exactly as changing one of the graph's committed prompts is
# a deliberate test edit. Updating this constant to make a change pass is the
# wrong move; adding `summon-v2` is the right one.
PINNED: dict[str, str] = {
    "summon-v1": "18d057fe8e5d39b9c33d591a07528754022f2c1cbaaad4f126021595d694905f",
}


@pytest.fixture
def flow() -> Flow:
    """Return the one tracked flow."""
    return load_flow("summon-v1")


def _scratch(tmp_path: Path, **overrides: object) -> Path:
    """Copy `summon-v1` into a scratch flows root, with the given fields changed."""
    root = tmp_path / "flows" / "summon-v1"
    root.mkdir(parents=True)
    source = load_flow("summon-v1").path
    document = json.loads((source / MANIFEST_NAME).read_text())
    document.update(overrides)
    (root / MANIFEST_NAME).write_text(json.dumps(document, indent=2) + "\n")
    (root / "graph.json").write_bytes((source / "graph.json").read_bytes())
    return tmp_path / "flows"


# --- what a manifest declares -------------------------------------------------


@pytest.mark.spec("image-generation:manifest:flow-declares-its-inputs")
def test_a_flow_declares_its_inputs_schema_vocabulary_and_dials(flow: Flow) -> None:
    assert flow.inputs == ("photo", "sheet")
    assert flow.schema == "identity.v1"
    assert set(flow.vocabulary) == {"name", "revision", "sha256"}
    assert set(flow.dials) >= {
        "cfg",
        "steps",
        "sampler_name",
        "scheduler",
        "denoise",
        "clip_skip",
        "ip_weight",
        "identity_cn_strength",
        "openpose_strength",
        "hires_scale",
        "hires_steps",
        "hires_denoise",
    }


@pytest.mark.spec("image-generation:manifest:flow-declares-its-inputs")
def test_no_value_in_a_manifest_is_derived_at_load_time(flow: Flow) -> None:
    document = json.loads((flow.path / MANIFEST_NAME).read_text())

    # Everything the loader returns is a value the file states, verbatim.
    assert document["dials"] == dict(flow.dials)
    assert document["prompt"] == dict(flow.prompt)
    assert document["models"] == list(flow.models)
    assert document["nodes"] == dict(flow.nodes)


@pytest.mark.spec("image-generation:manifest:flow-declares-its-inputs")
def test_the_dials_are_the_measured_ones_and_not_the_graph_files(flow: Flow) -> None:
    # The graph carries the prototype's committed values; every measured run
    # overrode them. A manifest transcribed from the graph would ship a
    # configuration nothing measured (design.md D12).
    graph = flow.graph()
    assert graph[flow.node("sampler")]["inputs"]["cfg"] == 7
    assert flow.dials["cfg"] == 5
    assert graph[flow.node("identity")]["inputs"]["cn_strength"] == 0.5
    assert flow.dials["identity_cn_strength"] == 0.8


@pytest.mark.spec("image-generation:manifest:tracked-flows-are-gate-checked")
def test_every_tracked_flow_parses(tmp_path: Path) -> None:
    assert tracked_flows() == ["summon-v1"]
    for name in tracked_flows():
        assert load_flow(name).id == name


@pytest.mark.spec("image-generation:manifest:tracked-flows-are-gate-checked")
def test_the_schema_and_vocabulary_each_flow_names_resolve() -> None:
    vocabulary = json.loads(
        (
            Path(__file__).resolve().parent.parent / "scripts" / "vocabulary.json"
        ).read_text()
    )["entries"][0]

    for name in tracked_flows():
        flow = load_flow(name)
        schema = load_schema(
            Path(__file__).resolve().parent.parent
            / "schemas"
            / f"{flow.schema}.json".replace(".v1.json", ".v1.json")
        )
        assert schema.name == flow.schema.split(".")[0]
        assert flow.vocabulary["name"] == vocabulary["dest"]
        assert flow.vocabulary["sha256"] == vocabulary["sha256"]
        assert flow.vocabulary["revision"] in vocabulary["sources"][0]


@pytest.mark.spec("image-generation:manifest:tracked-flows-are-gate-checked")
def test_every_model_a_flow_declares_has_a_manifest_entry() -> None:
    from isekai.provision import load_manifest

    declared = {entry["dest"] for entry in load_manifest()["entries"]}
    for name in tracked_flows():
        assert set(load_flow(name).models) <= declared


@pytest.mark.spec("image-generation:manifest:tracked-flows-are-gate-checked")
def test_every_model_a_flows_graph_needs_is_declared_by_that_flow() -> None:
    # Everything the graph names *and* everything its nodes fetch while naming
    # nothing. The gate is where an unpinned artifact is caught, so the list
    # being complete is what the check is worth (design.md D15).
    from isekai.provision import (
        annotator_files,
        graph_model_files,
        load_manifest,
        manifest_dest,
        self_fetched_model_files,
        unclassified_node_classes,
    )

    manifest = load_manifest()
    for name in tracked_flows():
        flow = load_flow(name)
        graph = flow.graph()
        assert unclassified_node_classes(graph) == []
        needed = (
            graph_model_files(graph)
            + self_fetched_model_files(graph)
            + annotator_files(graph)
        )
        assert needed
        for filename in needed:
            dest = manifest_dest(filename, manifest)
            assert dest is not None, filename
            assert dest in flow.models, filename


# --- refusals -----------------------------------------------------------------


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
@pytest.mark.parametrize("field", REQUIRED)
def test_a_manifest_missing_a_declared_field_is_refused_naming_it(
    tmp_path: Path, field: str
) -> None:
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-v1" / MANIFEST_NAME).read_text())
    del document[field]
    (root / "summon-v1" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert field in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_manifest_missing_a_prompt_fragment_is_refused_naming_it(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-v1" / MANIFEST_NAME).read_text())
    del document["prompt"]["trailer"]
    (root / "summon-v1" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert "trailer" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_refusing_a_manifest_does_not_require_the_flow_to_be_executed(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path, graph="nowhere.json")

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert "nowhere.json" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_manifest_from_an_unknown_version_is_refused(tmp_path: Path) -> None:
    root = _scratch(tmp_path, schema_version=FLOW_SCHEMA_VERSION + 1)

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert str(FLOW_SCHEMA_VERSION + 1) in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_manifest_that_calls_itself_something_else_is_refused(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path, flow="summon-v2")

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert "summon-v2" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_flow_that_does_not_exist_is_refused_naming_the_ones_that_do(
    tmp_path: Path,
) -> None:
    with pytest.raises(Refusal) as refused:
        load_flow("summon-v9")

    assert "summon-v1" in str(refused.value)


# --- immutability -------------------------------------------------------------


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
@pytest.mark.parametrize("name", sorted(PINNED))
def test_every_tracked_flow_matches_its_committed_digest(name: str) -> None:
    assert manifest_digest(name) == PINNED[name], (
        f"flow {name} has changed. A changed dial, prompt fragment or graph does "
        "not edit a flow -- it means a new flow identifier. Add the new flow "
        "rather than updating this digest."
    )


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
def test_every_tracked_flow_is_pinned_at_all() -> None:
    assert sorted(PINNED) == tracked_flows()


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
def test_editing_a_dial_in_a_scratch_copy_changes_the_digest(tmp_path: Path) -> None:
    root = _scratch(tmp_path)
    assert manifest_digest("summon-v1", root) == PINNED["summon-v1"]

    document = json.loads((root / "summon-v1" / MANIFEST_NAME).read_text())
    document["dials"]["cfg"] = 6
    (root / "summon-v1" / MANIFEST_NAME).write_text(
        json.dumps(document, indent=2) + "\n"
    )

    assert manifest_digest("summon-v1", root) != PINNED["summon-v1"]


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
def test_editing_the_graph_changes_the_digest_too(tmp_path: Path) -> None:
    root = _scratch(tmp_path)
    graph = json.loads((root / "summon-v1" / "graph.json").read_text())
    graph["10"]["inputs"]["steps"] = 30
    (root / "summon-v1" / "graph.json").write_text(json.dumps(graph, indent=2) + "\n")

    assert manifest_digest("summon-v1", root) != PINNED["summon-v1"]


# --- assembly -----------------------------------------------------------------


@pytest.mark.spec("image-generation:assembly:prompt-comes-from-sheet-and-dials")
def test_a_prompt_is_the_flows_fragments_and_the_sheets_fields_in_schema_order(
    flow: Flow,
) -> None:
    schema = load_schema()
    fields = {name: [] for name in schema.names}
    fields["count"] = ["1girl", "solo"]
    fields["hair_colour"] = ["brown hair"]
    fields["background"] = ["indoors"]

    positive, negative = assemble(fields, schema.names, flow)

    assert positive == (
        "masterpiece, best quality, amazing quality, newest, "
        "1girl, solo, brown hair, indoors, "
        "anime screencap, detailed eyes, soft lighting"
    )
    assert negative == flow.prompt["negative"]


@pytest.mark.spec("image-generation:assembly:prompt-comes-from-sheet-and-dials")
def test_no_text_is_taken_from_the_graphs_own_committed_strings(flow: Flow) -> None:
    schema = load_schema()
    graph = flow.graph()
    committed = graph[flow.node("positive")]["inputs"]["text"]
    committed_negative = graph[flow.node("negative")]["inputs"]["text"]

    positive, negative = assemble(
        {name: [] for name in schema.names}, schema.names, flow
    )

    assert committed not in positive
    assert negative != committed_negative
    assert "worst detail" in committed_negative
    assert "worst detail" not in negative


@pytest.mark.spec("image-generation:assembly:prompt-comes-from-sheet-and-dials")
def test_the_fields_appear_in_the_order_the_schema_declares(flow: Flow) -> None:
    schema = load_schema()
    fields = {name: [f"tag-{i}"] for i, name in enumerate(schema.names)}

    positive, _ = assemble(fields, schema.names, flow)

    order = [positive.index(f"tag-{i}") for i in range(len(schema.names))]
    assert order == sorted(order)

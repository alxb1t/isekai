"""The flow manifest: what it declares, what it refuses, and that it cannot drift.

The immutability test is the load-bearing one. An output's path identifies a
configuration only if a flow identifier never silently means something else, so a
changed dial has to fail here rather than change what an existing identifier
renders.
"""

import json
from pathlib import Path

import pytest

import isekai
from isekai.foundation.flow import (
    GRAPH_NAME,
    KNOWN,
    MANIFEST_NAME,
    MANIFEST_VERSION,
    REQUIRED,
    REQUIRED_HOSTED,
    REQUIRED_NODES,
    SIBLINGS,
    TRANSFERRED_INPUTS,
    Flow,
    Hosted,
    assemble,
    load_flow,
    manifest_digest,
    tracked_flows,
)
from isekai.foundation.refusal import Refusal

# The digest of every tracked flow's whole directory, committed here.
#
# **Changing a dial does not edit a flow; it creates a new one.** A tuned dial is
# not a variant of a flow, it is an untested flow -- so editing `summon-v1` fails
# this test naming it, exactly as changing one of the graph's committed prompts is
# a deliberate test edit. Updating this constant to make a change pass is the
# wrong move; adding `summon-v2` is the right one.
#
# **Re-pinned once, by 0016-flow-registry, under the exception that change's
# design.md D2 records: the flow's configuration did not change; its manifest's
# format did.** The schema and both briefings folded into the directory, so the
# digest now covers five files rather than two, and `manifest_version: 2` is that
# distinction in data. The failure message below gains no "unless" clause -- a
# test message that explains how to evade itself is one that gets evaded.
PINNED: dict[str, str] = {
    "summon-v1": "1d3c206b394d78d8547f808fb0f2a969f030f9a51468c950e2f235a2d2cfc3a5",
    # Added by 0017-conjure, the second flow. Adding a line here is the designed
    # cost of adding a flow, not a defect the change found: the pin list is what
    # makes adding or removing one a deliberate act.
    #
    # Re-pinned once within that same change, by converge round 1, when review
    # finding R1 showed both briefings eliciting skin tone and brow lightness in
    # words the vocabulary routes to `light` and `dark` -- a light source and a
    # dark image -- rather than to `pale skin` and nothing. The exception is that
    # the flow was still inside the change that introduces it and had never been
    # released: `v0.17` was not tagged, so no pinned digest had left the branch.
    # Once it has, this route is closed and the correction is `conjure-v2`.
    "conjure-v1": "260ea7a343166d60976bf0e77175eb01f3d85294d2e1db897243f9dac22e0116",
    # Added by 0019-open-models, the third flow and the first to declare a
    # `hosted` block. Its graph and schema are byte-identical copies of
    # `summon-v1`'s and its manifest differs from that one in exactly two places
    # -- the identifier and the block -- so what this digest freezes that the
    # incumbent's does not is the two briefings, which are authored rather than
    # ported: the prompt that produced the measured captions is gitignored and
    # was never on this branch.
    "summon-open-v1": (
        "e035d227dbaee2b935502a392bbd096876379cc5201ca17ed7c0e87ed4bafcc1"
    ),
}


@pytest.fixture
def flow() -> Flow:
    """Return the one tracked flow."""
    return load_flow("summon-v1")


def _scratch(tmp_path: Path, **overrides: object) -> Path:
    """Copy `summon-v1` into a scratch flows root, with the given fields changed.

    **All five files, not two.** The digest covers the whole directory, so a
    scratch carrying only the manifest and the graph would make the assertion that
    it matches `PINNED` accidentally true of a different set of bytes.
    """
    root = tmp_path / "flows" / "summon-v1"
    root.mkdir(parents=True)
    source = load_flow("summon-v1").path
    document = json.loads((source / MANIFEST_NAME).read_text())
    document.update(overrides)
    (root / MANIFEST_NAME).write_text(json.dumps(document, indent=2) + "\n")
    for name in SIBLINGS:
        (root / name).write_bytes((source / name).read_bytes())
    return tmp_path / "flows"


# --- what a manifest declares -------------------------------------------------


@pytest.mark.spec("image-generation:manifest:flow-declares-its-inputs")
def test_a_flow_declares_its_inputs_vocabulary_models_and_dials(flow: Flow) -> None:
    assert flow.inputs == ("photo", "sheet")
    assert set(flow.vocabulary) == {"name", "revision", "sha256"}
    assert {model.dest for model in flow.models}
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
    assert document["nodes"] == dict(flow.nodes)
    assert document["models"] == [
        {"dest": model.dest, "sha256": model.sha256} for model in flow.models
    ]


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
    assert tracked_flows()
    for name in tracked_flows():
        assert load_flow(name).id == name


@pytest.mark.spec("image-generation:manifest:tracked-flows-are-gate-checked")
def test_the_schema_briefings_and_graph_each_flow_needs_are_in_its_directory() -> None:
    vocabulary = json.loads(
        (
            Path(__file__).resolve().parent.parent / "scripts" / "vocabulary.json"
        ).read_text()
    )["entries"][0]

    for name in tracked_flows():
        flow = load_flow(name)
        for path in (
            flow.graph_path,
            flow.schema_path,
            flow.caption_briefing_path,
            flow.sheet_briefing_path,
        ):
            assert path.is_file(), path
            assert path.parent == flow.path
        assert flow.schema.names
        assert flow.vocabulary["name"] == vocabulary["dest"]
        assert flow.vocabulary["sha256"] == vocabulary["sha256"]
        assert flow.vocabulary["revision"] in vocabulary["sources"][0]


@pytest.mark.spec("image-generation:manifest:flow-is-five-flat-files")
def test_a_flow_is_five_flat_files_and_the_manifest_names_none_of_them() -> None:
    for name in tracked_flows():
        flow = load_flow(name)
        document = json.loads((flow.path / MANIFEST_NAME).read_text())

        assert sorted(path.name for path in flow.path.iterdir()) == sorted(
            (MANIFEST_NAME, *SIBLINGS)
        )
        assert [path for path in flow.path.iterdir() if path.is_dir()] == []
        stated = json.dumps(document)
        for filename in (MANIFEST_NAME, *SIBLINGS):
            assert filename not in stated, filename


@pytest.mark.spec("image-generation:manifest:manifest-declares-its-format-version")
def test_the_manifest_declares_the_version_of_its_own_format(flow: Flow) -> None:
    document = json.loads((flow.path / MANIFEST_NAME).read_text())

    assert document["manifest_version"] == MANIFEST_VERSION


@pytest.mark.spec("image-generation:manifest:tracked-flows-are-gate-checked")
def test_every_model_a_flow_declares_has_a_manifest_entry() -> None:
    from isekai.boundary.provision import load_manifest

    declared = {entry["dest"] for entry in load_manifest()["entries"]}
    for name in tracked_flows():
        assert {model.dest for model in load_flow(name).models} <= declared


def _manifest_digests() -> dict[str, str]:
    """Return the provisioning manifest's destination-to-digest map."""
    from isekai.boundary.provision import load_manifest

    return {entry["dest"]: entry["sha256"] for entry in load_manifest()["entries"]}


@pytest.mark.spec("image-generation:manifest:flow-pins-its-models-by-digest")
def test_every_model_a_flow_declares_carries_the_manifests_digest_for_it() -> None:
    # A destination path does not pin bytes. Re-pinning a checkpoint would
    # otherwise make an existing flow identifier render differently with the gate
    # green, on the 6.9 GB that decides what the image looks like (design.md D4).
    digests = _manifest_digests()
    for name in tracked_flows():
        flow = load_flow(name)
        assert flow.models
        for model in flow.models:
            assert model.sha256 == digests[model.dest], (
                f"flow {name} pins {model.dest} to bytes the provisioning "
                "manifest does not declare for it"
            )


@pytest.mark.spec("image-generation:manifest:flow-pins-its-models-by-digest")
def test_a_flow_whose_model_digest_disagrees_fails_naming_the_flow(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-v1" / MANIFEST_NAME).read_text())
    document["models"][0]["sha256"] = "0" * 64
    (root / "summon-v1" / MANIFEST_NAME).write_text(json.dumps(document))
    digests = _manifest_digests()

    flow = load_flow("summon-v1", root)
    wrong = [model.dest for model in flow.models if model.sha256 != digests[model.dest]]

    assert wrong == [flow.models[0].dest]


@pytest.mark.spec("image-generation:manifest:tracked-flows-are-gate-checked")
def test_every_model_a_flows_graph_needs_is_declared_by_that_flow() -> None:
    # Everything the graph names *and* everything its nodes fetch while naming
    # nothing. The gate is where an unpinned artifact is caught, so the list
    # being complete is what the check is worth (design.md D15).
    from isekai.boundary.provision import (
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
        pinned = {model.dest for model in flow.models}
        for filename in needed:
            dest = manifest_dest(filename, manifest)
            assert dest is not None, filename
            assert dest in pinned, filename


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


@pytest.mark.spec("image-generation:roles:a-missing-required-role-is-refused-offline")
@pytest.mark.parametrize("role", REQUIRED_NODES)
def test_a_flow_declaring_fewer_than_the_required_nodes_is_refused(
    tmp_path: Path, role: str
) -> None:
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-v1" / MANIFEST_NAME).read_text())
    del document["nodes"][role]
    (root / "summon-v1" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert role in str(refused.value)


@pytest.mark.spec("image-generation:roles:transferred-input-and-node-must-agree")
@pytest.mark.parametrize("key", ["inputs", "nodes"])
def test_a_flow_declaring_a_photograph_on_one_side_only_is_refused(
    tmp_path: Path, key: str
) -> None:
    # Declared under `nodes` alone, the photograph is never uploaded and the
    # `LoadImage` node keeps the filename committed inside `graph.json` -- a
    # render of whoever that file names. Declared under `inputs` alone, it is
    # uploaded and read nowhere. Both are refused here, off any endpoint.
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-v1" / MANIFEST_NAME).read_text())
    if key == "inputs":
        document["inputs"] = [name for name in document["inputs"] if name != "photo"]
    else:
        del document["nodes"]["photo"]
    (root / "summon-v1" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert "summon-v1" in str(refused.value)
    assert f"`{key}` declares no 'photo'" in str(refused.value)


@pytest.mark.spec("image-generation:roles:transferred-input-and-node-must-agree")
def test_the_tracked_flow_declares_its_photograph_on_both_sides(flow: Flow) -> None:
    assert TRANSFERRED_INPUTS == ("photo",)
    for name in TRANSFERRED_INPUTS:
        assert (name in flow.inputs) == (name in flow.nodes)


@pytest.mark.spec("image-generation:roles:a-missing-required-role-is-refused-offline")
def test_the_required_roles_are_the_four_every_image_flow_has(flow: Flow) -> None:
    assert REQUIRED_NODES == ("positive", "negative", "latent", "sampler")
    assert set(REQUIRED_NODES) <= set(flow.nodes)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
@pytest.mark.parametrize("sibling", SIBLINGS)
def test_a_flow_missing_one_of_its_five_files_is_refused_naming_it(
    tmp_path: Path, sibling: str
) -> None:
    root = _scratch(tmp_path)
    (root / "summon-v1" / sibling).unlink()

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert sibling in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_refusing_a_manifest_does_not_require_the_flow_to_be_executed(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path)
    (root / "summon-v1" / GRAPH_NAME).unlink()

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert GRAPH_NAME in str(refused.value)


@pytest.mark.spec("image-generation:manifest:manifest-declares-its-format-version")
def test_a_manifest_from_an_unknown_version_is_refused(tmp_path: Path) -> None:
    root = _scratch(tmp_path, manifest_version=MANIFEST_VERSION + 1)

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    message = str(refused.value)
    assert str(MANIFEST_VERSION + 1) in message
    assert "upgrade isekai" in message


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
    graph = json.loads((root / "summon-v1" / GRAPH_NAME).read_text())
    graph["10"]["inputs"]["steps"] = 30
    (root / "summon-v1" / GRAPH_NAME).write_text(json.dumps(graph, indent=2) + "\n")

    assert manifest_digest("summon-v1", root) != PINNED["summon-v1"]


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
@pytest.mark.parametrize("sibling", SIBLINGS)
def test_editing_any_of_the_five_files_changes_the_digest(
    tmp_path: Path, sibling: str
) -> None:
    root = _scratch(tmp_path)
    assert manifest_digest("summon-v1", root) == PINNED["summon-v1"]

    path = root / "summon-v1" / sibling
    path.write_bytes(path.read_bytes() + b"\n")

    assert manifest_digest("summon-v1", root) != PINNED["summon-v1"]


@pytest.mark.spec("image-generation:immutability:a-new-file-moves-the-digest")
def test_adding_a_new_file_to_a_flow_moves_its_digest(tmp_path: Path) -> None:
    # The property the fold rests on: the freeze covers the directory, not a
    # named pair. A sixth declared value has to move the digest, or holding the
    # schema and the briefings inside the flow means less than its own sentence.
    root = _scratch(tmp_path)
    assert manifest_digest("summon-v1", root) == PINNED["summon-v1"]

    (root / "summon-v1" / "extra.briefing.md").write_text("a sixth declared value\n")

    assert manifest_digest("summon-v1", root) != PINNED["summon-v1"]


# --- assembly -----------------------------------------------------------------


@pytest.mark.spec("image-generation:assembly:prompt-comes-from-sheet-and-dials")
def test_a_prompt_is_the_flows_fragments_and_the_sheets_fields_in_schema_order(
    flow: Flow,
) -> None:
    schema = flow.schema
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
    schema = flow.schema
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
    schema = flow.schema
    fields = {name: [f"tag-{i}"] for i, name in enumerate(schema.names)}

    positive, _ = assemble(fields, schema.names, flow)

    order = [positive.index(f"tag-{i}") for i in range(len(schema.names))]
    assert order == sorted(order)


# --- the hosted-model block, and the allowlist --------------------------------


@pytest.mark.spec("image-generation:hosted:flow-declares-its-hosted-models")
def test_a_flow_declaring_hosted_models_is_loaded_with_them(tmp_path: Path) -> None:
    root = _scratch(
        tmp_path,
        hosted={
            "implementation": "ollama",
            "reader": "a-reader",
            "sorter": "a-sorter",
        },
    )

    hosted = load_flow("summon-v1", root).hosted

    assert hosted == Hosted(
        implementation="ollama", reader="a-reader", sorter="a-sorter"
    )


@pytest.mark.spec("image-generation:hosted:flow-declares-its-hosted-models")
def test_no_value_in_a_hosted_block_is_derived_at_load_time(tmp_path: Path) -> None:
    """The block is read verbatim: what comes back is what the document said.

    The same property the manifest as a whole has, asserted of the one key this
    change adds. A derived value here would be a second place the implementation
    a flow runs on is decided, and the registry is the first.
    """
    declared = {"implementation": "x", "reader": "y", "sorter": "z"}
    root = _scratch(tmp_path, hosted=dict(declared))

    hosted = load_flow("summon-v1", root).hosted

    assert hosted is not None
    assert vars(hosted) == declared


@pytest.mark.spec("image-generation:hosted:absent-block-means-the-default")
def test_a_flow_declaring_no_hosted_block_reports_none(tmp_path: Path) -> None:
    root = _scratch(tmp_path)

    assert load_flow("summon-v1", root).hosted is None


@pytest.mark.spec("image-generation:hosted:absent-block-means-the-default")
def test_the_incumbent_flows_declare_no_hosted_block_and_load(
    flow: Flow,
) -> None:
    """Omitting the key is not refused -- which is what leaves both incumbents alone.

    Asserted against the flows that actually ship rather than a scratch copy,
    because "the version that adds this key edits no existing manifest" is a
    claim about the tracked directories.
    """
    assert flow.hosted is None
    assert load_flow("conjure-v1").hosted is None


@pytest.mark.spec("image-generation:manifest:unknown-key-is-refused")
def test_an_unrecognised_manifest_key_is_refused_naming_it(tmp_path: Path) -> None:
    root = _scratch(tmp_path, quality="high")

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert "quality" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:unknown-key-is-refused")
def test_refusing_an_unknown_key_does_not_require_the_flow_to_be_executed(
    tmp_path: Path,
) -> None:
    """The graph is gone and the refusal still fires, so nothing read it.

    The same shape as the sibling-file test above: an unknown key is caught by
    reading the manifest, not by running the flow that carries it.
    """
    root = _scratch(tmp_path, quality="high")
    (root / "summon-v1" / GRAPH_NAME).unlink()

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert "quality" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:misspelled-hosted-block-is-refused")
@pytest.mark.parametrize("typo", ["hostd", "Hosted", "host", "hosted_models"])
def test_a_misspelled_hosted_block_is_refused_rather_than_ignored(
    tmp_path: Path, typo: str
) -> None:
    """The silent path this allowlist exists to close.

    Absent means the default implementation, so without the allowlist a typo is
    indistinguishable from a deliberate omission and the flow runs the wrong
    models with a complete, correct-looking run to show for it.
    """
    root = _scratch(
        tmp_path,
        **{typo: {"implementation": "ollama", "reader": "r", "sorter": "s"}},
    )

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert typo in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
@pytest.mark.parametrize("absent", REQUIRED_HOSTED)
def test_a_hosted_block_missing_one_of_its_three_keys_is_refused(
    tmp_path: Path, absent: str
) -> None:
    """A declared block declares all three, or it is named rather than crashing.

    The shape `prompt`'s fragments are already checked in: an absent key here
    would otherwise reach the registry as a `KeyError` three frames later.
    """
    block = {"implementation": "ollama", "reader": "r", "sorter": "s"}
    del block[absent]
    root = _scratch(tmp_path, hosted=block)

    with pytest.raises(Refusal) as refused:
        load_flow("summon-v1", root)

    assert absent in str(refused.value)


@pytest.mark.spec("image-generation:hosted:incumbent-flows-are-unchanged")
def test_the_manifest_format_version_is_unchanged_by_the_optional_key() -> None:
    """Optional is what keeps this at 2, and 2 is what keeps the digests still.

    A required key plus a version bump was this change's first shape: it would
    have re-cut two frozen manifests to record a value that was already implied.
    """
    assert MANIFEST_VERSION == 2
    assert "hosted" in KNOWN
    assert "hosted" not in REQUIRED


@pytest.mark.spec("image-generation:hosted:flow-declares-its-hosted-models")
def test_the_open_flow_declares_the_implementation_it_is_meant_to_run() -> None:
    """The last hole, and the only thing that closes it.

    An absent `hosted` block means the default implementation, deliberately -- it
    is what keeps both incumbent manifests unedited. So the allowlist cannot
    refuse an omission, `manifest_digest` freezes bytes without knowing whether
    they are the right ones, and **the first commit is exactly where this mistake
    lives**. One assertion on the shipped flow is what costs (design.md D12).
    """
    hosted = load_flow("summon-open-v1").hosted

    assert hosted is not None
    assert hosted.implementation == "ollama"
    assert hosted.reader == "joycaption-beta-one-q4k"
    assert hosted.sorter == "qwen3:8b"


@pytest.mark.spec("image-generation:hosted:an-unread-key-is-carried")
def test_the_sorter_key_is_carried_dead_and_has_not_moved_the_digest() -> None:
    """A key no stage reads, and the reason it is still in the manifest.

    Stage (2) calls no hosted model after v0.21, so `hosted.sorter` is read by
    nothing -- and removing it would move `summon-open-v1`'s manifest digest,
    which `CLAUDE.md` makes a **new flow** rather than an edit. Both halves are
    asserted in one body because the scenario is the pair: the key loads, and
    the digest is the one it had before the stage stopped reading it.
    """
    package = Path(isekai.__file__).parent
    readers = sorted(
        str(module.relative_to(package))
        for module in package.rglob("*.py")
        if ".sorter" in module.read_text()
    )

    hosted = load_flow("summon-open-v1").hosted

    assert hosted is not None
    assert hosted.sorter == "qwen3:8b"
    assert "sorter" in REQUIRED_HOSTED
    assert readers == []
    assert manifest_digest("summon-open-v1") == PINNED["summon-open-v1"]


@pytest.mark.spec("image-generation:hosted:incumbent-flows-are-unchanged")
def test_the_open_flows_graph_and_schema_are_the_incumbents_byte_for_byte() -> None:
    """A copied flow, so what differs is the manifest and the two briefings only."""
    incumbent, open_flow = load_flow("summon-v1"), load_flow("summon-open-v1")

    for name in (GRAPH_NAME, "schema.json"):
        assert (open_flow.path / name).read_bytes() == (
            incumbent.path / name
        ).read_bytes()


@pytest.mark.spec("caption:inputs:only-the-photograph-is-passed")
def test_the_open_caption_briefing_licenses_absence_verbatim() -> None:
    """Licensing absence is the single largest measured gain in this pipeline.

    It is what stopped a reader confabulating nineteen identity marks across seven
    of ten subjects and dropping its score from 0.518 to 0.307, and it is carried
    byte for byte rather than paraphrased because a paraphrase is an untested
    briefing wearing a tested one's reasoning.
    """
    incumbent = load_flow("summon-v1").caption_briefing_path.read_text()
    start = incumbent.index("**Say so when something is not visible")
    licence = incumbent[start : incumbent.index("\n\n", start)]

    assert licence in load_flow("summon-open-v1").caption_briefing_path.read_text()


@pytest.mark.spec("sheet:schema:schema-is-read-from-the-flow")
def test_the_open_sheet_briefing_names_every_one_of_the_sixteen_fields() -> None:
    flow = load_flow("summon-open-v1")
    text = flow.sheet_briefing_path.read_text()

    assert [name for name in flow.schema.names if f"`{name}`" not in text] == []

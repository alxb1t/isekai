"""The flow manifest: what it declares, what it refuses, and that it cannot drift.

The immutability test is the load-bearing one. An output's path identifies a
configuration only if a flow identifier never silently means something else, so a
changed dial has to fail here rather than change what an existing identifier
renders.
"""

import json
from pathlib import Path

import pytest

from isekai.foundation.flow import (
    CAPTION_BRIEFING_NAME,
    GRAPH_NAME,
    KNOWN,
    MANIFEST_NAME,
    MANIFEST_VERSION,
    REQUIRED,
    REQUIRED_NODES,
    ROLE_DIALS,
    SAMPLER_DIALS,
    SCHEMA_NAME,
    SIBLINGS,
    TRANSFERRED_INPUTS,
    Flow,
    assemble,
    load_flow,
    manifest_digest,
    tracked_flows,
)
from isekai.foundation.refusal import Refusal

# The digest of every tracked flow's whole directory, committed here.
#
# **Changing a dial does not edit a flow; it creates a new one.** A tuned dial is
# not a variant of a flow, it is an untested flow -- so editing a flow fails
# this test naming it, exactly as changing one of the graph's committed prompts is
# a deliberate test edit. Updating this constant to make a change pass is the
# wrong move; adding a flow under a new identifier is the right one.
#
# **Re-pinned once, by 0016-flow-registry, under the exception that change's
# design.md D2 records: the flow's configuration did not change; its manifest's
# format did.** The schema and both briefings folded into the directory, so the
# digest now covers five files rather than two, and `manifest_version: 2` is that
# distinction in data. The failure message below gains no "unless" clause -- a
# test message that explains how to evade itself is one that gets evaded.
# **Rewritten whole by 0022-one-arm, and that is a flow-set replacement rather
# than a re-pin.** The exception recorded below -- a flow still inside the change
# that introduces it, never released -- is *not* what is being used here. The
# three flows this list used to hold were deleted: two of them selected the
# `claude` arm by declaring no `hosted` block and could not survive its removal,
# and the third lost `sheet.briefing.md`, which moves a digest and so makes a new
# flow rather than an edited one. Nothing was re-pinned; three identifiers went
# and two arrived.
PINNED: dict[str, str] = {
    # `conjure-v1`'s graph and schema, byte for byte, including all 21 fields --
    # `eyelashes` among them. Its caption briefing is a byte-identical copy of
    # `summon-anime-wai`'s: both flows read the same model for the same purpose,
    # and a second authored briefing would be a second untested artifact.
    "conjure-anime-wai": (
        "1e991c2be7290a40dbe3301619c67b0bb9c5bb9914f22e6c54ce7078903c6615"
    ),
    # `summon-open-v1`'s graph, schema and caption briefing, byte for byte. What
    # moved is the manifest -- the identifier, `manifest_version` 3, and the
    # `hosted` block flattened to one required top-level `model` -- and the
    # deletion of `sheet.briefing.md`, which has had no reader since v0.21.
    "summon-anime-wai": (
        "8ddd4016dadd16d2b8a740e420e9478ae37ef5b43959c4e86ec1974f5d0792fb"
    ),
}


@pytest.fixture
def flow() -> Flow:
    """Return the identity flow."""
    return load_flow("summon-anime-wai")


def _scratch(tmp_path: Path, **overrides: object) -> Path:
    """Copy `summon-anime-wai` into a scratch flows root, with fields changed.

    **Every file, not two.** The digest covers the whole directory, so a scratch
    carrying only the manifest and the graph would make the assertion that it
    matches `PINNED` accidentally true of a different set of bytes.
    """
    root = tmp_path / "flows" / "summon-anime-wai"
    root.mkdir(parents=True)
    source = load_flow("summon-anime-wai").path
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
        ):
            assert path.is_file(), path
            assert path.parent == flow.path
        assert flow.schema.names
        assert flow.vocabulary["name"] == vocabulary["dest"]
        assert flow.vocabulary["sha256"] == vocabulary["sha256"]
        assert flow.vocabulary["revision"] in vocabulary["sources"][0]


@pytest.mark.spec("image-generation:manifest:a-flow-is-flat-and-its-files-are-named")
def test_a_flow_is_flat_and_holds_its_named_files_and_nothing_else() -> None:
    """The rule names its files rather than tallying them, and asserts both ends.

    **`len(SIBLINGS)` is the assertion this rule has never had.** The set-equality
    below shrinks on both sides at once -- it stayed green through the removal of
    `sheet.briefing.md` and would stay green through the silent addition of a
    sixth sibling, which is exactly the thing the freeze exists to make loud. The
    count is pinned here, and only here, so the prose elsewhere can stop carrying
    a numeral (design.md D10).
    """
    assert len(SIBLINGS) == 3
    assert SIBLINGS == (GRAPH_NAME, SCHEMA_NAME, CAPTION_BRIEFING_NAME)

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
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    document["models"][0]["sha256"] = "0" * 64
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))
    digests = _manifest_digests()

    flow = load_flow("summon-anime-wai", root)
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
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    del document[field]
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert field in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_manifest_missing_a_prompt_fragment_is_refused_naming_it(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    del document["prompt"]["trailer"]
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "trailer" in str(refused.value)


@pytest.mark.spec("image-generation:roles:a-missing-required-role-is-refused-offline")
@pytest.mark.parametrize("role", REQUIRED_NODES)
def test_a_flow_declaring_fewer_than_the_required_nodes_is_refused(
    tmp_path: Path, role: str
) -> None:
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    del document["nodes"][role]
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert role in str(refused.value)


# --- what a role costs, and where its node has to be --------------------------


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
@pytest.mark.parametrize("dial", sorted(set(SAMPLER_DIALS)))
def test_a_manifest_missing_a_dial_its_own_roles_read_is_refused_naming_it(
    tmp_path: Path, dial: str
) -> None:
    """A manifest with an incomplete `dials` block used to load clean.

    It then passed all six gate commands, rented the pod, uploaded the
    photograph, and raised a bare `KeyError` out of `patch()` -- not a `Refusal`,
    so `across` never collected it and the rest of the batch died with it
    (v0.16 R8).
    """
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    del document["dials"][dial]
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert dial in str(refused.value)
    assert "`dials` declares no" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_dial_no_declared_role_reads_is_not_required(tmp_path: Path) -> None:
    """Role-conditional, never a flat list (design.md D4).

    A flat *every dial in a fixed list is present* check rejects
    `conjure-anime-wai`, which declares no identity adapter and no pose
    preprocessor and is correct. Asserted here on a scratch rather than only by
    the tracked flow below, so the property survives a change to either flow.
    """
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    document["inputs"] = [name for name in document["inputs"] if name != "photo"]
    for role in ("identity", "openpose", "photo"):
        del document["nodes"][role]
    for dial in ("ip_weight", "identity_cn_strength", "openpose_strength"):
        del document["dials"][dial]
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    loaded = load_flow("summon-anime-wai", root)

    assert "ip_weight" not in loaded.dials
    assert "identity" not in loaded.nodes


@pytest.mark.spec_exempt("behaviour; the scenario lands in 0024")
def test_a_role_naming_a_node_the_graph_does_not_carry_is_refused(
    tmp_path: Path,
) -> None:
    """Nothing locates a node by class, so a dangling id agrees with nothing.

    Until v0.22.1 it agreed with the gate too, right up to the rented machine
    (v0.17 R6).
    """
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    document["nodes"]["sampler"] = "9999"
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "sampler -> 9999" in str(refused.value)
    assert GRAPH_NAME in str(refused.value)


@pytest.mark.spec_exempt("behaviour; the scenario lands in 0024")
@pytest.mark.parametrize("name", tracked_flows())
def test_every_role_a_tracked_flow_names_resolves_in_its_own_graph(
    name: str,
) -> None:
    loaded = load_flow(name)
    committed = loaded.graph()

    assert loaded.nodes
    assert [role for role, node in loaded.nodes.items() if node not in committed] == []


@pytest.mark.spec_exempt("behaviour; the scenario lands in 0024")
@pytest.mark.parametrize("name", tracked_flows())
def test_every_dial_a_tracked_flow_declares_is_one_of_its_roles_reads(
    name: str,
) -> None:
    """Both directions, on both flows: nothing missing, and nothing spare.

    The refusal in `load_flow` only checks the first. This checks the second as
    a property of the flows that ship -- 12/12 for `summon-anime-wai` and 9/9
    for `conjure-anime-wai` -- so a dial added to `ROLE_DIALS` for a role
    nothing declares, or left in a manifest after its role went away, fails
    here rather than sitting unread.
    """
    loaded = load_flow(name)
    read = {
        dial
        for role, dials in ROLE_DIALS.items()
        if role in loaded.nodes
        for dial in dials
    }

    assert set(loaded.dials) == read


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
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    if key == "inputs":
        document["inputs"] = [name for name in document["inputs"] if name != "photo"]
    else:
        del document["nodes"]["photo"]
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "summon-anime-wai" in str(refused.value)
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
def test_a_flow_missing_one_of_its_named_files_is_refused_naming_it(
    tmp_path: Path, sibling: str
) -> None:
    root = _scratch(tmp_path)
    (root / "summon-anime-wai" / sibling).unlink()

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert sibling in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_refusing_a_manifest_does_not_require_the_flow_to_be_executed(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path)
    (root / "summon-anime-wai" / GRAPH_NAME).unlink()

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert GRAPH_NAME in str(refused.value)


@pytest.mark.spec("image-generation:manifest:manifest-declares-its-format-version")
def test_a_manifest_from_an_unknown_version_is_refused(tmp_path: Path) -> None:
    root = _scratch(tmp_path, manifest_version=MANIFEST_VERSION + 1)

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    message = str(refused.value)
    assert str(MANIFEST_VERSION + 1) in message
    assert "upgrade isekai" in message


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_manifest_that_calls_itself_something_else_is_refused(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path, flow="summon-anime-wai-2")

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "summon-anime-wai-2" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:invalid-manifest-names-the-field")
def test_a_flow_that_does_not_exist_is_refused_naming_the_ones_that_do(
    tmp_path: Path,
) -> None:
    with pytest.raises(Refusal) as refused:
        load_flow("summon-v9")

    assert "summon-anime-wai" in str(refused.value)


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
    assert manifest_digest("summon-anime-wai", root) == PINNED["summon-anime-wai"]

    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    document["dials"]["cfg"] = 6
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(
        json.dumps(document, indent=2) + "\n"
    )

    assert manifest_digest("summon-anime-wai", root) != PINNED["summon-anime-wai"]


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
def test_editing_the_graph_changes_the_digest_too(tmp_path: Path) -> None:
    root = _scratch(tmp_path)
    graph = json.loads((root / "summon-anime-wai" / GRAPH_NAME).read_text())
    graph["10"]["inputs"]["steps"] = 30
    (root / "summon-anime-wai" / GRAPH_NAME).write_text(
        json.dumps(graph, indent=2) + "\n"
    )

    assert manifest_digest("summon-anime-wai", root) != PINNED["summon-anime-wai"]


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
@pytest.mark.parametrize("sibling", SIBLINGS)
def test_editing_any_of_its_named_files_changes_the_digest(
    tmp_path: Path, sibling: str
) -> None:
    root = _scratch(tmp_path)
    assert manifest_digest("summon-anime-wai", root) == PINNED["summon-anime-wai"]

    path = root / "summon-anime-wai" / sibling
    path.write_bytes(path.read_bytes() + b"\n")

    assert manifest_digest("summon-anime-wai", root) != PINNED["summon-anime-wai"]


@pytest.mark.spec("image-generation:immutability:a-new-file-moves-the-digest")
def test_adding_a_new_file_to_a_flow_moves_its_digest(tmp_path: Path) -> None:
    # The property the fold rests on: the freeze covers the directory, not a
    # named pair. A further declared value has to move the digest, or holding the
    # schema and the briefing inside the flow means less than its own sentence.
    root = _scratch(tmp_path)
    assert manifest_digest("summon-anime-wai", root) == PINNED["summon-anime-wai"]

    (root / "summon-anime-wai" / "extra.briefing.md").write_text(
        "a further declared value\n"
    )

    assert manifest_digest("summon-anime-wai", root) != PINNED["summon-anime-wai"]


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


# --- the model key, and the allowlist -----------------------------------------


@pytest.mark.spec("image-generation:model:flow-declares-the-model-it-runs")
def test_a_flow_declaring_a_model_is_loaded_with_it(tmp_path: Path) -> None:
    """Read verbatim: what comes back is what the document said.

    The same property the manifest as a whole has, asserted of the key that
    replaced the `hosted` block. A derived value here would be a second place the
    model a flow runs on is decided, and the manifest is the first.
    """
    root = _scratch(tmp_path, model="a-reader")

    assert load_flow("summon-anime-wai", root).model == "a-reader"


@pytest.mark.spec("image-generation:model:flow-declares-the-model-it-runs")
def test_the_tracked_flows_each_declare_the_model_they_are_meant_to_run() -> None:
    """The last hole, and the only thing that closes it.

    `manifest_digest` freezes bytes without knowing whether they are the right
    ones, so a flow committed naming the wrong alias would be frozen naming the
    wrong alias. **The first commit is exactly where this mistake lives**, and one
    assertion on the shipped flows is what it costs (design.md D1).
    """
    for name in tracked_flows():
        assert load_flow(name).model == "joycaption-beta-one-q4k"


@pytest.mark.spec("image-generation:model:an-absent-model-is-refused")
def test_a_manifest_declaring_no_model_is_refused_naming_the_key(
    tmp_path: Path,
) -> None:
    """Required, not optional, and that is what carries `MANIFEST_VERSION` to 3.

    The key it replaced was optional so that adding it edited no frozen
    directory. That cost is no longer payable in either direction: the
    directories it was protecting are deleted by this change.
    """
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    del document["model"]
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "model" in str(refused.value)


@pytest.mark.spec("image-generation:model:an-empty-model-is-refused")
@pytest.mark.parametrize("value", [None, "", "   ", 3, [], {}])
def test_a_model_that_is_not_a_non_empty_string_is_refused(
    tmp_path: Path, value: object
) -> None:
    """The value, not only its presence.

    A bare `str()` loaded `{"model": null}` as the Python string `"None"` and sent
    a run at an alias that cannot exist -- a refusal at the first call, with the
    manifest looking correct the whole way there (design.md D4).
    """
    root = _scratch(tmp_path, model=value)

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "model" in str(refused.value)


@pytest.mark.spec("image-generation:manifest:unknown-key-is-refused")
def test_an_unrecognised_manifest_key_is_refused_naming_it(tmp_path: Path) -> None:
    root = _scratch(tmp_path, quality="high")

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

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
    (root / "summon-anime-wai" / GRAPH_NAME).unlink()

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "quality" in str(refused.value)


def _misspelled(tmp_path: Path, typo: str) -> Refusal:
    """Return the refusal from a manifest whose model key is written `typo`."""
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    document[typo] = document.pop("model")
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)
    return refused.value


@pytest.mark.spec("image-generation:manifest:a-misspelled-model-key-is-refused")
@pytest.mark.parametrize("typo", ["modl", "Model", "model_name"])
def test_a_misspelled_model_key_is_refused_naming_what_was_written(
    tmp_path: Path, typo: str
) -> None:
    """What flattening the block bought, and it cost no new check.

    The `hosted` block had no allowlist of its own -- `{"sortr": "x"}` inside it
    loaded clean -- and a top-level key is guarded by the allowlist that already
    existed. Each of these fails twice at once, as an unknown key *and* as a
    missing one, and the allowlist runs first so the message names the key the
    operator actually wrote rather than the one he did not (design.md D3).
    """
    assert typo not in KNOWN

    assert typo in str(_misspelled(tmp_path, typo))


@pytest.mark.spec("image-generation:manifest:a-misspelled-model-key-is-refused")
def test_a_typo_that_collides_with_a_real_key_is_refused_for_the_absence(
    tmp_path: Path,
) -> None:
    """`models` is the one near-miss the allowlist cannot see, and it is still caught.

    It is a real key -- the render weights -- so writing `model`'s value into it
    is not an unknown key at all. What the loader has left is the absence, and
    naming `model` is the correct diagnosis for this row: the operator did write
    a key this build reads, just not that one.
    """
    assert "models" in KNOWN

    assert "model" in str(_misspelled(tmp_path, "models"))


@pytest.mark.spec("image-generation:manifest:unknown-key-is-refused")
def test_every_key_this_build_reads_is_required() -> None:
    """There is no optional key, which is what leaves the allowlist doing it all.

    `hosted` was the one, and with it gone `KNOWN` and `REQUIRED` are the same
    tuple -- so a misspelling can no longer be indistinguishable from a
    deliberate omission, because there are no deliberate omissions.
    """
    assert MANIFEST_VERSION == 3
    assert KNOWN == REQUIRED
    assert "model" in REQUIRED

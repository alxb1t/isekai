"""The flow manifest: what it declares, what it refuses, and that it cannot drift.

The immutability test is the load-bearing one. An output's path identifies a
configuration only if a flow identifier never silently means something else, so a
changed dial has to fail here rather than change what an existing identifier
renders.
"""

import json
import shutil
from pathlib import Path
from typing import NamedTuple

import pytest

from isekai.boundary.provision import VOCABULARY_MANIFEST_PATH
from isekai.foundation.flow import (
    GRAPH_NAME,
    KNOWN,
    MANIFEST_NAME,
    MANIFEST_VERSION,
    REQUIRED,
    REQUIRED_NODES,
    SAMPLER_DIALS,
    SCHEMA_NAME,
    SIBLINGS,
    TRANSFERRED_INPUTS,
    Flow,
    assemble,
    dials_read,
    load_flow,
    manifest_digest,
    tracked_flows,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import PHOTO

# The digest of every tracked flow's whole directory, committed here.
#
# **The freeze's job is that nothing changes silently, not that nothing changes.**
# Editing any file in a flow fails the test below naming it, so the move can only
# happen in a change that says so and records what moved.
#
# **A divergence costs a new identifier.** Two flows are only comparable over one
# cohort if an identifier means one configuration, so a variant, another base or a
# second generation is a new flow, not a re-pin. Re-pinning is for the other case,
# where the old configuration is abandoned.
#
# The failure message below gains no "unless" clause -- a test message that
# explains how to evade itself is one that gets evaded.
PINNED: dict[str, str] = {
    "conjure-anime-wai": (
        "8123c38d701748d41e7dc6d9aea2af647c4fbcc24435c2a3c351860f36dc0180"
    ),
    "control-anime-wai": (
        "a5e41ce47810b0c9d087bae51255ac3c31500e1fd90e97248d9a356241720bcf"
    ),
    "summon-anime-wai": (
        "0b841d22d5d3e659541c1459d42fdf5281a7c6338a193a04189da199b8f83e47"
    ),
    "summon-flat-anime-wai": (
        "fa87fed5ff33e169ca94f82740716535679ff0990f0a676bdca9fee33380eec1"
    ),
    "summon-semireal-anime-wai": (
        "fbed851f8d9b049672cf73004457c5d4b7c4c1948a7935fc7fd9dbf9dc872b70"
    ),
    "summon-vivid-anime-wai": (
        "f72aa506e5668be9982515654b659e3760ac9e05c71a0d28e533e281468d006e"
    ),
}

# A control flow and the subject it is held equal to; a second control is one line.
CONTROLS: dict[str, str] = {"control-anime-wai": "summon-anime-wai"}


class Style(NamedTuple):
    """The subject a styled flow is held equal to, and the terms it appends."""

    subject: str
    trailer: str
    negative: str


# A styled flow and its style. An empty term adds nothing; a new look is one row.
FLAT = "summon-flat-anime-wai"
STYLED: dict[str, Style] = {
    FLAT: Style(
        "summon-anime-wai",
        "flat color, cel shading, anime coloring, colorful",
        "realistic, photorealistic, 3d, semi-realistic",
    ),
    "summon-semireal-anime-wai": Style("summon-anime-wai", "", ""),
    "summon-vivid-anime-wai": Style(
        "summon-anime-wai",
        "",
        "realistic, photorealistic, 3d, semi-realistic, "
        "monochrome, greyscale, muted color",
    ),
}

# The dials a control zeroes: the face chain, and nothing else.
FACE_DIALS = ("ip_weight", "identity_cn_strength")


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
    # configuration nothing measured.
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
def test_the_schema_and_graph_each_flow_needs_are_in_its_directory() -> None:
    vocabulary = json.loads(VOCABULARY_MANIFEST_PATH.read_text())["entries"][0]

    for name in tracked_flows():
        flow = load_flow(name)
        for path in (flow.graph_path, flow.schema_path):
            assert path.is_file(), path
            assert path.parent == flow.path
        assert flow.schema.names
        assert flow.vocabulary["name"] == vocabulary["dest"]
        assert flow.vocabulary["sha256"] == vocabulary["sha256"]
        assert flow.vocabulary["revision"] in vocabulary["sources"][0]


@pytest.mark.spec("image-generation:manifest:a-flow-is-flat-and-its-files-are-named")
def test_a_flow_is_flat_and_holds_its_named_files_and_nothing_else() -> None:
    """The rule names its files rather than tallying them, and asserts both ends.

    **`len(SIBLINGS)` is asserted as well as the set.** The set-equality below
    shrinks on both sides at once -- it would stay green through the removal of a
    sibling and through the silent addition of one, which is exactly the thing
    the freeze exists to make loud. The count is pinned here, and only here, so
    the prose elsewhere carries no numeral.
    """
    assert len(SIBLINGS) == 2
    assert SIBLINGS == (GRAPH_NAME, SCHEMA_NAME)

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
    # green, on the 6.9 GB that decides what the image looks like.
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
    # being complete is what the check is worth.
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
    """Unchecked, a manifest with an incomplete `dials` block would load clean.

    It would then pass the gate, rent the pod, upload the photograph, and raise a
    bare `KeyError` out of `patch()` -- not a `Refusal`, so `across` would never
    collect it and the rest of the batch would die with it.
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
    """Role-conditional, never a flat list.

    A flat *every dial in a fixed list is present* check rejects
    `conjure-anime-wai`, which declares no identity adapter and no pose
    preprocessor and is correct. Asserted here on a scratch rather than only by
    the tracked flows below, so the property survives a change to either of
    them.
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


@pytest.mark.spec("cli:manifest:a-dangling-node-id-is-refused-at-load")
def test_a_role_naming_a_node_the_graph_does_not_carry_is_refused(
    tmp_path: Path,
) -> None:
    """Nothing locates a node by class, so a dangling id agrees with nothing.

    Unchecked, it would agree with the gate too, right up to the rented machine.
    """
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    document["nodes"]["sampler"] = "9999"
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "sampler -> 9999" in str(refused.value)
    assert GRAPH_NAME in str(refused.value)


@pytest.mark.spec("cli:manifest:every-tracked-role-resolves")
@pytest.mark.parametrize("name", tracked_flows())
def test_every_role_a_tracked_flow_names_resolves_in_its_own_graph(
    name: str,
) -> None:
    loaded = load_flow(name)
    committed = loaded.graph()

    assert loaded.nodes
    assert [role for role, node in loaded.nodes.items() if node not in committed] == []


@pytest.mark.spec("cli:manifest:every-tracked-dial-is-read")
@pytest.mark.parametrize("name", tracked_flows())
def test_every_dial_a_tracked_flow_declares_is_one_of_its_roles_reads(
    name: str,
) -> None:
    """Both directions, on every flow: nothing missing, and nothing spare.

    The refusal in `load_flow` only checks the first. This checks the second as
    a property of the flows that ship -- 12/12 for `summon-anime-wai` and 9/9
    for `conjure-anime-wai` -- so a dial added to `ROLE_DIALS` for a role
    nothing declares, or left in a manifest after its role went away, fails
    here rather than sitting unread.
    """
    loaded = load_flow(name)

    assert set(loaded.dials) == dials_read(loaded.nodes)


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
    """`summon-anime-wai`, which is the only tracked flow that transfers one.

    Singular on purpose: `conjure-anime-wai` declares `inputs: ["sheet"]` and no
    `photo` node, so the property holds there vacuously and asserting it would
    advertise coverage the second flow does not give. The `flow` fixture is the
    identity flow and is not parametrized.
    """
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


@pytest.mark.spec("image-generation:immutability:a-re-pin-is-recorded")
def test_a_re_pin_leaves_a_record_a_later_reader_can_find() -> None:
    """Every committed digest appears in the changelog that moved it there.

    **Nothing on disk says which side of a re-pin a run falls on** -- a run's
    provenance records the graph digest, not the flow directory's -- so the only
    place a later reader learns that the bytes a run was produced from no longer
    exist is the prose of the change that moved it. `CHANGELOG.md` is that prose's
    home: a re-pinned flow's bullet names its new digest.

    **The digest is the witness, not the flow's name.** A name enters the
    changelog when the flow is introduced and stays there, so asserting it would
    pass for every re-pin that ever forgot to record itself. A digest is what a
    re-pin actually moves, so requiring each one to appear fires exactly when a
    digest changes and no entry says so.

    `CHANGELOG.md` is history and `PINNED` stays authoritative, so this makes no
    second source of truth: nothing reads a digest back out of the changelog.
    """
    changelog = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text()

    for name, digest in PINNED.items():
        assert digest in changelog, (
            f"flow {name} is pinned at {digest[:12]}... and no CHANGELOG.md entry "
            "carries that digest. A re-pin owes a statement of what moved, and a "
            "new flow a statement of what it is, in prose a later reader can find."
        )


@pytest.mark.spec("image-generation:immutability:flow-manifest-is-pinned-by-equality")
def test_every_tracked_flow_is_pinned_at_all() -> None:
    assert sorted(PINNED) == tracked_flows()


@pytest.mark.spec("run-directory:layout:photo-is-no-flow")
def test_no_tracked_flow_is_named_photo() -> None:
    assert PHOTO not in tracked_flows()


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
    # schema inside the flow means less than its own sentence.
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
def test_no_text_is_taken_from_the_graphs_own_committed_strings(
    tmp_path: Path,
) -> None:
    """Assembly ignores the graph's committed strings, proved against a witness.

    **Run on a scratch flow whose graph carries a distinctive negative**, not on
    the tracked one. The tracked graphs' negative node is empty, and asserting
    that emptiness against the tracked flow would be asserting the fixture --
    `negative != ""` holds for any non-empty prompt, so the leak this scenario
    exists to catch would have nothing to fail on. Planting a string the
    manifest cannot supply keeps a witness that can.
    """
    root = _scratch(tmp_path)
    scratch = root / "summon-anime-wai"
    flow = load_flow("summon-anime-wai", root)
    schema = flow.schema

    graph = json.loads((scratch / GRAPH_NAME).read_text())
    graph[flow.node("negative")]["inputs"]["text"] = "a string no manifest carries"
    (scratch / GRAPH_NAME).write_text(json.dumps(graph, indent=2) + "\n")

    flow = load_flow("summon-anime-wai", root)
    committed = flow.graph()[flow.node("positive")]["inputs"]["text"]
    committed_negative = flow.graph()[flow.node("negative")]["inputs"]["text"]

    positive, negative = assemble(
        {name: [] for name in schema.names}, schema.names, flow
    )

    assert committed not in positive
    assert committed_negative not in negative
    assert negative == flow.prompt["negative"]


@pytest.mark.spec("image-generation:assembly:prompt-comes-from-sheet-and-dials")
def test_every_tracked_flows_graph_carries_no_negative_of_its_own() -> None:
    # The other half, on the tracked flows: `flow.json`'s fragment is the only
    # negative there is. `generate.py` patches this node on every render, so a
    # string here would be dead data that reads like a second source of truth,
    # and would drift unnoticed.
    for name in tracked_flows():
        tracked = load_flow(name)
        node = tracked.graph()[tracked.node("negative")]["inputs"]["text"]
        assert node == "", f"{name}'s graph carries a negative of its own: {node!r}"


@pytest.mark.spec("image-generation:assembly:prompt-comes-from-sheet-and-dials")
def test_the_fields_appear_in_the_order_the_schema_declares(flow: Flow) -> None:
    schema = flow.schema
    fields = {name: [f"tag-{i}"] for i, name in enumerate(schema.names)}

    positive, _ = assemble(fields, schema.names, flow)

    order = [positive.index(f"tag-{i}") for i in range(len(schema.names))]
    assert order == sorted(order)


# --- the allowlist ------------------------------------------------------------


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
    """Return the refusal from a manifest whose tagger key is written `typo`."""
    root = _scratch(tmp_path)
    document = json.loads((root / "summon-anime-wai" / MANIFEST_NAME).read_text())
    document[typo] = document.pop("tagger")
    (root / "summon-anime-wai" / MANIFEST_NAME).write_text(json.dumps(document))

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)
    return refused.value


@pytest.mark.spec("image-generation:manifest:a-misspelled-key-is-refused")
@pytest.mark.parametrize("typo", ["taggr", "Tagger", "tagger_on"])
def test_a_misspelled_key_is_refused_naming_what_was_written(
    tmp_path: Path, typo: str
) -> None:
    """What a flat manifest buys, and it costs no new check.

    A nested block would need an allowlist of its own -- `{"sortr": "x"}` inside
    it would load clean -- and a top-level key is guarded by the allowlist that
    exists. Each of these fails twice at once, as an unknown key *and* as a
    missing one, and the allowlist runs first so the message names the key the
    operator actually wrote rather than the one he did not.
    """
    assert typo not in KNOWN

    assert typo in str(_misspelled(tmp_path, typo))


@pytest.mark.spec("image-generation:manifest:unknown-key-is-refused")
def test_every_key_this_build_reads_is_required() -> None:
    """There is no optional key, which is what leaves the allowlist doing it all.

    `KNOWN` and `REQUIRED` are the same tuple -- so a misspelling cannot be
    indistinguishable from a deliberate omission, because there are no
    deliberate omissions.
    """
    assert MANIFEST_VERSION == 5
    assert KNOWN == REQUIRED
    assert "model" not in REQUIRED
    assert "tagger" in REQUIRED


# --- the tagger key -----------------------------------------------------------


@pytest.mark.spec("image-generation:tagger:flow-declares-whether-it-is-tagged")
@pytest.mark.parametrize("value", [True, False])
def test_a_flow_is_loaded_with_the_tagger_value_it_declares(
    tmp_path: Path, value: bool
) -> None:
    root = _scratch(tmp_path, tagger=value)

    assert load_flow("summon-anime-wai", root).tagger is value


@pytest.mark.spec("image-generation:tagger:flow-declares-whether-it-is-tagged")
def test_the_tracked_flows_each_declare_the_tagger() -> None:
    for name in tracked_flows():
        document = json.loads((load_flow(name).path / MANIFEST_NAME).read_text())
        assert document["tagger"] is True
        assert load_flow(name).tagger is True


@pytest.mark.spec("image-generation:tagger:an-absent-declaration-is-refused")
def test_a_manifest_declaring_nothing_about_the_tagger_is_refused_naming_the_key(
    tmp_path: Path,
) -> None:
    root = _scratch(tmp_path)
    manifest = root / "summon-anime-wai" / MANIFEST_NAME
    document = json.loads(manifest.read_text())
    del document["tagger"]
    manifest.write_text(json.dumps(document))
    # Gone, so nothing past the manifest can have been read.
    (root / "summon-anime-wai" / GRAPH_NAME).unlink()

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "tagger" in str(refused.value)


@pytest.mark.spec("image-generation:tagger:a-non-boolean-declaration-is-refused")
@pytest.mark.parametrize("value", ["false", "true", 0, 1, None])
def test_a_tagger_that_is_not_a_boolean_is_refused_naming_the_key(
    tmp_path: Path, value: object
) -> None:
    root = _scratch(tmp_path, tagger=value)

    with pytest.raises(Refusal) as refused:
        load_flow("summon-anime-wai", root)

    assert "`tagger`" in str(refused.value)
    assert repr(value) in str(refused.value)


# --- a variant equals its subject ---------------------------------------------


def _pair(tmp_path: Path, variant: str, subject: str) -> tuple[Path, Path]:
    """Copy a tracked variant and its subject into a scratch root."""
    return (
        shutil.copytree(load_flow(variant).path, tmp_path / variant),
        shutil.copytree(load_flow(subject).path, tmp_path / "subject"),
    )


def _manifest_without(
    directory: Path, dials: tuple[str, ...] = (), prompt: tuple[str, ...] = ()
) -> dict:
    """Return a manifest without its name and the given dials and prompt keys."""
    document = json.loads((directory / MANIFEST_NAME).read_text())
    document.pop("flow")
    for dial in dials:
        document["dials"].pop(dial)
    for key in prompt:
        document["prompt"].pop(key)
    return document


# --- a control equals its subject ---------------------------------------------


def _control_differences(control_dir: Path, subject_dir: Path) -> list[str]:
    """Return the files separating a control from its subject beyond the face dials.

    e.g. `["graph.json"]`, or `["flow.json"]` when the manifests differ elsewhere.
    """
    differing = [
        name
        for name in SIBLINGS
        if (control_dir / name).read_bytes() != (subject_dir / name).read_bytes()
    ]
    if _manifest_without(control_dir, FACE_DIALS) != _manifest_without(
        subject_dir, FACE_DIALS
    ):
        differing.append(MANIFEST_NAME)
    return differing


@pytest.mark.spec("image-generation:control:files-equal-the-subject")
@pytest.mark.parametrize("control", sorted(CONTROLS))
def test_a_control_holds_the_subjects_graph_and_schema(control: str) -> None:
    differing = _control_differences(
        load_flow(control).path, load_flow(CONTROLS[control]).path
    )

    assert GRAPH_NAME not in differing
    assert SCHEMA_NAME not in differing


@pytest.mark.spec("image-generation:control:manifest-differs-only-in-the-face-dials")
@pytest.mark.parametrize("control", sorted(CONTROLS))
def test_a_control_manifest_differs_only_in_its_name_and_zeroed_face_dials(
    control: str,
) -> None:
    differing = _control_differences(
        load_flow(control).path, load_flow(CONTROLS[control]).path
    )

    assert MANIFEST_NAME not in differing
    assert [load_flow(control).dials[dial] for dial in FACE_DIALS] == [0, 0]


@pytest.mark.spec("image-generation:control:files-equal-the-subject")
def test_a_control_whose_graph_drifts_is_named(tmp_path: Path) -> None:
    control, subject = _pair(tmp_path, "control-anime-wai", "summon-anime-wai")
    assert _control_differences(control, subject) == []
    (control / GRAPH_NAME).write_text("{}\n")

    assert _control_differences(control, subject) == [GRAPH_NAME]


@pytest.mark.spec("image-generation:control:manifest-differs-only-in-the-face-dials")
def test_a_control_whose_manifest_differs_elsewhere_is_named(tmp_path: Path) -> None:
    control, subject = _pair(tmp_path, "control-anime-wai", "summon-anime-wai")
    document = json.loads((control / MANIFEST_NAME).read_text())
    document["dials"]["cfg"] = 99
    (control / MANIFEST_NAME).write_text(json.dumps(document, indent=2) + "\n")

    assert _control_differences(control, subject) == [MANIFEST_NAME]


# --- a styled flow equals its subject but for its style ------------------------


def _styled_differences(styled_dir: Path, subject_dir: Path) -> list[str]:
    """Return the files separating a styled flow from its subject beyond its style.

    The style is the identity node's `end_at`, `ip_weight`, the trailer and the
    negative. e.g. `["graph.json"]` when the graph differs anywhere else.
    """
    differing = [
        name
        for name in SIBLINGS
        if name != GRAPH_NAME
        and (styled_dir / name).read_bytes() != (subject_dir / name).read_bytes()
    ]
    style = {"dials": ("ip_weight",), "prompt": ("trailer", "negative")}
    manifest, subject_manifest = (
        _manifest_without(d, **style) for d in (styled_dir, subject_dir)
    )
    identity = subject_manifest["nodes"]["identity"]
    ours, theirs = (
        json.loads((d / GRAPH_NAME).read_text()) for d in (styled_dir, subject_dir)
    )
    ours[identity]["inputs"]["end_at"] = theirs[identity]["inputs"]["end_at"]
    if ours != theirs:
        differing.append(GRAPH_NAME)
    if manifest != subject_manifest:
        differing.append(MANIFEST_NAME)
    return differing


def _holds_the_subjects_schema(name: str, tmp_path: Path) -> None:
    ours, subject = _pair(tmp_path, name, STYLED[name].subject)
    assert _styled_differences(ours, subject) == []

    (ours / SCHEMA_NAME).write_text("{}\n")
    assert _styled_differences(ours, subject) == [SCHEMA_NAME]


def _graph_differs_only_in_the_face_chains_end(name: str, tmp_path: Path) -> None:
    ours, subject = _pair(tmp_path, name, STYLED[name].subject)
    tracked = load_flow(name)
    graph = tracked.graph()
    assert _styled_differences(ours, subject) == []
    assert graph[tracked.nodes["identity"]]["inputs"]["end_at"] < 1

    graph[tracked.nodes["hires_sampler"]]["inputs"]["denoise"] = 0.5
    (ours / GRAPH_NAME).write_text(json.dumps(graph, indent=2) + "\n")
    assert _styled_differences(ours, subject) == [GRAPH_NAME]


def _manifest_differs_only_in_its_name_and_its_style(name: str, tmp_path: Path) -> None:
    style = STYLED[name]
    ours, subject = load_flow(name), load_flow(style.subject)
    separator = subject.prompt["separator"]
    assert _styled_differences(ours.path, subject.path) == []
    for key, added in (("trailer", style.trailer), ("negative", style.negative)):
        terms = (subject.prompt[key], added) if added else (subject.prompt[key],)
        assert ours.prompt[key] == separator.join(terms)
    assert ours.dials["ip_weight"] < subject.dials["ip_weight"]

    scratch, scratch_subject = _pair(tmp_path, name, style.subject)
    document = json.loads((scratch / MANIFEST_NAME).read_text())
    document["dials"]["identity_cn_strength"] = 0.5
    (scratch / MANIFEST_NAME).write_text(json.dumps(document, indent=2) + "\n")
    assert _styled_differences(scratch, scratch_subject) == [MANIFEST_NAME]


@pytest.mark.spec("image-generation:flat:files-equal-the-subject")
def test_a_flat_flow_holds_the_subjects_schema(tmp_path: Path) -> None:
    _holds_the_subjects_schema(FLAT, tmp_path)


@pytest.mark.spec("image-generation:flat:the-graph-differs-in-the-face-chains-end")
def test_a_flat_graph_differs_only_in_the_face_chains_end(tmp_path: Path) -> None:
    _graph_differs_only_in_the_face_chains_end(FLAT, tmp_path)


@pytest.mark.spec("image-generation:flat:the-manifest-differs-in-the-style")
def test_a_flat_manifest_differs_only_in_its_name_and_its_style(
    tmp_path: Path,
) -> None:
    _manifest_differs_only_in_its_name_and_its_style(FLAT, tmp_path)


# --- a semireal and a vivid flow ----------------------------------------------

LOOKS = sorted(set(STYLED) - {FLAT})


@pytest.mark.spec("image-generation:styled:files-equal-the-subject")
@pytest.mark.parametrize("look", LOOKS)
def test_a_look_holds_the_subjects_schema(look: str, tmp_path: Path) -> None:
    _holds_the_subjects_schema(look, tmp_path)


@pytest.mark.spec("image-generation:styled:the-graph-differs-in-the-face-chains-end")
@pytest.mark.parametrize("look", LOOKS)
def test_a_look_graph_differs_only_in_the_face_chains_end(
    look: str, tmp_path: Path
) -> None:
    _graph_differs_only_in_the_face_chains_end(look, tmp_path)


@pytest.mark.spec("image-generation:styled:the-manifest-differs-in-the-style")
@pytest.mark.parametrize("look", LOOKS)
def test_a_look_manifest_differs_only_in_its_name_and_its_style(
    look: str, tmp_path: Path
) -> None:
    _manifest_differs_only_in_its_name_and_its_style(look, tmp_path)

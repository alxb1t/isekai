"""Stage (4): assembly before the session, seeds, render, atomicity, idempotence.

Everything here runs against `FakeComfyClient`, the double that stands in for the
endpoint. No GPU, no network, and the assembly tests assert that positively: the
client records every call it is given, so "no endpoint was contacted" is a count
rather than a hope.
"""

import io
import json
import random
import re
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path

import pytest

import isekai.foundation.run as run_module
import isekai.pipeline.generate as generate_module
from isekai.boundary.comfy import ComfyClient
from isekai.foundation.artifacts import PROMPT_FILE, RENDER_FILE, read
from isekai.foundation.flow import (
    CAPTION_BRIEFING_NAME,
    GRAPH_NAME,
    MANIFEST_NAME,
    MANIFEST_VERSION,
    SCHEMA_NAME,
    Flow,
    Schema,
    load_flow,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    OUTPUTS,
    PROMPTS,
    Run,
    across,
    artifact_name,
    attempts,
    open_run,
    record_failure,
)
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.generate import (
    SEED_BITS,
    approved_artifact,
    approved_flows,
    build_graph,
    draw_seeds,
    graph_digest,
    photo_resolution,
    prepare,
    prompt_artifact,
    render,
    rendered_seeds,
    seeds_for,
)
from isekai.pipeline.review import approve, review
from isekai.pipeline.tagging import FakeTagger
from isekai.shared.image import MAX_TARGET_LONG_SIDE
from isekai.shared.vocabulary import Vocabulary
from tests.fakes import FakeComfyClient, url_of
from tests.images import jpeg_bytes
from tests.stages import FIELD_MAP, Always, caption, fake_wd14, sheet

FLOW = "summon-anime-wai"


@pytest.fixture
def flow() -> Flow:
    """Return the one tracked flow."""
    return load_flow(FLOW)


def _run(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary, name: str = "ada"
) -> Run:
    """Return a run carried all the way to an approved sheet for `FLOW`."""
    photo = tmp_path / f"{name}.jpg"
    # Different bytes per name: the same bytes are the same run, by design.
    photo.write_bytes(jpeg_bytes(1200, 900 + 8 * len(name)))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader(prose="Brown hair, brown eyes."))
    sheet(
        made,
        schema,
        vocabulary,
    )
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    return made


@pytest.fixture
def run(tmp_path: Path, schema: Schema, vocabulary: Vocabulary) -> Run:
    """Return a run with an approved sheet for `FLOW`."""
    return _run(tmp_path, schema, vocabulary)


FEWER = "fewer-roles-v1"


def _fewer_roles_flow(tmp_path: Path) -> Flow:
    """Return a flow declaring the four required roles and none of the seven.

    **It is a `tmp_path` scratch and never a directory in `flows/`.** Anything in
    `flows/` becomes a product flow: pinned, bound into the provisioning union,
    selectable, and undeletable under the append-only rule (design.md D9).
    """
    source = load_flow(FLOW)
    root = tmp_path / "scratch-flows" / FEWER
    root.mkdir(parents=True)
    graph = {
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "committed"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "committed"}},
        "9": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
        },
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": 1,
                "cfg": 1,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
    }
    manifest = {
        "flow": FEWER,
        "manifest_version": MANIFEST_VERSION,
        # No photograph. The four roles below are the whole of what it patches.
        "inputs": ["sheet"],
        "vocabulary": dict(source.vocabulary),
        "prompt": dict(source.prompt),
        "dials": {
            "cfg": 5,
            "steps": 28,
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "denoise": 1.0,
        },
        "nodes": {"positive": "3", "negative": "4", "latent": "9", "sampler": "10"},
        "models": [],
        # Required of every flow since manifest version 3, and this one never
        # reaches it: nothing in the render path resolves a reader.
        "model": source.model,
    }
    (root / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n")
    (root / GRAPH_NAME).write_text(json.dumps(graph, indent=2) + "\n")
    for name in (SCHEMA_NAME, CAPTION_BRIEFING_NAME):
        (root / name).write_bytes((source.path / name).read_bytes())
    return load_flow(FEWER, root.parent)


def _run_for_fewer(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> tuple[Run, Flow]:
    """Return a run approved for the four-role flow, and the flow itself."""
    flow = _fewer_roles_flow(tmp_path)
    photo = tmp_path / "fewer.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader(prose="Brown hair, brown eyes."), flow=FEWER)
    sheet(
        made,
        schema,
        vocabulary,
        flow=FEWER,
    )
    review(made, FEWER)
    approve(made, FEWER, schema, vocabulary)
    prompt_artifact(made, flow, schema)
    return made, flow


# --- assembly -----------------------------------------------------------------


@pytest.mark.spec("image-generation:assembly:assembly-is-local-and-free")
def test_assembly_contacts_no_endpoint_and_writes_an_artifact(
    run: Run, flow: Flow, schema: Schema
) -> None:
    client = FakeComfyClient()

    written, refused = prepare(run, {FLOW: flow})

    assert list(written) == [FLOW] and refused == []
    body = read(written[FLOW], PROMPT_FILE)
    assert body["positive"].startswith("masterpiece, best quality")
    assert body["negative"] == flow.prompt["negative"]
    assert client.submissions == [] and client.uploaded is None


@pytest.mark.spec("image-generation:assembly:assembly-is-local-and-free")
def test_the_prompt_artifact_takes_the_approved_sheets_number(
    run: Run, flow: Flow, schema: Schema
) -> None:
    path = prompt_artifact(run, flow, schema)

    assert path.name == artifact_name(1)
    assert path.parent == run.path / FLOW / PROMPTS
    assert read(path, PROMPT_FILE)["producer"]["from"] == 1


@pytest.mark.spec("image-generation:assembly:bad-sheet-fails-before-the-session")
def test_a_malformed_approved_sheet_is_caught_before_anything_is_rented(
    run: Run, flow: Flow, schema: Schema
) -> None:
    approved = run.path / FLOW / "review" / "001.approved.json"
    body = json.loads(approved.read_text())
    del body["fields"]
    approved.write_text(json.dumps(body))

    with pytest.raises(Refusal) as refused:
        prompt_artifact(run, flow, schema)

    assert run.id in str(refused.value)
    assert list((run.path / FLOW / PROMPTS).glob("*.error.*")) != []
    assert not (run.path / FLOW / PROMPTS / "001.json").exists()


@pytest.mark.spec("image-generation:assembly:bad-sheet-fails-before-the-session")
def test_one_bad_sheet_does_not_stop_the_other_photographs(
    tmp_path: Path, flow: Flow, schema: Schema, vocabulary: Vocabulary
) -> None:
    from isekai.foundation.run import across

    good = _run(tmp_path, schema, vocabulary, "good")
    bad = _run(tmp_path, schema, vocabulary, "bad")
    approved = bad.path / FLOW / "review" / "001.approved.json"
    approved.write_text(json.dumps({"schema": {"name": "review", "version": 1}}))

    done: list[Run] = []

    def work(item: Run) -> None:
        prompt_artifact(item, flow, schema)
        done.append(item)

    refused = across([good, bad], work)

    assert done == [good]
    assert len(refused) == 1 and bad.id in refused[0]


# --- only an approved sheet ---------------------------------------------------


@pytest.mark.spec("image-generation:inputs:unapproved-flow-is-refused")
def test_a_flow_with_no_approved_sheet_is_refused_naming_the_commands(
    tmp_path: Path, flow: Flow, schema: Schema, vocabulary: Vocabulary
) -> None:
    photo = tmp_path / "p.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader())
    sheet(made, schema, vocabulary)
    review(made, FLOW)

    with pytest.raises(Refusal) as refused:
        prompt_artifact(made, flow, schema)

    message = str(refused.value)
    assert FLOW in message
    assert "python -m isekai review" in message
    assert "python -m isekai approve" in message


@pytest.mark.spec("image-generation:inputs:every-approved-flow-renders")
def test_every_flow_with_an_approved_artifact_is_selected_without_a_flag(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    caption(run, FakeReader(), flow="summon-v2")
    sheet(run, schema, vocabulary, flow="summon-v2")
    review(run, "summon-v2")
    approve(run, "summon-v2", schema, vocabulary)

    assert approved_flows(run) == [FLOW, "summon-v2"]


@pytest.mark.spec("image-generation:inputs:every-approved-flow-renders")
def test_a_flow_with_only_a_draft_is_not_selected(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    caption(run, FakeReader(), flow="summon-v2")
    sheet(run, schema, vocabulary, flow="summon-v2")
    review(run, "summon-v2")

    assert approved_flows(run) == [FLOW]


# --- seeds --------------------------------------------------------------------


@pytest.mark.spec("image-generation:seeds:count-draws-distinct-seeds")
def test_a_count_draws_that_many_distinct_seeds_from_the_injected_source() -> None:
    drawn = seeds_for(4, None, random.Random(7))

    assert len(drawn) == 4
    assert len(set(drawn)) == 4
    assert drawn == seeds_for(4, None, random.Random(7))


@pytest.mark.spec("image-generation:seeds:count-draws-distinct-seeds")
def test_a_drawn_seed_never_collides_with_one_already_rendered() -> None:
    rng = random.Random(7)
    first = draw_seeds(2, random.Random(7))

    drawn = draw_seeds(2, rng, first)

    assert set(drawn).isdisjoint(first)


@pytest.mark.spec("image-generation:seeds:explicit-seeds-render-exactly-those")
def test_explicit_seeds_render_exactly_those_and_draw_nothing() -> None:
    class Exploding(random.Random):
        def getrandbits(self, k: int) -> int:
            raise AssertionError("no seed should be drawn")

    assert seeds_for(None, [11, 22], Exploding()) == [11, 22]


@pytest.mark.spec("image-generation:seeds:count-and-seeds-are-exclusive")
def test_asking_for_both_a_count_and_seeds_is_refused() -> None:
    with pytest.raises(Refusal) as refused:
        seeds_for(2, [11], random.Random(7))

    assert "alternatives" in str(refused.value)


@pytest.mark.spec("cli:generate-signature:count-and-seed-are-exclusive")
def test_the_parser_refuses_a_count_and_a_seed_together() -> None:
    from isekai.interface.cli import build_parser

    with pytest.raises(SystemExit):
        build_parser().parse_args(
            ["generate", "--flow", FLOW, "--count", "2", "--seed", "7"]
        )


@pytest.mark.spec("cli:generate-signature:count-defaults-to-one")
def test_the_parser_defaults_to_one_render_with_a_drawn_seed() -> None:
    from isekai.interface.cli import build_parser

    parsed = build_parser().parse_args(["generate", "--flow", FLOW])

    assert parsed.count is None and parsed.seeds is None
    assert len(seeds_for(parsed.count, parsed.seeds, random.Random(7))) == 1


@pytest.mark.spec("cli:generate-signature:accepts-many-identifiers")
def test_the_parser_takes_several_photographs_in_one_invocation() -> None:
    from isekai.interface.cli import build_parser

    parsed = build_parser().parse_args(
        ["generate", "--flow", FLOW, "a.jpg", "b.jpg", "c.jpg"]
    )

    assert parsed.photos == ["a.jpg", "b.jpg", "c.jpg"]


# --- rendering ----------------------------------------------------------------


@pytest.mark.spec("image-generation:transport:offline-double-drives-the-stage")
def test_the_stage_renders_through_the_double_with_no_gpu(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()

    produced = render(run, flow, client, seeds=[42], poll=0)

    assert len(produced) == 1
    assert produced[0].image.name == "42.png"
    assert produced[0].image.parent == run.path / FLOW / OUTPUTS / "001"
    assert produced[0].image.read_bytes() == client.view_bytes
    assert len(client.submissions) == 1


# The transport's own two scenarios, held here because `render` is now the only
# caller of the seam. They moved out of `tests/test_polling.py` with the render
# path that file drove; the behaviour they describe is unchanged, and deleting
# them would have deleted a requirement that is still true (design.md D8).


@pytest.mark.spec("comfy-transport:polling:polls-history-until-complete")
def test_the_stage_polls_history_until_the_prompt_completes(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient(pending_polls=2)

    produced = render(run, flow, client, seeds=[42], poll=0)

    # Two empty answers, then the real one: the loop waits rather than reading
    # the first reply as the render.
    assert client.history_calls == 3
    assert produced[0].image.read_bytes() == client.view_bytes


@pytest.mark.spec("comfy-transport:retrieval:downloads-image-named-in-history")
def test_the_stage_downloads_the_image_named_in_the_history(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    image = {"filename": "anime_00001.png", "subfolder": "sub", "type": "output"}
    client = FakeComfyClient(image=image)

    render(run, flow, client, seeds=[42], poll=0)

    # The whole dict, not just the filename: `subfolder` and `type` are what the
    # endpoint needs to find the file again, and dropping either fetches nothing.
    assert client.viewed == image


@pytest.mark.spec("image-generation:immutability:output-records-the-graph-digest")
def test_the_provenance_records_the_flow_the_seed_the_version_and_the_graph(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()

    produced = render(run, flow, client, seeds=[42], poll=0)

    body = read(produced[0].provenance, RENDER_FILE)
    assert body["flow"] == FLOW
    assert body["seed"] == 42
    assert body["sheet_version"] == 1
    assert body["graph_sha256"] == graph_digest(client.submissions[0])
    assert body["flow_graph_sha256"] == flow.graph_digest()


@pytest.mark.spec("image-generation:immutability:output-records-the-graph-digest")
def test_two_renders_from_one_flow_with_different_graphs_are_distinguishable(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prompt = (
        read(run.directory(FLOW, PROMPTS) / artifact_name(1), PROMPT_FILE)
        if (run.directory(FLOW, PROMPTS) / artifact_name(1)).exists()
        else None
    )
    prepare(run, {FLOW: flow})
    prompt = read(run.directory(FLOW, PROMPTS) / artifact_name(1), PROMPT_FILE)

    one = build_graph(flow, run.photo, "up.png", prompt, 42)
    other = build_graph(flow, run.photo, "up.png", prompt, 43)

    assert graph_digest(one) != graph_digest(other)
    assert graph_digest(one) == graph_digest(
        build_graph(flow, run.photo, "up.png", prompt, 42)
    )


@pytest.mark.spec("image-generation:manifest:flow-declares-its-inputs")
def test_the_submitted_graph_carries_the_manifests_dials_not_the_files(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()

    render(run, flow, client, seeds=[42], poll=0)

    graph = client.submissions[0]
    assert graph[flow.node("sampler")]["inputs"]["cfg"] == 5
    assert graph[flow.node("sampler")]["inputs"]["seed"] == 42
    assert graph[flow.node("identity")]["inputs"]["cn_strength"] == 0.8
    assert graph[flow.node("hires_sampler")]["inputs"]["denoise"] == 0.35
    assert graph[flow.node("hires_sampler")]["inputs"]["steps"] == 20
    assert graph[flow.node("clip_skip")]["inputs"]["stop_at_clip_layer"] == -2


@pytest.mark.spec("image-generation:manifest:flow-declares-its-inputs")
def test_the_submitted_graph_is_sized_from_the_photographs_own_header(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()

    render(run, flow, client, seeds=[42], poll=0)

    graph = client.submissions[0]
    latent = graph[flow.node("latent")]["inputs"]
    assert (latent["width"], latent["height"]) == (1344, 1024)
    hires = graph[flow.node("hires_resize")]["inputs"]
    assert (hires["width"], hires["height"]) == (2016, 1536)


# --- idempotence --------------------------------------------------------------


@pytest.mark.spec("image-generation:idempotence:existing-seed-is-not-rerendered")
def test_a_named_seed_already_rendered_is_skipped(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()
    render(run, flow, client, seeds=[42], poll=0)
    before = len(client.submissions)

    assert render(run, flow, client, seeds=[42], poll=0) == []
    assert len(client.submissions) == before


@pytest.mark.spec("image-generation:idempotence:raising-count-renders-the-shortfall")
def test_raising_the_count_renders_only_the_difference(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()
    render(run, flow, client, count=2, rng=random.Random(7), poll=0)
    directory = run.path / FLOW / OUTPUTS / "001"
    first = rendered_seeds(directory, flow.output_suffix)
    stamps = {p.name: p.read_bytes() for p in directory.iterdir()}

    produced = render(run, flow, client, count=3, rng=random.Random(9), poll=0)

    assert len(first) == 2
    assert len(produced) == 1
    assert len(rendered_seeds(directory, flow.output_suffix)) == 3
    for name, body in stamps.items():
        assert (directory / name).read_bytes() == body


@pytest.mark.spec("image-generation:seeds:outputs-carry-the-sheet-version")
def test_the_same_seed_against_two_approved_versions_does_not_overwrite(
    run: Run, flow: Flow, schema: Schema, vocabulary: Vocabulary
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()
    render(run, flow, client, seeds=[42], poll=0)

    second = review(run, FLOW, new_version=True)
    assert second is not None
    body = json.loads(second.read_text())
    body["fields"]["clothes"] = ["collared shirt"]
    second.write_text(json.dumps(body))
    approve(run, FLOW, schema, vocabulary)
    prepare(run, {FLOW: flow})
    render(run, flow, client, seeds=[42], poll=0)

    assert (run.path / FLOW / OUTPUTS / "001" / "42.png").exists()
    assert (run.path / FLOW / OUTPUTS / "002" / "42.png").exists()


@pytest.mark.spec("image-generation:seeds:count-draws-distinct-seeds")
def test_each_render_is_named_by_the_seed_that_produced_it(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    client = FakeComfyClient()

    produced = render(run, flow, client, count=3, rng=random.Random(7), poll=0)

    for made in produced:
        assert made.image.stem == str(made.seed)
        assert read(made.provenance, RENDER_FILE)["seed"] == made.seed


# --- the unapproved run, the unreadable header, the interrupted write ----------


@pytest.mark.spec("image-generation:inputs:unapproved-flow-is-refused")
def test_generate_on_a_run_approved_for_nothing_refuses_at_the_command(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    # The CLI's own path, not `approved_artifact` called directly: `prepare`
    # filters to the flows a run is approved for, so a refusal only `prepare`
    # cannot reach leaves `generate` printing nothing and exiting 0 -- the worst
    # outcome for an operator who has just rented a pod.
    from isekai.interface.cli import build_parser, dispatch
    from isekai.interface.wiring import Wiring

    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    runs = tmp_path / "runs"
    open_run(photo, runs)
    err = io.StringIO()
    wired = Wiring(
        reader=Always(FakeReader(prose="unused")),
        tagger=fake_wd14(),
        hosted_tagger=Always(FakeTagger()),
        client=FakeComfyClient(),
        vocabulary=lambda: vocabulary,
        field_map=lambda _: FIELD_MAP,
        runs_root=runs,
        out=io.StringIO(),
        err=err,
    )

    status = dispatch(
        build_parser().parse_args(["generate", "--flow", FLOW, str(photo)]), wired
    )

    message = err.getvalue()
    assert status == 1
    assert FLOW in message
    assert "python -m isekai review" in message
    assert "python -m isekai approve" in message
    # *Names the commands that would produce one* -- so the commands it names
    # have to be ones this build accepts. Every stage verb has required `--flow`
    # since v0.16, and until v0.22.1 both of these were printed without it, so
    # copy-pasting the remedy got an argparse usage error (v0.16 R5).
    named = re.findall(r"`python -m isekai ([^`]+)`", message)
    assert len(named) == 2
    for command in named:
        assert build_parser().parse_args([*command.split(), str(photo)]).flows == [FLOW]


@pytest.mark.spec("image-generation:inputs:every-approved-flow-renders")
def test_an_approved_flow_still_needs_no_flag_to_be_selected(
    run: Run, flow: Flow, schema: Schema
) -> None:
    # The refusal above fires only when *nothing* asked for is approved, so the
    # "a run renders everything it has been approved for" rule is untouched.
    assembled, refused = prepare(run, {FLOW: flow})
    assert list(assembled) == [FLOW] and refused == []


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
def test_one_unreadable_header_does_not_cost_the_batch_its_turn(
    tmp_path: Path, flow: Flow, schema: Schema, vocabulary: Vocabulary
) -> None:
    # Different name lengths, because `_run` derives the photograph's bytes from
    # the name's length and identical bytes are the same run by design.
    bad = _run(tmp_path, schema, vocabulary, "bella")
    good = _run(tmp_path, schema, vocabulary, "ada")
    # A run admits a photograph on its 8-byte magic alone, so a truncated PNG
    # opens a run cleanly and only the header read ever finds it.
    bad.photo.write_bytes(b"\x89PNG\r\n\x1a\n")

    # `_generate`'s own composition: `prepare` now returns one run's per-flow
    # refusals rather than raising at the first, so the batch's collection is
    # `across`'s list plus theirs (v0.16 R6).
    broken: list[str] = []

    def assemble_one(one: Run) -> None:
        broken.extend(prepare(one, {FLOW: flow})[1])

    refused = across([bad, good], assemble_one) + broken

    assert len(refused) == 1
    assert "re-export the photograph" in refused[0]
    assert (good.directory(FLOW, PROMPTS) / artifact_name(1)).is_file()
    assert list(bad.directory(FLOW, PROMPTS).glob("001.error.1.permanent.json"))


@pytest.mark.spec("image-generation:assembly:a-bad-sheet-is-per-flow")
def test_one_flows_malformed_sheet_does_not_cost_its_siblings_their_assembly(
    tmp_path: Path, flow: Flow, schema: Schema, vocabulary: Vocabulary
) -> None:
    """Two flows on one run, one of them broken: the other is still assembled.

    The flows of a run are independent -- separate subtrees, separate sheets,
    separate error records -- so the dict comprehension that raised at the first
    broken one took its siblings' turn with it, after having already written a
    permanent record into the broken flow's own directory (v0.16 R6).
    """
    fewer = _fewer_roles_flow(tmp_path)
    photo = tmp_path / "ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    for name in (FLOW, FEWER):
        caption(made, FakeReader(prose="Brown hair, brown eyes."), flow=name)
        sheet(made, schema, vocabulary, flow=name)
        review(made, name)
        approve(made, name, schema, vocabulary)

    # The one sheet nothing can assemble: the approved artifact has lost the
    # key the whole prompt is built from.
    _, source = approved_artifact(made, FEWER)
    body = json.loads(source.read_text())
    del body["fields"]
    source.write_text(json.dumps(body, indent=2) + "\n")

    assembled, refused = prepare(made, {FLOW: flow, FEWER: fewer})

    assert list(assembled) == [FLOW]
    assert (made.directory(FLOW, PROMPTS) / artifact_name(1)).is_file()
    assert len(refused) == 1 and FEWER in refused[0]
    # The record is written into the broken flow's own subtree, so the flow
    # beside it is untouched by it -- and stays assembled on the next pass.
    assert list(made.directory(FEWER, PROMPTS).glob("001.error.1.permanent.json"))
    assert not list(made.directory(FLOW, PROMPTS).glob("*.error.*"))

    again, still = prepare(made, {FLOW: flow, FEWER: fewer})

    assert list(again) == [FLOW]
    # Still exactly one refusal on the second pass, and it is the budget
    # short-circuit reading the record the first pass wrote -- into the broken
    # flow's directory, which is why the flow beside it assembles again.
    assert len(still) == 1 and "failed permanently" in still[0]


@pytest.mark.spec("image-generation:assembly:a-bad-sheet-is-per-flow")
@pytest.mark.parametrize("broken", [["a list"], None])
def test_an_unassemblable_sheet_names_its_record_and_the_command(
    run: Run, flow: Flow, broken: object
) -> None:
    _, source = approved_artifact(run, FLOW)
    body = json.loads(source.read_text())
    if broken is None:
        body["producer"] = "not an object"
    else:
        body["fields"] = broken
    source.write_text(json.dumps(body))

    assembled, refused = prepare(run, {FLOW: flow})

    assert assembled == {} and len(refused) == 1
    assert f"delete {FLOW}/{PROMPTS}/001.error.1.permanent.json" in refused[0]
    assert refused[0].endswith(f"`python -m isekai generate --flow {FLOW} {run.id}`")


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
def test_an_unreadable_header_inside_the_render_loop_is_recorded_not_fatal(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow})
    run.photo.write_bytes(b"\x89PNG\r\n\x1a\n")
    client = FakeComfyClient()

    with pytest.raises(Refusal) as refused:
        render(run, flow, client, seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    assert "re-export the photograph" in str(refused.value)
    assert client.submissions == []
    assert list(directory.glob("001.error.1.permanent.json"))


@pytest.mark.spec("image-generation:failure:an-unreachable-endpoint-is-transient")
def test_an_unreachable_endpoint_is_recorded_transient_not_permanent(
    run: Run, flow: Flow, schema: Schema, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A closed tunnel says nothing about the graph, so it is not permanent.

    Through a real `ComfyClient`, rather than by raising `TransportFailure` directly:
    what is under test is that a transport-level `URLError` reaches the record as
    transient, and the classification happens in the client.
    """
    prepare(run, {FLOW: flow})

    def closed_after_the_upload(req: urllib.request.Request | str) -> io.BytesIO:
        # The upload lands and the tunnel then closes, so `submit` is what fails.
        if url_of(req).endswith("/upload/image"):
            return io.BytesIO(b'{"name": "photo.png"}')
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", closed_after_the_upload)

    with pytest.raises(Refusal) as refused:
        render(run, flow, ComfyClient("http://127.0.0.1:8188"), seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    assert "the rendering endpoint could not be reached" in str(refused.value)
    assert [one.kind for one in attempts(directory, 1)] == ["transient"]
    assert not list(directory.glob("001.error.1.permanent.json"))


def _answering(monkeypatch: pytest.MonkeyPatch, code: int, body: bytes) -> None:
    """Patch `urlopen` so the upload lands and the submission gets `code`."""

    def answer(req: urllib.request.Request | str) -> io.BytesIO:
        url = url_of(req)
        if url.endswith("/upload/image"):
            return io.BytesIO(b'{"name": "photo.png"}')
        if code == 200:
            return io.BytesIO(body)
        raise urllib.error.HTTPError(url, code, "status", Message(), io.BytesIO(body))

    monkeypatch.setattr(urllib.request, "urlopen", answer)


@pytest.mark.spec("image-generation:failure:a-rejected-graph-is-permanent")
def test_a_rejected_graph_is_recorded_permanent(
    run: Run, flow: Flow, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(run, {FLOW: flow})
    _answering(monkeypatch, 400, b'{"error": {"message": "Prompt outputs failed"}}')

    with pytest.raises(Refusal) as refused:
        render(run, flow, ComfyClient("http://127.0.0.1:8188"), seeds=[42], poll=0)

    message = str(refused.value)
    directory = run.path / FLOW / OUTPUTS / "001"
    assert [one.kind for one in attempts(directory, 1)] == ["permanent"]
    assert "HTTP 400" in message and "Prompt outputs failed" in message
    assert "tunnel" not in message and "infra/up.sh" not in message


@pytest.mark.spec("image-generation:failure:a-server-error-is-transient")
def test_a_server_error_is_recorded_transient(
    run: Run, flow: Flow, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(run, {FLOW: flow})
    _answering(monkeypatch, 502, b"Bad Gateway")

    with pytest.raises(Refusal) as refused:
        render(run, flow, ComfyClient("http://127.0.0.1:8188"), seeds=[42], poll=0)

    message = str(refused.value)
    directory = run.path / FLOW / OUTPUTS / "001"
    assert [one.kind for one in attempts(directory, 1)] == ["transient"]
    assert "HTTP 502" in message and "ComfyUI log" in message


@pytest.mark.spec("image-generation:failure:a-failed-upload-is-recorded")
def test_a_failed_upload_is_recorded(
    run: Run, flow: Flow, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(run, {FLOW: flow})

    def closed(req: urllib.request.Request | str) -> io.BytesIO:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", closed)
    client = ComfyClient("http://127.0.0.1:8188")

    with pytest.raises(Refusal) as refused:
        render(run, flow, client, seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    recorded = attempts(directory, 1)
    assert [one.kind for one in recorded] == ["transient"]
    assert "seed" not in json.loads(recorded[0].path.read_text())
    assert f"{FLOW}/{OUTPUTS}/001/001.error.1.transient.json" in str(refused.value)
    assert "delete it before rendering again" in str(refused.value)

    with pytest.raises(Refusal) as again:
        render(run, flow, client, seeds=[42], poll=0)
    assert "001.error.1.transient.json" in str(again.value)


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
@pytest.mark.parametrize(
    "record",
    [{}, {"outputs": ["a list"]}, {"outputs": {"SaveImage": {"images": []}}}],
)
def test_a_history_without_an_image_is_refused_and_recorded(
    run: Run, flow: Flow, record: dict[str, object]
) -> None:
    prepare(run, {FLOW: flow})

    class Malformed(FakeComfyClient):
        def history(self, prompt_id: str) -> dict[str, object]:
            return {prompt_id: record}

    with pytest.raises(Refusal) as refused:
        render(run, flow, Malformed(), seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    assert [one.kind for one in attempts(directory, 1)] == ["permanent"]
    assert "ComfyUI log" in str(refused.value)
    assert "render again" not in str(refused.value)


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
@pytest.mark.parametrize("body", [b'["a list"]', b"null", b'"a string"'])
def test_a_submission_answered_in_the_wrong_shape_is_refused_permanent(
    run: Run, flow: Flow, monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    prepare(run, {FLOW: flow})
    _answering(monkeypatch, 200, body)

    with pytest.raises(Refusal) as refused:
        render(run, flow, ComfyClient("http://127.0.0.1:8188"), seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    assert [one.kind for one in attempts(directory, 1)] == ["permanent"]
    assert "a shape this build does not read" in str(refused.value)


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
@pytest.mark.parametrize("body", [b"3", b'["a list"]', b"null"])
def test_a_history_that_is_not_an_object_is_refused_permanent(
    run: Run, flow: Flow, monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    """A list matters most: `in` on it never matches, so the poll never ends."""
    prepare(run, {FLOW: flow})

    def answer(req: urllib.request.Request | str) -> io.BytesIO:
        url = url_of(req)
        if url.endswith("/upload/image"):
            return io.BytesIO(b'{"name": "photo.png"}')
        if url.endswith("/prompt"):
            return io.BytesIO(b'{"prompt_id": "pid-1"}')
        return io.BytesIO(body)

    monkeypatch.setattr(urllib.request, "urlopen", answer)

    with pytest.raises(Refusal) as refused:
        render(run, flow, ComfyClient("http://127.0.0.1:8188"), seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    assert [one.kind for one in attempts(directory, 1)] == ["permanent"]
    assert "history" in str(refused.value) and "--server" in str(refused.value)


@pytest.mark.spec("image-generation:immutability:output-records-the-graph-digest")
def test_the_sidecar_is_written_before_its_image(
    run: Run, flow: Flow, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(run, {FLOW: flow})

    def crashed(path: Path, body: bytes) -> None:
        raise OSError("the process died between the writes")

    monkeypatch.setattr(generate_module, "write_atomically", crashed)

    with pytest.raises(OSError):
        render(run, flow, FakeComfyClient(), seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    assert (directory / "42.json").is_file()
    assert not (directory / f"42{flow.output_suffix}").exists()
    assert rendered_seeds(directory, flow.output_suffix) == []


@pytest.mark.spec("run-directory:budget:at-budget-the-stage-refuses")
def test_a_transient_render_record_still_refuses_the_next_attempt_on_the_count(
    run: Run, flow: Flow, schema: Schema
) -> None:
    """`transient` classifies the failure; it does not buy a second attempt here.

    Rendering's budget is **one**, deliberately -- `run-directory`'s own
    requirement is that a render which has failed once costs a person's attention
    rather than another attempt, and `test_the_rendering_stages_budget_is_one`
    pins the number. So the remedy after a closed tunnel is still deleting the
    record by hand; what the classification changes is which sentence says so,
    and that the failure is not short-circuited as one that would recur.

    Asserted rather than left implicit, because the arithmetic is invisible from
    the record alone and the test beside this one could be read as promising the
    next attempt proceeds (converge R1).
    """
    prepare(run, {FLOW: flow})
    directory = run.path / FLOW / OUTPUTS / "001"
    directory.mkdir(parents=True)
    record_failure(
        directory,
        1,
        "transient",
        {"stage": "render", "seed": 42, "detail": "the endpoint did not answer"},
    )

    client = FakeComfyClient()
    with pytest.raises(Refusal) as refused:
        render(run, flow, client, seeds=[42], poll=0)

    message = str(refused.value)
    assert "used its 1 attempt" in message
    assert "001.error.1.transient.json" in message
    # Not the permanent short-circuit's wording, which is the whole of what the
    # classification changed for this stage.
    assert "failed permanently" not in message
    assert client.submissions == []


@pytest.mark.spec("run-directory:atomicity:interrupted-write-leaves-nothing")
def test_an_interrupted_render_leaves_no_png_for_resume_to_skip(
    run: Run, flow: Flow, schema: Schema, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(run, {FLOW: flow})

    def interrupted(descriptor: int) -> None:
        raise OSError("the disk went away mid-write")

    monkeypatch.setattr(run_module.os, "fsync", interrupted)

    with pytest.raises(OSError):
        render(run, flow, FakeComfyClient(), seeds=[42], poll=0)

    directory = run.path / FLOW / OUTPUTS / "001"
    assert not (directory / f"42{flow.output_suffix}").exists()
    assert rendered_seeds(directory, flow.output_suffix) == []


# --- the aspect-ratio ceiling -------------------------------------------------

# The third of the three ceilings `isekai.shared.image` states, enforced where a target
# is computed rather than where a header is read. What it bounds and why is beside
# the constant; what is asserted here is that it refuses, that it refuses per
# photograph, and that it does not refuse what merely reaches it.


def _photo(tmp_path: Path, name: str, width: int, height: int) -> Path:
    """Write a photograph of exactly this size and return its path."""
    path = tmp_path / name
    path.write_bytes(jpeg_bytes(width, height))
    return path


@pytest.mark.spec(
    "image-generation:working-resolution:an-extreme-aspect-ratio-is-refused"
)
def test_a_photograph_whose_target_passes_the_long_side_bound_is_refused(
    tmp_path: Path,
) -> None:
    photo = _photo(tmp_path, "panorama.jpg", 5000, 1000)

    with pytest.raises(Refusal) as refused:
        photo_resolution(photo)

    # A `Refusal`, not a `SystemExit`: the batch must survive one extreme
    # photograph the same way it survives one unreadable header.
    message = str(refused.value)
    assert photo.name in message
    assert "5120" in message and "1024" in message
    assert str(MAX_TARGET_LONG_SIDE) in message


@pytest.mark.spec(
    "image-generation:working-resolution:an-extreme-aspect-ratio-is-refused"
)
def test_a_photograph_at_exactly_the_bound_is_still_rendered(tmp_path: Path) -> None:
    # 4:1 exactly. The bound refuses what is past it, not what reaches it.
    photo = _photo(tmp_path, "wide.jpg", 4096, 1024)

    assert photo_resolution(photo) == (MAX_TARGET_LONG_SIDE, 1024)


@pytest.mark.spec("image-generation:working-resolution:a-refusal-is-per-photograph")
def test_one_photograph_past_the_bound_does_not_cost_the_batch_its_session(
    tmp_path: Path,
) -> None:
    photos = [
        _photo(tmp_path, "first.jpg", 1600, 1200),
        _photo(tmp_path, "middle.jpg", 5000, 1000),
        _photo(tmp_path, "last.jpg", 1200, 1600),
    ]
    resolved: list[tuple[int, int]] = []

    refusals = across(photos, lambda photo: resolved.append(photo_resolution(photo)))

    # The other two are still rendered, and the refusal names the photograph it
    # belongs to rather than the batch.
    assert resolved == [(1344, 1024), (1024, 1344)]
    assert len(refusals) == 1
    assert "middle.jpg" in refusals[0]
    assert "first.jpg" not in refusals[0] and "last.jpg" not in refusals[0]


@pytest.mark.spec("image-generation:seeds:seeds-are-drawn-at-full-64-bit-width")
def test_a_drawn_seed_spans_the_full_sampler_width() -> None:
    # Carried forward from `workflow-mutation:jitter:seed-is-64-bit`, which was
    # the only binding on the width in the living spec. An output is named by its
    # seed, so the seed space is the reproducibility contract at its finest grain
    # and narrowing it raises the collision rate the drawing rule already guards.
    assert SEED_BITS == 64

    class _Widest(random.Random):
        """A source answering with the widest value the width it is asked for allows."""

        asked: list[int] = []

        def getrandbits(self, k: int) -> int:
            self.asked.append(k)
            return (1 << k) - 1

    source = _Widest()
    drawn = draw_seeds(1, source)

    # The width comes from the one constant rather than a literal at the draw:
    # a repeated literal is a second place to change and a silent way to disagree.
    assert source.asked == [SEED_BITS]
    assert drawn == [2**64 - 1]


# --- a flow that declares fewer roles ------------------------------------------


@pytest.mark.spec("image-generation:roles:optional-roles-are-not-assumed")
def test_a_flow_with_fewer_roles_builds_its_graph(
    tmp_path: Path,
) -> None:
    flow = _fewer_roles_flow(tmp_path)
    photo = tmp_path / "fewer.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))

    graph = build_graph(
        flow, photo, "", {"positive": "a, b", "negative": "bad"}, seed=7
    )

    assert graph["3"]["inputs"]["text"] == "a, b"
    assert graph["4"]["inputs"]["text"] == "bad"
    assert graph["9"]["inputs"]["width"] == photo_resolution(photo)[0]
    assert graph["10"]["inputs"]["seed"] == 7
    assert graph["10"]["inputs"]["cfg"] == 5


@pytest.mark.spec("image-generation:roles:optional-roles-are-not-assumed")
def test_a_flow_with_fewer_roles_patches_only_what_it_declares(tmp_path: Path) -> None:
    flow = _fewer_roles_flow(tmp_path)
    photo = tmp_path / "fewer.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    before = flow.graph()

    graph = build_graph(flow, photo, "", {"positive": "a", "negative": "b"}, seed=1)

    assert set(graph) == set(before)
    assert set(graph) == {"3", "4", "9", "10"}


@pytest.mark.spec("image-generation:roles:optional-roles-are-not-assumed")
def test_a_flow_declaring_fewer_roles_renders(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    made, flow = _run_for_fewer(tmp_path, schema, vocabulary)
    client = FakeComfyClient()

    produced = render(made, flow, client, seeds=[11], rng=random.Random(0))

    assert [render_.seed for render_ in produced] == [11]
    assert produced[0].image.is_file()


@pytest.mark.spec("image-generation:roles:undeclared-input-is-not-uploaded")
def test_a_flow_that_declares_no_photograph_uploads_nothing(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    made, flow = _run_for_fewer(tmp_path, schema, vocabulary)
    client = FakeComfyClient()

    assert "photo" not in flow.inputs

    render(made, flow, client, seeds=[11], rng=random.Random(0))

    assert client.uploaded is None
    assert client.submissions

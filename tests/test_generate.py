"""Stage (4): assembly before the session, seeds, preflight, render, idempotence.

Everything here runs against `FakeComfyClient`, the double the existing suite
already drives `pipeline.run` with. No GPU, no network, and the assembly tests
assert that positively: the client records every call it is given, so "no
endpoint was contacted" is a count rather than a hope.
"""

import json
import random
from pathlib import Path

import pytest

from isekai.caption import FakeReader, caption
from isekai.flow import Flow, load_flow
from isekai.generate import (
    OUTPUTS,
    PROMPTS,
    approved_flows,
    build_graph,
    draw_seeds,
    graph_digest,
    missing_models,
    preflight,
    prepare,
    prompt_artifact,
    render,
    rendered_seeds,
    seeds_for,
)
from isekai.refusal import Refusal
from isekai.review import approve, review
from isekai.run import Run, artifact_name, open_run, read_artifact
from isekai.sheet import FakeSorter, Schema, load_schema, sheet
from isekai.vocabulary import Vocabulary, read_tags
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes
from tests.test_vocabulary import CSV

FLOW = "summon-v1"


@pytest.fixture
def schema() -> Schema:
    """Return the tracked identity schema."""
    return load_schema()


@pytest.fixture
def vocabulary() -> Vocabulary:
    """Return the small offline vocabulary the mapping tests use."""
    return Vocabulary("wd14/selected_tags.csv", "f" * 40, "a" * 64, read_tags(CSV))


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
        FakeSorter(answers={"hair_colour": ["brown"], "eye_colour": ["brown"]}),
        schema,
        vocabulary,
        [FLOW],
    )
    review(made, FLOW)
    approve(made, FLOW, schema, vocabulary)
    return made


@pytest.fixture
def run(tmp_path: Path, schema: Schema, vocabulary: Vocabulary) -> Run:
    """Return a run with an approved sheet for `FLOW`."""
    return _run(tmp_path, schema, vocabulary)


def _present(flow: Flow) -> list[str]:
    """Return the volume contents a preflight would find for a healthy pod."""
    return list(flow.models)


# --- assembly -----------------------------------------------------------------


@pytest.mark.spec("image-generation:assembly:assembly-is-local-and-free")
def test_assembly_contacts_no_endpoint_and_writes_an_artifact(
    run: Run, flow: Flow, schema: Schema
) -> None:
    client = FakeComfyClient()

    written = prepare(run, {FLOW: flow}, schema)

    assert list(written) == [FLOW]
    body = read_artifact(written[FLOW])
    assert body["positive"].startswith("masterpiece, best quality")
    assert body["negative"] == flow.prompt["negative"]
    assert client.submissions == [] and client.uploaded is None


@pytest.mark.spec("image-generation:assembly:assembly-is-local-and-free")
def test_the_prompt_artifact_takes_the_approved_sheets_number(
    run: Run, flow: Flow, schema: Schema
) -> None:
    path = prompt_artifact(run, flow, schema)

    assert path.name == artifact_name(1)
    assert path.parent == run.path / PROMPTS / FLOW
    assert read_artifact(path)["producer"]["from"] == 1


@pytest.mark.spec("image-generation:assembly:bad-sheet-fails-before-the-session")
def test_a_malformed_approved_sheet_is_caught_before_anything_is_rented(
    run: Run, flow: Flow, schema: Schema
) -> None:
    approved = run.path / "review" / FLOW / "001.approved.json"
    body = json.loads(approved.read_text())
    del body["fields"]
    approved.write_text(json.dumps(body))

    with pytest.raises(Refusal) as refused:
        prompt_artifact(run, flow, schema)

    assert run.id in str(refused.value)
    assert list((run.path / PROMPTS / FLOW).glob("*.error.*")) != []
    assert not (run.path / PROMPTS / FLOW / "001.json").exists()


@pytest.mark.spec("image-generation:assembly:bad-sheet-fails-before-the-session")
def test_one_bad_sheet_does_not_stop_the_other_photographs(
    tmp_path: Path, flow: Flow, schema: Schema, vocabulary: Vocabulary
) -> None:
    from isekai.run import across

    good = _run(tmp_path, schema, vocabulary, "good")
    bad = _run(tmp_path, schema, vocabulary, "bad")
    approved = bad.path / "review" / FLOW / "001.approved.json"
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
    sheet(made, FakeSorter(), schema, vocabulary, [FLOW])
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
    sheet(run, FakeSorter(), schema, vocabulary, ["summon-v2"])
    review(run, "summon-v2")
    approve(run, "summon-v2", schema, vocabulary)

    assert approved_flows(run) == [FLOW, "summon-v2"]


@pytest.mark.spec("image-generation:inputs:every-approved-flow-renders")
def test_a_flow_with_only_a_draft_is_not_selected(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sheet(run, FakeSorter(), schema, vocabulary, ["summon-v2"])
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
    from isekai.__main__ import build_parser

    with pytest.raises(SystemExit):
        build_parser().parse_args(["generate", "--count", "2", "--seed", "7"])


@pytest.mark.spec("cli:generate-signature:count-defaults-to-one")
def test_the_parser_defaults_to_one_render_with_a_drawn_seed() -> None:
    from isekai.__main__ import build_parser

    parsed = build_parser().parse_args(["generate"])

    assert parsed.count is None and parsed.seeds is None
    assert len(seeds_for(parsed.count, parsed.seeds, random.Random(7))) == 1


@pytest.mark.spec("cli:generate-signature:accepts-many-identifiers")
def test_the_parser_takes_several_photographs_in_one_invocation() -> None:
    from isekai.__main__ import build_parser

    parsed = build_parser().parse_args(["generate", "a.jpg", "b.jpg", "c.jpg"])

    assert parsed.photos == ["a.jpg", "b.jpg", "c.jpg"]


# --- preflight ----------------------------------------------------------------


@pytest.mark.spec("image-generation:preflight:absent-models-refuse-early")
def test_an_absent_artifact_refuses_before_any_work_is_submitted(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()
    short = [dest for dest in flow.models if "RealESRGAN" not in dest]

    with pytest.raises(Refusal) as refused:
        render(run, flow, client, present=short, rng=random.Random(7))

    message = str(refused.value)
    assert "RealESRGAN_x4plus_anime_6B.pth" in message
    assert "download_models.sh" in message
    assert client.submissions == []


@pytest.mark.spec("image-generation:preflight:absent-models-refuse-early")
def test_a_complete_volume_passes_the_preflight(flow: Flow) -> None:
    assert missing_models(flow, _present(flow)) == []
    preflight(flow, _present(flow))


# --- rendering ----------------------------------------------------------------


@pytest.mark.spec("image-generation:transport:offline-double-drives-the-stage")
def test_the_stage_renders_through_the_double_with_no_gpu(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()

    produced = render(run, flow, client, seeds=[42], present=_present(flow), poll=0)

    assert len(produced) == 1
    assert produced[0].image.name == "42.png"
    assert produced[0].image.parent == run.path / OUTPUTS / FLOW / "001"
    assert produced[0].image.read_bytes() == client.view_bytes
    assert len(client.submissions) == 1


@pytest.mark.spec("image-generation:immutability:output-records-the-graph-digest")
def test_the_provenance_records_the_flow_the_seed_the_version_and_the_graph(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()

    produced = render(run, flow, client, seeds=[42], present=_present(flow), poll=0)

    body = read_artifact(produced[0].provenance)
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
        read_artifact(run.directory(PROMPTS, FLOW) / artifact_name(1))
        if (run.directory(PROMPTS, FLOW) / artifact_name(1)).exists()
        else None
    )
    prepare(run, {FLOW: flow}, schema)
    prompt = read_artifact(run.directory(PROMPTS, FLOW) / artifact_name(1))

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
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()

    render(run, flow, client, seeds=[42], present=_present(flow), poll=0)

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
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()

    render(run, flow, client, seeds=[42], present=_present(flow), poll=0)

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
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()
    render(run, flow, client, seeds=[42], present=_present(flow), poll=0)
    before = len(client.submissions)

    assert render(run, flow, client, seeds=[42], present=_present(flow), poll=0) == []
    assert len(client.submissions) == before


@pytest.mark.spec("image-generation:idempotence:raising-count-renders-the-shortfall")
def test_raising_the_count_renders_only_the_difference(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()
    render(
        run, flow, client, count=2, rng=random.Random(7), present=_present(flow), poll=0
    )
    directory = run.path / OUTPUTS / FLOW / "001"
    first = rendered_seeds(directory)
    stamps = {p.name: p.read_bytes() for p in directory.iterdir()}

    produced = render(
        run, flow, client, count=3, rng=random.Random(9), present=_present(flow), poll=0
    )

    assert len(first) == 2
    assert len(produced) == 1
    assert len(rendered_seeds(directory)) == 3
    for name, body in stamps.items():
        assert (directory / name).read_bytes() == body


@pytest.mark.spec("image-generation:seeds:outputs-carry-the-sheet-version")
def test_the_same_seed_against_two_approved_versions_does_not_overwrite(
    run: Run, flow: Flow, schema: Schema, vocabulary: Vocabulary
) -> None:
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()
    render(run, flow, client, seeds=[42], present=_present(flow), poll=0)

    second = review(run, FLOW)
    assert second is not None
    body = json.loads(second.read_text())
    body["fields"]["clothes"] = ["collared shirt"]
    second.write_text(json.dumps(body))
    approve(run, FLOW, schema, vocabulary)
    prepare(run, {FLOW: flow}, schema)
    render(run, flow, client, seeds=[42], present=_present(flow), poll=0)

    assert (run.path / OUTPUTS / FLOW / "001" / "42.png").exists()
    assert (run.path / OUTPUTS / FLOW / "002" / "42.png").exists()


@pytest.mark.spec("image-generation:seeds:count-draws-distinct-seeds")
def test_each_render_is_named_by_the_seed_that_produced_it(
    run: Run, flow: Flow, schema: Schema
) -> None:
    prepare(run, {FLOW: flow}, schema)
    client = FakeComfyClient()

    produced = render(
        run, flow, client, count=3, rng=random.Random(7), present=_present(flow), poll=0
    )

    for made in produced:
        assert made.image.stem == str(made.seed)
        assert read_artifact(made.provenance)["seed"] == made.seed

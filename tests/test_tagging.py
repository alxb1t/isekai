"""Stage (1)'s two tag artifacts: what goes out, what is stored, what refuses.

Offline throughout. The hosted tagger is driven through `FakeTransport` and
`FakeTagger`, and the local one through `tests/test_wd14.py`'s fake session over
a three-row label index -- no network, no 467 MB file, and nothing here imports
`numpy`, `Pillow` or `onnxruntime`.

**What is deliberately not asserted anywhere in this file is narrowing.** Neither
stage canonicalises, filters against the vocabulary, deduplicates or re-orders on
anything but confidence, and the tests that look like they are checking content
are checking that content survived untouched.
"""

import base64
import dataclasses
import io
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from isekai.boundary import provision
from isekai.boundary.wd14 import MODEL_DEST, LocalTagger
from isekai.foundation.artifacts import TAGS_FILE, WD14_FILE, read
from isekai.foundation.flow import (
    FLOWS_DIR,
    MANIFEST_NAME,
    SIBLINGS,
    Flow,
    load_flow,
    tracked_flows,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    TAGS,
    WD14,
    Run,
    StageFailure,
    constant_record,
    open_run,
    record_failure,
)
from isekai.interface import wiring
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import READER_OPTIONS, FakeReader, OllamaReader
from isekai.pipeline.tagging import (
    SEPARATOR,
    TAG_PROMPT,
    TAGGER_OPTIONS,
    FakeTagger,
    OllamaTagger,
    Tagger,
    Tagging,
    tag_hosted,
    tag_wd14,
)
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
from tests.stages import (
    FAKE_PINS,
    FIELD_MAP,
    Always,
    FakeSession,
    fake_tagger,
    fake_wd14,
)
from tests.transports import FakeTransport

FLOW = "summon-anime-wai"


@pytest.fixture
def run(tmp_path: Path) -> Run:
    """Return a run with a photograph in it and nothing else."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    return open_run(photo, tmp_path / "runs")


@pytest.fixture
def local() -> LocalTagger:
    """Return one opened fake tagger: row 1 of the index is `1girl` at 0.9.

    Stated once rather than at six call sites -- the vector and the index are
    the ordering contract, and six spellings of it are six places to drift.
    """
    return fake_tagger()


def _answer(text: str) -> FakeTransport:
    """Return a transport answering `text` as the hosted tagger's whole reply."""
    return FakeTransport(payload={"response": text, "done_reason": "stop"})


# --- what the hosted tagger is given -----------------------------------------


@pytest.mark.spec("tagging:inputs:only-the-photograph-is-passed")
def test_the_hosted_tagger_is_sent_the_photograph_and_one_fixed_prompt(
    run: Run,
) -> None:
    transport = _answer("1girl, solo, brown hair")

    tag_hosted(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

    (body,) = transport.bodies()
    assert body["prompt"] == TAG_PROMPT
    assert body["images"] == [base64.b64encode(run.photo.read_bytes()).decode()]
    assert body["options"] == dict(TAGGER_OPTIONS)
    # No briefing, no schema, no vocabulary, no flow identifier: a tagger told
    # what a sheet wants is a tagger being pressed into stage (2)'s job.
    assert set(body) == {"model", "prompt", "images", "stream", "options"}


@pytest.mark.spec("tagging:inputs:only-the-photograph-is-passed")
def test_the_prompt_asks_for_a_long_list_and_is_not_chat_framed() -> None:
    # "Long" is the lever -- 34-40 tags becomes 45-51, and in-vocabulary yield
    # 11-23% becomes 24%. The llama-3 framing is refused because the Modelfile
    # pins `TEMPLATE {{ .Prompt }}` and the prose briefing goes through it
    # unframed (design.md D11).
    assert TAG_PROMPT == "Write a long list of Booru tags for this image.\n"
    assert "<|" not in TAG_PROMPT


@pytest.mark.spec("tagging:inputs:only-the-photograph-is-passed")
def test_the_sampling_options_carry_the_sorters_repeat_penalty() -> None:
    # Kept on the sorter's precedent rather than a budget argument: at
    # temperature 0 there is no sampling noise to break a loop, and a
    # comma-separated list is that loop with more surface (design.md D12).
    assert TAGGER_OPTIONS == {
        "temperature": 0,
        "seed": 1,
        "num_predict": 1024,
        # The reader's window, for the reader's reason. This prompt is the
        # cheaper of the two: measured `prompt_eval_count` 779 against the
        # reader's 1275, the 48-byte prompt costing ~50 tokens beside the same
        # constant ~729 for the photograph.
        "num_ctx": 4096,
        "repeat_penalty": 1.15,
    }
    # One window for both prompts, because one model answers both -- and the
    # pinned value is the one Ollama was already resolving, so neither output
    # moves.
    assert TAGGER_OPTIONS["num_ctx"] == READER_OPTIONS["num_ctx"]


# --- what is stored -----------------------------------------------------------


@pytest.mark.spec("tagging:output:artifact-is-a-list-of-tags")
def test_the_hosted_artifact_is_a_list_of_tags_under_the_flow(run: Run) -> None:
    path = tag_hosted(run, FLOW, FakeTagger())

    assert path is not None
    assert path.parent == run.directory(FLOW, TAGS)
    assert read(path, TAGS_FILE)["tags"] == ["1girl", "solo", "looking at viewer"]


@pytest.mark.spec("tagging:output:the-list-is-stored-unnarrowed")
def test_every_tag_is_stored_exactly_as_it_came_including_the_unusable(
    run: Run,
) -> None:
    # `fashion photography` and `high resolution` are out of the vocabulary and
    # `blue eyes` contradicts what the reader wrote about the same photograph.
    # All three are stored: narrowing is stage (2)'s job, and seeing behind it is
    # why this artifact exists (design.md D1).
    answered = "1girl, fashion photography, blue eyes, high resolution, solo"
    transport = _answer(answered)

    path = tag_hosted(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

    assert path is not None
    assert read(path, TAGS_FILE)["tags"] == answered.split(", ")


@pytest.mark.spec("tagging:output:the-list-is-stored-unnarrowed")
def test_whitespace_is_stripped_and_nothing_else_is(run: Run) -> None:
    transport = _answer("  1girl ,solo,   looking at viewer  ,, ")

    path = tag_hosted(run, FLOW, OllamaTagger("m", transport))

    assert path is not None
    # Empty elements go, because an empty chip is not a tag anyone offered. The
    # order is the model's and no tag is rewritten.
    assert read(path, TAGS_FILE)["tags"] == ["1girl", "solo", "looking at viewer"]


@pytest.mark.spec("tagging:output:artifact-is-a-list-of-tags")
def test_the_local_artifact_is_scored_and_sorted_under_its_own_directory(
    run: Run, local: LocalTagger
) -> None:
    path = tag_wd14(run, FLOW, lambda: local)

    assert path is not None
    assert path.parent == run.directory(FLOW, WD14)
    assert read(path, WD14_FILE)["tags"] == [{"tag": "1girl", "confidence": 0.9}]


# --- failure ------------------------------------------------------------------


@pytest.mark.spec("tagging:failure:a-response-with-no-comma-is-permanent")
def test_a_response_with_no_comma_is_a_permanent_failure(run: Run) -> None:
    transport = _answer("The photograph shows a person standing in a garden.")

    with pytest.raises(Refusal) as refused:
        tag_hosted(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

    assert "permanent" in str(refused.value)
    recorded = list(run.directory(FLOW, TAGS).glob("*.error.*.json"))
    assert [path.name for path in recorded] == ["001.error.1.permanent.json"]


@pytest.mark.spec("tagging:failure:a-response-with-no-comma-is-permanent")
def test_a_single_comma_is_enough_and_content_is_never_judged(run: Run) -> None:
    # One comma separates "not a list at all" from "wrong", and only the first is
    # a failure here. Anything richer starts filtering (design.md D15).
    path = tag_hosted(run, FLOW, OllamaTagger("m", _answer("nonsense, drivel")))

    assert path is not None
    assert read(path, TAGS_FILE)["tags"] == ["nonsense", "drivel"]


@pytest.mark.spec("tagging:failure:a-response-with-no-comma-is-permanent")
def test_the_refusal_names_the_verb_the_operator_would_actually_run(run: Run) -> None:
    # `python -m isekai tags` does not exist: one verb writes both lists (0032
    # design D2), so naming the stage here would name a command that refuses
    # with "unknown verb".
    with pytest.raises(Refusal) as refused:
        tag_hosted(run, FLOW, OllamaTagger("m", _answer("prose with no separator")))

    message = str(refused.value)
    assert f"python -m isekai tag --flow {FLOW} {run.id}" in message
    assert f"{FLOW}/{TAGS}/" in message


@pytest.mark.spec("tagging:budget:each-tagger-has-its-own-budget")
def test_the_hosted_tagger_stops_after_its_own_three_attempts(run: Run) -> None:
    directory = run.directory(FLOW, TAGS)
    directory.mkdir(parents=True, exist_ok=True)
    for _ in range(3):
        record_failure(directory, 1, "transient", {"stage": TAGS, "detail": "x"})
    tagger = FakeTagger()

    with pytest.raises(Refusal) as refused:
        tag_hosted(run, FLOW, tagger)

    assert "3 attempts" in str(refused.value)
    assert tagger.calls == []


# --- independence -------------------------------------------------------------


@pytest.mark.spec("tagging:independence:a-complete-tagger-makes-no-call")
def test_a_second_pass_over_a_complete_hosted_artifact_makes_no_call(
    run: Run,
) -> None:
    tagger = FakeTagger()
    assert tag_hosted(run, FLOW, tagger) is not None

    assert tag_hosted(run, FLOW, tagger) is None
    assert len(tagger.calls) == 1


@pytest.mark.spec("tagging:independence:a-complete-tagger-makes-no-call")
def test_a_second_pass_over_a_complete_local_artifact_opens_no_session(
    run: Run, local: LocalTagger
) -> None:
    assert tag_wd14(run, FLOW, lambda: local) is not None

    assert tag_wd14(run, FLOW, lambda: local) is None
    assert isinstance(local.session, FakeSession)
    assert local.session.calls == 1


@pytest.mark.spec("tagging:independence:each-tagger-resumes-on-its-own")
def test_a_failed_hosted_tagger_leaves_the_local_artifact_complete(
    run: Run, local: LocalTagger
) -> None:
    written = tag_wd14(run, FLOW, lambda: local)

    with pytest.raises(Refusal):
        tag_hosted(run, FLOW, OllamaTagger("m", _answer("prose, ".replace(", ", ""))))

    assert written is not None and written.is_file()
    assert read(written, WD14_FILE)["tags"] == [{"tag": "1girl", "confidence": 0.9}]
    # And the complete one is not re-run to repair the failed one.
    assert tag_wd14(run, FLOW, lambda: fake_tagger([1.0, 1.0, 1.0])) is None


@pytest.mark.spec("tagging:independence:each-tagger-resumes-on-its-own")
def test_the_two_taggers_write_into_two_directories(
    run: Run, local: LocalTagger
) -> None:
    scored = tag_wd14(run, FLOW, lambda: local)
    hosted = tag_hosted(run, FLOW, FakeTagger())

    assert scored is not None and hosted is not None
    assert scored.parent != hosted.parent
    assert {scored.parent.name, hosted.parent.name} == {WD14, TAGS}


# --- provenance ---------------------------------------------------------------


@pytest.mark.spec("tagging:provenance:the-local-tagger-declares-its-pin")
def test_the_local_producer_claims_a_pin_and_names_both_digests(
    run: Run, local: LocalTagger
) -> None:
    path = tag_wd14(run, FLOW, lambda: local)

    assert path is not None
    producer = read(path, WD14_FILE)["producer"]
    # The first producer in this repository that can honestly claim one: a local
    # file with a digest is not the hosted service `pinned` was written for
    # (design.md D17).
    assert producer["pinned"] is True
    assert producer["implementation"] == "wd14"
    # **The digests the session was verified against**, carried through from
    # `verified_paths`, not re-read from the manifest at write time. They are the
    # fake's, which is what proves they came from the tagger rather than from
    # `config/vocabulary.json` -- a re-read would have recorded the real ones.
    assert producer["artifacts"] == FAKE_PINS


@pytest.mark.spec("tagging:provenance:the-local-tagger-declares-its-pin")
def test_the_real_pins_are_the_two_the_manifest_commits(tmp_path: Path) -> None:
    # And the shape the fake stands in for: both entries the vocabulary manifest
    # declares, each with the digest it commits. Either alone is half a claim.
    manifest = provision.load_manifest(provision.VOCABULARY_MANIFEST_PATH)

    assert set(FAKE_PINS) == {entry["dest"] for entry in manifest["entries"]}
    assert all(set(pin) == {"sha256"} for pin in FAKE_PINS.values())


@pytest.mark.spec("tagging:provenance:the-hosted-tagger-records-its-prompt-digest")
def test_the_hosted_producer_records_the_prompt_digest_and_no_path(run: Run) -> None:
    path = tag_hosted(run, FLOW, FakeTagger())

    assert path is not None
    producer = read(path, TAGS_FILE)["producer"]
    assert producer["pinned"] is False
    # Digest only. A module constant has no file, and a record that invented a
    # path would assert a location that does not exist (design.md D16).
    assert producer["prompt"] == constant_record(TAG_PROMPT)
    assert "path" not in producer["prompt"]


@pytest.mark.spec("tagging:provenance:the-hosted-tagger-records-its-prompt-digest")
def test_constant_record_carries_a_digest_and_nothing_else() -> None:
    record = constant_record("some instructions\n")

    assert set(record) == {"sha256"}
    assert len(record["sha256"]) == 64


@pytest.mark.spec("tagging:provenance:the-hosted-tagger-records-its-prompt-digest")
def test_the_producer_names_the_model_that_actually_answered(run: Run) -> None:
    transport = _answer("1girl, solo")

    path = tag_hosted(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

    assert path is not None
    producer = read(path, TAGS_FILE)["producer"]
    assert producer["implementation"] == "ollama"
    assert producer["models"] == ["joycaption-beta-one-q4k"]


@pytest.mark.spec_exempt("structural: the separator this stage splits on")
def test_the_separator_is_a_comma() -> None:
    assert SEPARATOR == ","


# --- resolution and ordering, through the CLI ---------------------------------


@pytest.mark.spec("tagging:independence:the-local-tagger-needs-no-model-key")
def test_the_local_tagger_resolves_identically_for_every_tracked_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Proved by calling it, with the 467 MB open replaced: every tracked flow
    # gets a tagger, none of them is refused, and **no flow is ever read** -- no
    # manifest key names the local tagger's model, because it is a file this
    # build pins and there is no flow for which it would be wrong (design.md D3).
    opened = fake_tagger()
    monkeypatch.setattr(wiring, "open_session", lambda *_a, **_k: opened)

    tracked = tracked_flows()

    resolved = {flow_id: wiring.tagger_for(load_flow(flow_id)) for flow_id in tracked}

    assert tracked
    assert all(pair == opened for pair in resolved.values())


@pytest.mark.spec("tagging:independence:the-hosted-tagger-runs-the-flows-model")
@pytest.mark.parametrize("flow_id", tracked_flows())
def test_the_hosted_tagger_runs_the_model_the_flow_names(flow_id: str) -> None:
    """There is no absence case left, which is what this replaces.

    The scenario it retires described a flow declaring no hosted model. `model`
    is required of every flow now, so that state is not merely unreached but
    unrepresentable -- the loader refuses the manifest before anything resolves.
    What is asserted instead is what the tagger does (design.md D25).
    """
    flow = load_flow(flow_id)

    resolved = wiring.hosted_tagger_for(flow)

    assert isinstance(resolved, OllamaTagger)
    assert resolved.implementation == "ollama"
    assert resolved.model == flow.model


@pytest.mark.spec("tagging:independence:the-hosted-tagger-runs-the-flows-model")
def test_each_flow_gets_a_hosted_tagger_on_the_model_its_own_reader_runs() -> None:
    """Resolved per flow, on the key the reader also reads.

    One alias answers both prompts, which is why the tag prompt is not
    chat-framed -- so the tagger's model being the reader's model is asserted
    rather than left as a coincidence of the two flows shipping the same alias.
    """
    for flow_id in tracked_flows():
        flow = load_flow(flow_id)

        tagger = wiring.hosted_tagger_for(flow)
        reader = wiring.reader_for(flow)

        assert isinstance(tagger, OllamaTagger)
        assert isinstance(reader, OllamaReader)
        assert tagger.model == reader.model == flow.model


class Failing:
    """A hosted tagger that cannot succeed, however many times it is asked."""

    def tag(self, photo: Path) -> Tagging:
        raise StageFailure("permanent", "the host answered with prose")


def _wired(
    tmp_path: Path,
    *,
    tagger: Callable[[Flow], LocalTagger] | None = None,
    hosted: Tagger | None = None,
    flows_dir: Path = FLOWS_DIR,
) -> Wiring:
    """Return an offline wiring, with the taggers a test means to vary."""
    return Wiring(
        reader=Always(FakeReader()),
        tagger=fake_wd14() if tagger is None else tagger,
        hosted_tagger=Always(FakeTagger() if hosted is None else hosted),
        client=None,
        vocabulary=lambda: Vocabulary("v", "r" * 40, "d" * 64, {}),
        field_map=lambda _: FIELD_MAP,
        runs_root=tmp_path / "runs",
        out=io.StringIO(),
        err=io.StringIO(),
        flows_dir=flows_dir,
    )


def _photo(tmp_path: Path) -> Path:
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    return photo


def _dispatch(wired: Wiring, *argv: str) -> int:
    return dispatch(build_parser().parse_args(list(argv)), wired)


@pytest.mark.spec("tagging:order:a-late-failure-leaves-the-earlier-artifacts-complete")
def test_a_failing_hosted_tagger_leaves_the_wd14_list_on_disk(
    tmp_path: Path,
) -> None:
    photo = _photo(tmp_path)
    wired = _wired(tmp_path, hosted=Failing())

    status = _dispatch(wired, "tag", "--flow", FLOW, str(photo))

    assert status == 1
    run = open_run(photo, wired.runs_root)
    assert (run.directory(FLOW, WD14) / "001.json").is_file()
    assert not list(run.directory(FLOW, TAGS).glob("001.json"))
    assert (run.directory(FLOW, TAGS) / "001.error.1.permanent.json").is_file()


def _unreadable(flow: Flow) -> LocalTagger:
    """Return a local tagger whose session cannot decode this photograph."""

    class Broken:
        def run(self, photo: Path) -> list[float]:
            raise OSError("cannot identify image file")

    return dataclasses.replace(fake_tagger(), session=Broken())


def _unopenable(flow: Flow) -> LocalTagger:
    """Refuse the way an absent model file does: for the build, not a photograph."""
    raise Refusal("wd14/model.onnx is absent; provision the vocabulary")


@pytest.mark.spec("tagging:order:a-local-failure-leaves-the-hosted-list-written")
@pytest.mark.parametrize(
    ("resolver", "names"),
    [(_unreadable, "cannot identify image file"), (_unopenable, "is absent")],
    ids=["a-failing-photograph", "an-unopenable-tagger"],
)
def test_a_failing_local_tagger_leaves_the_hosted_list_written(
    tmp_path: Path, resolver: Callable[[Flow], LocalTagger], names: str
) -> None:
    photo = _photo(tmp_path)
    hosted = FakeTagger()
    wired = _wired(tmp_path, tagger=resolver, hosted=hosted)

    status = _dispatch(wired, "tag", "--flow", FLOW, str(photo))

    assert status == 1
    run = open_run(photo, wired.runs_root)
    assert (run.directory(FLOW, TAGS) / "001.json").is_file()
    assert hosted.calls == [run.photo]
    assert not (run.directory(FLOW, WD14) / "001.json").is_file()
    assert isinstance(wired.err, io.StringIO)
    assert names in wired.err.getvalue()


@pytest.mark.spec("tagging:order:captioning-writes-no-tag-list")
def test_captioning_writes_the_prose_and_calls_no_tagger(tmp_path: Path) -> None:
    photo = _photo(tmp_path)
    local = fake_tagger()
    hosted = FakeTagger()
    wired = _wired(tmp_path, tagger=Always(local), hosted=hosted)

    status = _dispatch(wired, "caption", "--flow", FLOW, str(photo))

    assert status == 0
    run = open_run(photo, wired.runs_root)
    assert (run.directory(FLOW, "captions") / "001.json").is_file()
    assert not run.directory(FLOW, WD14).exists()
    assert not run.directory(FLOW, TAGS).exists()
    assert isinstance(local.session, FakeSession)
    assert local.session.calls == 0
    assert hosted.calls == []


@pytest.mark.spec(
    "cli:resolution:a-pinned-seam-resolves-for-every-flow-that-declares-it"
)
@pytest.mark.parametrize("flow_id", tracked_flows())
def test_tagging_a_tracked_flow_resolves_and_runs_the_local_tagger(
    tmp_path: Path, flow_id: str
) -> None:
    photo = _photo(tmp_path)
    local = fake_tagger()
    wired = _wired(tmp_path, tagger=Always(local))

    status = _dispatch(wired, "tag", "--flow", flow_id, str(photo))

    assert status == 0
    run = open_run(photo, wired.runs_root)
    assert (run.directory(flow_id, WD14) / "001.json").is_file()
    assert isinstance(local.session, FakeSession)
    assert local.session.calls == 1
    # The label index is the flow's vocabulary, which the sheet reads; nothing
    # in the manifest names the model the local tagger runs.
    flow = load_flow(flow_id)
    assert flow.tagger is True
    assert MODEL_DEST not in (flow.path / MANIFEST_NAME).read_text()


def _untagged_flows(tmp_path: Path) -> Path:
    """Return a flows root holding `summon-anime-wai` and a copy declaring no tagger."""
    root = tmp_path / "flows"
    source = load_flow(FLOW).path
    for name, tagged in ((FLOW, True), ("untagged", False)):
        directory = root / name
        directory.mkdir(parents=True)
        document = json.loads((source / MANIFEST_NAME).read_text())
        document.update(flow=name, tagger=tagged)
        (directory / MANIFEST_NAME).write_text(json.dumps(document, indent=2))
        for sibling in SIBLINGS:
            (directory / sibling).write_bytes((source / sibling).read_bytes())
    return root


@pytest.mark.spec("tagging:declaration:a-flow-without-a-tagger-is-refused")
def test_tagging_a_flow_that_declares_no_tagger_is_refused_before_any_work(
    tmp_path: Path,
) -> None:
    photo = _photo(tmp_path)
    local = fake_tagger()
    hosted = FakeTagger()
    wired = _wired(
        tmp_path,
        tagger=Always(local),
        hosted=hosted,
        flows_dir=_untagged_flows(tmp_path),
    )

    status = _dispatch(wired, "tag", "--flow", FLOW, "--flow", "untagged", str(photo))

    assert status == 1
    assert isinstance(wired.err, io.StringIO)
    message = wired.err.getvalue()
    assert "untagged" in message
    assert '"tagger": false' in message
    assert "drop `--flow untagged`" in message
    # Before any identifier: no run is opened, and the tagged flow named with it
    # is not tagged either.
    assert not wired.runs_root.exists()
    assert isinstance(local.session, FakeSession)
    assert local.session.calls == 0
    assert hosted.calls == []


@pytest.mark.spec_exempt("twin: the refusal above is the declaration's, not the root's")
def test_tagging_the_tagged_flow_alone_from_that_root_succeeds(
    tmp_path: Path,
) -> None:
    """The twin: the refusal is the declaration's, not the scratch root's."""
    photo = _photo(tmp_path)
    wired = _wired(tmp_path, flows_dir=_untagged_flows(tmp_path))

    assert _dispatch(wired, "tag", "--flow", FLOW, str(photo)) == 0


@pytest.mark.spec("tagging:independence:a-complete-tagger-makes-no-call")
def test_a_complete_local_artifact_is_not_paid_for_by_opening_the_graph(
    run: Run, local: LocalTagger
) -> None:
    # The whole reason the seam is a thunk. Opening the tagger hashes 467 MB and
    # loads a graph; a run whose list is already written must not pay for that
    # to return `None`, and a completed run must still resume on a machine that
    # has since emptied `models/` (design.md D14).
    assert tag_wd14(run, FLOW, lambda: local) is not None

    def refuse() -> LocalTagger:
        raise AssertionError("the completed stage opened the graph anyway")

    assert tag_wd14(run, FLOW, refuse) is None


@pytest.mark.spec("tagging:budget:each-tagger-has-its-own-budget")
def test_a_photograph_the_decoder_cannot_read_is_recorded_and_is_permanent(
    run: Run,
) -> None:
    # The budget of one is not decoration: what can still fail once the session
    # is open is this photograph's own bytes, and that is permanent by
    # construction. Without a record, `show` and the run directory would carry
    # no trace of it while an identical `tags` failure leaves one.
    def unreadable() -> LocalTagger:
        tagger = fake_tagger()

        class Broken:
            def run(self, photo: Path) -> list[float]:
                raise OSError("cannot identify image file")

        return dataclasses.replace(tagger, session=Broken())

    with pytest.raises(Refusal) as refused:
        tag_wd14(run, FLOW, unreadable)

    assert "permanent" in str(refused.value)
    recorded = list(run.directory(FLOW, WD14).glob("*.error.*.json"))
    assert [path.name for path in recorded] == ["001.error.1.permanent.json"]

    # And the budget of one is then spent: a second pass refuses without calling.
    with pytest.raises(Refusal) as again:
        tag_wd14(run, FLOW, unreadable)
    assert "failed permanently" in str(again.value)

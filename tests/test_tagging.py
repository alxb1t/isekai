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
from pathlib import Path
from typing import Any

import pytest

from isekai.boundary import provision
from isekai.boundary.claude_cli import CliFailure, constant_record
from isekai.boundary.wd14 import LocalTagger
from isekai.foundation.flow import Flow, Hosted, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    TAGS,
    WD14,
    Run,
    open_run,
    read_artifact,
    record_failure,
)
from isekai.interface import wiring
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.sheet import FakeSorter
from isekai.pipeline.tagging import (
    SEPARATOR,
    TAG_PROMPT,
    TAGGER_OPTIONS,
    FakeTagger,
    OllamaTagger,
    Tagging,
    caption_tags,
    caption_wd14,
)
from isekai.shared.vocabulary import Vocabulary
from tests.images import jpeg_bytes
from tests.stages import FAKE_PINS, Always, FakeSession, fake_tagger, fake_wd14
from tests.transports import FakeTransport

FLOW = "summon-open-v1"


@pytest.fixture
def run(tmp_path: Path) -> Run:
    """Return a run with a photograph in it and nothing else."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    return open_run(photo, tmp_path / "runs")


def _producer(path: Path) -> dict[str, Any]:
    """Return one written artifact's producer record."""
    producer: Any = read_artifact(path)["producer"]
    return producer


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

    caption_tags(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

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
        "repeat_penalty": 1.15,
    }


# --- what is stored -----------------------------------------------------------


@pytest.mark.spec("tagging:output:artifact-is-a-list-of-tags")
def test_the_hosted_artifact_is_a_list_of_tags_under_the_flow(run: Run) -> None:
    path = caption_tags(run, FLOW, FakeTagger())

    assert path is not None
    assert path.parent == run.directory(FLOW, TAGS)
    assert read_artifact(path)["tags"] == ["1girl", "solo", "looking at viewer"]


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

    path = caption_tags(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

    assert path is not None
    assert read_artifact(path)["tags"] == answered.split(", ")


@pytest.mark.spec("tagging:output:the-list-is-stored-unnarrowed")
def test_whitespace_is_stripped_and_nothing_else_is(run: Run) -> None:
    transport = _answer("  1girl ,solo,   looking at viewer  ,, ")

    path = caption_tags(run, FLOW, OllamaTagger("m", transport))

    assert path is not None
    # Empty elements go, because an empty chip is not a tag anyone offered. The
    # order is the model's and no tag is rewritten.
    assert read_artifact(path)["tags"] == ["1girl", "solo", "looking at viewer"]


@pytest.mark.spec("tagging:output:artifact-is-a-list-of-tags")
def test_the_local_artifact_is_scored_and_sorted_under_its_own_directory(
    run: Run, local: LocalTagger
) -> None:
    path = caption_wd14(run, FLOW, lambda: local)

    assert path is not None
    assert path.parent == run.directory(FLOW, WD14)
    assert read_artifact(path)["tags"] == [{"tag": "1girl", "confidence": 0.9}]


# --- failure ------------------------------------------------------------------


@pytest.mark.spec("tagging:failure:a-response-with-no-comma-is-permanent")
def test_a_response_with_no_comma_is_a_permanent_failure(run: Run) -> None:
    transport = _answer("The photograph shows a person standing in a garden.")

    with pytest.raises(Refusal) as refused:
        caption_tags(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

    assert "permanent" in str(refused.value)
    recorded = list(run.directory(FLOW, TAGS).glob("*.error.*.json"))
    assert [path.name for path in recorded] == ["001.error.1.permanent.json"]


@pytest.mark.spec("tagging:failure:a-response-with-no-comma-is-permanent")
def test_a_single_comma_is_enough_and_content_is_never_judged(run: Run) -> None:
    # One comma separates "not a list at all" from "wrong", and only the first is
    # a failure here. Anything richer starts filtering (design.md D15).
    path = caption_tags(run, FLOW, OllamaTagger("m", _answer("nonsense, drivel")))

    assert path is not None
    assert read_artifact(path)["tags"] == ["nonsense", "drivel"]


@pytest.mark.spec("tagging:failure:a-response-with-no-comma-is-permanent")
def test_the_refusal_names_the_verb_the_operator_would_actually_run(run: Run) -> None:
    # `python -m isekai tags` does not exist: one verb produces all three
    # artifacts (design.md D8), so naming the stage here would name a command
    # that refuses with "unknown verb".
    with pytest.raises(Refusal) as refused:
        caption_tags(run, FLOW, OllamaTagger("m", _answer("prose with no separator")))

    message = str(refused.value)
    assert "python -m isekai caption" in message
    assert f"{FLOW}/{TAGS}/" in message


@pytest.mark.spec("tagging:budget:each-tagger-has-its-own-budget")
def test_the_hosted_tagger_stops_after_its_own_three_attempts(run: Run) -> None:
    directory = run.directory(FLOW, TAGS)
    directory.mkdir(parents=True, exist_ok=True)
    for _ in range(3):
        record_failure(directory, 1, "transient", {})
    tagger = FakeTagger()

    with pytest.raises(Refusal) as refused:
        caption_tags(run, FLOW, tagger)

    assert "3 attempts" in str(refused.value)
    assert tagger.calls == []


# --- independence -------------------------------------------------------------


@pytest.mark.spec("tagging:independence:a-complete-tagger-makes-no-call")
def test_a_second_pass_over_a_complete_hosted_artifact_makes_no_call(
    run: Run,
) -> None:
    tagger = FakeTagger()
    assert caption_tags(run, FLOW, tagger) is not None

    assert caption_tags(run, FLOW, tagger) is None
    assert len(tagger.calls) == 1


@pytest.mark.spec("tagging:independence:a-complete-tagger-makes-no-call")
def test_a_second_pass_over_a_complete_local_artifact_opens_no_session(
    run: Run, local: LocalTagger
) -> None:
    assert caption_wd14(run, FLOW, lambda: local) is not None

    assert caption_wd14(run, FLOW, lambda: local) is None
    assert isinstance(local.session, FakeSession)
    assert local.session.calls == 1


@pytest.mark.spec("tagging:independence:each-tagger-resumes-on-its-own")
def test_a_failed_hosted_tagger_leaves_the_local_artifact_complete(
    run: Run, local: LocalTagger
) -> None:
    written = caption_wd14(run, FLOW, lambda: local)

    with pytest.raises(Refusal):
        caption_tags(run, FLOW, OllamaTagger("m", _answer("prose, ".replace(", ", ""))))

    assert written is not None and written.is_file()
    assert read_artifact(written)["tags"] == [{"tag": "1girl", "confidence": 0.9}]
    # And the complete one is not re-run to repair the failed one.
    assert caption_wd14(run, FLOW, lambda: fake_tagger([1.0, 1.0, 1.0])) is None


@pytest.mark.spec("tagging:independence:each-tagger-resumes-on-its-own")
def test_the_two_taggers_write_into_two_directories(
    run: Run, local: LocalTagger
) -> None:
    scored = caption_wd14(run, FLOW, lambda: local)
    hosted = caption_tags(run, FLOW, FakeTagger())

    assert scored is not None and hosted is not None
    assert scored.parent != hosted.parent
    assert {scored.parent.name, hosted.parent.name} == {WD14, TAGS}


# --- provenance ---------------------------------------------------------------


@pytest.mark.spec("tagging:provenance:the-local-tagger-declares-its-pin")
def test_the_local_producer_claims_a_pin_and_names_both_digests(
    run: Run, local: LocalTagger
) -> None:
    path = caption_wd14(run, FLOW, lambda: local)

    assert path is not None
    producer = _producer(path)
    # The first producer in this repository that can honestly claim one: a local
    # file with a digest is not the hosted service `pinned` was written for
    # (design.md D17).
    assert producer["pinned"] is True
    assert producer["implementation"] == "wd14"
    # **The digests the session was verified against**, carried through from
    # `verified_paths`, not re-read from the manifest at write time. They are the
    # fake's, which is what proves they came from the tagger rather than from
    # `scripts/vocabulary.json` -- a re-read would have recorded the real ones.
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
    path = caption_tags(run, FLOW, FakeTagger())

    assert path is not None
    producer = _producer(path)
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

    path = caption_tags(run, FLOW, OllamaTagger("joycaption-beta-one-q4k", transport))

    assert path is not None
    producer = _producer(path)
    assert producer["implementation"] == "ollama"
    assert producer["models"] == ["joycaption-beta-one-q4k"]


@pytest.mark.spec_exempt("structural: the separator this stage splits on")
def test_the_separator_is_a_comma() -> None:
    assert SEPARATOR == ","


# --- resolution and ordering, through the CLI ---------------------------------


@pytest.mark.spec("tagging:independence:the-local-tagger-needs-no-manifest-key")
def test_the_local_tagger_resolves_identically_for_every_tracked_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Proved by calling it, with the 467 MB open replaced: every tracked flow
    # gets a tagger, none of them is refused, and **no flow is ever read** -- the
    # local tagger resolves through no manifest key, because it is a file this
    # build pins and there is no flow for which it would be wrong (design.md D3).
    opened = fake_tagger()
    monkeypatch.setattr(wiring, "open_session", lambda *_a, **_k: opened)

    resolved = {
        flow_id: wiring.tagger_for(load_flow(flow_id))
        for flow_id in ("summon-v1", "conjure-v1", "summon-open-v1")
    }

    assert set(resolved) == {"summon-v1", "conjure-v1", "summon-open-v1"}
    assert all(pair == opened for pair in resolved.values())
    # Two of those three declare no `hosted` block at all, which is the case a
    # key-driven registry would have had to refuse or default.
    assert [load_flow(flow_id).hosted is None for flow_id in resolved] == [
        True,
        True,
        False,
    ]


@pytest.mark.spec(
    "tagging:independence:the-hosted-tagger-is-absent-without-a-hosted-block"
)
@pytest.mark.parametrize(
    ("flow_id", "expected"),
    [("summon-v1", None), ("conjure-v1", None), ("summon-open-v1", "ollama")],
)
def test_the_hosted_tagger_resolves_only_where_a_flow_declares_an_arm(
    flow_id: str, expected: str | None
) -> None:
    resolved = wiring.hosted_tagger_for(load_flow(flow_id))

    if expected is None:
        # Absent, not refused. A flow with no `hosted` block simply has no hosted
        # tag list, and that may not stop a review (design.md D20).
        assert resolved is None
    else:
        assert isinstance(resolved, OllamaTagger)
        assert resolved.implementation == expected


@pytest.mark.spec(
    "cli:resolution:a-seam-without-a-manifest-key-resolves-for-every-flow"
)
def test_two_flows_on_two_arms_each_get_their_own_hosted_tagger() -> None:
    hosted = wiring.hosted_tagger_for(load_flow("summon-open-v1"))
    default = wiring.hosted_tagger_for(load_flow("summon-v1"))

    assert isinstance(hosted, OllamaTagger)
    assert hosted.model == "joycaption-beta-one-q4k"
    assert default is None
    # `claude-cli` is in the table and maps to nothing, which is not the same as
    # being absent from it: an arm this build has never heard of must name what
    # it does carry rather than resolve to silence.
    assert wiring.HOSTED_TAGGERS.keys() == {"claude-cli", "ollama"}
    assert wiring.HOSTED_TAGGERS["claude-cli"](load_flow("summon-v1")) is None


@pytest.mark.spec("tagging:order:a-late-failure-leaves-the-earlier-artifacts-complete")
def test_a_failing_hosted_tagger_leaves_the_caption_and_the_wd14_list_on_disk(
    tmp_path: Path,
) -> None:
    # `across()` catches `Refusal` per *input*, not per stage, so the ordering is
    # the failure isolation: prose, then the deterministic local tagger, then the
    # one with a port and a retry budget (design.md D7).
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    flow = "summon-v1"

    class Failing:
        """A hosted tagger that cannot succeed, however many times it is asked."""

        def tag(self, photo: Path) -> Tagging:
            raise CliFailure("permanent", "the host answered with prose")

    wired = Wiring(
        reader=Always(FakeReader()),
        sorter=Always(FakeSorter(answers={})),
        tagger=fake_wd14(),
        hosted_tagger=Always(Failing()),
        client=None,
        vocabulary=lambda: Vocabulary("v", "r" * 40, "d" * 64, {}),
        runs_root=tmp_path / "runs",
        out=io.StringIO(),
        err=io.StringIO(),
    )

    status = dispatch(
        build_parser().parse_args(["caption", "--flow", flow, str(photo)]), wired
    )

    assert status == 1
    run = open_run(photo, wired.runs_root)
    # Both earlier artifacts are on disk and complete; only the last one failed.
    assert (run.directory(flow, "captions") / "001.json").is_file()
    assert (run.directory(flow, WD14) / "001.json").is_file()
    assert not list(run.directory(flow, TAGS).glob("001.json"))
    assert (run.directory(flow, TAGS) / "001.error.1.permanent.json").is_file()


@pytest.mark.spec("cli:resolution:uncomposed-seam-refuses-by-name")
def test_an_arm_this_build_has_no_tagger_for_refuses_naming_what_it_carries(
    tmp_path: Path,
) -> None:
    # The reason `hosted_tagger_for` goes through `_resolve` rather than a
    # `.get()`: silence is the right answer for "this arm has no tagger" and the
    # wrong one for "nobody has heard of this arm", and only a table tells them
    # apart. Without the table an unknown arm resolves to `None`, and D20 then
    # makes that silence unreportable anywhere by design.
    declared = load_flow("summon-open-v1")
    unknown = dataclasses.replace(
        declared,
        hosted=dataclasses.replace(_hosted(declared), implementation="vllm"),
    )

    with pytest.raises(Refusal) as refused:
        wiring.hosted_tagger_for(unknown)

    message = str(refused.value)
    assert "vllm" in message
    assert "ollama" in message


def _hosted(flow: Flow) -> Hosted:
    """Return `flow`'s hosted block, narrowing away an absence a fixture rules out."""
    assert flow.hosted is not None
    return flow.hosted


@pytest.mark.spec("tagging:independence:a-complete-tagger-makes-no-call")
def test_a_complete_local_artifact_is_not_paid_for_by_opening_the_graph(
    run: Run, local: LocalTagger
) -> None:
    # The whole reason the seam is a thunk. Opening the tagger hashes 467 MB and
    # loads a graph; a run whose list is already written must not pay for that
    # to return `None`, and a completed run must still resume on a machine that
    # has since emptied `models/` (design.md D14).
    assert caption_wd14(run, FLOW, lambda: local) is not None

    def refuse() -> LocalTagger:
        raise AssertionError("the completed stage opened the graph anyway")

    assert caption_wd14(run, FLOW, refuse) is None


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
        caption_wd14(run, FLOW, unreadable)

    assert "permanent" in str(refused.value)
    recorded = list(run.directory(FLOW, WD14).glob("*.error.*.json"))
    assert [path.name for path in recorded] == ["001.error.1.permanent.json"]

    # And the budget of one is then spent: a second pass refuses without calling.
    with pytest.raises(Refusal) as again:
        caption_wd14(run, FLOW, unreadable)
    assert "failed permanently" in str(again.value)

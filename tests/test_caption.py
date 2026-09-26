"""Stage (1): what the reader is given, what it returns, and how it fails.

Every test drives the stage through `FakeReader`, which counts its calls -- so
"no network was reached" is asserted rather than assumed, and so is "no call was
made" when the stage is already complete.
"""

import base64
import json
import re
import urllib.error
from pathlib import Path

import pytest

from isekai.foundation.artifacts import CAPTION_FILE, read
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    BUDGETS,
    CAPTIONS,
    Run,
    StageFailure,
    attempts,
    instructions_record,
    open_run,
    versions,
)
from isekai.pipeline.caption import FakeReader, OllamaReader
from tests.images import jpeg_bytes
from tests.stages import CAPTION_BRIEFING as BRIEFING_PATH
from tests.stages import FLOW, caption
from tests.transports import FakeTransport


@pytest.fixture
def run(tmp_path: Path) -> Run:
    """Return a run with a photograph in it and nothing else."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    return open_run(photo, tmp_path / "runs")


# --- the seam -----------------------------------------------------------------


@pytest.mark.spec("caption:seam:offline-double-satisfies-the-interface")
def test_the_stage_writes_a_caption_with_no_network(run: Run) -> None:
    reader = FakeReader(prose="She is wearing a grey coat.")

    path = caption(run, reader)

    assert path is not None
    assert read(path, CAPTION_FILE)["prose"] == "She is wearing a grey coat."
    assert len(reader.calls) == 1


@pytest.mark.spec("caption:seam:producer-names-the-implementation")
def test_the_producer_names_the_implementation_and_the_models_that_ran(
    run: Run,
) -> None:
    path = caption(run, FakeReader(implementation="fake-reader", models=("a", "b")))

    assert path is not None
    producer = read(path, CAPTION_FILE)["producer"]
    assert producer["implementation"] == "fake-reader"
    assert producer["models"] == ["a", "b"]


@pytest.mark.spec("caption:seam:producer-names-the-implementation")
def test_two_readers_are_distinguishable_from_the_record_alone(
    run: Run, tmp_path: Path
) -> None:
    first = caption(run, FakeReader(implementation="fake-reader"))
    second = caption(run, FakeReader(implementation="other-reader"), new_version=True)

    assert first is not None and second is not None
    assert read(first, CAPTION_FILE)["producer"]["implementation"] == "fake-reader"
    assert read(second, CAPTION_FILE)["producer"]["implementation"] == "other-reader"


@pytest.mark.spec("run-directory:provenance:unpinned-producer-is-declared")
def test_the_hosted_reader_declares_that_it_is_not_pinned(run: Run) -> None:
    path = caption(run, FakeReader())

    assert path is not None
    producer = read(path, CAPTION_FILE)["producer"]
    assert producer["pinned"] is False
    assert "revision" not in producer


# --- the inputs ---------------------------------------------------------------


@pytest.mark.spec("caption:inputs:only-the-photograph-is-passed")
def test_the_reader_receives_the_photograph_and_its_briefing_and_nothing_else(
    run: Run,
) -> None:
    reader = FakeReader()

    caption(run, reader)

    ((photo, briefing),) = reader.calls
    assert photo == run.photo
    assert briefing == BRIEFING_PATH.read_text()


@pytest.mark.spec("caption:inputs:only-the-photograph-is-passed")
def test_the_briefing_names_no_schema_field() -> None:
    text = BRIEFING_PATH.read_text().lower()
    words = set(re.findall(r"[a-z_]+", text))

    schema = FLOW.schema
    named = [name for name in schema.names if name in words or name in text]
    assert named == []


@pytest.mark.spec("caption:inputs:only-the-photograph-is-passed")
def test_the_briefing_mentions_no_vocabulary_and_no_flow() -> None:
    text = BRIEFING_PATH.read_text().lower()

    for forbidden in ("schema", "vocabulary", "tag", "flow", "json", "field"):
        assert forbidden not in text, forbidden


# --- the output ---------------------------------------------------------------


@pytest.mark.spec("caption:output:artifact-is-prose")
def test_the_artifact_is_one_block_of_prose_and_carries_no_structure(
    run: Run,
) -> None:
    path = caption(run, FakeReader(prose="Two sentences. Like this."))

    assert path is not None
    artifact = read(path, CAPTION_FILE)
    assert artifact["prose"] == "Two sentences. Like this."
    assert set(artifact) == {"schema", "producer", "prose"}


@pytest.mark.spec("caption:output:caption-belongs-to-one-flow")
def test_a_second_flow_produces_its_own_caption(run: Run) -> None:
    reader = FakeReader()
    first = caption(run, reader)

    # A flow arriving later asks the same stage for the same photograph, and gets
    # its own reading: its briefing is part of its own frozen directory, so it
    # cannot inherit a reading written to answer a different question.
    second = caption(run, reader, flow="summon-v2")

    assert first is not None and second is not None
    assert first.parent == run.path / FLOW.id / "captions"
    assert second.parent == run.path / "summon-v2" / "captions"
    assert len(reader.calls) == 2


@pytest.mark.spec("caption:output:caption-belongs-to-one-flow")
def test_a_flows_caption_is_neither_read_nor_changed_by_another(run: Run) -> None:
    first = caption(run, FakeReader(prose="One reading."))
    assert first is not None
    frozen = first.read_bytes()

    caption(run, FakeReader(prose="A different reading."), flow="summon-v2")

    assert first.read_bytes() == frozen
    assert versions(run.path / FLOW.id / "captions") == [1]


@pytest.mark.spec("caption:inputs:briefing-comes-from-the-flow")
def test_the_standing_instructions_come_from_the_flows_own_directory(
    run: Run,
) -> None:
    reader = FakeReader()

    path = caption(run, reader)

    assert path is not None
    assert BRIEFING_PATH.parent == FLOW.path
    assert reader.calls[0][1] == BRIEFING_PATH.read_text()
    recorded = read(path, CAPTION_FILE)["producer"]["briefing"]
    assert recorded == instructions_record(BRIEFING_PATH)


@pytest.mark.spec("caption:absence:absence-is-permitted-here")
def test_an_absence_statement_survives_into_the_artifact(run: Run) -> None:
    prose = "There is no jewellery visible, and no tattoos on the forearms."

    path = caption(run, FakeReader(prose=prose))

    assert path is not None
    assert read(path, CAPTION_FILE)["prose"] == prose


@pytest.mark.spec("caption:absence:absence-is-permitted-here")
def test_the_briefing_licenses_the_reader_to_state_absence() -> None:
    text = BRIEFING_PATH.read_text().lower()

    assert "not visible" in text or "is not there" in text


@pytest.mark.spec("run-directory:provenance:producer-records-the-briefing")
def test_the_producer_records_the_briefings_path_and_digest(
    run: Run, tmp_path: Path
) -> None:
    other = tmp_path / "other.md"
    other.write_text("Different standing instructions entirely.")

    first = caption(run, FakeReader())
    second = caption(run, FakeReader(), new_version=True, briefing_path=other)

    assert first is not None and second is not None
    one = read(first, CAPTION_FILE)["producer"]["briefing"]
    two = read(second, CAPTION_FILE)["producer"]["briefing"]
    assert one["path"] == "flows/summon-anime-wai/caption.briefing.md"
    assert one["sha256"] != two["sha256"]
    assert instructions_record(BRIEFING_PATH)["sha256"] == one["sha256"]


# --- failure classification ---------------------------------------------------


@pytest.mark.spec("caption:failure:rate-limit-is-transient")
def test_a_transient_failure_counts_against_the_budget(run: Run) -> None:
    reader = FakeReader(failure=StageFailure("transient", "rate limited"))

    with pytest.raises(Refusal):
        caption(run, reader)

    recorded = attempts(run.path / FLOW.id / "captions", 1)
    assert [(a.attempt, a.kind) for a in recorded] == [(1, "transient")]
    assert versions(run.path / FLOW.id / "captions") == []


@pytest.mark.spec("caption:failure:rate-limit-is-transient")
def test_the_stage_refuses_once_the_budget_is_spent(run: Run) -> None:
    reader = FakeReader(failure=StageFailure("transient", "rate limited"))
    for _ in range(BUDGETS["caption"]):
        with pytest.raises(Refusal):
            caption(run, reader)

    before = len(reader.calls)
    with pytest.raises(Refusal) as refused:
        caption(run, reader)

    assert len(reader.calls) == before
    assert run.id in str(refused.value)


@pytest.mark.spec("caption:failure:decline-is-permanent")
def test_a_decline_names_the_photograph_and_writes_no_artifact(run: Run) -> None:
    """The scenario lost its second clause with the second arm (design.md D21).

    It used to assert that no *other implementation* was substituted. With one
    arm that is vacuously true, and this repository has a written standard against
    asserting what cannot fail. What survives is the live half: a decline is
    recorded as permanent, naming the photograph, and no caption is written for
    the attempt.
    """
    reader = FakeReader(failure=StageFailure("permanent", "the reader declined"))

    with pytest.raises(Refusal) as refused:
        caption(run, reader)

    assert run.id in str(refused.value)
    assert "declined" in str(refused.value)
    assert versions(run.path / FLOW.id / "captions") == []


@pytest.mark.spec("caption:failure:unusable-response-is-permanent")
def test_a_response_the_stage_cannot_read_as_prose_is_permanent(
    tmp_path: Path,
) -> None:
    """A 200 carrying nothing readable, which is not a transport failure.

    The host answered and the model ran; what came back is unusable, so the
    adapter -- not `ollama.py` -- is what classifies it, and permanently: a
    second pass over the same photograph returns the same nothing.
    """
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    reader = OllamaReader(
        model="a-reader", transport=FakeTransport(payload={"response": ""})
    )

    with pytest.raises(StageFailure) as failed:
        reader.read(photo, "brief", tmp_path)

    assert failed.value.kind == "permanent"


@pytest.mark.spec("caption:failure:unusable-response-is-permanent")
def test_no_caption_artifact_is_written_for_an_unusable_response(run: Run) -> None:
    reader = FakeReader(failure=StageFailure("permanent", "not prose"))

    with pytest.raises(Refusal):
        caption(run, reader)

    assert versions(run.path / FLOW.id / "captions") == []


# --- the Ollama adapter -------------------------------------------------------


@pytest.mark.spec_exempt("structural: the request body, asserted without a call")
def test_the_open_readers_body_carries_the_photograph_and_the_pinned_sampling(
    tmp_path: Path,
) -> None:
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    reader = OllamaReader(model="a-reader")

    body = reader.body(photo, "Describe the person.")

    assert body["model"] == "a-reader"
    assert body["images"] == [base64.b64encode(photo.read_bytes()).decode()]
    assert body["stream"] is False
    assert body["options"] == {
        "temperature": 0,
        "seed": 1,
        "num_predict": 1024,
        # The window Ollama was already resolving, pinned so it stops depending
        # on the host: measured 1275 + 1024 of 4096, with the photograph's share
        # constant across sizes. See `READER_OPTIONS` for the table.
        "num_ctx": 4096,
    }


@pytest.mark.spec("caption:inputs:only-the-photograph-is-passed")
def test_the_open_reader_is_sent_no_schema_and_no_structure(tmp_path: Path) -> None:
    """No `format`, no schema, no field list: structure is stage (2)'s to require.

    Pressing a reader into a field list is measured to make it invent. `format` is
    the field that would do it on this transport, and its absence is the assertion.
    """
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))

    body = OllamaReader(model="a-reader").body(photo, "Describe the person.")

    assert "format" not in body
    assert "schema" not in body
    assert not any("schema" in str(value).lower() for value in body["options"])


@pytest.mark.spec_exempt("structural: the photograph is sent unresized")
def test_the_photograph_is_sent_as_its_own_bytes_unresized(tmp_path: Path) -> None:
    """The bytes on disk are the bytes on the wire, decoded back to prove it.

    Nothing is resampled and nothing needs to be: the vision tower encodes at
    patch14-384 whatever it is handed, and the decoder PIL would provide is in the
    `eval` extra, which this module may not import.
    """
    photo = tmp_path / "aunt-ada.jpg"
    original = jpeg_bytes(1600, 1200)
    photo.write_bytes(original)

    body = OllamaReader(model="a-reader").body(photo, "Describe.")

    assert base64.b64decode(body["images"][0]) == original


@pytest.mark.spec("caption:inputs:only-the-photograph-is-passed")
def test_the_open_reader_ignores_the_workspace_and_reads_the_file_itself(
    tmp_path: Path,
) -> None:
    """A workspace the photograph is nowhere inside, and the caption still arrives.

    The argument is in the `Reader` Protocol because a reader may need a directory
    granted to it. This one is handed the bytes, so the parameter is inert --
    asserted rather than assumed, because an adapter that quietly needed it would
    fail only on a real machine.
    """
    photo = tmp_path / "elsewhere" / "aunt-ada.jpg"
    photo.parent.mkdir()
    photo.write_bytes(jpeg_bytes(1200, 900))
    reader = OllamaReader(
        model="a-reader", transport=FakeTransport(payload={"response": "A person."})
    )

    reading = reader.read(photo, "Describe.", tmp_path / "not-the-photos-home")

    assert reading.prose == "A person."


@pytest.mark.spec_exempt("structural: the path is not in the open reader's prompt")
def test_the_open_readers_prompt_carries_no_path_from_this_machine(
    tmp_path: Path,
) -> None:
    """No path from this machine goes to the model, because none would mean anything.

    This reader is handed the bytes, so a path would be an unactionable
    instruction and a detail about the operator's machine sent for nothing.
    """
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))

    body = OllamaReader(model="a-reader").body(photo, "Describe the person.")

    assert str(photo) not in body["prompt"]
    assert str(tmp_path) not in json.dumps(body["prompt"])


@pytest.mark.spec("caption:selection:the-flow-names-the-model")
def test_the_readers_artifact_names_ollama_and_the_model_that_ran(
    run: Run,
) -> None:
    reader = OllamaReader(
        model="a-reader", transport=FakeTransport(payload={"response": "A person."})
    )

    path = caption(run, reader)

    assert path is not None
    producer = read(path, CAPTION_FILE)["producer"]
    assert producer["implementation"] == "ollama"
    assert producer["models"] == ["a-reader"]
    assert producer["pinned"] is False


@pytest.mark.spec("caption:reachability:unreachable-host-refuses-without-an-attempt")
def test_an_unreachable_host_refuses_and_records_no_attempt(run: Run) -> None:
    """The refusal names what to start, and the error-record directory stays empty.

    Asserting the directory rather than merely that a refusal was raised is the
    point: a spent attempt leaves a run whose records have to be deleted by hand
    before it can resume, and a server that is not running is not a model tried
    and failed.
    """
    reader = OllamaReader(
        model="a-reader",
        transport=FakeTransport(error=urllib.error.URLError("Connection refused")),
    )

    with pytest.raises(Refusal) as refused:
        caption(run, reader)

    assert "ollama serve" in str(refused.value)
    directory = run.directory(FLOW.id, CAPTIONS)
    assert attempts(directory, 1) == []
    assert not any(path.name.endswith(".json") for path in directory.glob("*.error.*"))


@pytest.mark.spec("caption:reachability:absent-model-names-how-to-create-it")
def test_an_absent_model_names_the_command_that_creates_it_and_costs_no_attempt(
    run: Run,
) -> None:
    """The reader's remedy is `ollama create`, not `ollama pull`.

    The alias is machine-local and built from the committed recipe, so naming the
    registry command instead would send the operator after a tag that does not
    exist.
    """
    reader = OllamaReader(
        model="a-reader",
        transport=FakeTransport(payload={"error": "not found"}, status=404),
    )

    with pytest.raises(Refusal) as refused:
        caption(run, reader)

    message = str(refused.value)
    assert "ollama create a-reader" in message
    assert "scripts/joycaption.Modelfile" in message
    directory = run.directory(FLOW.id, CAPTIONS)
    assert attempts(directory, 1) == []


@pytest.mark.spec("caption:failure:rate-limit-is-transient")
def test_an_open_reader_failure_is_recorded_with_its_kind(run: Run) -> None:
    """A real failure does spend an attempt, which is what makes the two distinct.

    Without this the "records no attempt" assertions above would pass for a stage
    that never records anything at all.
    """
    reader = OllamaReader(
        model="a-reader", transport=FakeTransport(payload={"error": "busy"}, status=503)
    )

    with pytest.raises(Refusal):
        caption(run, reader)

    recorded = attempts(run.directory(FLOW.id, CAPTIONS), 1)
    assert [one.kind for one in recorded] == ["transient"]


@pytest.mark.spec("caption:failure:decline-is-permanent")
def test_a_truncated_response_is_recorded_permanent_and_written_nowhere(
    run: Run,
) -> None:
    """The truncation row: a permanent failure is recorded and surfaced.

    Never routed around and never assembled from something else -- the artifact
    that is not written is the assertion, because writing one would mean a
    provenance record naming a read that did not produce it.
    """
    reader = OllamaReader(
        model="a-reader",
        transport=FakeTransport(payload={"response": "A per", "done_reason": "length"}),
    )

    with pytest.raises(Refusal):
        caption(run, reader)

    directory = run.directory(FLOW.id, CAPTIONS)
    recorded = attempts(directory, 1)
    assert [one.kind for one in recorded] == ["permanent"]
    assert "length" in json.loads(recorded[0].path.read_text())["detail"]
    assert versions(directory) == []

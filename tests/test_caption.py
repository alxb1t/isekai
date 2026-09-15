"""Stage (1): what the reader is given, what it returns, and how it fails.

Every test drives the stage through `FakeReader`, which counts its calls -- so
"no network was reached" is asserted rather than assumed, and so is "no call was
made" when the stage is already complete.
"""

import json
import re
from collections.abc import Sequence
from pathlib import Path

import pytest

from isekai.caption import (
    BRIEFING_PATH,
    ClaudeReader,
    FakeReader,
    Reading,
    caption,
)
from isekai.claude_cli import (
    BASE_FLAGS,
    CliFailure,
    classify,
    instructions_record,
    models_that_ran,
)
from isekai.refusal import Refusal
from isekai.run import BUDGETS, Run, attempts, open_run, read_artifact, versions
from isekai.sheet import load_schema
from tests.images import jpeg_bytes


@pytest.fixture
def run(tmp_path: Path) -> Run:
    """Return a run with a photograph in it and nothing else."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    return open_run(photo, tmp_path / "runs")


def _envelope(**fields: object) -> str:
    """Return a `claude -p --output-format json` envelope as the CLI prints it."""
    body = {"type": "result", "subtype": "success", "is_error": False}
    body.update(fields)
    return json.dumps(body)


# --- the seam -----------------------------------------------------------------


@pytest.mark.spec("caption:seam:offline-double-satisfies-the-interface")
def test_the_stage_writes_a_caption_with_no_network(run: Run) -> None:
    reader = FakeReader(prose="She is wearing a grey coat.")

    path = caption(run, reader)

    assert path is not None
    assert read_artifact(path)["prose"] == "She is wearing a grey coat."
    assert len(reader.calls) == 1


@pytest.mark.spec("caption:seam:producer-names-the-implementation")
def test_the_producer_names_the_implementation_and_the_models_that_ran(
    run: Run,
) -> None:
    path = caption(run, FakeReader(implementation="fake-reader", models=("a", "b")))

    assert path is not None
    producer = read_artifact(path)["producer"]
    assert producer["implementation"] == "fake-reader"
    assert producer["models"] == ["a", "b"]


@pytest.mark.spec("caption:seam:producer-names-the-implementation")
def test_two_readers_are_distinguishable_from_the_record_alone(
    run: Run, tmp_path: Path
) -> None:
    first = caption(run, FakeReader(implementation="fake-reader"))
    second = caption(run, FakeReader(implementation="other-reader"), new_version=True)

    assert first is not None and second is not None
    assert read_artifact(first)["producer"]["implementation"] == "fake-reader"
    assert read_artifact(second)["producer"]["implementation"] == "other-reader"


@pytest.mark.spec("run-directory:provenance:unpinned-producer-is-declared")
def test_the_hosted_reader_declares_that_it_is_not_pinned(run: Run) -> None:
    path = caption(run, FakeReader())

    assert path is not None
    producer = read_artifact(path)["producer"]
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

    named = [name for name in load_schema().names if name in words or name in text]
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
    artifact = read_artifact(path)
    assert artifact["prose"] == "Two sentences. Like this."
    assert set(artifact) == {"schema", "producer", "prose"}


@pytest.mark.spec("caption:output:caption-is-flow-neutral")
def test_a_second_flow_reuses_the_existing_caption(run: Run) -> None:
    reader = FakeReader()
    first = caption(run, reader)

    # A flow arriving later asks the same stage for the same run. Nothing about
    # a flow is an input here, so there is nothing to ask differently.
    again = caption(run, reader)

    assert first is not None and again is None
    assert versions(run.path / "captions") == [1]
    assert len(reader.calls) == 1


@pytest.mark.spec("caption:absence:absence-is-permitted-here")
def test_an_absence_statement_survives_into_the_artifact(run: Run) -> None:
    prose = "There is no jewellery visible, and no tattoos on the forearms."

    path = caption(run, FakeReader(prose=prose))

    assert path is not None
    assert read_artifact(path)["prose"] == prose


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
    one = read_artifact(first)["producer"]["briefing"]
    two = read_artifact(second)["producer"]["briefing"]
    assert one["path"] == "briefings/caption.md"
    assert one["sha256"] != two["sha256"]
    assert instructions_record(BRIEFING_PATH)["sha256"] == one["sha256"]


# --- the adapter --------------------------------------------------------------


@pytest.mark.spec_exempt("structural: the invocation's locked-down argument vector")
def test_the_argument_vector_carries_every_load_bearing_flag(tmp_path: Path) -> None:
    argv = ClaudeReader().argv(tmp_path / "photo.jpg", tmp_path, "the briefing")

    for flag in (
        "--safe-mode",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--permission-prompts",
        "--output-format",
    ):
        assert flag in argv
    assert argv[argv.index("--tools") + 1] == "Read"
    assert argv[argv.index("--add-dir") + 1] == str(tmp_path)
    assert argv[argv.index("--permission-prompts") + 1] == "none"
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[:2] == ["claude", "-p"]
    assert set(BASE_FLAGS) <= set(argv)
    # The photograph's path travels in the prompt. A trailing positional is
    # silently dropped by the CLI's parser, which would leave the reader told to
    # describe a photograph and never told where it is.
    assert "the briefing" in argv[2]
    assert str(tmp_path / "photo.jpg") in argv[2]


@pytest.mark.spec("caption:seam:offline-double-satisfies-the-interface")
def test_the_adapter_reads_prose_out_of_the_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []

    def fake_runner(argv: Sequence[str]) -> tuple[int, str, str]:
        seen.append(list(argv))
        return 0, _envelope(result="  She is wearing a grey coat.  "), ""

    monkeypatch.setattr("isekai.claude_cli.shutil.which", lambda _: "/usr/bin/claude")
    reading = ClaudeReader(runner=fake_runner).read(
        tmp_path / "p.jpg", "brief", tmp_path
    )

    assert reading == Reading("She is wearing a grey coat.", "claude-cli", ())
    assert seen and seen[0][0] == "claude"


@pytest.mark.spec("caption:seam:producer-names-the-implementation")
def test_the_models_that_ran_come_from_the_envelope_not_from_the_flag() -> None:
    parsed = json.loads(
        _envelope(
            model="claude-opus-5",
            modelUsage={"claude-opus-5": {}, "claude-haiku-4-5-20251001": {}},
        )
    )

    assert models_that_ran(parsed) == ("claude-haiku-4-5-20251001", "claude-opus-5")


# --- failure classification ---------------------------------------------------


@pytest.mark.spec("caption:failure:rate-limit-is-transient")
@pytest.mark.parametrize(
    "subtype",
    ["rate_limit_error", "overloaded_error", "timeout", "api_error", "503 from edge"],
)
def test_a_rate_limit_a_server_error_or_a_timeout_is_transient(subtype: str) -> None:
    parsed = json.loads(_envelope(is_error=True, subtype=subtype))

    assert classify(parsed) == "transient"


@pytest.mark.spec("caption:failure:rate-limit-is-transient")
def test_a_transient_failure_counts_against_the_budget(run: Run) -> None:
    reader = FakeReader(failure=CliFailure("transient", "rate limited"))

    with pytest.raises(Refusal):
        caption(run, reader)

    recorded = attempts(run.path / "captions", 1)
    assert [(a.attempt, a.kind) for a in recorded] == [(1, "transient")]
    assert versions(run.path / "captions") == []


@pytest.mark.spec("caption:failure:rate-limit-is-transient")
def test_the_stage_refuses_once_the_budget_is_spent(run: Run) -> None:
    reader = FakeReader(failure=CliFailure("transient", "rate limited"))
    for _ in range(BUDGETS["caption"]):
        with pytest.raises(Refusal):
            caption(run, reader)

    before = len(reader.calls)
    with pytest.raises(Refusal) as refused:
        caption(run, reader)

    assert len(reader.calls) == before
    assert run.id in str(refused.value)


@pytest.mark.spec("caption:failure:decline-is-permanent")
def test_a_declined_request_is_permanent() -> None:
    parsed = json.loads(_envelope(is_error=False, stop_reason="refusal"))

    assert classify(parsed) == "permanent"


@pytest.mark.spec("caption:failure:decline-is-permanent")
def test_a_decline_names_the_photograph_and_no_other_reader_is_substituted(
    run: Run,
) -> None:
    reader = FakeReader(failure=CliFailure("permanent", "the reader declined"))

    with pytest.raises(Refusal) as refused:
        caption(run, reader)

    assert run.id in str(refused.value)
    assert "declined" in str(refused.value)

    # No fallback: a second invocation does not reach for another implementation,
    # it refuses on the permanent record.
    other = FakeReader(implementation="other-reader")
    with pytest.raises(Refusal):
        caption(run, other)
    assert other.calls == []
    assert versions(run.path / "captions") == []


@pytest.mark.spec("caption:failure:unusable-response-is-permanent")
def test_a_response_the_stage_cannot_read_as_prose_is_permanent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("isekai.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    def empty(argv: Sequence[str]) -> tuple[int, str, str]:
        return 0, _envelope(result="   "), ""

    with pytest.raises(CliFailure) as failed:
        ClaudeReader(runner=empty).read(tmp_path / "p.jpg", "brief", tmp_path)

    assert failed.value.kind == "permanent"


@pytest.mark.spec("caption:failure:unusable-response-is-permanent")
def test_no_caption_artifact_is_written_for_an_unusable_response(run: Run) -> None:
    reader = FakeReader(failure=CliFailure("permanent", "not prose"))

    with pytest.raises(Refusal):
        caption(run, reader)

    assert versions(run.path / "captions") == []


@pytest.mark.spec("caption:failure:unusable-response-is-permanent")
def test_output_that_is_not_an_envelope_at_all_is_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("isekai.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    def garbage(argv: Sequence[str]) -> tuple[int, str, str]:
        return 1, "not json", "command not understood"

    with pytest.raises(CliFailure) as failed:
        ClaudeReader(runner=garbage).read(tmp_path / "p.jpg", "brief", tmp_path)

    assert failed.value.kind == "permanent"


# --- the absent binary --------------------------------------------------------


@pytest.mark.spec("caption:refusal:absent-reader-names-the-fix")
def test_an_absent_reader_refuses_naming_what_to_install(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("isekai.claude_cli.shutil.which", lambda _: None)

    with pytest.raises(Refusal) as refused:
        ClaudeReader().read(run.photo, "brief", run.path)

    message = str(refused.value)
    assert "not on PATH" in message
    assert "npm install -g @anthropic-ai/claude-code" in message


@pytest.mark.spec("caption:refusal:absent-reader-names-the-fix")
def test_an_absent_reader_leaves_the_run_directory_untouched(
    run: Run, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("isekai.claude_cli.shutil.which", lambda _: None)
    before = sorted(p.name for p in run.path.rglob("*"))

    with pytest.raises(Refusal):
        caption(run, ClaudeReader())

    assert versions(run.path / "captions") == []
    assert attempts(run.path / "captions", 1) == []
    assert sorted(p.name for p in run.path.rglob("*")) == before

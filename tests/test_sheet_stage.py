"""Stage (2): prose in, canonical fields out, once per schema-and-vocabulary pair.

Driven through `FakeSorter`, which counts its calls, so "one fill served two
flows" and "no network was reached" are both asserted rather than assumed.
"""

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from isekai.boundary.claude_cli import BASE_FLAGS, CliFailure
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    BUDGETS,
    Run,
    attempts,
    open_run,
    read_artifact,
    versions,
)
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.sheet import (
    ClaudeSorter,
    FakeSorter,
    OllamaSorter,
    Schema,
    output_shape,
)
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV
from tests.images import jpeg_bytes
from tests.stages import SHEET_BRIEFING as BRIEFING_PATH
from tests.stages import caption, sheet
from tests.transports import FakeTransport

FLOW = "summon-v1"

PROSE = "Dark brown hair past the shoulders, brown eyes, a white collared shirt."


def _body(path: Path | None) -> dict[str, Any]:
    """Read the sheet the stage says it wrote, refusing to read None."""
    assert path is not None
    return read_artifact(path)


@pytest.fixture
def run(tmp_path: Path) -> Run:
    """Return a run whose photograph has already been read into prose."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader(prose=PROSE))
    return made


def _envelope(**fields: object) -> str:
    """Return a `claude -p --output-format json` envelope as the CLI prints it."""
    body: dict[str, object] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "api_error_status": None,
    }
    body.update(fields)
    return json.dumps(body)


# --- the seam -----------------------------------------------------------------


@pytest.mark.spec("sheet:seam:offline-double-satisfies-the-interface")
def test_a_sheet_is_written_with_no_network(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sorter = FakeSorter(answers={"hair_colour": ["dark brown"]})

    written = sheet(run, sorter, schema, vocabulary)

    assert written is not None and written.name == "001.json"
    assert _body(written)["fields"]["hair_colour"] == ["brown hair"]
    assert sorter.calls == [PROSE]


@pytest.mark.spec("sheet:seam:structure-constrained-content-free")
def test_the_model_is_required_to_return_exactly_the_schemas_fields(
    schema: Schema,
) -> None:
    shape = output_shape(schema)

    assert list(shape["properties"]) == list(schema.names)
    assert shape["required"] == list(schema.names)
    assert shape["additionalProperties"] is False


@pytest.mark.spec("sheet:seam:structure-constrained-content-free")
def test_the_wording_is_not_restricted_to_vocabulary_terms(schema: Schema) -> None:
    shape = output_shape(schema)

    for field in shape["properties"].values():
        assert field == {"type": "array", "items": {"type": "string"}}
        assert "enum" not in field["items"]
    assert "wd14" not in json.dumps(shape)


@pytest.mark.spec("sheet:seam:structure-constrained-content-free")
def test_the_argument_vector_disables_every_tool_and_states_the_shape(
    schema: Schema,
) -> None:
    argv = ClaudeSorter().argv(PROSE, schema, "the briefing")

    assert set(BASE_FLAGS) <= set(argv)
    assert argv[argv.index("--tools") + 1] == ""
    assert json.loads(argv[argv.index("--json-schema") + 1]) == output_shape(schema)
    assert PROSE in argv[2]


@pytest.mark.spec("sheet:seam:offline-double-satisfies-the-interface")
def test_the_adapter_reads_the_structured_answer_out_of_the_envelope(
    schema: Schema, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "isekai.boundary.claude_cli.shutil.which", lambda _: "/bin/claude"
    )
    answer = {name: [] for name in schema.names}
    answer["hair_colour"] = ["dark brown"]

    def runner(argv: Sequence[str]) -> tuple[int, str, str]:
        return 0, _envelope(structured_output=answer, result=json.dumps(answer)), ""

    sorting = ClaudeSorter(runner=runner).sort(PROSE, schema, "brief")

    assert sorting.answers["hair_colour"] == ["dark brown"]
    assert sorting.answers["marks"] == []


@pytest.mark.spec("sheet:failure:structural-mismatch-is-permanent")
def test_a_response_that_does_not_carry_the_schemas_fields_is_permanent(
    schema: Schema, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "isekai.boundary.claude_cli.shutil.which", lambda _: "/bin/claude"
    )

    def runner(argv: Sequence[str]) -> tuple[int, str, str]:
        return 0, _envelope(result=json.dumps({"hair_colour": ["brown"]})), ""

    with pytest.raises(CliFailure) as failed:
        ClaudeSorter(runner=runner).sort(PROSE, schema, "brief")

    assert failed.value.kind == "permanent"
    assert "age_band" in failed.value.detail


@pytest.mark.spec("sheet:failure:structural-mismatch-is-permanent")
def test_no_sheet_is_written_for_a_structural_mismatch(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sorter = FakeSorter(
        failure=CliFailure("permanent", "the response does not carry age_band")
    )

    with pytest.raises(Refusal):
        sheet(run, sorter, schema, vocabulary)

    directory = run.path / FLOW / "sheets"
    assert versions(directory) == []
    assert [a.kind for a in attempts(directory, 1)] == ["permanent"]


@pytest.mark.spec("sheet:failure:structural-mismatch-is-permanent")
def test_a_permanent_sorter_failure_is_not_retried(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    failing = FakeSorter(failure=CliFailure("permanent", "structural mismatch"))
    with pytest.raises(Refusal):
        sheet(run, failing, schema, vocabulary)

    second = FakeSorter()
    with pytest.raises(Refusal):
        sheet(run, second, schema, vocabulary)

    assert second.calls == []


@pytest.mark.spec("run-directory:budget:at-budget-the-stage-refuses")
def test_the_sorter_stage_refuses_once_its_budget_is_spent(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sorter = FakeSorter(failure=CliFailure("transient", "rate limited"))
    for _ in range(BUDGETS["sheet"]):
        with pytest.raises(Refusal):
            sheet(run, sorter, schema, vocabulary)

    before = len(sorter.calls)
    with pytest.raises(Refusal) as refused:
        sheet(run, sorter, schema, vocabulary)

    assert len(sorter.calls) == before
    assert run.id in str(refused.value)


# --- the output ---------------------------------------------------------------


@pytest.mark.spec("sheet:output:sheet-stores-fields-only")
def test_the_sheet_carries_one_entry_per_field_and_no_prompt(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, FakeSorter(), schema, vocabulary)

    artifact = _body(written)
    assert tuple(artifact["fields"]) == schema.names
    assert "prompt" not in artifact
    assert "positive" not in artifact


@pytest.mark.spec("sheet:output:empty-field-is-legal")
def test_a_field_the_prose_carried_nothing_for_is_present_and_empty(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(
        run,
        FakeSorter(answers={"hair_colour": ["dark brown"]}),
        schema,
        vocabulary,
    )

    fields = _body(written)["fields"]
    assert fields["marks"] == []
    assert fields["hair_colour"] == ["brown hair"]


@pytest.mark.spec("sheet:output:sheet-names-its-vocabulary")
def test_the_sheet_records_the_vocabularys_name_revision_and_digest(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, FakeSorter(), schema, vocabulary)

    assert _body(written)["vocabulary"] == {
        "name": "wd14/selected_tags.csv",
        "revision": "f" * 40,
        "sha256": "a" * 64,
    }


@pytest.mark.spec("sheet:output:sheet-names-its-vocabulary")
def test_a_sheet_filled_from_another_vocabulary_is_distinguishable(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    other = Vocabulary("other/tags.csv", "e" * 40, "b" * 64, read_tags(CSV))

    first = sheet(run, FakeSorter(), schema, vocabulary)
    second = sheet(run, FakeSorter(), schema, other, new_version=True)

    assert _body(first)["vocabulary"]["sha256"] == "a" * 64
    assert _body(second)["vocabulary"]["sha256"] == "b" * 64


@pytest.mark.spec("run-directory:provenance:producer-records-its-source")
def test_the_producer_names_the_caption_version_it_sorted(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, FakeSorter(), schema, vocabulary)

    assert _body(written)["producer"]["from"] == 1


@pytest.mark.spec("sheet:purity:absence-clause-is-dropped")
def test_an_absence_clause_in_an_answer_leaves_its_field_empty(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sorter = FakeSorter(answers={"accessories": ["no glasses", "none visible"]})

    written = sheet(run, sorter, schema, vocabulary)

    assert _body(written)["fields"]["accessories"] == []


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_every_tag_in_a_written_sheet_is_in_the_vocabulary(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sorter = FakeSorter(
        answers={
            "hair_colour": ["dark brown"],
            "eye_colour": ["hazel"],
            "clothes": ["a crisp collared shirt"],
            "expression": ["an air of quiet competence"],
        }
    )

    written = sheet(run, sorter, schema, vocabulary)

    fields = _body(written)["fields"]
    for tags in fields.values():
        for tag in tags:
            assert tag in vocabulary
    assert fields["eye_colour"] == []


# --- one flow, one sheet ------------------------------------------------------


@pytest.mark.spec("run-directory:layout:stage-artifacts-live-under-the-flow")
def test_the_sheet_is_written_under_the_flow_that_asked_for_it(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, FakeSorter(), schema, vocabulary)

    assert written is not None
    assert written.parent == run.path / FLOW / "sheets"


@pytest.mark.spec("run-directory:layout:a-second-flow-adds-one-subtree")
def test_a_second_flow_gets_its_own_fill_and_leaves_the_first_alone(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    # Sharing is gone: two flows over one input are two independent readings,
    # so the class of error where a flow inherits another's answer cannot occur
    # rather than being checked for (design.md D5).
    caption(run, FakeReader(prose=PROSE), flow="summon-v2")
    first = sheet(run, FakeSorter(), schema, vocabulary)

    second = sheet(run, FakeSorter(), schema, vocabulary, flow="summon-v2")

    assert first is not None and second is not None
    assert first.parent == run.path / FLOW / "sheets"
    assert second.parent == run.path / "summon-v2" / "sheets"
    assert versions(run.path / FLOW / "sheets") == [1]


@pytest.mark.spec("run-directory:idempotence:rerun-is-a-no-op")
def test_a_repeat_invocation_writes_nothing_and_calls_nothing(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sorter = FakeSorter()
    sheet(run, sorter, schema, vocabulary)

    assert sheet(run, sorter, schema, vocabulary) is None
    assert len(sorter.calls) == 1


@pytest.mark.spec_exempt("structural: the stage needs a caption to sort")
def test_a_run_with_no_caption_is_refused_and_told_which_command_to_run(
    tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    photo = tmp_path / "p.jpg"
    photo.write_bytes(jpeg_bytes(800, 600))
    bare = open_run(photo, tmp_path / "runs")

    with pytest.raises(Refusal) as refused:
        sheet(bare, FakeSorter(), schema, vocabulary)

    assert "python -m isekai caption" in str(refused.value)


# --- the briefing -------------------------------------------------------------


@pytest.mark.spec("sheet:schema:field-names-are-identifier-safe")
def test_every_field_name_the_briefing_mentions_exists_in_the_schema(
    schema: Schema,
) -> None:
    # The two places a briefing names a *field*: the field list's bullets, and
    # the left column of each worked example's sheet. Tag names in prose are not
    # field names and are deliberately not matched here.
    text = BRIEFING_PATH.read_text()
    mentioned = set(re.findall(r"^- `([a-z_]+)` —", text, re.MULTILINE)) | set(
        re.findall(r"^(\w+)\s{2,}\[", text, re.MULTILINE)
    )

    assert mentioned - set(schema.names) == set()
    assert set(schema.names) - mentioned == set()


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_every_phrase_the_briefings_examples_emit_maps_to_a_real_tag(
    schema: Schema,
) -> None:
    # A worked example is the strongest instruction in the briefing, so one that
    # demonstrates a phrasing the cascade drops teaches the sorter to waste a
    # field. The acceptance run found exactly that: `count` came back empty on
    # five of five photographs, and `gaze` came back as `camera`.
    from isekai.shared.vocabulary import DEFAULT_MODELS_DIR, VOCABULARY_DEST, map_phrase
    from isekai.shared.vocabulary import load as load_vocabulary

    if not (DEFAULT_MODELS_DIR / VOCABULARY_DEST).exists():
        pytest.skip("the vocabulary is not provisioned in this environment")
    provisioned = load_vocabulary()
    suffixes = {field.name: field.suffix for field in schema.fields}

    text = BRIEFING_PATH.read_text()
    unmapped = [
        (field, phrase)
        for field, items in re.findall(r"^(\w+)\s+\[(.*)\]$", text, re.MULTILINE)
        for phrase in re.findall(r'"([^"]+)"', items)
        if not map_phrase(phrase, provisioned, suffixes.get(field))
    ]
    assert unmapped == []


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_the_briefing_never_teaches_the_word_camera_as_a_gaze() -> None:
    # `camera` is a canonical tag meaning a camera is *in the picture*, so a
    # briefing that says "looking at the camera" teaches the sorter to have one
    # drawn. What is named is what gets rendered.
    text = BRIEFING_PATH.read_text()

    assert "Never the\n  word *camera*" in text
    assert '"looking at the camera"' not in text


@pytest.mark.spec("sheet:purity:absence-clause-is-dropped")
def test_the_briefing_forbids_writing_a_negation() -> None:
    text = BRIEFING_PATH.read_text().lower()

    assert "never write a negation" in text
    assert "empty field is a correct answer" in text


@pytest.mark.spec_exempt("structural: the briefing's two worked examples")
def test_the_briefing_carries_two_worked_examples() -> None:
    text = BRIEFING_PATH.read_text()

    assert text.count("**The prose:**") == 2
    assert text.count("**The sheet:**") == 2


# --- the Ollama adapter -------------------------------------------------------


def _answer(schema: Schema, **fields: list[str]) -> bytes:
    """Return a response body carrying every field the schema names."""
    return json.dumps(
        {"response": json.dumps({name: fields.get(name, []) for name in schema.names})}
    ).encode()


@pytest.mark.spec("sheet:selection:structure-is-required-of-every-implementation")
def test_the_open_sorters_format_is_the_schemas_own_shape(schema: Schema) -> None:
    """`format` equals `output_shape(schema)`, not merely resembles it.

    The constraint is what keeps a malformed answer permanent: the runtime
    compiles this into a grammar, so the structure is required server-side rather
    than asked for politely. An adapter carrying its own near-copy would drift
    from the Claude arm's `--json-schema` without a test noticing.
    """
    body = OllamaSorter(model="a-sorter").body(PROSE, schema, "Sort it.")

    assert body["format"] == output_shape(schema)


@pytest.mark.spec("sheet:selection:structure-is-required-of-every-implementation")
def test_the_open_sorter_sends_thinking_off_and_the_pinned_sampling(
    schema: Schema,
) -> None:
    """`think: false` and `repeat_penalty` are the two the compatible endpoint lacks.

    Both are load-bearing by measurement: thinking tokens truncated the JSON
    mid-string on the third subject, and at temperature 0 one field came back with
    the same phrase forty times until the budget ran out.
    """
    body = OllamaSorter(model="a-sorter").body(PROSE, schema, "Sort it.")

    assert body["think"] is False
    assert body["stream"] is False
    assert body["options"] == {
        "temperature": 0,
        "seed": 1,
        "num_predict": 2048,
        "repeat_penalty": 1.15,
    }


@pytest.mark.spec("sheet:selection:answer-in-the-body-is-read")
def test_the_answer_is_read_from_the_response_body(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    """No separate structured field, and the stage records no failure for it.

    `answers_from` already falls back to parsing the body; this is what stops a
    later edit from breaking the only path an Ollama answer takes.
    """
    transport = FakeTransport(raw=_answer(schema, hair_colour=["dark brown"]))

    written = sheet(
        run, OllamaSorter(model="a-sorter", transport=transport), schema, vocabulary
    )

    assert written is not None
    assert _body(written)["fields"]["hair_colour"] == ["brown hair"]
    assert attempts(run.directory(FLOW, "sheets"), 1) == []


@pytest.mark.spec("sheet:selection:truncation-is-permanent-and-named")
def test_a_truncated_answer_is_permanent_and_the_record_carries_done_reason(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    """Truncated and malformed are indistinguishable without `done_reason`.

    Only one of the two is fixed by raising the output budget, so the record has
    to say which it was rather than leaving the operator to guess.
    """
    transport = FakeTransport(
        payload={"response": '{"hair_colour": ["dark bro', "done_reason": "length"}
    )

    with pytest.raises(Refusal):
        sheet(
            run, OllamaSorter(model="a-sorter", transport=transport), schema, vocabulary
        )

    recorded = attempts(run.directory(FLOW, "sheets"), 1)
    assert [one.kind for one in recorded] == ["permanent"]
    assert "length" in json.loads(recorded[0].path.read_text())["detail"]


@pytest.mark.spec("sheet:selection:the-flow-names-the-implementation")
def test_the_open_sorters_sheet_names_ollama_and_the_model_that_ran(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    transport = FakeTransport(raw=_answer(schema, hair_colour=["dark brown"]))

    written = sheet(
        run, OllamaSorter(model="a-sorter", transport=transport), schema, vocabulary
    )

    producer = _body(written)["producer"]
    assert producer["implementation"] == "ollama"
    assert producer["models"] == ["a-sorter"]
    assert producer["pinned"] is False


@pytest.mark.spec("sheet:purity:absence-clause-is-dropped")
def test_an_absence_clause_from_the_open_sorter_still_empties_the_field(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    """The cascade is downstream of the seam and does not know which arm filled it.

    `shared/vocabulary.py` and `shared/fields.py` are unmodified by this change,
    and this is the assertion that says so behaviourally rather than by diff.
    """
    transport = FakeTransport(
        raw=_answer(schema, marks=["no visible tattoos"], hair_colour=["dark brown"])
    )

    written = sheet(
        run, OllamaSorter(model="a-sorter", transport=transport), schema, vocabulary
    )

    fields = _body(written)["fields"]
    assert fields["marks"] == []
    assert fields["hair_colour"] == ["brown hair"]


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_a_non_vocabulary_tag_from_the_open_sorter_is_refused(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    """The validation is shared too, and an open arm gets no exemption from it."""
    transport = FakeTransport(
        raw=_answer(schema, hair_colour=["a shade nothing in the vocabulary names"])
    )

    written = sheet(
        run, OllamaSorter(model="a-sorter", transport=transport), schema, vocabulary
    )

    assert _body(written)["fields"]["hair_colour"] == []

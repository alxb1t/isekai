"""Stage (2): a tag list in, canonical fields out, routed by the committed table.

**There is no double to drive it through any more, and that is stronger than one.**
The stage reaches nothing: it reads one artifact and looks each tag up in a table,
so "no model was reached" is asserted by rigging both transports to explode rather
than by counting a fake's calls. `tests/stages.sheet` writes the tag list the
stage refuses without, which is why a test says what it wants routed on one line.
"""

import json
import re
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from isekai.boundary.claude_cli import BASE_FLAGS, CliFailure
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    BUDGETS,
    CAPTIONS,
    Run,
    open_run,
    read_artifact,
    record_failure,
    versions,
)
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.sheet import (
    ClaudeSorter,
    OllamaSorter,
    Schema,
    output_shape,
)
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV
from tests.images import jpeg_bytes
from tests.stages import FAKE_PINS, FIELD_MAP, caption, sheet
from tests.stages import SHEET_BRIEFING as BRIEFING_PATH

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


@pytest.mark.spec("field-map:routing:a-tag-goes-to-its-primary")
def test_a_tag_is_placed_in_its_primary_criterion_and_no_model_is_reached(
    run: Run, schema: Schema, vocabulary: Vocabulary, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-vacuous: both transports are rigged to explode before the stage runs.

    `tests/test_isolation.py`'s argument, applied to the stage that used to have
    a seam. A router that reached a model would be caught here rather than being
    trusted not to.
    """

    def unreachable(*args: object, **kwargs: object) -> object:
        raise AssertionError("a model was reached")

    monkeypatch.setattr("subprocess.Popen", unreachable)
    monkeypatch.setattr("urllib.request.urlopen", unreachable)

    written = sheet(run, schema, vocabulary, tags=["brown hair"])

    assert written is not None and written.name == "001.json"
    fields = _body(written)["fields"]
    assert fields["hair_colour"] == ["brown hair"]
    assert all(tags == [] for name, tags in fields.items() if name != "hair_colour")


@pytest.mark.spec("field-map:routing:an-undeclared-criterion-drops-its-tags")
def test_a_tag_whose_criterion_the_flow_does_not_declare_is_dropped(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    # `thick eyebrows` routes to `eyebrows`, which `summon-v1` declares; the
    # table also places `brown hair` under `hair_colour`. A criterion no flow
    # declared would take its tags nowhere -- proven by narrowing the schema.
    narrowed = Schema(name=schema.name, fields=tuple(schema.fields[:1]))

    written = sheet(run, narrowed, vocabulary, tags=["brown hair", "thick eyebrows"])

    fields = _body(written)["fields"]
    assert tuple(fields) == narrowed.names
    assert all(tags == [] for tags in fields.values())


@pytest.mark.spec("field-map:routing:the-tagger-s-order-is-kept")
def test_the_taggers_order_survives_inside_each_criterion(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(
        run, schema, vocabulary, tags=["short hair", "long hair", "wavy hair"]
    )

    assert _body(written)["fields"]["hair_silhouette"] == [
        "short hair",
        "long hair",
        "wavy hair",
    ]


@pytest.mark.spec("field-map:routing:no-tag-is-invented")
def test_nothing_the_tagger_did_not_return_reaches_the_sheet(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    offered = ["brown hair", "smile"]

    written = sheet(run, schema, vocabulary, tags=offered)

    fields = _body(written)["fields"]
    assert [tag for tags in fields.values() for tag in tags] == offered


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


@pytest.mark.spec("run-directory:budget:at-budget-the-stage-refuses")
def test_the_stage_refuses_once_its_budget_of_one_is_spent(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    """The budget is one now, because a dictionary lookup has no transient failure.

    There is nothing left to *make* fail transiently, so the attempt is recorded
    directly -- which is the honest shape of the assertion anyway: the guard is
    about what is on disk, not about what raised.
    """
    directory = run.path / FLOW / "sheets"
    assert BUDGETS["sheet"] == 1
    record_failure(directory, 1, "transient", {"stage": "sheet"})

    with pytest.raises(Refusal) as refused:
        sheet(run, schema, vocabulary)

    assert versions(directory) == []
    assert run.id in str(refused.value)


# --- the output ---------------------------------------------------------------


@pytest.mark.spec("sheet:output:sheet-stores-fields-only")
def test_the_sheet_carries_one_entry_per_field_and_no_prompt(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, schema, vocabulary)

    artifact = _body(written)
    assert tuple(artifact["fields"]) == schema.names
    assert "prompt" not in artifact
    assert "positive" not in artifact


@pytest.mark.spec("sheet:output:empty-field-is-legal")
def test_a_field_the_tag_list_carried_nothing_for_is_present_and_empty(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, schema, vocabulary, tags=["brown hair"])

    fields = _body(written)["fields"]
    assert fields["marks"] == []
    assert fields["hair_colour"] == ["brown hair"]


@pytest.mark.spec("sheet:output:sheet-names-its-vocabulary")
def test_the_sheet_records_the_vocabularys_name_revision_and_digest(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, schema, vocabulary)

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

    first = sheet(run, schema, vocabulary)
    second = sheet(run, schema, other, new_version=True)

    assert _body(first)["vocabulary"]["sha256"] == "a" * 64
    assert _body(second)["vocabulary"]["sha256"] == "b" * 64


@pytest.mark.spec("sheet:output:sheet-names-its-field-map")
def test_the_sheet_records_the_field_map_it_was_routed_by(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, schema, vocabulary)

    assert _body(written)["field_map"] == {
        "name": "tests/stages.py",
        "revision": 1,
        "sha256": "f" * 64,
    }


@pytest.mark.spec("sheet:output:sheet-names-its-field-map")
def test_two_sheets_routed_by_different_revisions_are_distinguishable(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    moved = replace(FIELD_MAP, revision=2, digest="e" * 64)

    first = sheet(run, schema, vocabulary)
    second = sheet(run, schema, vocabulary, field_map=moved, new_version=True)

    assert _body(first)["field_map"]["revision"] == 1
    assert _body(second)["field_map"]["revision"] == 2


@pytest.mark.spec("sheet:output:the-stage-reads-the-tag-list")
def test_the_stage_reads_the_tag_list_and_never_opens_the_caption(
    run: Run, schema: Schema, vocabulary: Vocabulary, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The run carries **both** artifacts, so reading the wrong one is possible.

    A test that gave it only a tag list would pass whichever file the stage
    reached for. The caption is on disk and is booby-trapped: any read of it
    fails the test by name.
    """
    caption_path = run.directory(FLOW, CAPTIONS) / "001.json"
    assert caption_path.exists()
    original = Path.read_text

    def guarded(self: Path, *args: object, **kwargs: object) -> str:
        if self == caption_path:
            raise AssertionError("the caption was read")
        return original(self, *args, **kwargs)  # ty: ignore[invalid-argument-type]

    monkeypatch.setattr(Path, "read_text", guarded)

    written = sheet(run, schema, vocabulary, tags=["brown hair", "smile"])

    fields = _body(written)["fields"]
    assert fields["hair_colour"] == ["brown hair"]
    assert fields["expression"] == ["smile"]


@pytest.mark.spec("sheet:output:an-absent-tag-list-is-refused")
def test_an_absent_tag_list_is_refused_naming_the_verb_that_writes_it(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    with pytest.raises(Refusal) as refused:
        sheet(run, schema, vocabulary, tags=None)

    message = str(refused.value)
    assert "python -m isekai caption" in message
    assert versions(run.path / FLOW / "sheets") == []


@pytest.mark.spec("run-directory:provenance:producer-records-its-source")
def test_the_producer_names_the_tag_list_version_it_routed(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, schema, vocabulary)

    producer = _body(written)["producer"]
    assert producer["from"] == 1
    # The pin travels across from the artifact the tags came out of rather than
    # being re-derived: these are the digests that session actually opened.
    assert producer["implementation"] == "wd14"
    assert producer["pinned"] is True
    assert producer["artifacts"] == FAKE_PINS


@pytest.mark.spec("sheet:purity:no-tag-outside-the-vocabulary")
def test_every_tag_in_a_written_sheet_is_in_the_vocabulary(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    # `hair` is in the vocabulary and in the table; `jeans` is in both as well.
    # Nothing here can be outside it, which is the property's new form: the
    # tagger's output layer *is* the vocabulary and the router invents nothing.
    written = sheet(run, schema, vocabulary, tags=["brown hair", "jeans", "hair"])

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
    written = sheet(run, schema, vocabulary)

    assert written is not None
    assert written.parent == run.path / FLOW / "sheets"


@pytest.mark.spec("run-directory:layout:a-second-flow-adds-one-subtree")
def test_a_second_flow_gets_its_own_fill_and_leaves_the_first_alone(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    # Sharing is gone: two flows over one input are two independent tag lists,
    # so the class of error where a flow inherits another's answer cannot occur
    # rather than being checked for (design.md D5).
    first = sheet(run, schema, vocabulary, tags=["brown hair"])

    second = sheet(run, schema, vocabulary, flow="summon-v2", tags=["long hair"])

    assert first is not None and second is not None
    assert first.parent == run.path / FLOW / "sheets"
    assert second.parent == run.path / "summon-v2" / "sheets"
    assert versions(run.path / FLOW / "sheets") == [1]
    assert _body(first)["fields"]["hair_colour"] == ["brown hair"]
    assert _body(second)["fields"]["hair_silhouette"] == ["long hair"]


@pytest.mark.spec("run-directory:idempotence:rerun-is-a-no-op")
def test_a_repeat_invocation_writes_nothing(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(run, schema, vocabulary)
    assert written is not None
    before = written.read_bytes()

    assert sheet(run, schema, vocabulary) is None
    assert written.read_bytes() == before
    assert versions(run.path / FLOW / "sheets") == [1]


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

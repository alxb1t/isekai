"""Stage (2): a tag list in, canonical fields out, routed by the committed table.

**There is no double to drive it through any more, and that is stronger than one.**
The stage reaches nothing: it reads one artifact and looks each tag up in a table,
so "no model was reached" is asserted by rigging both transports to explode rather
than by counting a fake's calls. `tests/stages.sheet` writes the tag list the
stage refuses without, which is why a test says what it wants routed on one line.
"""

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from isekai.foundation.artifacts import SHEET_FILE, DanbooruTag, Sheet, read
from isekai.foundation.flow import Schema
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    BUDGETS,
    CAPTIONS,
    Run,
    open_run,
    record_failure,
    versions,
)
from isekai.pipeline.caption import FakeReader
from isekai.shared.vocabulary import Vocabulary, read_tags
from tests.conftest import CSV
from tests.images import jpeg_bytes
from tests.stages import FAKE_PINS, FIELD_MAP, caption, sheet, write_wd14

FLOW = "summon-anime-wai"

PROSE = "Dark brown hair past the shoulders, brown eyes, a white collared shirt."


def _body(path: Path | None) -> Sheet:
    """Read the sheet the stage says it wrote, refusing to read None."""
    assert path is not None
    return read(path, SHEET_FILE)


@pytest.fixture
def run(tmp_path: Path) -> Run:
    """Return a run whose photograph has already been read into prose."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader(prose=PROSE))
    return made


# --- the router ---------------------------------------------------------------


@pytest.mark.spec("field-map:routing:a-tag-goes-to-its-primary")
def test_a_tag_is_placed_in_its_primary_criterion_and_no_model_is_reached(
    run: Run, schema: Schema, vocabulary: Vocabulary, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-vacuous: both transports are rigged to explode before the stage runs.

    The isolation argument, applied to the stage that used to have a seam. A
    router that reached a model would be caught here rather than being trusted
    not to.
    """

    def unreachable(*args: object, **kwargs: object) -> object:
        raise AssertionError("a model was reached")

    monkeypatch.setattr("subprocess.Popen", unreachable)
    monkeypatch.setattr("urllib.request.urlopen", unreachable)

    written = sheet(run, schema, vocabulary, tags=[DanbooruTag("brown_hair")])

    assert written is not None and written.name == "001.json"
    fields = _body(written)["fields"]
    assert fields["hair_colour"] == ["brown hair"]
    assert all(tags == [] for name, tags in fields.items() if name != "hair_colour")


@pytest.mark.spec("field-map:routing:a-tag-goes-to-its-primary")
def test_the_taggers_own_underscore_spelling_routes(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    """The list arrives in Danbooru's spelling, because `wd14/` is not narrowed.

    `boundary/wd14.py` stores the label index's own `blonde_hair`; the vocabulary
    and the table are normalised at their own read. A bare lookup between them
    misses every multi-word tag and says nothing, which is the shape of defect
    this repository keeps paying for -- so the fixture writes the underscore
    rather than the spelling that would make the test pass either way.
    """
    written = sheet(
        run,
        schema,
        vocabulary,
        tags=[DanbooruTag("brown_hair"), DanbooruTag("blue_eyes")],
    )

    fields = _body(written)["fields"]
    assert fields["hair_colour"] == ["brown hair"]
    assert fields["eye_colour"] == ["blue eyes"]


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
def test_a_non_string_tag_routes_nowhere(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    listed = write_wd14(run, [DanbooruTag("brown_hair")])
    body = json.loads(listed.read_text())
    body["tags"].append({"tag": 42, "confidence": 0.5})
    listed.write_text(json.dumps(body))

    written = sheet(run, schema, vocabulary, tags=None)

    fields = _body(written)["fields"]
    assert fields["hair_colour"] == ["brown hair"]
    assert all("42" not in tags for tags in fields.values())


@pytest.mark.spec("run-directory:budget:one-failure-does-not-halt-the-batch")
@pytest.mark.parametrize(
    ("damage", "named"),
    [
        (lambda body: body.pop("tags"), "records no `tags` list"),
        (lambda body: body.update(tags={"a": 1}), "records no `tags` list"),
        (lambda body: body.pop("producer"), "records no `producer` object"),
        (lambda body: body["producer"].pop("models"), "records no `models` list"),
        (lambda body: body["producer"].pop("pinned"), "records no `pinned` flag"),
        (lambda body: body["producer"].pop("artifacts"), "records no `artifacts`"),
        (lambda body: body["tags"].append("brown_hair"), "tag entry 1 records no"),
        (lambda body: body["tags"].append({"confidence": 0.5}), "tag entry 1"),
    ],
)
def test_a_tag_list_missing_a_key_is_refused_naming_it(
    run: Run,
    schema: Schema,
    vocabulary: Vocabulary,
    damage: Callable[[dict[str, Any]], object],
    named: str,
) -> None:
    listed = write_wd14(run, [DanbooruTag("brown_hair")])
    body = json.loads(listed.read_text())
    damage(body)
    listed.write_text(json.dumps(body))

    with pytest.raises(Refusal) as refused:
        sheet(run, schema, vocabulary, tags=None)

    message = str(refused.value)
    assert message.startswith("001.json: ") and named in message
    assert f"`python -m isekai caption --flow {FLOW} --new-version {run.id}`" in message
    assert versions(run.directory(FLOW, "sheets")) == []


@pytest.mark.spec("field-map:routing:an-undeclared-criterion-drops-its-tags")
def test_a_tag_whose_criterion_the_flow_does_not_declare_is_dropped(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    # `thick eyebrows` routes to `eyebrows`, which `summon-anime-wai` declares;
    # the table also places `brown hair` under `hair_colour`. A criterion no flow
    # declared would take its tags nowhere -- proven by narrowing the schema.
    narrowed = Schema(name=schema.name, fields=tuple(schema.fields[:1]))

    written = sheet(
        run,
        narrowed,
        vocabulary,
        tags=[DanbooruTag("brown_hair"), DanbooruTag("thick_eyebrows")],
    )

    fields = _body(written)["fields"]
    assert tuple(fields) == narrowed.names
    assert all(tags == [] for tags in fields.values())


@pytest.mark.spec("field-map:routing:the-tagger-s-order-is-kept")
def test_the_taggers_order_survives_inside_each_criterion(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    written = sheet(
        run,
        schema,
        vocabulary,
        tags=[
            DanbooruTag("short_hair"),
            DanbooruTag("long_hair"),
            DanbooruTag("wavy_hair"),
        ],
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
    written = sheet(
        run, schema, vocabulary, tags=[DanbooruTag("brown_hair"), DanbooruTag("smile")]
    )

    fields = _body(written)["fields"]
    assert [tag for tags in fields.values() for tag in tags] == ["brown hair", "smile"]


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
    record_failure(directory, 1, "transient", {"stage": "sheet", "detail": "x"})

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
    written = sheet(run, schema, vocabulary, tags=[DanbooruTag("brown_hair")])

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

    written = sheet(
        run, schema, vocabulary, tags=[DanbooruTag("brown_hair"), DanbooruTag("smile")]
    )

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
    written = sheet(
        run,
        schema,
        vocabulary,
        tags=[DanbooruTag("brown_hair"), DanbooruTag("jeans"), DanbooruTag("hair")],
    )

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
    first = sheet(run, schema, vocabulary, tags=[DanbooruTag("brown_hair")])

    second = sheet(
        run, schema, vocabulary, flow="summon-v2", tags=[DanbooruTag("long_hair")]
    )

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


# --- the briefing, which nothing reads any more --------------------------------
#

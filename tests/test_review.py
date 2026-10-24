"""Stage (3): the copy, the draft, the validation, and the rename that is approval.

The load-bearing assertion in this file is negative: after every path through
this stage, `<flow>/sheets/` is byte-identical to what stage (2) wrote.
"""

import io
import json
import re
from pathlib import Path

import pytest

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    SHEET_FILE,
    Renders,
    read,
    renders_of,
)
from isekai.foundation.flow import Flow, Schema, assemble, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    Run,
    approved_versions,
    open_run,
    record_failure,
    versions,
)
from isekai.interface.cli import build_parser, dispatch
from isekai.interface.wiring import Wiring
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.generate import prompt_artifact
from isekai.pipeline.review import (
    ENCODER_WINDOW,
    approve,
    cancel,
    cancellable,
    current_draft,
    discard,
    estimate_tokens,
    review,
    revise,
    save_draft,
    state,
    token_budget,
)
from isekai.shared.vocabulary import Vocabulary
from tests.conftest import snapshot
from tests.images import jpeg_bytes
from tests.stages import caption, runs_flag, sheet

FLOW = "summon-anime-wai"


@pytest.fixture
def flow() -> Flow:
    """Return the tracked flow, which is what supplies the prefix and trailer."""
    return load_flow(FLOW)


@pytest.fixture
def run(tmp_path: Path, schema: Schema, vocabulary: Vocabulary) -> Run:
    """Return a run carrying a caption and one filled sheet for `FLOW`."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader(prose="Dark brown hair, brown eyes."))
    sheet(
        made,
        schema,
        vocabulary,
    )
    return made


def _edit(path: Path, **fields: list[str]) -> None:
    """Edit a draft the way an operator would: open it, change it, save it."""
    body = json.loads(path.read_text())
    body["fields"].update(fields)
    path.write_text(json.dumps(body, indent=2) + "\n")


# --- the copy -----------------------------------------------------------------


@pytest.mark.spec("review:copy:review-writes-to-its-own-directory")
def test_review_writes_a_copy_and_touches_no_sheet(run: Run) -> None:
    before = snapshot(run.path / FLOW / "sheets")

    draft = review(run, FLOW)

    assert draft is not None
    assert draft.parent == run.path / FLOW / "review"
    assert draft.name == "001.draft.json"
    assert snapshot(run.path / FLOW / "sheets") == before


@pytest.mark.spec("review:copy:review-writes-to-its-own-directory")
def test_editing_the_draft_leaves_the_sheet_untouched(run: Run) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    before = snapshot(run.path / FLOW / "sheets")

    _edit(draft, hair_colour=["black hair"])

    assert snapshot(run.path / FLOW / "sheets") == before
    assert read(run.path / FLOW / "sheets" / "001.json", SHEET_FILE)["fields"][
        "hair_colour"
    ] == ["brown hair"]


@pytest.mark.spec("review:copy:highest-sheet-is-copied")
def test_the_highest_sheet_is_copied_and_its_version_recorded(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sheet(
        run,
        schema,
        vocabulary,
        new_version=True,
    )
    assert versions(run.path / FLOW / "sheets") == [1, 2]

    draft = review(run, FLOW)

    assert draft is not None
    body = read(draft, DRAFT_FILE)
    assert body["sheet"] == 2
    assert body["producer"]["from"] == 2
    assert body["producer"]["source"] == "sheets"


@pytest.mark.spec("review:copy:second-review-appends")
def test_reviewing_again_appends_from_the_approved_copy(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    first = review(run, FLOW)
    assert first is not None
    _edit(first, hair_silhouette=["long hair"])
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    frozen = approved.read_bytes()

    second = review(run, FLOW, new_version=True)

    assert second is not None
    assert second.name == "002.draft.json"
    assert approved.read_bytes() == frozen
    # The correction starts from the last thing the operator agreed with.
    assert read(second, DRAFT_FILE)["fields"]["hair_silhouette"] == ["long hair"]
    assert read(second, DRAFT_FILE)["producer"]["source"] == "review"


@pytest.mark.spec("review:copy:second-review-appends")
def test_a_waiting_draft_is_not_overwritten_by_a_repeat_invocation(
    run: Run,
) -> None:
    first = review(run, FLOW)
    assert first is not None
    _edit(first, hair_colour=["black hair"])
    frozen = first.read_bytes()

    assert review(run, FLOW) is None
    assert first.read_bytes() == frozen


@pytest.mark.spec_exempt("structural: the stage needs a sheet to copy")
def test_a_flow_with_no_sheet_is_refused_and_told_which_command_to_run(
    run: Run,
) -> None:
    with pytest.raises(Refusal) as refused:
        review(run, "summon-v9")

    assert "python -m isekai sheet" in str(refused.value)


# --- approval -----------------------------------------------------------------


@pytest.mark.spec("review:approval:draft-is-not-done")
def test_a_draft_is_not_treated_as_complete(run: Run) -> None:
    review(run, FLOW)
    directory = run.path / FLOW / "review"

    assert current_draft(directory) == directory / "001.draft.json"
    assert approved_versions(directory) == []
    assert state(directory) == "draft"


@pytest.mark.spec("review:approval:approve-validates-then-renames")
def test_approval_carries_the_operators_content_across_unchanged(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _edit(draft, hair_silhouette=["long hair"], clothes=["collared shirt"])
    before = json.loads(draft.read_text())["fields"]

    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None

    assert approved.name == "001.approved.json"
    assert read(approved, APPROVED_FILE)["fields"] == before
    assert not draft.exists()


@pytest.mark.spec("review:approval:approve-validates-then-renames")
def test_approval_is_decidable_from_the_filename_alone(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)
    approve(run, FLOW, schema, vocabulary)
    directory = run.path / FLOW / "review"

    assert [p.name for p in directory.iterdir()] == ["001.approved.json"]
    assert approved_versions(directory) == [1]
    assert state(directory) == "approved"


@pytest.mark.spec("review:approval:approved-is-not-overwritten")
def test_an_approved_artifact_is_never_overwritten(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    frozen = approved.read_bytes()

    second = review(run, FLOW, new_version=True)
    assert second is not None
    _edit(second, hair_silhouette=["long hair"])
    corrected, _ = approve(run, FLOW, schema, vocabulary)
    assert corrected is not None

    assert corrected.name == "002.approved.json"
    assert approved.read_bytes() == frozen


@pytest.mark.spec("review:approval:approved-is-not-overwritten")
def test_approving_with_no_draft_refuses_and_names_the_command(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert f"python -m isekai review --flow {FLOW}" in str(refused.value)


@pytest.mark.spec("run-directory:idempotence:approving-an-approved-flow-writes-nothing")
def test_approving_an_approved_flow_writes_nothing(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    first = review(run, FLOW)
    assert first is not None
    stale = first.read_bytes()
    approve(run, FLOW, schema, vocabulary)
    review(run, FLOW, new_version=True)
    approve(run, FLOW, schema, vocabulary)
    # A draft numbered below the approval: left by a crash, or restored by hand.
    first.write_bytes(stale)
    before = snapshot(run.path)

    written, warnings = approve(run, FLOW, schema, vocabulary)

    assert (written, warnings) == (None, [])
    assert snapshot(run.path) == before


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
def test_an_approved_sheet_without_its_sheet_number_is_refused(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    _damage(approved, "sheet", None)

    with pytest.raises(Refusal) as refused:
        review(run, FLOW, new_version=True)

    message = str(refused.value)
    assert message.startswith("001.approved.json: records no `sheet` number")
    assert f"--new-version {run.id}`" in message
    assert current_draft(run.directory(FLOW, "review")) is None


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
@pytest.mark.parametrize(
    ("key", "value"),
    [("vocabulary", None), ("fields", None), ("fields", ["a list"]), ("sheet", "one")],
)
def test_an_approved_artifact_missing_a_key_is_refused_naming_it(
    run: Run, schema: Schema, vocabulary: Vocabulary, key: str, value: object
) -> None:
    review(run, FLOW)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    _damage(approved, key, value)

    with pytest.raises(Refusal) as refused:
        review(run, FLOW, new_version=True)

    message = str(refused.value)
    assert message.startswith(f"001.approved.json: records no `{key}`")
    assert f"--new-version {run.id}`" in message
    assert current_draft(run.directory(FLOW, "review")) is None


@pytest.mark.spec("cli:refusals:refusal-names-the-remedy")
@pytest.mark.parametrize(("key", "value"), [("vocabulary", None), ("fields", "x")])
def test_a_sheet_missing_a_key_is_refused_before_it_is_copied(
    run: Run, key: str, value: object
) -> None:
    _damage(run.path / FLOW / "sheets" / "001.json", key, value)

    with pytest.raises(Refusal) as refused:
        review(run, FLOW)

    message = str(refused.value)
    assert message.startswith(f"001.json: records no `{key}` object")
    flag = runs_flag(run)
    assert (
        f"`python -m isekai sheet --flow {FLOW}{flag} --new-version {run.id}`"
        in message
    )
    assert versions(run.directory(FLOW, "review")) == []


@pytest.mark.spec("review:draft-update:a-changed-field-set-is-refused")
@pytest.mark.parametrize("value", [None, ["a list"]])
def test_saving_a_draft_without_a_fields_object_is_refused(
    run: Run, schema: Schema, value: object
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _damage(draft, "fields", value)
    before = draft.read_bytes()

    with pytest.raises(Refusal) as refused:
        save_draft(run, FLOW, {name: [] for name in schema.names})

    assert str(refused.value).startswith("001.draft.json: records no `fields` object")
    assert f"delete {draft}" in str(refused.value)
    assert draft.read_bytes() == before


@pytest.mark.spec("review:validation:missing-field-refuses-approval")
@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("sheet", None),
        ("sheet", "one"),
        ("producer", None),
        ("producer", ["a list"]),
        ("vocabulary", None),
    ],
)
def test_a_draft_missing_a_key_refuses_approval_naming_it(
    run: Run, schema: Schema, vocabulary: Vocabulary, key: str, value: object
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _damage(draft, key, value)

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    message = str(refused.value)
    assert message.startswith(f"001.draft.json: records no `{key}`")
    assert f"delete {draft}" in message and f"--new-version {run.id}`" in message
    assert approved_versions(run.directory(FLOW, "review")) == []


@pytest.mark.spec("review:validation:missing-field-refuses-approval")
def test_a_source_sheet_without_fields_refuses_approval_naming_it(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    assert review(run, FLOW) is not None
    source = run.path / FLOW / "sheets" / "001.json"
    _damage(source, "fields", None)

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert str(refused.value).startswith("001.json: records no `fields` object")
    assert f"delete {source}" not in str(refused.value)
    assert approved_versions(run.directory(FLOW, "review")) == []

    # The printed fix, followed: it keeps the damaged sheet, so no number is freed
    # for a later sheet to reuse, and the approval computes `edited` honestly.
    _follow(str(refused.value), run, schema, vocabulary)
    assert source.exists()
    assert _approved_edited(run, schema, vocabulary) == (True, 2)


@pytest.mark.spec("review:provenance:edited-copy-is-declared")
@pytest.mark.parametrize("damage", ["not json", "not an object", "another version"])
def test_a_source_sheet_that_does_not_parse_is_refused_keeping_the_sheet(
    run: Run, schema: Schema, vocabulary: Vocabulary, damage: str
) -> None:
    assert review(run, FLOW) is not None
    source = run.path / FLOW / "sheets" / "001.json"
    if damage == "not json":
        source.write_text("{ not json")
    elif damage == "not an object":
        source.write_text("[]")
    else:
        body = json.loads(source.read_text())
        body["schema"]["version"] = SHEET_FILE.version + 1
        source.write_text(json.dumps(body))

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    # `read`'s default fix deletes the file, which frees the sheet's number.
    assert str(refused.value).startswith("001.json: ")
    assert f"delete {source}" not in str(refused.value)
    assert approved_versions(run.directory(FLOW, "review")) == []

    _follow(str(refused.value), run, schema, vocabulary)
    assert source.exists()
    assert _approved_edited(run, schema, vocabulary) == (True, 2)


@pytest.mark.spec("review:provenance:edited-copy-is-declared")
def test_a_missing_source_sheet_refuses_approval_rather_than_guessing_unedited(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _edit(draft, clothes=["collared shirt"])
    source = run.path / FLOW / "sheets" / "001.json"
    source.unlink()

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert str(refused.value).startswith(f"{draft.name}: was copied from {source}")
    assert approved_versions(run.directory(FLOW, "review")) == []
    assert draft.exists()

    _follow(str(refused.value), run, schema, vocabulary)
    assert _approved_edited(run, schema, vocabulary) == (True, 1)


@pytest.mark.spec("review:provenance:edited-copy-is-declared")
@pytest.mark.parametrize("damage", ["fields", "sheet"])
def test_a_reopened_draft_whose_sheet_is_damaged_is_refused_keeping_the_approval(
    run: Run, schema: Schema, vocabulary: Vocabulary, damage: str
) -> None:
    review(run, FLOW)
    first, _ = approve(run, FLOW, schema, vocabulary)
    assert first is not None
    draft = review(run, FLOW, new_version=True)
    assert draft is not None
    _edit(draft, clothes=["collared shirt"])
    source = run.path / FLOW / "sheets" / "001.json"
    if damage == "fields":
        _damage(source, "fields", None)
    else:
        source.unlink()

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    # A fresh copy would come from the approval, which names this same sheet, so
    # the fix that works is to leave the flow approved as it was.
    assert f"delete {draft}" in str(refused.value)
    draft.unlink()
    assert approve(run, FLOW, schema, vocabulary) == (None, [])
    assert approved_versions(run.directory(FLOW, "review")) == [1]


@pytest.mark.spec("run-directory:kind:another-kind-is-refused")
@pytest.mark.parametrize("reader", ["review", "generate"])
def test_an_approval_of_another_kind_is_restored_by_hand_never_deleted(
    run: Run, schema: Schema, vocabulary: Vocabulary, reader: str
) -> None:
    review(run, FLOW)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    _damage(approved, "schema", {"name": "sheet", "version": 1})

    with pytest.raises(Refusal) as refused:
        if reader == "review":
            review(run, FLOW, new_version=True)
        else:
            prompt_artifact(run, load_flow(FLOW), schema)

    # No command rewrites an approval, so deleting it would lose the human's work.
    message = str(refused.value)
    assert "declares kind 'sheet'" in message
    assert f"restore it in {approved}" in message
    assert f"delete {approved}" not in message


def _follow(message: str, run: Run, schema: Schema, vocabulary: Vocabulary) -> None:
    """Run the two commands a no-approval source-sheet refusal prints, in order."""
    flag = runs_flag(run)
    assert (
        f"`python -m isekai sheet --flow {FLOW}{flag} --new-version {run.id}`"
        in message
    )
    assert (
        f"`python -m isekai review --flow {FLOW}{flag} --new-version {run.id}`"
        in message
    )
    sheet(run, schema, vocabulary, new_version=True)
    copied = review(run, FLOW, new_version=True)
    assert copied is not None
    # The operator carries the correction across into the fresh copy.
    _edit(copied, clothes=["collared shirt"])


def _approved_edited(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> tuple[bool, int]:
    """Approve the current draft and return what it records: edited, and its sheet."""
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    body = read(approved, APPROVED_FILE)
    return body["producer"]["edited"], body["sheet"]


def _damage(path: Path, key: str, value: object) -> None:
    """Hand-edit one key of a run file: drop it when `value` is None, else set it."""
    body = json.loads(path.read_text())
    if value is None:
        del body[key]
    else:
        body[key] = value
    path.write_text(json.dumps(body))


@pytest.mark.spec("review:validation:missing-field-refuses-approval")
@pytest.mark.parametrize("held", [None, ["a list"]])
def test_a_draft_without_fields_is_refused_naming_them(
    run: Run, schema: Schema, vocabulary: Vocabulary, held: list[str] | None
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _damage(draft, "fields", held)

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert f"the sheet is missing {', '.join(schema.names)};" in str(refused.value)
    assert approved_versions(run.directory(FLOW, "review")) == []


# --- validation ---------------------------------------------------------------


@pytest.mark.spec("review:validation:unknown-tag-refuses-approval")
def test_a_tag_absent_from_the_vocabulary_refuses_approval(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _edit(draft, eye_colour=["hazel eyes"])
    frozen = draft.read_bytes()

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert "hazel eyes" in str(refused.value)
    assert "eye_colour" in str(refused.value)
    assert draft.read_bytes() == frozen
    assert approved_versions(run.path / FLOW / "review") == []


@pytest.mark.spec("review:validation:message-states-the-prediction-set")
def test_the_refusal_does_not_claim_the_tag_is_unreal(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _edit(draft, eye_colour=["hazel eyes"])

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    message = str(refused.value)
    assert "prediction set" in message
    for overclaim in ("does not exist", "is not a real tag", "invalid tag"):
        assert overclaim not in message


@pytest.mark.spec("review:validation:missing-field-refuses-approval")
def test_a_draft_missing_a_field_refuses_approval(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    body = json.loads(draft.read_text())
    del body["fields"]["pose"]
    draft.write_text(json.dumps(body, indent=2) + "\n")

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert "pose" in str(refused.value)


@pytest.mark.spec("review:validation:missing-field-refuses-approval")
def test_an_empty_field_is_not_treated_as_missing(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)

    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None

    assert read(approved, APPROVED_FILE)["fields"]["pose"] == []


# --- the token window ---------------------------------------------------------


@pytest.mark.spec("review:budget:over-window-warns-not-refuses")
def test_an_over_long_prompt_warns_and_still_approves(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    every = [tag for tag in vocabulary.counts]
    _edit(draft, clothes=every, accessories=every)

    approved, warnings = approve(run, FLOW, schema, vocabulary)

    assert approved is not None and approved.exists()
    assert len(warnings) == 1
    assert str(ENCODER_WINDOW) in warnings[0]
    assert "warning and not a refusal" in warnings[0]


@pytest.mark.spec("review:budget:over-window-warns-not-refuses")
def test_a_short_prompt_warns_about_nothing(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)

    _, warnings = approve(run, FLOW, schema, vocabulary)

    assert warnings == []


@pytest.mark.spec("review:budget:over-window-warns-not-refuses")
def test_the_estimate_counts_words_separators_and_the_encoders_own_two(
    schema: Schema,
) -> None:
    fields = {name: [] for name in schema.names}
    fields["hair_colour"] = ["brown hair"]
    fields["clothes"] = ["collared shirt", "jeans"]

    # 2 + 2 + 1 words, two separators, two the encoder adds itself.
    assert estimate_tokens(fields, schema) == 9


# --- provenance ---------------------------------------------------------------


@pytest.mark.spec("review:provenance:unedited-copy-is-declared")
def test_an_untouched_copy_is_recorded_as_unedited(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)

    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None

    body = read(approved, APPROVED_FILE)
    assert body["producer"]["edited"] is False
    assert body["sheet"] == 1


@pytest.mark.spec("review:provenance:edited-copy-is-declared")
def test_a_changed_copy_is_recorded_as_edited_without_being_told(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _edit(draft, clothes=["collared shirt"])

    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None

    body = read(approved, APPROVED_FILE)
    assert body["producer"]["edited"] is True
    assert body["sheet"] == 1
    # Nothing the operator wrote says so; it is computed against the sheet.
    # The sheet is the draft's sibling stage under the same flow -- named rather
    # than counted in `.parent` hops, which is what a layout change breaks.
    sheet_artifact = run.directory(FLOW, "sheets") / "001.json"
    assert "edited" not in json.loads(sheet_artifact.read_text())["producer"]


# --- refusals leave no state --------------------------------------------------


@pytest.mark.spec("review:refusal:no-error-record-is-written")
def test_a_refusal_writes_no_error_record_and_leaves_the_run_unchanged(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    _edit(draft, eye_colour=["hazel eyes"])
    before = snapshot(run.path)

    with pytest.raises(Refusal):
        approve(run, FLOW, schema, vocabulary)
    with pytest.raises(Refusal):
        review(run, "summon-v9")

    assert snapshot(run.path) == before
    assert [p.name for p in run.path.rglob("*.error.*")] == []


@pytest.mark.spec("run-directory:idempotence:rerun-is-a-no-op")
def test_reviewing_an_approved_flow_again_does_nothing_without_the_flag(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)
    approve(run, FLOW, schema, vocabulary)
    before = snapshot(run.path)

    assert review(run, FLOW) is None
    assert snapshot(run.path) == before


@pytest.mark.spec("run-directory:idempotence:rerun-is-a-no-op")
def test_approving_an_approved_flow_again_does_nothing_and_does_not_refuse(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)
    approve(run, FLOW, schema, vocabulary)
    before = snapshot(run.path)

    assert approve(run, FLOW, schema, vocabulary) == (None, [])
    assert snapshot(run.path) == before


@pytest.mark.spec("run-directory:idempotence:new-version-must-be-asked-for")
def test_the_explicit_flag_opens_the_next_draft_and_leaves_the_last_alone(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    frozen = approved.read_bytes()

    second = review(run, FLOW, new_version=True)

    assert second is not None and second.name == "002.draft.json"
    assert approved.read_bytes() == frozen


# --- the draft is updated in place, by one owner -------------------------------


@pytest.mark.spec("review:draft-update:values-are-replaced-in-place")
def test_draft_update_replaces_the_values_and_keeps_the_version(run: Run) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    before = read(draft, DRAFT_FILE)
    corrected = {name: list(tags) for name, tags in before["fields"].items()}
    corrected["hair_colour"] = ["blonde"]

    path = save_draft(run, FLOW, corrected)

    assert path == draft
    after = read(path, DRAFT_FILE)
    assert after["fields"]["hair_colour"] == ["blonde"]
    # The version and the sheet it came from are the draft's identity, and an
    # update is not a new draft: `review()` is the only thing that opens one.
    assert after["sheet"] == before["sheet"]
    assert versions(run.directory(FLOW, "review")) == [1]
    assert path == current_draft(run.directory(FLOW, "review"))


@pytest.mark.spec("review:draft-update:a-changed-field-set-is-refused")
def test_draft_update_refuses_a_changed_field_set(run: Run) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    frozen = draft.read_bytes()
    dropped = {
        name: list(tags)
        for name, tags in read(draft, DRAFT_FILE)["fields"].items()
        if name != "eye_colour"
    }

    with pytest.raises(Refusal) as refused:
        save_draft(run, FLOW, dropped)

    assert "eye_colour" in str(refused.value)
    assert draft.read_bytes() == frozen

    invented = {
        name: list(tags) for name, tags in read(draft, DRAFT_FILE)["fields"].items()
    }
    invented["favourite_biscuit"] = ["hobnob"]

    with pytest.raises(Refusal) as second:
        save_draft(run, FLOW, invented)

    assert "favourite_biscuit" in str(second.value)
    assert draft.read_bytes() == frozen


@pytest.mark.spec("review:draft-update:no-draft-refuses-the-update")
def test_draft_update_refuses_when_there_is_no_draft(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    directory = run.directory(FLOW, "review")

    with pytest.raises(Refusal) as refused:
        save_draft(run, FLOW, {"hair_colour": ["blonde"]})

    assert FLOW in str(refused.value)
    assert not directory.exists() or not versions(directory)

    # And once the draft has been approved it is gone, so the same refusal covers
    # a stale tab reaching a finished input.
    review(run, FLOW)
    approve(run, FLOW, schema, vocabulary)
    before = snapshot(run.path)

    with pytest.raises(Refusal):
        save_draft(run, FLOW, {"hair_colour": ["blonde"]})

    assert snapshot(run.path) == before


# --- the token budget, counted over the prompt the renderer reads --------------


@pytest.mark.spec("review:budget:count-covers-the-assembled-prompt")
def test_the_budget_counts_the_assembled_prompt_not_the_tags_alone(
    run: Run, schema: Schema, flow: Flow
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    fields = read(draft, DRAFT_FILE)["fields"]

    budget = token_budget(fields, schema, flow)

    positive, _ = assemble(fields, schema.names, flow)
    assert flow.prompt["prefix"] in positive
    assert flow.prompt["trailer"] in positive
    # `estimate_tokens` counts the tags alone, and that is exactly the number the
    # encoder does not read. The gap is at least the prefix's and the trailer's
    # own words -- which is what makes a sheet reported inside 77 actually past it.
    fixed = len(flow.prompt["prefix"].split()) + len(flow.prompt["trailer"].split())
    assert budget.total >= estimate_tokens(fields, schema) + fixed


@pytest.mark.spec("review:budget:shares-and-overhead-sum-to-the-total")
def test_the_budget_shares_and_overhead_sum_to_the_total(
    run: Run, schema: Schema, flow: Flow
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    fields = {
        name: list(tags) for name, tags in read(draft, DRAFT_FILE)["fields"].items()
    }

    budget = token_budget(fields, schema, flow)

    assert sum(budget.per_field.values()) + budget.overhead == budget.total
    assert set(budget.per_field) == set(schema.names)
    empty = [name for name in schema.names if not fields.get(name)]
    assert empty, "the fixture's sorter answers two fields, so the rest are empty"
    assert all(budget.per_field[name] == 0 for name in empty)


@pytest.mark.spec("review:budget:an-absent-field-is-counted-as-empty")
def test_the_budget_counts_an_absent_field_as_empty(
    run: Run, schema: Schema, flow: Flow
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    fields = {
        name: list(tags) for name, tags in read(draft, DRAFT_FILE)["fields"].items()
    }
    absent = {name: tags for name, tags in fields.items() if name != "eye_colour"}

    # A mid-edit draft is what the surface recomputes this over per keystroke, so
    # a field that is not there yet must contribute nothing rather than raise.
    budget = token_budget(absent, schema, flow)
    whole = token_budget({**absent, "eye_colour": []}, schema, flow)

    assert budget.per_field["eye_colour"] == 0
    assert budget.total == whole.total
    assert sum(budget.per_field.values()) + budget.overhead == budget.total


@pytest.mark.spec("review:copy:the-sheet-records-are-carried")
def test_the_draft_and_the_approval_carry_the_sheets_schema_and_field_map(
    run: Run, tmp_path: Path, schema: Schema, vocabulary: Vocabulary
) -> None:
    recorded = read(run.path / FLOW / "sheets" / "001.json", SHEET_FILE)
    draft = review(run, FLOW)
    assert draft is not None
    drafted = read(draft, DRAFT_FILE)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    for body in (drafted, read(approved, APPROVED_FILE)):
        assert body.get("schema_document") == recorded["schema_document"]
        assert body.get("field_map") == recorded["field_map"]

    # A sheet that records no field map yields a draft and approval with none.
    photo = tmp_path / "bea.jpg"
    photo.write_bytes(jpeg_bytes(1200, 908))
    bare = open_run(photo, tmp_path / "runs")
    written = sheet(bare, schema, vocabulary)
    assert written is not None
    body = json.loads(written.read_text())
    del body["field_map"]
    written.write_text(json.dumps(body))
    review(bare, FLOW)
    approved, _ = approve(bare, FLOW, schema, vocabulary)
    assert approved is not None
    assert "field_map" not in read(approved, APPROVED_FILE)


# --- copying another flow's approval ------------------------------------------

CONTROL = "control-anime-wai"


def _approved_source(run: Run, schema: Schema, vocabulary: Vocabulary) -> Path:
    """Approve `FLOW` unedited and return its approval."""
    review(run, FLOW)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    return approved


@pytest.mark.spec("review:copy-from:fields-are-copied-and-validated")
def test_a_copy_carries_the_sources_fields_and_the_targets_schema_validates_them(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    source = _approved_source(run, schema, vocabulary)
    narrower = Schema(schema.name, schema.fields[1:])

    with pytest.raises(Refusal) as refused:
        approve(run, CONTROL, narrower, vocabulary, source=FLOW)
    assert schema.fields[0].name in str(refused.value)
    assert not (run.path / CONTROL / "review").exists()

    copied, warnings = approve(run, CONTROL, schema, vocabulary, source=FLOW)

    assert copied == run.path / CONTROL / "review" / "001.approved.json"
    assert warnings == []
    assert (
        read(copied, APPROVED_FILE)["fields"] == read(source, APPROVED_FILE)["fields"]
    )


@pytest.mark.spec("review:copy-from:the-origin-is-recorded")
def test_a_copied_approval_names_its_flow_and_the_approval_it_came_from(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    source = _approved_source(run, schema, vocabulary)

    copied, _ = approve(run, CONTROL, schema, vocabulary, source=FLOW)

    assert copied is not None
    body = read(copied, APPROVED_FILE)
    assert body["flow"] == CONTROL
    assert body["producer"]["copied_from"] == {"flow": FLOW, "approval": 1}
    assert body["sheet"] == read(source, APPROVED_FILE)["sheet"]


@pytest.mark.spec("run-directory:layout:a-named-source-is-recorded")
def test_a_copy_records_its_source_and_leaves_the_sources_files_alone(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _approved_source(run, schema, vocabulary)
    before = snapshot(run.path / FLOW)

    copied, _ = approve(run, CONTROL, schema, vocabulary, source=FLOW)

    assert copied is not None
    assert read(copied, APPROVED_FILE)["producer"]["copied_from"]["flow"] == FLOW
    assert snapshot(run.path / FLOW) == before


@pytest.mark.spec("review:copy-from:no-source-approval-is-refused")
def test_a_source_with_no_approval_is_refused_naming_it_and_the_command(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)

    with pytest.raises(Refusal) as refused:
        approve(run, CONTROL, schema, vocabulary, source=FLOW)

    message = str(refused.value)
    assert FLOW in message
    flag = runs_flag(run)
    assert f"`python -m isekai approve --flow {FLOW}{flag} {run.id}`" in message
    assert not (run.path / CONTROL / "review").exists()


@pytest.mark.spec("review:copy-from:an-approved-target-writes-nothing")
def test_an_approved_target_is_not_copied_over(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _approved_source(run, schema, vocabulary)
    copied, _ = approve(run, CONTROL, schema, vocabulary, source=FLOW)
    assert copied is not None
    before = snapshot(run.path / CONTROL)

    again, warnings = approve(run, CONTROL, schema, vocabulary, source=FLOW)

    assert (again, warnings) == (None, [])
    assert snapshot(run.path / CONTROL) == before


@pytest.mark.spec("review:copy-from:a-newer-source-approval-is-copied-again")
@pytest.mark.parametrize("target", ["an older copy", "a hand approval"])
def test_a_target_not_copied_from_the_sources_latest_is_copied_again(
    run: Run, schema: Schema, vocabulary: Vocabulary, target: str
) -> None:
    _approved_source(run, schema, vocabulary)
    if target == "an older copy":
        approve(run, CONTROL, schema, vocabulary, source=FLOW)
    else:
        sheet(run, schema, vocabulary, flow=CONTROL)
        review(run, CONTROL)
        approve(run, CONTROL, schema, vocabulary)
    held = run.path / CONTROL / "review" / "001.approved.json"
    frozen = held.read_bytes()
    draft = review(run, FLOW, new_version=True)
    assert draft is not None
    _edit(draft, hair_silhouette=["long hair"])
    newer, _ = approve(run, FLOW, schema, vocabulary)
    assert newer is not None

    copied, _ = approve(run, CONTROL, schema, vocabulary, source=FLOW)

    assert copied == run.path / CONTROL / "review" / "002.approved.json"
    body = read(copied, APPROVED_FILE)
    assert body["producer"]["copied_from"] == {"flow": FLOW, "approval": 2}
    assert body["fields"] == read(newer, APPROVED_FILE)["fields"]
    assert held.read_bytes() == frozen


# --- ④ renders: how many images, and which seeds -------------------------------


def _with_renders(run: Run, count: int, seeds: list[int]) -> Path:
    """Open a draft and save it with `count` and `seeds`, as Review's ④ does."""
    draft = review(run, FLOW)
    assert draft is not None
    fields = read(draft, DRAFT_FILE)["fields"]
    return save_draft(run, FLOW, fields, {"count": count, "seeds": seeds})


@pytest.mark.spec("review:renders:an-old-draft-reads-as-one")
def test_a_draft_without_renders_reads_as_one_drawn_image(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    body = read(draft, DRAFT_FILE)
    assert "renders" not in body

    assert renders_of(draft, body, "unused") == {"count": 1, "seeds": []}
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    assert "renders" not in read(approved, APPROVED_FILE)


@pytest.mark.spec("review:renders:a-count-below-its-seeds-is-refused")
def test_a_count_below_its_seeds_refuses_approval_naming_the_count(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = _with_renders(run, 1, [])
    fields = read(draft, DRAFT_FILE)["fields"]
    with pytest.raises(Refusal, match="renders count 1 is below the 2 seeds"):
        save_draft(run, FLOW, fields, {"count": 1, "seeds": [7, 8]})
    _damage(draft, "renders", {"count": 1, "seeds": [7, 8]})

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert "renders count 1 is below the 2 seeds" in str(refused.value)
    assert draft.exists()
    assert approved_versions(run.directory(FLOW, "review")) == []
    save_draft(run, FLOW, fields, {"count": 3, "seeds": [7, 8]})
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    assert read(approved, APPROVED_FILE)["renders"] == {"count": 3, "seeds": [7, 8]}
    again = review(run, FLOW, new_version=True)
    assert again is not None
    assert read(again, DRAFT_FILE)["renders"] == {"count": 3, "seeds": [7, 8]}


@pytest.mark.spec("review:renders:a-seed-out-of-range-is-refused")
@pytest.mark.parametrize("seed", [-1, 2**64])
def test_a_seed_out_of_range_refuses_approval_naming_the_seed(
    run: Run, schema: Schema, vocabulary: Vocabulary, seed: int
) -> None:
    # By hand: the draft's own update refuses the seed as approval does.
    draft = _with_renders(run, 1, [])
    _damage(draft, "renders", {"count": 1, "seeds": [seed]})

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert f"renders seed {seed} is outside" in str(refused.value)
    assert draft.exists()
    assert approved_versions(run.directory(FLOW, "review")) == []


@pytest.mark.spec("review:renders:a-repeated-seed-is-refused")
def test_a_repeated_seed_refuses_approval_naming_the_seed(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    draft = _with_renders(run, 1, [])
    fields = read(draft, DRAFT_FILE)["fields"]
    with pytest.raises(Refusal, match="renders seed 144 is listed twice"):
        save_draft(run, FLOW, fields, {"count": 2, "seeds": [144, 144]})
    _damage(draft, "renders", {"count": 2, "seeds": [144, 144]})

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert "renders seed 144 is listed twice" in str(refused.value)
    assert draft.exists()
    assert approved_versions(run.directory(FLOW, "review")) == []


# --- revise and discard -------------------------------------------------------

SEED = 1840266731


def _approved(
    run: Run,
    schema: Schema,
    vocabulary: Vocabulary,
    renders: Renders | None = None,
    **fields: list[str],
) -> Path:
    """Open the next draft, edit it, save `renders` if given, and approve it."""
    draft = review(run, FLOW, new_version=True)
    assert draft is not None
    _edit(draft, **fields)
    if renders is not None:
        save_draft(run, FLOW, read(draft, DRAFT_FILE)["fields"], renders)
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    return approved


@pytest.mark.spec("review:revise:a-revision-copies-the-images-approval")
def test_a_revision_copies_the_images_approval_and_keeps_its_seed(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    first = _approved(run, schema, vocabulary, hair_silhouette=["long hair"])
    _approved(run, schema, vocabulary, clothes=["collared shirt"])

    _image(run, 1, SEED)
    draft = revise(run, FLOW, 1, SEED)

    assert draft.name == "003.draft.json"
    body = read(draft, DRAFT_FILE)
    assert body["fields"] == read(first, APPROVED_FILE)["fields"]
    assert body["producer"] == {
        "implementation": "review",
        "from": 1,
        "source": "review",
    }
    assert body["renders"] == {"count": 1, "seeds": [SEED]}


@pytest.mark.spec("review:revise:a-waiting-draft-refuses")
def test_a_waiting_draft_refuses_a_revision_and_nothing_is_written(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _approved(run, schema, vocabulary, hair_silhouette=["long hair"])
    assert review(run, FLOW, new_version=True) is not None
    before = snapshot(run.directory(FLOW, "review"))

    with pytest.raises(Refusal, match="002.draft.json waiting"):
        revise(run, FLOW, 1, SEED)

    assert snapshot(run.directory(FLOW, "review")) == before


@pytest.mark.spec("review:revise:an-unchanged-revision-is-refused")
@pytest.mark.parametrize("listed", [[SEED], []], ids=["listed", "drawn-and-rendered"])
def test_an_unchanged_revision_is_refused_naming_the_images_it_would_reproduce(
    run: Run, schema: Schema, vocabulary: Vocabulary, listed: list[int]
) -> None:
    # Drawn: the approval lists no seed, and the revised image is one it drew.
    _approved(run, schema, vocabulary, {"count": 1, "seeds": listed})
    _image(run, 1, SEED)
    draft = revise(run, FLOW, 1, SEED)

    with pytest.raises(Refusal) as refused:
        approve(run, FLOW, schema, vocabulary)

    assert f"seeds {SEED}," in str(refused.value)
    assert f"{run.id}/{FLOW}/outputs/001/" in str(refused.value)
    assert draft.exists()
    assert approved_versions(run.directory(FLOW, "review")) == [1]


@pytest.mark.spec("review:revise:new-seeds-alone-are-a-change")
def test_a_revision_whose_only_change_is_its_seeds_is_approved(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _approved(run, schema, vocabulary, {"count": 1, "seeds": [SEED]})
    _image(run, 1, SEED)
    draft = revise(run, FLOW, 1, SEED)
    save_draft(run, FLOW, read(draft, DRAFT_FILE)["fields"], {"count": 1, "seeds": [7]})

    approved, _ = approve(run, FLOW, schema, vocabulary)

    assert approved is not None
    assert read(approved, APPROVED_FILE)["renders"] == {"count": 1, "seeds": [7]}


@pytest.mark.spec("review:discard:a-draft-is-discarded")
def test_discarding_deletes_the_waiting_draft_and_leaves_every_approval(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    approved = _approved(run, schema, vocabulary, hair_silhouette=["long hair"])
    frozen = approved.read_bytes()
    waiting = review(run, FLOW, new_version=True)
    assert waiting is not None

    assert discard(run, FLOW) == waiting

    assert not waiting.exists()
    assert versions(run.directory(FLOW, "review")) == [1]
    assert approved.read_bytes() == frozen


@pytest.mark.spec("review:discard:an-approval-is-never-discarded")
def test_discarding_an_approved_flow_is_refused_and_changes_nothing(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _approved(run, schema, vocabulary, hair_silhouette=["long hair"])
    before = snapshot(run.directory(FLOW, "review"))

    with pytest.raises(Refusal, match="001.approved.json"):
        discard(run, FLOW)

    assert snapshot(run.directory(FLOW, "review")) == before


def _image(run: Run, version: int, seed: int) -> Path:
    """Write what a render leaves for `seed` under approval `version`."""
    group = run.directory(FLOW, "outputs", f"{version:03d}")
    group.mkdir(parents=True, exist_ok=True)
    (group / f"{seed}.render.json").write_text("{}\n")
    image = group / f"{seed}.png"
    image.write_bytes(b"png")
    return image


def _revise_verb(vocabulary: Vocabulary, *images: Path) -> tuple[int, str]:
    """Run `isekai revise` on `images`, returning its status and its stderr."""
    err = io.StringIO()
    wired = Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=lambda: vocabulary,
        field_map=lambda _: pytest.fail("revise reads no field map"),
        out=io.StringIO(),
        err=err,
    )
    parsed = build_parser().parse_args(["revise", *map(str, images)])
    return dispatch(parsed, wired), err.getvalue()


def _second_run(run: Run, schema: Schema, vocabulary: Vocabulary) -> Run:
    """Return another run beside `run`, with its own sheet for `FLOW`."""
    photo = run.path.parent.parent / "uncle-bo.jpg"
    photo.write_bytes(jpeg_bytes(1000, 800))
    made = open_run(photo, run.path.parent)
    caption(made, FakeReader(prose="Black hair, grey eyes."))
    sheet(made, schema, vocabulary)
    return made


@pytest.mark.spec("cli:revise:every-image-is-revised")
def test_the_verb_revises_each_image_in_its_own_run(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    other = _second_run(run, schema, vocabulary)
    for each in (run, other):
        _approved(each, schema, vocabulary, hair_silhouette=["long hair"])

    status, err = _revise_verb(vocabulary, _image(run, 1, SEED), _image(other, 1, 7))

    assert (status, err) == (0, "")
    for each, seed in ((run, SEED), (other, 7)):
        draft = read(each.directory(FLOW, "review") / "002.draft.json", DRAFT_FILE)
        assert draft["renders"] == {"count": 1, "seeds": [seed]}


@pytest.mark.spec("cli:revise:one-refusal-writes-nothing")
def test_one_refused_image_leaves_every_run_without_a_revision(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    other = _second_run(run, schema, vocabulary)
    for each in (run, other):
        _approved(each, schema, vocabulary, hair_silhouette=["long hair"])
    assert review(other, FLOW, new_version=True) is not None
    blocked = _image(other, 1, 7)

    status, err = _revise_verb(vocabulary, _image(run, 1, SEED), blocked)

    assert status == 1
    assert f"{blocked}" in err
    assert "002.draft.json waiting" in err
    assert versions(run.directory(FLOW, "review")) == [1]

    # The waiting draft goes, and the approval it was copied from is broken.
    discard(other, FLOW)
    (other.directory(FLOW, "review") / "001.approved.json").write_text("{")

    status, err = _revise_verb(vocabulary, _image(run, 1, SEED), blocked)

    assert status == 1
    assert f"refused: {blocked}: 001.approved.json: is not valid JSON" in err
    assert versions(run.directory(FLOW, "review")) == [1]

    # One run reached by two spellings is one run, and its flow one revision.
    spelled = run.path.parent.parent / "spelled"
    spelled.symlink_to(run.path.parent)
    _image(run, 1, 7)
    twin = spelled / run.id / FLOW / "outputs" / "001" / "7.png"

    status, err = _revise_verb(vocabulary, _image(run, 1, SEED), twin)

    assert status == 1
    assert f"refused: {twin}: {run.id}/{FLOW}: is in this selection twice" in err
    assert versions(run.directory(FLOW, "review")) == [1]

    # A padded name is no render's, though its seed's render lies beside it.
    _image(run, 1, 42)
    padded = run.directory(FLOW, "outputs", "001") / "0042.png"
    padded.write_bytes(b"png")

    status, err = _revise_verb(vocabulary, padded)

    assert status == 1
    assert f"refused: {padded}: is not an image a render wrote" in err
    assert versions(run.directory(FLOW, "review")) == [1]


# --- cancel -------------------------------------------------------------------


def _approved_with_draft(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> tuple[Path, bytes]:
    """Approve a draft listing a seed, and return the approval and the draft's bytes."""
    draft = review(run, FLOW)
    assert draft is not None
    _edit(draft, hair_silhouette=["long hair"])
    save_draft(run, FLOW, read(draft, DRAFT_FILE)["fields"], {"count": 2, "seeds": [7]})
    held = draft.read_bytes()
    approved, _ = approve(run, FLOW, schema, vocabulary)
    assert approved is not None
    return approved, held


@pytest.mark.spec("review:cancel:a-cancel-restores-the-draft")
def test_a_cancel_writes_back_the_draft_the_approval_was_made_from(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    approved, held = _approved_with_draft(run, schema, vocabulary)
    assert cancellable(run, FLOW) is None

    draft = cancel(run, FLOW)

    assert draft == run.directory(FLOW, "review") / "001.draft.json"
    assert draft.read_bytes() == held
    assert not approved.exists()
    assert state(run.directory(FLOW, "review")) == "draft"


@pytest.mark.spec("review:cancel:an-older-approval-stays")
def test_cancelling_a_revision_leaves_the_rendered_approval_it_revised(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    first = _approved(run, schema, vocabulary, hair_silhouette=["long hair"])
    frozen = first.read_bytes()
    _image(run, 1, SEED)
    revised = revise(run, FLOW, 1, SEED)
    _edit(revised, clothes=["collared shirt"])
    assert approve(run, FLOW, schema, vocabulary)[0] is not None

    assert cancel(run, FLOW) == revised

    assert first.read_bytes() == frozen
    assert approved_versions(run.directory(FLOW, "review")) == [1]
    assert state(run.directory(FLOW, "review")) == "re-opened"


@pytest.mark.spec("review:cancel:anything-made-from-it-refuses")
@pytest.mark.parametrize(
    ("made", "named", "way"),
    [
        ("prompt", "prompts/001.json", "--new-version"),
        ("failure", "prompts/001.error.1.permanent.json", "--new-version"),
        ("empty group", "outputs/001", "--new-version"),
        ("image", "outputs/001", "isekai revise "),
    ],
)
def test_anything_made_from_an_approval_refuses_its_cancel_and_changes_nothing(
    run: Run,
    schema: Schema,
    vocabulary: Vocabulary,
    made: str,
    named: str,
    way: str,
) -> None:
    _approved_with_draft(run, schema, vocabulary)
    if made == "prompt":
        prompt_artifact(run, load_flow(FLOW), schema)
    elif made == "failure":
        record_failure(
            run.directory(FLOW, "prompts"),
            1,
            "permanent",
            {"stage": "assemble", "detail": "x"},
        )
    elif made == "empty group":
        run.directory(FLOW, "outputs", "001").mkdir(parents=True)
    else:
        _image(run, 1, SEED)
    before = snapshot(run.path)

    with pytest.raises(Refusal) as refused:
        cancel(run, FLOW)

    assert f"{FLOW}/{named} came from it" in str(refused.value)
    assert way in str(refused.value)
    assert cancellable(run, FLOW) == str(refused.value)
    assert snapshot(run.path) == before

    waiting = review(run, FLOW, new_version=True)
    assert waiting is not None
    reopened = cancellable(run, FLOW)
    assert reopened is not None
    assert f"{FLOW}/{named} came from it" in reopened
    assert str(waiting) in reopened
    assert "--discard" not in reopened


@pytest.mark.spec("review:cancel:a-copy-taken-from-it-refuses")
def test_a_copy_in_another_flow_refuses_the_sources_cancel(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _approved_source(run, schema, vocabulary)
    approve(run, CONTROL, schema, vocabulary, source=FLOW)
    before = snapshot(run.path)

    with pytest.raises(Refusal, match=f"{CONTROL}/review/001.approved.json came"):
        cancel(run, FLOW)
    assert re.search(
        f"approve --flow {CONTROL} .*--cancel", str(cancellable(run, FLOW))
    )

    assert snapshot(run.path) == before
    assert cancel(run, CONTROL) is None
    assert cancel(run, FLOW) == run.directory(FLOW, "review") / "001.draft.json"


@pytest.mark.spec("review:cancel:a-copy-is-deleted-and-a-reopened-sheet-refused")
def test_a_copy_is_deleted_and_an_approval_with_a_later_draft_refuses_its_discard(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    _approved_source(run, schema, vocabulary)
    copy, _ = approve(run, CONTROL, schema, vocabulary, source=FLOW)
    assert copy is not None
    held = copy.read_bytes()
    assert review(run, FLOW, new_version=True) is not None
    before = snapshot(run.path)

    assert cancel(run, CONTROL) is None
    gone = str(copy.relative_to(run.path))
    assert snapshot(run.path) == {k: v for k, v in before.items() if k != gone}
    with pytest.raises(Refusal, match=f"review --flow {FLOW} .*--discard"):
        cancel(run, FLOW)
    assert approve(run, CONTROL, schema, vocabulary, source=FLOW)[0] == copy
    assert copy.read_bytes() == held


@pytest.mark.spec("review:cancel:an-interrupted-cancel-finishes")
def test_a_cancel_interrupted_before_its_delete_finishes_when_run_again(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    approved, held = _approved_with_draft(run, schema, vocabulary)
    beside = run.directory(FLOW, "review") / "001.draft.json"
    beside.write_bytes(held)
    assert state(run.directory(FLOW, "review")) == "approved"

    assert cancel(run, FLOW) == beside

    assert sorted(path.name for path in beside.parent.iterdir()) == [beside.name]
    assert beside.read_bytes() == held

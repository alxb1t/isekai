"""Stage (3): the copy, the draft, the validation, and the rename that is approval.

The load-bearing assertion in this file is negative: after every path through
this stage, `sheets/<flow>/` is byte-identical to what stage (2) wrote.
"""

import json
from pathlib import Path

import pytest

from isekai.caption import FakeReader, caption
from isekai.refusal import Refusal
from isekai.review import (
    ENCODER_WINDOW,
    approve,
    draft_versions,
    estimate_tokens,
    is_complete,
    review,
)
from isekai.run import Run, approved_versions, open_run, read_artifact, versions
from isekai.sheet import FakeSorter, Schema, sheet
from isekai.vocabulary import Vocabulary
from tests.conftest import snapshot
from tests.images import jpeg_bytes

FLOW = "summon-v1"


@pytest.fixture
def run(tmp_path: Path, schema: Schema, vocabulary: Vocabulary) -> Run:
    """Return a run carrying a caption and one filled sheet for `FLOW`."""
    photo = tmp_path / "aunt-ada.jpg"
    photo.write_bytes(jpeg_bytes(1200, 900))
    made = open_run(photo, tmp_path / "runs")
    caption(made, FakeReader(prose="Dark brown hair, brown eyes."))
    sheet(
        made,
        FakeSorter(answers={"hair_colour": ["dark brown"], "eye_colour": ["brown"]}),
        schema,
        vocabulary,
        [FLOW],
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
    before = snapshot(run.path / "sheets")

    draft = review(run, FLOW)

    assert draft is not None
    assert draft.parent == run.path / "review" / FLOW
    assert draft.name == "001.draft.json"
    assert snapshot(run.path / "sheets") == before


@pytest.mark.spec("review:copy:review-writes-to-its-own-directory")
def test_editing_the_draft_leaves_the_sheet_untouched(run: Run) -> None:
    draft = review(run, FLOW)
    assert draft is not None
    before = snapshot(run.path / "sheets")

    _edit(draft, hair_colour=["black hair"])

    assert snapshot(run.path / "sheets") == before
    assert read_artifact(run.path / "sheets" / FLOW / "001.json")["fields"][
        "hair_colour"
    ] == ["brown hair"]


@pytest.mark.spec("review:copy:highest-sheet-is-copied")
def test_the_highest_sheet_is_copied_and_its_version_recorded(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    sheet(
        run,
        FakeSorter(answers={"hair_colour": ["black"]}),
        schema,
        vocabulary,
        [FLOW],
        new_version=True,
    )
    assert versions(run.path / "sheets" / FLOW) == [1, 2]

    draft = review(run, FLOW)

    assert draft is not None
    body = read_artifact(draft)
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
    assert read_artifact(second)["fields"]["hair_silhouette"] == ["long hair"]
    assert read_artifact(second)["producer"]["source"] == "review"


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
    directory = run.path / "review" / FLOW

    assert draft_versions(directory) == [1]
    assert approved_versions(directory) == []
    assert not is_complete(directory)


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
    assert read_artifact(approved)["fields"] == before
    assert not draft.exists()


@pytest.mark.spec("review:approval:approve-validates-then-renames")
def test_approval_is_decidable_from_the_filename_alone(
    run: Run, schema: Schema, vocabulary: Vocabulary
) -> None:
    review(run, FLOW)
    approve(run, FLOW, schema, vocabulary)
    directory = run.path / "review" / FLOW

    assert [p.name for p in directory.iterdir()] == ["001.approved.json"]
    assert approved_versions(directory) == [1]
    assert is_complete(directory)


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
    assert approved_versions(run.path / "review" / FLOW) == []


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

    assert read_artifact(approved)["fields"]["pose"] == []


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

    body = read_artifact(approved)
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

    body = read_artifact(approved)
    assert body["producer"]["edited"] is True
    assert body["sheet"] == 1
    # Nothing the operator wrote says so; it is computed against the sheet.
    assert (
        "edited"
        not in json.loads(
            draft.parent.parent.parent.joinpath("sheets", FLOW, "001.json").read_text()
        )["producer"]
    )


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

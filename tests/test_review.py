"""Stage (3): the copy, the draft, the validation, and the rename that is approval.

The load-bearing assertion in this file is negative: after every path through
this stage, `<flow>/sheets/` is byte-identical to what stage (2) wrote.
"""

import json
from pathlib import Path

import pytest

from isekai.foundation.artifacts import APPROVED_FILE, DRAFT_FILE, SHEET_FILE, read
from isekai.foundation.flow import Flow, Schema, assemble, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    Run,
    approved_versions,
    open_run,
    versions,
)
from isekai.pipeline.caption import FakeReader
from isekai.pipeline.review import (
    ENCODER_WINDOW,
    approve,
    draft_versions,
    estimate_tokens,
    review,
    save_draft,
    state,
    token_budget,
)
from isekai.shared.vocabulary import Vocabulary
from tests.conftest import snapshot
from tests.images import jpeg_bytes
from tests.stages import caption, sheet

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

    assert draft_versions(directory) == [1]
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
    assert draft_versions(run.directory(FLOW, "review")) == [1]


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
    # a stale tab reaching a finished input (design.md D5).
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

"""Stage (3): the operator's correction, on a copy, approved by a rename.

**The machine's sheet is never edited, and that is a property of the layout
rather than a rule a tool is trusted to follow.** `sheets/<flow>/` is written
once by stage (2) and is read-only to everything else; `review/<flow>/` is the
only mutable directory in a run. The alternative -- both stages writing into one
directory, told apart by number -- makes "the machine's sheet is never edited" a
convention that an editor, a script or a careless command can break silently and
permanently.

**The baseline is what is being protected.** The unreviewed route carries 0.568
of a sheet's attributes into the render and the reviewed one carries 0.917.
Editing in place destroys the thing that difference is measured against, on every
run. Separating the directories also makes rendering the machine's raw draft an
*explicit* act -- approve it unedited, and the artifact records that it was
unedited -- which turns "was this reviewed" into a fact on disk.

**Saving is not approving.** A draft is parkable half-edited for as long as the
operator wants; approval is a separate act, and it is what a directory listing
reads to decide whether this stage is done.

**On "the bytes are unchanged".** Approval must not alter what the operator
wrote, and it does not: the `fields` block is carried across byte for byte. It
*does* add one thing the operator cannot write themselves -- whether the content
differs from the sheet it was copied from -- because the whole point of that
record is that it does not depend on anybody having said so. A literal
never-add-a-byte reading would make that record impossible to write at all.

**This stage writes no error record and consumes no retry budget.** Error records
exist so a batch of twenty photographs does not halt on one item; here there is
no batch and no unattended retry, the operator is present by definition, and a
refusal is a message to them rather than state for a later resume to reason about.

Stdlib only.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    SHEET_FILE,
    ReviewApproved,
    ReviewDraft,
    read,
    require,
    write,
)
from isekai.foundation.flow import Flow, Schema, assemble
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    REVIEW,
    SHEETS,
    Run,
    approved_versions,
    artifact_name,
    latest,
    latest_artifact,
    next_version,
    versions,
)
from isekai.shared.fields import validate
from isekai.shared.vocabulary import Vocabulary

STAGE = "review"

DRAFT = "draft"

# SDXL's text encoders read 77 tokens at a time; past that the prompt is chunked
# and the chunks are averaged, which is not the same prompt. Sheets already run
# well past it and nothing said so, so every one was being silently averaged.
ENCODER_WINDOW = 77

# The three states stage ③ has, and the strings the review UI puts on the wire.
Status = Literal["draft", "approved", "re-opened"]


def current_draft(directory: Path) -> Path | None:
    """Return the highest draft numbered above the highest approval, or None.

    **The one definition of the draft being worked on.** A draft at or below an
    approval is stale -- left by a crash between approving and unlinking, or
    older than the approval -- so it neither re-opens the input nor is approved.
    e.g. `001.draft.json 002.approved.json` -> None
    """
    draft = latest_artifact(directory, DRAFT)
    approved = approved_versions(directory)
    if draft is None or (approved and int(draft.name[:3]) <= approved[-1]):
        return None
    return draft


def state(directory: Path) -> Status:
    """Return where this input stands in stage ③, from filenames alone.

    **The one definition of the three states**, because the alternative --
    `readonly`, the `PUT` gate and the rail's status as three expressions over
    the same two predicates -- is true together only while they happen to
    agree.

    `re-opened` is an approved artifact with a **later** version beside it,
    which is exactly what `review --flow F --new-version <run>` writes and nothing
    else does. Later rather than merely present, so a draft that predated
    the approval could never re-open one -- and `approved_versions()[-1]` is
    the number the approved artifact records as `approved_from`, because
    `approve()` derives its filename and that field from one local.

    Filenames only: no artifact is opened, and the common unapproved case
    costs a single listing.
    """
    approved = approved_versions(directory)
    if not approved:
        return "draft"
    later = [version for version in versions(directory) if version > approved[-1]]
    return "re-opened" if later else "approved"


def review(run: Run, flow: str, *, new_version: bool = False) -> Path | None:
    """Copy `flow`'s sheet into the review directory as an editable draft.

    The highest sheet is what is copied, and the copy records which version that
    was. Where an approved copy already exists, the new draft is written from
    *it* rather than from the sheet -- a correction starts from the last thing
    the operator agreed with, not from the machine's first attempt -- and the
    approved copy is left exactly as it was.

    Returns the draft's path, or None when there is nothing to do -- which is
    either because a draft is already waiting, or because this flow is already
    approved. Both are the same rule: **a new version is an explicit act.** An
    unapproved draft is the operator's and re-running must not overwrite their
    half-finished edit; an approved flow is finished, and quietly opening a new
    draft every time somebody re-ran the pipeline would make resume write.
    """
    sheets = run.directory(flow, SHEETS)
    review_directory = run.directory(flow, REVIEW)

    if versions(review_directory) and not new_version:
        return None

    source_sheet = latest(sheets)
    if source_sheet is None:
        raise Refusal(
            f"{run.id}: flow {flow} has no sheet to review; run "
            f"`python -m isekai sheet --flow {flow} {run.id}` first"
        )

    again = _again(run, flow)
    approved = approved_versions(review_directory)
    if approved:
        copied = review_directory / artifact_name(approved[-1], APPROVED)
        # An approved artifact is never replaced, so only a hand repairs it.
        remedy = f"restore it in {copied}, then run {again} again"
        carried = read(copied, APPROVED_FILE, remedy=remedy)
        require(
            copied,
            carried,
            "sheet",
            int,
            f"a draft copied from it cannot name its sheet; add the sheet version "
            f"it was approved from as `sheet` in {copied}, then run {again} again",
        )
        came_from, source, sheet_version = approved[-1], REVIEW, carried["sheet"]
    else:
        copied = sheets / artifact_name(source_sheet)
        carried = read(copied, SHEET_FILE)
        remedy = (
            f"run `python -m isekai sheet --flow {flow} --new-version {run.id}`, "
            f"then {again}"
        )
        came_from, source, sheet_version = source_sheet, SHEETS, source_sheet

    require(copied, carried, "vocabulary", dict, remedy)
    require(copied, carried, "fields", dict, remedy)
    version = next_version(review_directory)
    path = review_directory / artifact_name(version, DRAFT)
    draft: ReviewDraft = {
        "schema": DRAFT_FILE.schema,
        "producer": {"implementation": STAGE, "from": came_from, "source": source},
        "flow": flow,
        "sheet": sheet_version,
        "vocabulary": carried["vocabulary"],
        "fields": carried["fields"],
    }
    # Carried where the source records them, so the approval can name the
    # schema and table its fields came through.
    if "schema_document" in carried:
        draft["schema_document"] = carried["schema_document"]
    if "field_map" in carried:
        draft["field_map"] = carried["field_map"]
    write(path, DRAFT_FILE, draft)
    return path


def estimate_tokens(fields: Mapping[str, Sequence[str]], schema: Schema) -> int:
    """Estimate what the text encoder will read from this sheet, in tokens.

    Deliberately crude and deliberately stated: one token per word plus one per
    tag separator, plus the two the encoder adds itself. It is an estimate for a
    warning, not a budget anything is enforced against -- the exact count depends
    on the tokenizer's merges, and a number that pretended otherwise would invite
    being trusted.
    """
    tags = [tag for name in schema.names for tag in fields.get(name, ())]
    words = sum(len(tag.split()) for tag in tags)
    separators = max(len(tags) - 1, 0)
    return words + separators + 2


def save_draft(run: Run, flow: str, fields: Mapping[str, Sequence[str]]) -> Path:
    """Replace the current draft's field values in place, and return its path.

    The one owner of a draft update. The draft's shape is otherwise built only at
    creation, and a second writer arriving without a single owner is how two shapes
    of one file drift apart.

    **It does not create.** `review()` owns that, and teaching this to create too
    would spend a version number on a stray keypress -- there is no Save control
    on the surface that calls it and no confirm step to attribute one to. The
    version and the sheet the draft records are its identity and are carried
    across untouched.

    **A changed field set is refused**, which is what makes this owner
    load-bearing rather than clerical: a missing field and a field the schema does
    not have are two of the four ways a sheet can be invalid at approval, and
    comparing the set at the one write point turns both from a property the
    editing surface is trusted to have into a property of the write path -- for
    one comparison, without opening the validator.
    """
    directory = run.directory(flow, REVIEW)
    path = current_draft(directory)
    if path is None:
        raise Refusal(
            f"{run.id}: flow {flow} has no draft to update; a draft is opened by "
            f"`python -m isekai review --flow {flow} {run.id}`, and an approved "
            "flow has none because approval is the end of it"
        )

    body = read(path, DRAFT_FILE)
    require(path, body, "fields", dict, _recopy(run, flow, path))
    existing = set(body["fields"])
    offered = set(fields)
    if offered != existing:
        missing = sorted(existing - offered)
        unknown = sorted(offered - existing)
        raise Refusal(
            f"{path.name}: an update replaces a draft's values and never its "
            f"field set; missing {missing}, unknown {unknown}"
        )

    updated: ReviewDraft = {
        **body,
        "fields": {name: list(fields[name]) for name in body["fields"]},
    }
    write(path, DRAFT_FILE, updated)
    return path


@dataclass(frozen=True)
class TokenBudget:
    """What the text encoder will read from this sheet, and where it comes from.

    Three numbers from one rule, so they reconcile instead of disagreeing: the
    shares sum into the total and `overhead` is the remainder. The operator's
    question while correcting is never *how many tokens* but *which tag goes*,
    and a total with no breakdown cannot answer it.
    """

    total: int
    per_field: Mapping[str, int]
    overhead: int


def token_budget(
    fields: Mapping[str, Sequence[str]], schema: Schema, flow: Flow
) -> TokenBudget:
    """Count the assembled positive prompt, and split it into shares.

    `total` is taken over `assemble()`'s own output, so the flow's prefix, its
    trailer and the separators that join them fall out of one rule rather than
    being added back by hand. That is the whole point: counting the tags alone
    understates what the encoder reads by about nineteen tokens against a window
    of seventy-seven, so a sheet reported comfortably inside the budget is past it
    and silently chunked.

    `estimate_tokens` is deliberately left alone. It is `approve()`'s, it is
    passed a `Schema` and never a `Flow`, and changing its signature would move
    every one of its call sites for a warning on a path deprecated as guidance.

    A field absent from a mid-edit draft contributes nothing rather than raising,
    because the surface recomputes this on every keystroke.
    """
    separator = flow.prompt["separator"]
    positive, _ = assemble(fields, schema.names, flow)
    total = len(positive.split()) + positive.count(separator) + 2

    per_field: dict[str, int] = {}
    for name in schema.names:
        tags = list(fields.get(name, ()))
        per_field[name] = sum(len(tag.split()) for tag in tags) + len(tags)

    return TokenBudget(total, per_field, total - sum(per_field.values()))


def approve(
    run: Run,
    flow: str,
    schema: Schema,
    vocabulary: Vocabulary,
    source: str | None = None,
) -> tuple[Path | None, list[str]]:
    """Validate `flow`'s current draft and approve it, returning it and any warnings.

    With `source`, no draft is read: `source`'s latest approval is copied under
    `flow` instead, and the copy names where it came from.

    Validation is the last place an invented tag can be caught: one that merely
    looks canonical passes every later check on its way into the prompt. The
    refusal says the tag is not in the vocabulary's *prediction set*, which is
    what is true -- that set is a subset of the wider tag corpus, so calling an
    absent tag unreal would overclaim.
    """
    if source is not None:
        return _copy_approval(run, flow, schema, vocabulary, source), []
    directory = run.directory(flow, REVIEW)
    draft = current_draft(directory)
    if draft is None:
        if approved_versions(directory):
            # Already approved, and approving again would have nothing to act on.
            # A no-op rather than a refusal, because re-running every command is
            # the whole of resume and resume must not exit non-zero.
            return None, []
        raise Refusal(
            f"{run.id}: flow {flow} has no draft to approve; run "
            f"`python -m isekai review --flow {flow} {run.id}` to take a copy, "
            "edit it, then approve it"
        )

    version = int(draft.name[:3])
    body = read(draft, DRAFT_FILE)
    # A hand-edited draft without a `fields` object holds no fields, so
    # validation refuses it naming every one it lacks.
    held = body.get("fields")
    fields: dict[str, list[str]] = (
        {name: list(tags) for name, tags in held.items()}
        if isinstance(held, dict)
        else {}
    )
    validate(fields, schema, vocabulary)

    warnings: list[str] = []
    estimate = estimate_tokens(fields, schema)
    if estimate > ENCODER_WINDOW:
        warnings.append(
            f"{run.id}/{flow}: the assembled prompt is about {estimate} tokens "
            f"and the text encoder reads {ENCODER_WINDOW} at a time, so it will "
            "be chunked and averaged; the sheet is the record of what was asked "
            "for, so this is a warning and not a refusal"
        )

    remedy = _recopy(run, flow, draft)
    for key, shape in (("sheet", int), ("producer", dict), ("vocabulary", dict)):
        require(draft, body, key, shape, remedy)
    sheet_version, producer = body["sheet"], body["producer"]
    sheet_path = run.directory(flow, SHEETS) / artifact_name(sheet_version)
    approved_body: ReviewApproved = {
        "schema": APPROVED_FILE.schema,
        "producer": {
            **producer,
            "edited": _differs(fields, draft, sheet_path, _resheet(run, flow, draft)),
            "approved_from": version,
        },
        "flow": flow,
        "sheet": sheet_version,
        "vocabulary": body["vocabulary"],
        "fields": fields,
    }
    if "schema_document" in body:
        approved_body["schema_document"] = body["schema_document"]
    if "field_map" in body:
        approved_body["field_map"] = body["field_map"]

    path = directory / artifact_name(version, APPROVED)
    if path.exists():
        raise Refusal(
            f"{path.name} already exists in {flow}/{REVIEW}/ and an approved "
            f"artifact is never replaced; run {_again(run, flow)} to correct it "
            "under the next number"
        )
    write(path, APPROVED_FILE, approved_body)
    draft.unlink()
    return path, warnings


def _copy_approval(
    run: Run, flow: str, schema: Schema, vocabulary: Vocabulary, source: str
) -> Path | None:
    """Write `source`'s latest approval under `flow`, or None if `flow` is in step.

    `flow` is in step when its latest approval is a copy of `source`'s latest; an
    older copy or a hand approval is copied over under the next number. The fields
    are validated against `flow`'s schema, so a copy the target cannot hold is
    refused like any draft. `sheet` stays `source`'s: it is provenance, and
    `copied_from` says where to look.
    """
    origin = run.directory(source, REVIEW)
    versions_held = approved_versions(origin)
    if not versions_held:
        raise Refusal(
            f"{run.id}: {flow} is copied from {source}, which has no approved "
            f"sheet; run `python -m isekai review --flow {source} {run.id}`, edit "
            f"the draft, then `python -m isekai approve --flow {source} {run.id}` "
            "first"
        )
    approval = versions_held[-1]
    directory = run.directory(flow, REVIEW)
    held = approved_versions(directory)
    if held:
        mine = directory / artifact_name(held[-1], APPROVED)
        latest = read(mine, APPROVED_FILE)
        require(
            mine,
            latest,
            "producer",
            dict,
            f"delete {mine}, then run {_again(run, flow)} to approve it afresh",
        )
        copied_from = latest["producer"].get("copied_from")
        if copied_from == {"flow": source, "approval": approval}:
            return None

    path = origin / artifact_name(approval, APPROVED)
    body = read(path, APPROVED_FILE)
    remedy = f"delete {path}, then run {_again(run, source)} to approve it afresh"
    for key, shape in (
        ("fields", dict),
        ("sheet", int),
        ("producer", dict),
        ("vocabulary", dict),
    ):
        require(path, body, key, shape, remedy)
    fields = {name: list(tags) for name, tags in body["fields"].items()}
    validate(fields, schema, vocabulary)

    copied: ReviewApproved = {
        **body,
        "producer": {
            **body["producer"],
            "copied_from": {"flow": source, "approval": approval},
        },
        "flow": flow,
        "fields": fields,
    }
    target = directory / artifact_name(next_version(directory), APPROVED)
    write(target, APPROVED_FILE, copied)
    return target


def _again(run: Run, flow: str) -> str:
    """Return the command that copies `flow`'s draft afresh under the next number."""
    return f"`python -m isekai review --flow {flow} --new-version {run.id}`"


def _recopy(run: Run, flow: str, draft: Path) -> str:
    """Return the remedy for a draft that lost a key: a fresh copy, newly numbered."""
    return f"delete {draft}, then run {_again(run, flow)} to take a fresh copy"


def _resheet(run: Run, flow: str, draft: Path) -> str:
    """Return the remedy for a draft whose sheet cannot be compared against.

    The sheet is kept rather than deleted: deleting it would free its number for
    the next `sheet` run to reuse under different content. With no approval, a
    new sheet and a fresh copy of it give `edited` something true to be computed
    against, and the old draft stays to carry the correction across. A re-opened
    draft is copied from the approval, which names this same sheet, so a fresh
    copy would be refused again; there the fix is to keep the approval.
    """
    approved = approved_versions(draft.parent)
    if approved:
        return (
            f"delete {draft} to leave {flow} approved as "
            f"{artifact_name(approved[-1], APPROVED)} records it"
        )
    return (
        f"run `python -m isekai sheet --flow {flow} --new-version {run.id}`, then "
        f"{_again(run, flow)} to copy the new sheet; {draft.name} keeps your "
        "edits to carry across"
    )


def _differs(
    fields: Mapping[str, Sequence[str]], draft: Path, source: Path, remedy: str
) -> bool:
    """Say whether `fields` differs from the sheet it was copied from.

    Computed rather than declared. Whether a sheet was actually corrected is the
    difference between the 0.568 route and the 0.917 one, and a flag the operator
    sets is an assumption wearing a fact's clothes. A missing sheet is refused
    rather than read as unedited, which would be exactly such an assumption.
    """
    if not source.exists():
        raise Refusal(
            f"{draft.name}: was copied from {source}, which is not there, so "
            f"whether it was edited cannot be computed; {remedy}"
        )
    body = read(source, SHEET_FILE, remedy=remedy)
    require(source, body, "fields", dict, remedy)
    original = body["fields"]
    return {name: list(tags) for name, tags in original.items()} != {
        name: list(tags) for name, tags in fields.items()
    }

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

import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    ONE_RENDER,
    SHEET_FILE,
    SIDECAR,
    CopiedFrom,
    Renders,
    ReviewApproved,
    ReviewDraft,
    Sheet,
    read,
    renders_of,
    require,
    write,
)
from isekai.foundation.flow import Flow, Schema, assemble
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    NEW_VERSION,
    PROMPTS,
    REVIEW,
    SHEETS,
    Run,
    approval_of,
    approved_versions,
    artifact_name,
    attempts,
    group_of,
    is_seed,
    latest,
    latest_artifact,
    next_version,
    sheet_of,
    stage_command,
    versions,
)
from isekai.shared.fields import validate
from isekai.shared.vocabulary import Vocabulary

STAGE = "review"

DRAFT = "draft"

# The option that deletes a flow's waiting draft.
DISCARD = ("--discard",)

# The option that cancels a flow's newest approval.
CANCEL = ("--cancel",)

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
    the approval could never re-open one -- and for an approval made from a
    draft, `approved_versions()[-1]` is the number it records as
    `approved_from`, because `approve()` derives its filename and that field
    from one local. A copy keeps its source's producer and names its origin in
    `copied_from` instead.

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
            f"`{stage_command(run, 'sheet', flow)}` first"
        )

    approved = approved_versions(review_directory)
    if approved:
        carried = _approval(run, flow, approved[-1], f"run {_again(run, flow)} again")
        return _write_draft(
            run,
            flow,
            approved[-1],
            REVIEW,
            carried,
            carried["sheet"],
            carried.get("renders"),
        )
    copied = sheets / artifact_name(source_sheet)
    carried = read(copied, SHEET_FILE)
    remedy = (
        f"run `{stage_command(run, 'sheet', flow, options=NEW_VERSION)}`, "
        f"then {_again(run, flow)}"
    )
    require(copied, carried, "vocabulary", dict, remedy)
    require(copied, carried, "fields", dict, remedy)
    return _write_draft(run, flow, source_sheet, SHEETS, carried, source_sheet)


def revise(run: Run, flow: str, version: int, seed: int) -> Path:
    """Copy the approval numbered `version` into the next draft, listing `seed`.

    The draft starts from the sheet the image was rendered under, newest or not,
    with a count of one and the image's seed, so an edit lands on the same
    composition. Refused as `refuse_revision` refuses.
    e.g. (run, f, 1, 1840266731) -> review/003.draft.json, seeds [1840266731]
    """
    carried = refuse_revision(run, flow, version, seed)
    renders: Renders = {"count": 1, "seeds": [seed]}
    return _write_draft(run, flow, version, REVIEW, carried, carried["sheet"], renders)


def draft_from(
    run: Run, flow: str, source: str, version: int | None, schema: Schema
) -> Path:
    """Write `flow`'s draft from `source`'s approval `version`, else its newest.

    Each field of `schema` the approval holds is the approval's; every other is
    `flow`'s newest sheet's, as are the records the fields came through. No seeds
    are carried: the approval's are another flow's. A waiting draft equal to its
    sheet, rendering one drawn seed, holds no work, so it is replaced at its
    number; one with edited fields, or a count or seeds of its own, refuses.
    e.g. (run, conjure, summon, None, schema) -> conjure/review/001.draft.json
    """
    then = "then draft it again"
    if source == flow:
        raise Refusal(
            f"{run.id}: flow {flow} is drafted from its own approval; run "
            f"{_again(run, flow)} to copy it, or name another flow to draft from"
        )
    sheet_version = latest(run.directory(flow, SHEETS))
    if sheet_version is None:
        raise Refusal(
            f"{run.id}: flow {flow} has no sheet to draft {source}'s approval into; "
            f"run `{stage_command(run, 'assign', flow)}`, then Prepare, {then}"
        )
    held = approved_versions(run.directory(source, REVIEW))
    approval = held[-1] if version is None and held else version
    if approval is None or approval not in held:
        named = "an approval" if approval is None else artifact_name(approval, APPROVED)
        raise Refusal(
            f"{run.id}: flow {source} has no {named} to draft {flow} from; run "
            f"`{stage_command(run, 'approve', source)}` to approve its draft, {then}"
        )
    carried = _approval(run, source, approval, f"draft {flow} again")
    copied = sheet_of(run, flow, sheet_version)
    body = read(copied, SHEET_FILE)
    remedy = f"run `{stage_command(run, 'sheet', flow, options=NEW_VERSION)}`, {then}"
    require(copied, body, "vocabulary", dict, remedy)
    require(copied, body, "fields", dict, remedy)
    discarding = f"run `{stage_command(run, STAGE, flow, options=DISCARD)}`, {then}"
    waiting = current_draft(run.directory(flow, REVIEW))
    if waiting is not None and _edited(run, flow, waiting, discarding):
        raise Refusal(
            f"{run.id}: flow {flow} has {waiting.name} waiting with edits of its "
            "own, and a draft from another flow never replaces an edit; approve "
            f"it, or {discarding}"
        )
    merged = {**body["fields"], **carried["fields"]}
    fields = {name: list(merged[name]) for name in schema.names if name in merged}
    return _write_draft(
        run,
        flow,
        sheet_version,
        SHEETS,
        {**body, "fields": fields},
        sheet_version,
        version=None if waiting is None else int(waiting.name[:3]),
        drafted_from={"flow": source, "approval": approval},
    )


def _edited(run: Run, flow: str, draft: Path, remedy: str) -> bool:
    """Return whether `draft` holds work a replacement would lose.

    Its fields differ from the sheet it records, as approval says, or it renders
    anything but one drawn seed: a count or seeds set in Review, or the seed a
    revision lists. A draft taken from a sheet does neither.
    """
    body = read(draft, DRAFT_FILE, remedy=remedy)
    require(draft, body, "sheet", int, remedy)
    require(draft, body, "fields", dict, remedy)
    if renders_of(draft, body, remedy) != ONE_RENDER:
        return True
    return _differs(body["fields"], draft, sheet_of(run, flow, body["sheet"]), remedy)


# An image to revise: its run, its flow, its approval's number and its seed.
Revision = tuple[Run, str, int, int]


def refuse_revisions(selection: Sequence[tuple[Path, Revision]]) -> list[str | None]:
    """Return why each image of `selection` cannot be revised, None where it can.

    Checked whole before anything is written, so a selection is revised all or
    not at all; a flow takes one revision at a time, and its run is known by the
    identity of its directory, never by the text of its path.
    e.g. [(a.png, (run, f, 1, 7)), (b.png, (run, f, 2, 8))]
         -> [None, "<run>/f: is in this selection twice, …"]
    """
    seen: dict[tuple[int, int, str], int] = {}
    refused: list[str | None] = []
    for index, (image, (run, flow, version, seed)) in enumerate(selection):
        try:
            held = run.path.stat()
            first = seen.setdefault((held.st_dev, held.st_ino, flow), index)
            if first != index:
                raise Refusal(
                    f"{run.id}/{flow}: is in this selection twice, and a flow takes "
                    "one revision at a time; run "
                    f"`{_revise_command(selection[first][0])}` alone, "
                    "and revise this image once that draft is approved"
                )
            refuse_revision(run, flow, version, seed, f"run `{_revise_command(image)}`")
            refused.append(None)
        except Refusal as refusal:
            refused.append(str(refusal))
    return refused


def _revise_command(image: Path) -> str:
    """Return the command that revises `image`, as it is pasted.

    e.g. r/f/outputs/001/7.png -> "python -m isekai revise r/f/outputs/001/7.png"
    """
    return f"python -m isekai revise {shlex.quote(str(image))}"


def refuse_revision(
    run: Run, flow: str, version: int, seed: int, again: str = "revise the image again"
) -> ReviewApproved:
    """Return the approval `revise` copies for `seed`, refusing what it cannot write.

    A waiting draft is the operator's, so a revision never replaces it. The
    approval is read here, so a selection is checked whole before anything is
    written. `again` is what to do once the refusal's cause is fixed.
    """
    waiting = current_draft(run.directory(flow, REVIEW))
    if waiting is not None:
        raise Refusal(
            f"{run.id}: flow {flow} has {waiting.name} waiting, and a revision "
            "never replaces a draft; approve it, or run "
            f"`{stage_command(run, STAGE, flow, options=DISCARD)}`, then {again}"
        )
    copied = approval_of(run, flow, version)
    if not copied.exists():
        raise Refusal(
            f"{run.id}: flow {flow} has no {copied.name} to revise from; restore "
            f"{copied}, then {again}"
        )
    if not (group_of(run, flow, version) / f"{seed}{SIDECAR}").is_file():
        raise Refusal(
            f"{run.id}: flow {flow} rendered no seed {seed} under {copied.name}; "
            f"run `{stage_command(run, 'show')}` to list the seeds its renders "
            "wrote, and revise one of those"
        )
    return _approval(run, flow, version, again)


def discard(run: Run, flow: str) -> Path:
    """Delete `flow`'s highest draft while it is unapproved, and return its path.

    An approval is never discarded, so a highest number that is approved
    refuses; `cancel` takes back one nothing was made from.
    """
    directory = run.directory(flow, REVIEW)
    draft = current_draft(directory)
    if draft is not None:
        draft.unlink()
        return draft
    approved = approved_versions(directory)
    if approved:
        raise Refusal(
            f"{run.id}: flow {flow}'s highest number is "
            f"{artifact_name(approved[-1], APPROVED)}, and an approval is never "
            f"discarded; run {_again(run, flow)} to open a draft from it"
        )
    raise Refusal(
        f"{run.id}: flow {flow} has no draft to discard; run "
        f"`{stage_command(run, STAGE, flow)}` to take a copy"
    )


def cancellable(run: Run, flow: str) -> str | None:
    """Return why `flow`'s newest approval cannot be cancelled, or None if it can."""
    try:
        _cancelling(run, flow)
    except Refusal as refusal:
        return str(refusal)
    return None


def cancel(run: Run, flow: str) -> Path | None:
    """Cancel `flow`'s newest approval, and return what the flow is left on.

    An approval goes back to its draft, written before the approval is deleted,
    so a crash between leaves both, which reads as approved and is finished by
    cancelling again.
    A copy has no draft to go back to, so it is deleted, as `approve --from`
    copies the source's newest approval again, and the flow is left on the draft
    open above what lies beneath, else the approval beneath, else None.
    e.g. review/002.approved.json -> review/002.draft.json
    e.g. a copy, review/002.approved.json -> review/001.approved.json
    """
    version, body = _cancelling(run, flow)
    approval = approval_of(run, flow, version)
    directory = run.directory(flow, REVIEW)
    if body["producer"].get("copied_from") is not None:
        approval.unlink()
        return current_draft(directory) or latest_artifact(directory, APPROVED)
    path = directory / artifact_name(version, DRAFT)
    if not path.exists():
        producer = body["producer"]
        _write_draft(
            run,
            flow,
            producer["from"],
            producer["source"],
            body,
            body["sheet"],
            body.get("renders"),
            version,
            drafted_from(body),
        )
    approval.unlink()
    return path


def _cancelling(run: Run, flow: str) -> tuple[int, ReviewApproved]:
    """Return the newest approval of `flow` and its number, refusing its cancel.

    Refused while anything derives from it: a file numbered for it in the
    flow's prompts or outputs, or another flow's approval copied or drafted from
    it. That is checked before a waiting draft, so a draft is never named for
    discarding while the cancel would still be refused.
    """
    directory = run.directory(flow, REVIEW)
    approved = approved_versions(directory)
    if not approved:
        raise Refusal(
            f"{run.id}: flow {flow} has no approval to cancel; run "
            f"`{stage_command(run, 'approve', flow)}` to approve its draft"
        )
    version = approved[-1]
    name = artifact_name(version, APPROVED)
    again = f"`{stage_command(run, 'approve', flow, options=CANCEL)}`"
    body = _approval(run, flow, version, f"run {again}")
    copied = approval_of(run, flow, version)
    require(copied, body, "producer", dict, f"restore it in {copied}, then {again}")
    waiting = current_draft(directory)
    derived, copies = _derived(run, flow, version)
    if derived:
        group = group_of(run, flow, version)
        image = (
            min((path for path in group.iterdir() if is_seed(path.stem)), default=None)
            if group.is_dir()
            else None
        )
        if waiting is not None:
            way = (
                f"{waiting} is open above it; edit it, then run "
                f"`{stage_command(run, 'approve', flow)}` to approve the correction"
            )
        elif len(copies) == len(derived):
            first = ", then ".join(
                f"`{stage_command(run, 'approve', other, options=CANCEL)}`"
                for other in copies
            )
            way = f"run {first}, then {again}"
        elif image is not None:
            way = f"run `{_revise_command(image)}` to correct an image of it"
        else:
            way = f"run {_again(run, flow)} to correct it under the next number"
        raise Refusal(
            f"{run.id}: flow {flow}'s {name} cannot be cancelled, because "
            f"{', '.join(derived)} came from it; {way}"
        )
    if waiting is not None:
        raise Refusal(
            f"{run.id}: flow {flow} has {waiting.name} open above {name}, and a "
            "cancel never replaces a draft; run "
            f"`{stage_command(run, STAGE, flow, options=DISCARD)}`, then {again}"
        )
    return version, body


def _derived(run: Run, flow: str, version: int) -> tuple[list[str], list[str]]:
    """Return what derives from `flow`'s approval `version`, and what can go first.

    Each derived file is named by its path in the run; the flows are those whose
    copy of it, or approval drafted from it, is their newest approval and can be
    cancelled.

    e.g. (run, f, 2) -> (["f/prompts/002.json", "g/review/001.approved.json"], [])
    """
    prompts = run.directory(flow, PROMPTS)
    made = [
        prompts / artifact_name(version),
        *(attempt.path for attempt in attempts(prompts, version)),
        group_of(run, flow, version),
    ]
    found = [str(path.relative_to(run.path)) for path in made if path.exists()]
    copies: list[str] = []
    source = {"flow": flow, "approval": version}
    for other in run.flows:
        if other == flow:
            continue
        held_versions = approved_versions(run.directory(other, REVIEW))
        for held in held_versions:
            path = approval_of(run, other, held)
            copy = read(path, APPROVED_FILE, remedy=f"restore it in {path} by hand")
            producer = copy.get("producer")
            if isinstance(producer, dict) and source in (
                producer.get("copied_from"),
                producer.get("drafted_from"),
            ):
                found.append(f"{other}/{REVIEW}/{path.name}")
                if held == held_versions[-1] and cancellable(run, other) is None:
                    copies.append(other)
    return found, copies


def _approval(run: Run, flow: str, version: int, retry: str) -> ReviewApproved:
    """Read the approval numbered `version`, refusing one a draft cannot copy."""
    copied = approval_of(run, flow, version)
    # An approved artifact is never replaced, so only a hand repairs it.
    remedy = f"restore it in {copied}, then {retry}"
    carried = read(copied, APPROVED_FILE, remedy=remedy)
    require(
        copied,
        carried,
        "sheet",
        int,
        f"a draft copied from it cannot name its sheet; add the sheet version "
        f"it was approved from as `sheet` in {copied}, then {retry}",
    )
    require(copied, carried, "vocabulary", dict, remedy)
    require(copied, carried, "fields", dict, remedy)
    return carried


def _write_draft(
    run: Run,
    flow: str,
    came_from: int,
    source: str,
    carried: Sheet | ReviewApproved,
    sheet_version: int,
    renders: Renders | None = None,
    version: int | None = None,
    drafted_from: CopiedFrom | None = None,
) -> Path:
    """Write `flow`'s draft numbered `version`, else the next, and return its path."""
    review_directory = run.directory(flow, REVIEW)
    number = next_version(review_directory) if version is None else version
    path = review_directory / artifact_name(number, DRAFT)
    draft: ReviewDraft = {
        "schema": DRAFT_FILE.schema,
        "producer": {"implementation": STAGE, "from": came_from, "source": source},
        "flow": flow,
        "sheet": sheet_version,
        "vocabulary": carried["vocabulary"],
        "fields": carried["fields"],
    }
    # Carried where the source records them, so the approval can name the
    # schema and table its fields came through, and a correction keeps its count.
    if "schema_document" in carried:
        draft["schema_document"] = carried["schema_document"]
    if "field_map" in carried:
        draft["field_map"] = carried["field_map"]
    if renders is not None:
        draft["renders"] = renders
    if drafted_from is not None:
        draft["producer"]["drafted_from"] = drafted_from
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


def save_draft(
    run: Run,
    flow: str,
    fields: Mapping[str, Sequence[str]],
    renders: Renders | None = None,
) -> Path:
    """Replace the current draft's field values in place, and return its path.

    `renders`, when given, replaces the draft's count and seeds, refused as
    approval would refuse it.

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
            f"`{stage_command(run, STAGE, flow)}`, and an approved "
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
    if renders is not None:
        fix = "nothing was saved; send a count of at least one and its seeds"
        updated["renders"] = renders_of(path, {"renders": renders}, fix)
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
            f"`{stage_command(run, STAGE, flow)}` to take a copy, "
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
    renders = renders_of(
        draft,
        body,
        f"correct `renders` in {draft}, then run "
        f"`{stage_command(run, 'approve', flow)}` again",
    )
    sheet_version, producer = body["sheet"], body["producer"]
    origin = came_from(body)
    if origin is not None:
        _refuse_unchanged(run, flow, draft, origin, fields, renders)
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
    # Written only where the draft states it, so an older draft's approval is
    # byte for byte what it always was.
    if "renders" in body:
        approved_body["renders"] = renders

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
            f"sheet; run `{stage_command(run, STAGE, source)}`, edit the draft, "
            f"then `{stage_command(run, 'approve', source)}` first"
        )
    approval = versions_held[-1]
    directory = run.directory(flow, REVIEW)
    mine = latest_artifact(directory, APPROVED)
    if mine is not None:
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


def _refuse_unchanged(
    run: Run,
    flow: str,
    draft: Path,
    version: int,
    fields: Mapping[str, Sequence[str]],
    renders: Renders,
) -> None:
    """Refuse a draft that would render only images its approval already makes.

    That is a draft with its approval's fields whose every image is a listed
    seed its approval lists or rendered: rendering it pays for what exists. New
    seeds alone are a change, and a count above its seeds draws new ones.
    e.g. 002 from 001, fields equal, `{count 1, seeds [7]}`, 001 rendered 7 -> refused
    """
    origin = approval_of(run, flow, version)
    remedy = f"restore {origin}, then run `{stage_command(run, 'approve', flow)}` again"
    if not origin.exists():
        raise Refusal(
            f"{draft.name}: was copied from {origin}, which is not there, so "
            f"whether it changes anything cannot be computed; {remedy}"
        )
    body = read(origin, APPROVED_FILE, remedy=remedy)
    seeds = renders["seeds"]
    group = group_of(run, flow, version)
    made = set(renders_of(origin, body, remedy)["seeds"]) | {
        seed for seed in seeds if (group / f"{seed}{SIDECAR}").is_file()
    }
    held = body.get("fields")
    same = isinstance(held, Mapping) and same_fields(held, fields)
    if not same or renders["count"] > len(seeds) or not set(seeds) <= made:
        return
    raise Refusal(
        f"{draft.name}: has the fields of {origin.name} and only its seeds "
        f"{', '.join(map(str, seeds))}, so it would render the images of "
        f"{run.id}/{group.relative_to(run.path)}/ again; edit a field, the "
        f"count or the seeds in {draft}, then run "
        f"`{stage_command(run, 'approve', flow)}` again, or run "
        f"`{stage_command(run, STAGE, flow, options=DISCARD)}`"
    )


def _again(run: Run, flow: str) -> str:
    """Return the command that copies `flow`'s draft afresh under the next number."""
    return f"`{stage_command(run, STAGE, flow, options=NEW_VERSION)}`"


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
        f"run `{stage_command(run, 'sheet', flow, options=NEW_VERSION)}`, then "
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
    return not same_fields(body["fields"], fields)


def same_fields(
    one: Mapping[str, Sequence[str]], other: Mapping[str, Sequence[str]]
) -> bool:
    """Return whether two `fields` objects hold the same tags, field by field."""
    return {name: list(tags) for name, tags in one.items()} == {
        name: list(tags) for name, tags in other.items()
    }


def drafted_from(body: Mapping[str, object]) -> CopiedFrom | None:
    """Return the other flow's approval a draft was drafted from, or None.

    e.g. producer `{…, "drafted_from": {"flow": "f", "approval": 1}}` -> that
    """
    producer = body.get("producer")
    origin = producer.get("drafted_from") if isinstance(producer, Mapping) else None
    if not isinstance(origin, Mapping):
        return None
    flow, approval = origin.get("flow"), origin.get("approval")
    if not isinstance(flow, str) or not isinstance(approval, int):
        return None
    return {"flow": flow, "approval": approval}


def came_from(body: Mapping[str, object]) -> int | None:
    """Return the approval of its own flow a draft or approval was copied from.

    A copy of a sheet, or of another flow's approval, names none.
    e.g. producer `{"from": 1, "source": "review"}` -> 1
    """
    producer = body.get("producer")
    if not isinstance(producer, Mapping) or "copied_from" in producer:
        return None
    version = producer.get("from")
    if producer.get("source") != REVIEW or isinstance(version, bool):
        return None
    return version if isinstance(version, int) else None

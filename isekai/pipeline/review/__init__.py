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

from pathlib import Path
from typing import Literal, NamedTuple

from isekai.foundation.artifacts import ReviewApproved, require
from isekai.foundation.discard import _holds_render as _holds_render
from isekai.foundation.discard import withdraw as withdraw
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    DRAFT,
    PROMPTS,
    REVIEW,
    Run,
    approval_of,
    approved_versions,
    artifact_name,
    attempts,
    current_draft,
    group_of,
    latest_artifact,
    source_copy,
    stage_command,
    version_of,
    versions,
)
from isekai.pipeline.review.approval import approve as approve
from isekai.pipeline.review.budget import ENCODER_WINDOW as ENCODER_WINDOW
from isekai.pipeline.review.budget import TokenBudget as TokenBudget
from isekai.pipeline.review.budget import estimate_tokens as estimate_tokens
from isekai.pipeline.review.budget import token_budget as token_budget
from isekai.pipeline.review.drafts import Revision as Revision
from isekai.pipeline.review.drafts import draft_from as draft_from
from isekai.pipeline.review.drafts import drafting_approval as drafting_approval
from isekai.pipeline.review.drafts import drafting_sheet as drafting_sheet
from isekai.pipeline.review.drafts import refuse_drafts as refuse_drafts
from isekai.pipeline.review.drafts import refuse_revision as refuse_revision
from isekai.pipeline.review.drafts import review as review
from isekai.pipeline.review.drafts import revise as revise
from isekai.pipeline.review.drafts import waiting_edit as waiting_edit
from isekai.pipeline.review.records import (
    DISCARD,
    STAGE,
    _again,
    _approval,
    _draft_command,
    _first_image,
    _write_draft,
    draft_image,
    is_copy,
)
from isekai.pipeline.review.records import came_from as came_from
from isekai.pipeline.review.records import save_draft as save_draft

# The option that cancels a flow's newest approval.
CANCEL = ("--cancel",)


class Cancelled(NamedTuple):
    """What a cancel left a flow on, and whether it took an approval back."""

    left: Path | None
    changed: bool


# The three states stage ③ has, and the strings the review UI puts on the wire.
Status = Literal["draft", "approved", "re-opened"]


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
    from one local. A copy keeps its source's producer and says `copied`.

    Filenames only: no artifact is opened, and the common unapproved case
    costs a single listing.
    """
    approved = approved_versions(directory)
    if not approved:
        return "draft"
    later = [version for version in versions(directory) if version > approved[-1]]
    return "re-opened" if later else "approved"


def discard(run: Run, flow: str) -> Path:
    """Delete `flow`'s highest draft while it is unapproved, and return its path.

    The draft's source copy goes with it, and `sources/` when that empties it;
    the flow and its sheets stay. An approval is never discarded, so a highest
    number that is approved refuses; `cancel` takes back one nothing was made from.
    """
    directory = run.directory(flow, REVIEW)
    draft = current_draft(directory)
    if draft is not None:
        draft.unlink()
        copy = source_copy(run, flow, version_of(draft))
        if copy.is_file():
            copy.unlink()
            if not any(copy.parent.iterdir()):
                copy.parent.rmdir()
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


def cancel(run: Run, flow: str) -> Cancelled:
    """Cancel `flow`'s newest approval, and return what the flow is left on.

    An approval goes back to its draft, written before the approval is deleted,
    so a crash between leaves both, which reads as approved and is finished by
    cancelling again.
    A copy has no draft to go back to, so it is deleted, as `approve --from`
    copies the source's newest approval again, and the flow is left on the draft
    open above what lies beneath, else the approval beneath, else None.
    A flow at its draft, with no approval, is left unchanged on that draft.
    e.g. review/002.approved.json -> (review/002.draft.json, True)
    e.g. a copy, review/002.approved.json -> (review/001.approved.json, True)
    e.g. review/001.draft.json alone -> (review/001.draft.json, False)
    """
    directory = run.directory(flow, REVIEW)
    if (at := _at_draft(directory)) is not None:
        return Cancelled(at, changed=False)
    version, body = _cancelling(run, flow)
    approval = approval_of(run, flow, version)
    if is_copy(body["producer"]):
        approval.unlink()
        left = current_draft(directory) or latest_artifact(directory, APPROVED)
        return Cancelled(left, changed=True)
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
            renders=body.get("renders"),
            version=version,
            image=draft_image(body),
        )
    approval.unlink()
    return Cancelled(path, changed=True)


def _at_draft(directory: Path) -> Path | None:
    """Return the draft a flow holding no approval is at, or None."""
    return None if approved_versions(directory) else current_draft(directory)


def _cancelling(run: Run, flow: str) -> tuple[int, ReviewApproved]:
    """Return the newest approval of `flow` and its number, refusing its cancel.

    Refused while a file numbered for it in the flow's prompts or outputs
    derives from it; what another flow took from it never refuses it. That is
    checked before a waiting draft, so a draft is never named for discarding
    while the cancel would still be refused.
    """
    directory = run.directory(flow, REVIEW)
    if (at := _at_draft(directory)) is not None:
        raise Refusal(
            f"{run.id}: flow {flow} is at its draft {at.name}, with no approval"
        )
    approved = approved_versions(directory)
    if not approved:
        raise Refusal(
            f"{run.id}: flow {flow} has no draft and no approval to cancel; run "
            f"`{stage_command(run, STAGE, flow)}` to draft its sheet"
        )
    version = approved[-1]
    name = artifact_name(version, APPROVED)
    again = f"`{stage_command(run, 'approve', flow, options=CANCEL)}`"
    body = _approval(run, flow, version, f"run {again}")
    copied = approval_of(run, flow, version)
    require(copied, body, "producer", dict, f"restore it in {copied}, then {again}")
    waiting = current_draft(directory)
    derived = _derived(run, flow, version)
    if derived:
        image = _first_image(group_of(run, flow, version))
        if waiting is not None:
            way = (
                f"{waiting} is open above it; edit it, then run "
                f"`{stage_command(run, 'approve', flow)}` to approve the correction"
            )
        elif image is not None:
            way = f"run `{_draft_command(image, flow)}` to correct an image of it"
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


def _derived(run: Run, flow: str, version: int) -> list[str]:
    """Return the files of `flow`'s own that derive from its approval `version`.

    Each is named by its path in the run: the prompt, its failure records and
    the outputs group numbered for it. What another flow took from it holds its
    own copy, so it is not listed.

    e.g. (run, f, 2) -> ["f/prompts/002.json", "f/outputs/002"]
    """
    prompts = run.directory(flow, PROMPTS)
    made = [
        prompts / artifact_name(version),
        *(attempt.path for attempt in attempts(prompts, version)),
        group_of(run, flow, version),
    ]
    return [str(path.relative_to(run.path)) for path in made if path.exists()]

"""The discard and the cancel of stage (3).

Holds `discard`, `cancel` and what they share. It imports `records.py`, and
neither the front door nor another part.
"""

from pathlib import Path
from typing import NamedTuple

from isekai.foundation.artifacts import ReviewApproved, require
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
)
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

# The option that cancels a flow's newest approval.
CANCEL = ("--cancel",)


class Cancelled(NamedTuple):
    """What a cancel left a flow on, and whether it took an approval back."""

    left: Path | None
    changed: bool


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

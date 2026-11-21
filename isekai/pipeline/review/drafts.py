"""The drafts of stage (3), and what refuses them.

Holds `review`, `revise`, `draft_from` and the refusals they share. It imports
`records.py`, and neither the front door nor another part.
"""

import shlex
from collections.abc import Sequence
from pathlib import Path

from isekai.foundation.artifacts import (
    DRAFT_FILE,
    ONE_RENDER,
    SHEET_FILE,
    Renders,
    ReviewApproved,
    Sheet,
    read,
    renders_of,
    require,
)
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.flow import OUTPUT_SUFFIX, Schema
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    NEW_VERSION,
    REVIEW,
    SHEETS,
    RenderRef,
    Run,
    approval_of,
    approved_versions,
    artifact_name,
    command,
    current_draft,
    group_of,
    is_rendered,
    latest,
    next_version,
    render_image,
    sheet_of,
    source_copy,
    stage_command,
    version_of,
    versions,
)
from isekai.pipeline.review.records import (
    DISCARD,
    STAGE,
    _again,
    _approval,
    _differs,
    _draft_command,
    _first_image,
    _write_draft,
    copied_renders,
)


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
            renders=carried.get("renders"),
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
    composition. A waiting draft equal to its sheet is replaced at its number.
    Refused as `refuse_revision` refuses.
    e.g. (run, f, 1, 1840266731) -> review/003.draft.json, seeds [1840266731]
    """
    carried = refuse_revision(run, flow, version, seed)
    renders: Renders = {"count": 1, "seeds": [seed]}
    return _write_draft(
        run,
        flow,
        version,
        REVIEW,
        carried,
        carried["sheet"],
        renders=renders,
        version=_waiting_number(run, flow),
        image={"flow": flow, "version": version, "seed": seed},
    )


# How every refusal of a draft from another flow's approval ends.
_DRAFT_AGAIN = "then draft it again"


def draft_from(
    run: Run,
    flow: str,
    source: str,
    version: int | None,
    schema: Schema,
    seed: int | None = None,
) -> Path:
    """Write `flow`'s draft from `source`'s approval `version`, else its newest.

    Each field of `schema` the approval holds is the approval's; every other is
    `flow`'s newest sheet's, as are the records the fields came through. The
    draft names neither `source` nor its approval. `seed` names the image of that
    approval the draft is written from, copied to the draft's `source_copy` and
    listed as its one render, and refuses as `drafting_approval` refuses; with no
    `seed`, the renders are the approval's seeds, as `copied_renders` lists them.
    A waiting draft equal to its sheet, rendering one drawn seed, holds no work,
    so it is replaced at its number; one with edited fields, or a count or seeds
    of its own, refuses.
    e.g. (run, conjure, summon, None, schema) -> conjure/review/001.draft.json
    """
    approval = drafting_approval(run, flow, source, version, seed)
    sheet_version = latest(run.directory(flow, SHEETS))
    if sheet_version is None:
        raise Refusal(
            f"{run.id}: flow {flow} has no sheet to draft {source}'s approval into; "
            f"run `{stage_command(run, 'assign', flow)}`, then Prepare, {_DRAFT_AGAIN}"
        )
    carried = _approval(run, source, approval, f"draft {flow} again")
    body = drafting_sheet(run, flow, sheet_version)
    _refuse_edited(run, flow)
    merged = {**body["fields"], **carried["fields"]}
    fields = {name: list(merged[name]) for name in schema.names if name in merged}
    number = _waiting_number(run, flow) or next_version(run.directory(flow, REVIEW))
    if seed is not None:
        image = render_image(group_of(run, source, approval), seed, OUTPUT_SUFFIX)
        write_atomically(source_copy(run, flow, number), image.read_bytes())
    return _write_draft(
        run,
        flow,
        sheet_version,
        SHEETS,
        {**body, "fields": fields},
        sheet_version,
        renders=copied_renders(run, source, approval, carried)
        if seed is None
        else {"count": 1, "seeds": [seed]},
        version=number,
    )


def drafting_sheet(run: Run, flow: str, version: int) -> Sheet:
    """Read and check the target sheet a cross-flow draft copies, without writes."""
    copied = sheet_of(run, flow, version)
    body = read(copied, SHEET_FILE)
    resheet = stage_command(run, "sheet", flow, options=NEW_VERSION)
    remedy = f"run `{resheet}`, {_DRAFT_AGAIN}"
    require(copied, body, "vocabulary", dict, remedy)
    require(copied, body, "fields", dict, remedy)
    return body


def drafting_approval(
    run: Run, flow: str, source: str, version: int | None, seed: int | None = None
) -> int:
    """Return the approval of `source` that `draft_from` drafts `flow` from.

    `version`, else `source`'s newest. Refuses `flow` itself as the source, an
    approval `source` does not hold, one a draft cannot copy, and a `seed` it
    rendered no image for, so a caller that writes before drafting is refused
    before its first write.
    e.g. (run, conjure, summon, None) -> 2
    """
    if source == flow:
        raise Refusal(
            f"{run.id}: flow {flow} is drafted from its own approval; run "
            f"{_again(run, flow)} to copy it, or name another flow to draft from"
        )
    held = approved_versions(run.directory(source, REVIEW))
    approval = held[-1] if version is None and held else version
    if approval is None or approval not in held:
        named = "an approval" if approval is None else artifact_name(approval, APPROVED)
        raise Refusal(
            f"{run.id}: flow {source} has no {named} to draft {flow} from; "
            f"{_held_way(run, flow, source, held)}"
        )
    _approval(run, source, approval, f"draft {flow} again")
    group = group_of(run, source, approval)
    if seed is not None and not is_rendered(group, seed, OUTPUT_SUFFIX):
        raise Refusal(
            f"{run.id}: flow {source} rendered no seed {seed} under "
            f"{artifact_name(approval, APPROVED)}; run `{stage_command(run, 'show')}` "
            f"to list the seeds its renders wrote, and draft {flow} from one of those"
        )
    return approval


def _held_way(run: Run, flow: str, source: str, held: Sequence[int]) -> str:
    """Return the way to draft `flow` from an approval `source` holds.

    The draft of the first image of the newest approval that has one, else a
    render of `source`; with no approval held, its approval.
    """
    if not held:
        return (
            f"run `{stage_command(run, 'approve', source)}` to approve its draft, "
            f"{_DRAFT_AGAIN}"
        )
    names = ", ".join(artifact_name(version, APPROVED) for version in held)
    for version in reversed(held):
        if (image := _first_image(group_of(run, source, version))) is not None:
            return (
                f"{source} holds {names}; run `{_draft_command(image, flow)}` "
                "to draft it from an image of one"
            )
    rendering = command("render", shlex.quote(str(run.path.parent)), f"{source}=1")
    return f"{source} holds {names}; run `{rendering}` to render one, {_DRAFT_AGAIN}"


def waiting_edit(run: Run, flow: str) -> Path | None:
    """Return `flow`'s waiting draft when it holds work a new draft never replaces.

    That is edited fields, or a count or seeds of its own; else None.
    """
    waiting = current_draft(run.directory(flow, REVIEW))
    if waiting is None or not _edited(run, flow, waiting, _discarding(run, flow)):
        return None
    return waiting


def _refuse_edited(run: Run, flow: str, again: str = "draft it again") -> None:
    """Refuse `flow`'s waiting draft with edits of its own, naming its discard.

    `again` is what to do once it is discarded.
    """
    if (edited := waiting_edit(run, flow)) is not None:
        raise Refusal(
            f"{run.id}: flow {flow} has {edited.name} waiting with edits of its "
            "own, and a new draft never replaces an edit; approve it, or run "
            f"`{stage_command(run, STAGE, flow, options=DISCARD)}`, then {again}"
        )


def _waiting_number(run: Run, flow: str) -> int | None:
    """Return the number of `flow`'s waiting draft, which a new draft replaces.

    e.g. review/002.draft.json -> 2; no draft waiting -> None
    """
    waiting = current_draft(run.directory(flow, REVIEW))
    return None if waiting is None else version_of(waiting)


def _discarding(run: Run, flow: str) -> str:
    """Return the remedy that discards `flow`'s waiting draft before drafting again."""
    return f"run `{stage_command(run, STAGE, flow, options=DISCARD)}`, {_DRAFT_AGAIN}"


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
Revision = RenderRef


def refuse_drafts(
    target: str, selection: Sequence[tuple[Path, Revision]]
) -> list[str | None]:
    """Return why each image of `selection` cannot be drafted into `target`, else None.

    An image of `target` is checked as `refuse_revision` checks it, any other as
    `draft_from` refuses before it writes. Checked whole before anything is
    written, so a selection is drafted all or not at all; a flow takes one draft
    at a time, and its run is known by the identity of its directory, never by
    the text of its path.
    e.g. ("c", [(a.png, (run, s, 1, 7)), (b.png, (run, s, 2, 8))])
         -> [None, "<run>/c: is in this selection twice, …"]
    """
    seen: dict[tuple[int, int], int] = {}
    refused: list[str | None] = []
    for index, (image, (run, flow, version, seed)) in enumerate(selection):
        try:
            held = run.path.stat()
            first = seen.setdefault((held.st_dev, held.st_ino), index)
            if first != index:
                raise Refusal(
                    f"{run.id}/{target}: is in this selection twice, and a flow takes "
                    "one draft at a time; run "
                    f"`{_draft_command(selection[first][0], target)}` alone, "
                    "and draft this image once that draft is approved"
                )
            again = f"run `{_draft_command(image, target)}`"
            if flow == target:
                refuse_revision(run, flow, version, seed, again)
            else:
                drafting_approval(run, target, flow, version, seed)
                _refuse_edited(run, target, again)
            refused.append(None)
        except Refusal as refusal:
            refused.append(str(refusal))
    return refused


def refuse_revision(
    run: Run, flow: str, version: int, seed: int, again: str = "revise the image again"
) -> ReviewApproved:
    """Return the approval `revise` copies for `seed`, refusing what it cannot write.

    A waiting draft with edits of its own is the operator's, so a revision never
    replaces it. The approval is read here, so a selection is checked whole
    before anything is written. `again` is what to do once the refusal's cause
    is fixed.
    """
    _refuse_edited(run, flow, again)
    copied = approval_of(run, flow, version)
    if not copied.exists():
        raise Refusal(
            f"{run.id}: flow {flow} has no {copied.name} to revise from; restore "
            f"{copied}, then {again}"
        )
    if not is_rendered(group_of(run, flow, version), seed, OUTPUT_SUFFIX):
        raise Refusal(
            f"{run.id}: flow {flow} rendered no seed {seed} under {copied.name}; "
            f"run `{stage_command(run, 'show')}` to list the seeds its renders "
            "wrote, and revise one of those"
        )
    return _approval(run, flow, version, again)

"""Stage (3): the operator's correction, on a copy, approved by a rename.

**The machine's sheet is never edited, and that is a property of the layout
rather than a rule a tool is trusted to follow.** `sheets/<flow>/` is written
once by stage (2) and is read-only to everything else; `review/<flow>/` is the
only mutable directory in a run. The alternative -- both stages writing into one
directory, told apart by number -- makes "the machine's sheet is never edited" a
convention that an editor, a script or a careless command can break silently and
permanently (design.md D3).

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
from pathlib import Path

from isekai.flow import Schema
from isekai.refusal import Refusal
from isekai.run import (
    APPROVED,
    REVIEW,
    SHEETS,
    Run,
    approved_versions,
    artifact_name,
    envelope,
    latest,
    next_version,
    read_artifact,
    versions,
    write_json,
)
from isekai.sheet import validate
from isekai.vocabulary import Vocabulary

STAGE = "review"

DRAFT = "draft"

# SDXL's text encoders read 77 tokens at a time; past that the prompt is chunked
# and the chunks are averaged, which is not the same prompt. Sheets already run
# well past it and nothing said so, so every one was being silently averaged.
ENCODER_WINDOW = 77


def draft_versions(directory: Path) -> list[int]:
    """Return the versions in `directory` whose filenames say they are drafts."""
    if not directory.is_dir():
        return []
    approved = set(approved_versions(directory))
    return [version for version in versions(directory) if version not in approved]


def is_complete(directory: Path) -> bool:
    """Say whether this stage is finished, from filenames alone.

    A draft is not complete. That is the point of approval being its own act:
    downstream stages read this, and they must not proceed from something the
    operator is still in the middle of.
    """
    return bool(approved_versions(directory))


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
    sheets = run.directory(SHEETS, flow)
    review_directory = run.directory(REVIEW, flow)

    if versions(review_directory) and not new_version:
        return None

    source_sheet = latest(sheets)
    if source_sheet is None:
        raise Refusal(
            f"{run.id}: flow {flow} has no sheet to review; run "
            f"`python -m isekai sheet` for this photograph first"
        )

    approved = approved_versions(review_directory)
    if approved:
        origin = review_directory / artifact_name(approved[-1], APPROVED)
        came_from, source = approved[-1], REVIEW
    else:
        origin = sheets / artifact_name(source_sheet)
        came_from, source = source_sheet, SHEETS

    carried = read_artifact(origin)
    version = next_version(review_directory)
    path = review_directory / artifact_name(version, DRAFT)
    write_json(
        path,
        envelope(
            STAGE,
            {"implementation": STAGE, "from": came_from, "source": source},
            {
                "flow": flow,
                "sheet": int(carried.get("sheet", source_sheet)),
                "vocabulary": carried["vocabulary"],
                "fields": carried["fields"],
            },
        ),
    )
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


def approve(
    run: Run,
    flow: str,
    schema: Schema,
    vocabulary: Vocabulary,
) -> tuple[Path | None, list[str]]:
    """Validate `flow`'s highest draft and approve it, returning it and any warnings.

    Validation is the last place an invented tag can be caught: one that merely
    looks canonical passes every later check on its way into the prompt. The
    refusal says the tag is not in the vocabulary's *prediction set*, which is
    what is true -- that set is a subset of the wider tag corpus, so calling an
    absent tag unreal would overclaim.
    """
    directory = run.directory(REVIEW, flow)
    drafts = draft_versions(directory)
    if not drafts:
        if approved_versions(directory):
            # Already approved, and approving again would have nothing to act on.
            # A no-op rather than a refusal, because re-running every command is
            # the whole of resume and resume must not exit non-zero.
            return None, []
        raise Refusal(
            f"{run.id}: flow {flow} has no draft to approve; run "
            f"`python -m isekai review --flow {flow}` to take a copy, edit it, "
            "then approve it"
        )

    version = drafts[-1]
    draft = directory / artifact_name(version, DRAFT)
    body = read_artifact(draft)
    fields: dict[str, list[str]] = {
        name: list(tags) for name, tags in body["fields"].items()
    }
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

    sheet_version = int(body["sheet"])
    source = run.directory(SHEETS, flow) / artifact_name(sheet_version)
    approved_body = envelope(
        STAGE,
        {
            **body["producer"],
            "edited": _differs(fields, source),
            "approved_from": version,
        },
        {
            "flow": flow,
            "sheet": sheet_version,
            "vocabulary": body["vocabulary"],
            "fields": fields,
        },
    )

    path = directory / artifact_name(version, APPROVED)
    if path.exists():
        raise Refusal(
            f"{path.name} already exists in {REVIEW}/{flow}/ and an approved "
            f"artifact is never replaced; run `python -m isekai review --flow "
            f"{flow} --new-version` to correct it under the next number"
        )
    write_json(path, approved_body)
    draft.unlink()
    return path, warnings


def _differs(fields: Mapping[str, Sequence[str]], source: Path) -> bool:
    """Say whether `fields` differs from the sheet it was copied from.

    Computed rather than declared. Whether a sheet was actually corrected is the
    difference between the 0.568 route and the 0.917 one, and a flag the operator
    sets is an assumption wearing a fact's clothes.
    """
    if not source.exists():
        return False
    original = read_artifact(source)["fields"]
    return {name: list(tags) for name, tags in original.items()} != {
        name: list(tags) for name, tags in fields.items()
    }

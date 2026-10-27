"""Draft a flow from an image's approval, filling a flow with no sheet first.

The verb and the page run one sequence: sheet, draft. No stage may call
another, so the sequence is composed here, and each step stays its stage's.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

from isekai.foundation.flow import Flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import SHEETS, Run, latest
from isekai.pipeline.review import (
    Revision,
    draft_from,
    drafting_approval,
    drafting_sheet,
    refuse_drafts,
    revise,
)
from isekai.pipeline.sheet import prepare_sheet, sheet
from isekai.shared.field_map import FieldMap
from isekai.shared.vocabulary import Vocabulary


def draft_across(
    run: Run,
    target: Flow,
    source: str,
    version: int,
    vocabulary: Callable[[], Vocabulary],
    field_map: Callable[[], FieldMap],
    seed: int,
) -> Path:
    """Return `target`'s draft from `source`'s approval `version`.

    `seed` names the image of that approval the draft records.
    A target with no sheet has its sheet filled from `source`'s tag list first,
    and that write is what assigns it. The approval is checked whole, and the
    sheet stage checks the tag list before its write, so a refusal writes nothing.
    The vocabulary and the table are read only for that fill.
    """
    approval = drafting_approval(run, target.id, source, version, seed)
    if latest(run.directory(target.id, SHEETS)) is None:
        sheet(
            run,
            target.id,
            target.schema,
            vocabulary(),
            field_map(),
            tagged=target.tagger,
            flow_digest=target.digest,
            tags_from=source,
        )
    return draft_from(run, target.id, source, approval, target.schema, seed)


def draft_from_image(
    target: Flow,
    image: Revision,
    vocabulary: Callable[[], Vocabulary],
    field_map: Callable[[], FieldMap],
) -> Path:
    """Return `target`'s draft from the approval and seed of `image`.

    The image's own flow is a revision; any other is drafted across, as
    `draft_across` drafts it.
    e.g. (conjure, (run, summon, 1, 7)) -> conjure/review/001.draft.json
    """
    run, flow, version, seed = image
    if flow == target.id:
        return revise(run, flow, version, seed)
    return draft_across(run, target, flow, version, vocabulary, field_map, seed)


def refuse_image_drafts(
    target: Flow,
    selection: Sequence[tuple[Path, Revision]],
    vocabulary: Callable[[], Vocabulary],
    field_map: Callable[[], FieldMap],
) -> list[str | None]:
    """Check all source approvals and target sheet inputs before any batch write.

    Review owns the draft checks; sheet owns routing and validating a first
    sheet. Composition here checks both stages without one calling the other.
    """
    refused = refuse_drafts(target.id, selection)
    for index, (_, (run, source, _, _)) in enumerate(selection):
        if refused[index] is not None or source == target.id:
            continue
        try:
            version = latest(run.directory(target.id, SHEETS))
            if version is None:
                prepare_sheet(
                    run,
                    target.id,
                    target.schema,
                    vocabulary(),
                    field_map(),
                    tagged=target.tagger,
                    flow_digest=target.digest,
                    tags_from=source,
                )
            else:
                drafting_sheet(run, target.id, version)
        except Refusal as refusal:
            refused[index] = str(refusal)
    return refused

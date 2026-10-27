"""Draft a flow from another flow's approval, filling a flow with no sheet first.

The verb and the page run one sequence: sheet, draft. No stage may call
another, so the sequence is composed here, and each step stays its stage's.
"""

from collections.abc import Callable
from pathlib import Path

from isekai.foundation.flow import Flow
from isekai.foundation.run import SHEETS, Run, latest
from isekai.pipeline.review import draft_from, drafting_approval
from isekai.pipeline.sheet import sheet
from isekai.shared.field_map import FieldMap
from isekai.shared.vocabulary import Vocabulary


def draft_across(
    run: Run,
    target: Flow,
    source: str,
    version: int | None,
    vocabulary: Callable[[], Vocabulary],
    field_map: Callable[[], FieldMap],
    seed: int | None = None,
) -> Path:
    """Return `target`'s draft from `source`'s approval `version`, else its newest.

    `seed`, where given, names the image of that approval the draft records.
    A target with no sheet has its sheet filled from `source`'s tag list first,
    and that write is what assigns it. The approval is checked whole, and the
    sheet stage checks the tag list before its write, so a refusal writes nothing.
    The vocabulary and the table are read only for that fill.
    """
    approval = drafting_approval(run, target.id, source, version)
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

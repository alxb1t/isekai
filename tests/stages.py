"""The two stages that read a briefing, bound to the one tracked flow's copies.

A briefing is part of a flow now, so `caption` and `sheet` are handed the path
they read it from rather than defaulting to a file at the repository root. Almost
every test in the suite drives them over `summon-v1`; binding that argument once
here keeps it from being repeated at seventy call sites, and a test that means to
vary the briefing passes `briefing_path=` and overrides it.

Shared here rather than imported from one test module by another, which would
make that module undeletable -- the same rule `tests/images.py` is under.
"""

from collections.abc import Sequence
from pathlib import Path

from isekai.foundation.flow import Schema, load_flow
from isekai.foundation.run import Run
from isekai.pipeline import caption as caption_stage
from isekai.pipeline import sheet as sheet_stage
from isekai.shared.vocabulary import Vocabulary

FLOW = load_flow("summon-v1")
CAPTION_BRIEFING = FLOW.caption_briefing_path
SHEET_BRIEFING = FLOW.sheet_briefing_path


def caption(
    run: Run,
    reader: caption_stage.Reader,
    *,
    briefing_path: Path = CAPTION_BRIEFING,
    new_version: bool = False,
) -> Path | None:
    """Call the caption stage under `summon-v1`'s standing instructions."""
    return caption_stage.caption(
        run, reader, briefing_path=briefing_path, new_version=new_version
    )


def sheet(
    run: Run,
    sorter: sheet_stage.Sorter,
    schema: Schema,
    vocabulary: Vocabulary,
    flows: Sequence[str],
    *,
    briefing_path: Path = SHEET_BRIEFING,
    new_version: bool = False,
) -> list[Path]:
    """Call the sheet stage under `summon-v1`'s standing instructions."""
    return sheet_stage.sheet(
        run,
        sorter,
        schema,
        vocabulary,
        flows,
        briefing_path=briefing_path,
        new_version=new_version,
    )

"""The verbs' front door: what `cli.py` reads of the package.

Import from here. A module of the package imports its siblings by their own name,
never this file.
"""

from isekai.interface.verbs.common import (
    Reporter,
    Verb,
    once,
    require_tracked,
    run_for,
    run_or_photo,
    say,
)
from isekai.interface.verbs.drafts import DISCARD_ROW, DRAFT_ROW
from isekai.interface.verbs.edits import EDIT_ROW, INK_ROW
from isekai.interface.verbs.generate import GENERATE_ROW, generate_batch
from isekai.interface.verbs.library import COMPARE_ROW, IMPORT_ROW, UI_ROW
from isekai.interface.verbs.prepare import PREPARE_ROW, run_prepare
from isekai.interface.verbs.session import RENDER_ROW

__all__ = [
    "COMPARE_ROW",
    "DISCARD_ROW",
    "DRAFT_ROW",
    "EDIT_ROW",
    "GENERATE_ROW",
    "IMPORT_ROW",
    "INK_ROW",
    "PREPARE_ROW",
    "RENDER_ROW",
    "UI_ROW",
    "Reporter",
    "Verb",
    "generate_batch",
    "once",
    "require_tracked",
    "run_for",
    "run_or_photo",
    "run_prepare",
    "say",
]

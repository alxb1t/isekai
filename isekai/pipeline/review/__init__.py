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
from typing import Literal

from isekai.foundation.discard import _holds_render as _holds_render
from isekai.foundation.discard import withdraw as withdraw
from isekai.foundation.run import DRAFT as DRAFT
from isekai.foundation.run import approved_versions, versions
from isekai.foundation.run import current_draft as current_draft
from isekai.foundation.run import source_copy as source_copy
from isekai.pipeline.review.approval import approve as approve
from isekai.pipeline.review.budget import ENCODER_WINDOW as ENCODER_WINDOW
from isekai.pipeline.review.budget import TokenBudget as TokenBudget
from isekai.pipeline.review.budget import estimate_tokens as estimate_tokens
from isekai.pipeline.review.budget import token_budget as token_budget
from isekai.pipeline.review.cancelling import Cancelled as Cancelled
from isekai.pipeline.review.cancelling import cancel as cancel
from isekai.pipeline.review.cancelling import cancellable as cancellable
from isekai.pipeline.review.cancelling import discard as discard
from isekai.pipeline.review.drafts import Revision as Revision
from isekai.pipeline.review.drafts import draft_from as draft_from
from isekai.pipeline.review.drafts import drafting_approval as drafting_approval
from isekai.pipeline.review.drafts import drafting_sheet as drafting_sheet
from isekai.pipeline.review.drafts import refuse_drafts as refuse_drafts
from isekai.pipeline.review.drafts import refuse_revision as refuse_revision
from isekai.pipeline.review.drafts import review as review
from isekai.pipeline.review.drafts import revise as revise
from isekai.pipeline.review.drafts import waiting_edit as waiting_edit
from isekai.pipeline.review.records import came_from as came_from
from isekai.pipeline.review.records import draft_image as draft_image
from isekai.pipeline.review.records import save_draft as save_draft

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

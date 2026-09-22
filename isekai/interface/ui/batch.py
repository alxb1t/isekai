"""The inputs one invocation of the surface holds, and how they are established.

**No web framework is imported here, and that is the point.** Everything the
surface refuses, it refuses before a port is bound -- so the whole startup order
is exercised by the main suite, stdlib-only and offline, without the `ui` extra
being installed at all. `app.py` is the only module in this package that imports
FastAPI.

**The batch lives in memory and nothing writes it down.** Nothing on disk says
that ten photographs belong together: a run is one input and the layout has no
batch object, so recording one would add an artifact to a layout whose own rules
make a shape change a hand migration. A restart loses the rail and one retyped
command restores it; the sheets are independent of it and survive either way
(design.md D3).

**The approved count is read from the directory, never from memory**, so the
surface stays truthful when something is approved by the verb while it is
running. A directory cannot lie; a cached count can.

Stdlib only.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from isekai.foundation.flow import Flow, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    CAPTIONS,
    FRAME_NAME,
    REVIEW,
    TAGS,
    WD14,
    Run,
    across,
    latest_artifact,
)
from isekai.interface.wiring import Wiring
from isekai.pipeline.review import DRAFT, review
from isekai.shared.field_map import FieldMap
from isekai.shared.image import dimensions_or_refuse
from isekai.shared.vocabulary import Vocabulary


@dataclass(frozen=True)
class Input:
    """One photograph under review, with everything resolved at startup.

    The dimensions are read once, here, because `image_dimensions()` reports an
    unreadable header by calling `sys.exit()` -- a `BaseException` that inside a
    request handler would take the worker down rather than become a response.
    Since v0.22.1 `_prepare` turns that exit into a `Refusal` at startup, so an
    unreadable header costs its own photograph and not the batch.
    """

    run: Run
    width: int
    height: int

    @property
    def id(self) -> str:
        """Return the run identifier this input is addressed by."""
        return self.run.id


@dataclass(frozen=True)
class Batch:
    """One invocation's inputs, its single flow, and what the page reads.

    Exactly one flow, because the flow is what supplies the schema the sheet is
    filled against and the directory the draft is written into. A serving verb
    that took two would be serving two pages.
    """

    flow: Flow
    inputs: tuple[Input, ...]
    vocabulary: Vocabulary
    field_map: FieldMap
    bundle: Path

    def find(self, identifier: str) -> Input:
        """Return the input this identifier names, refusing one outside the batch."""
        for held in self.inputs:
            if held.id == identifier:
                return held
        raise Refusal(
            f"{identifier} is not one of the inputs this surface was started "
            f"for; it holds {', '.join(held.id for held in self.inputs)}"
        )

    def caption_path(self, held: Input) -> Path | None:
        """Return the highest caption for this input, or None if there is none."""
        return latest_artifact(held.run.directory(self.flow.id, CAPTIONS))

    def wd14_path(self, held: Input) -> Path | None:
        """Return the local tagger's scored list for this input, or None.

        **`None` is never a refusal here**, and neither is it for `tags_path`
        below. A run captioned before v0.20 has no such directory, a flow with no
        `hosted` block never produces the sibling, and a failed tagger leaves
        neither -- three legitimate absences, none of which may stop a review.
        The tag lists are an aid, and a surface that refused to open because a
        helper was missing would have confused an aid for an input
        (design.md D20).
        """
        return latest_artifact(held.run.directory(self.flow.id, WD14))

    def tags_path(self, held: Input) -> Path | None:
        """Return the hosted tagger's raw list for this input, or None."""
        return latest_artifact(held.run.directory(self.flow.id, TAGS))

    def draft_path(self, held: Input) -> Path | None:
        """Return the draft waiting for this input, or None once it is approved."""
        return latest_artifact(held.run.directory(self.flow.id, REVIEW), DRAFT)

    def approved_path(self, held: Input) -> Path | None:
        """Return this input's approved artifact, or None while it is still a draft."""
        return latest_artifact(held.run.directory(self.flow.id, REVIEW), APPROVED)

    @property
    def approved_count(self) -> int:
        """Return how many of the batch's inputs are approved, from disk."""
        return sum(1 for held in self.inputs if self.approved_path(held) is not None)


def establish(
    wired: Wiring,
    flow: str,
    identifiers: Sequence[str],
    *,
    bundle: Callable[[], Path],
) -> Batch:
    """Resolve everything the surface needs, refusing before any port is bound.

    The order is the refusal order: the flow, then every named input with a draft
    taken and its header read, then the vocabulary, then the table held against
    it, then the bundle. A refusal the
    operator cannot read is a refusal that did not happen, and the terminal is
    where they already are when they start this -- the browser has no designed
    home for one until a refusal surface exists (design.md D6).

    **Every input's failure is reported together.** Ten photographs with two
    missing sheets must name both and start nothing, rather than making the
    operator discover them one restart at a time.

    `review()` is called per input, which is what takes a draft where none exists
    and does nothing where one is already waiting or the flow is already approved.
    The surface never opens a draft itself.
    """
    loaded = load_flow(flow, wired.flows_dir)

    resolved: list[Input] = []
    refused = across(
        list(identifiers), lambda i: resolved.append(_prepare(i, wired, loaded.id))
    )
    if refused:
        raise Refusal("; ".join(refused))
    if not resolved:
        raise Refusal(
            "no inputs were named; give the run identifiers `python -m isekai "
            "show` prints, and the surface will open a draft for each"
        )

    vocabulary = wired.vocabulary()
    return Batch(
        loaded, tuple(resolved), vocabulary, wired.field_map(vocabulary), bundle()
    )


def _prepare(identifier: str, wired: Wiring, flow: str) -> Input:
    """Resolve one input: its run, its draft, and the size its photograph loads at."""
    directory = wired.runs_root / identifier
    if not (directory / FRAME_NAME).is_file():
        raise Refusal(
            f"{identifier} is not a run under {wired.runs_root.name}/; this "
            "surface reviews work that already exists, so give the identifiers "
            "`python -m isekai show` prints rather than a photograph"
        )
    run = Run(identifier, directory)
    review(run, flow)
    # Through the one wrap, in the module that owns the hazard: an unreadable
    # header is reported by `sys.exit`, a `BaseException` that `across` walks
    # straight past -- so unwrapped, one bad photograph killed the batch and
    # named nothing (v0.18 R7).
    width, height = dimensions_or_refuse(
        run.photo,
        "the surface reads the photograph's own header to size the page and "
        "there is nothing to fall back to -- re-export it as a JPEG or PNG and "
        "start the surface again",
    )
    return Input(run, width, height)

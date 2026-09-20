"""The two stages that read a briefing, bound to the one tracked flow's copies.

A briefing is part of a flow now, so `caption` and `sheet` are handed the path
they read it from rather than defaulting to a file at the repository root. Almost
every test in the suite drives them over `summon-v1`; binding that argument once
here keeps it from being repeated at seventy call sites, and a test that means to
vary the briefing passes `briefing_path=` and overrides it.

Shared here rather than imported from one test module by another, which would
make that module undeletable -- the same rule `tests/images.py` is under. That is
also why `FakeSession` and the three-row label index live here rather than in
`tests/test_wd14.py`: `tests/stages.py` is imported by the module that proves the
ordering *and* by the modules that compose a `Wiring`, and a double defined in
one test module and reached from three is the coupling this file exists to avoid.
"""

from dataclasses import dataclass
from pathlib import Path

from isekai.boundary.wd14 import Label, read_labels
from isekai.foundation.flow import Flow, Schema, load_flow
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
    flow: str = FLOW.id,
    briefing_path: Path = CAPTION_BRIEFING,
    new_version: bool = False,
) -> Path | None:
    """Call the caption stage under `summon-v1`'s standing instructions."""
    return caption_stage.caption(
        run, flow, reader, briefing_path=briefing_path, new_version=new_version
    )


def sheet(
    run: Run,
    sorter: sheet_stage.Sorter,
    schema: Schema,
    vocabulary: Vocabulary,
    *,
    flow: str = FLOW.id,
    briefing_path: Path = SHEET_BRIEFING,
    new_version: bool = False,
) -> Path | None:
    """Call the sheet stage under `summon-v1`'s standing instructions."""
    return sheet_stage.sheet(
        run,
        flow,
        sorter,
        schema,
        vocabulary,
        briefing_path=briefing_path,
        new_version=new_version,
    )


@dataclass(frozen=True)
class Always[T]:
    """A resolver that hands every flow the same double.

    `Wiring.reader` and `Wiring.sorter` are resolvers now, because the flow is
    what decides which implementation runs. A test that means to drive one double
    over any number of flows says so with this rather than by repeating a lambda,
    and `.double` is what keeps the counting assertions -- how many times was the
    reader actually reached -- reaching the object that did the counting.
    """

    double: T

    def __call__(self, flow: Flow) -> T:
        """Return the one double, whatever flow asked."""
        return self.double


# A three-row label index, in the shipped file's own column order and with one
# row of each category that matters: a rating meta-tag, a general tag and a
# character name. Small enough that "row 1" is a thing a human can check by eye,
# and **row 1 is `1girl`** -- which is the assertion the ordering contract rests
# on, so it lives here once rather than in each module that needs it.
INDEX = """tag_id,name,category,count
9999999,sensitive,9,3994361
1,1girl,0,6000000
2,hatsune_miku,4,300000
"""


class FakeSession:
    """A WD14 session that answers one fixed vector and counts how often it was asked.

    The double `tagging:seam:offline-double-satisfies-the-interface` names. It
    opens nothing, reads nothing and imports nothing -- which is only possible
    because the seam takes the photograph rather than a prepared array, so
    `numpy` and `Pillow` sit behind it with the graph (design.md D26).

    The counter is what makes the idempotence assertion provable: showing that a
    completed stage opens no session needs something that counts.
    """

    def __init__(self, vector: list[float]) -> None:
        """Answer `vector` to every call."""
        self.vector = vector
        self.calls = 0
        self.seen: list[Path] = []

    def run(self, photo: Path) -> list[float]:
        """Return the fixed vector, recording that it was asked and about what."""
        self.calls += 1
        self.seen.append(photo)
        return self.vector


def fake_wd14(
    vector: list[float] | None = None,
) -> Always[tuple[FakeSession, list[Label]]]:
    """Return a resolver handing every flow one fake session and one label index.

    `Always`'s reason, applied to the local tagger: a test driving one double over
    any number of flows should not repeat a lambda, and a wiring composed for a
    verb that never tags still has to say what it *would* have tagged with.
    """
    session = FakeSession([0.0, 0.9, 0.0] if vector is None else vector)
    return Always((session, read_labels(INDEX)))

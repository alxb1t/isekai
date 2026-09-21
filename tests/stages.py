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

from isekai.boundary.wd14 import LocalTagger, read_labels
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
    """A WD14 session that answers one fixed vector and records what it was asked.

    The double `tagging:seam:offline-double-satisfies-the-interface` names. It
    opens nothing, reads nothing and imports nothing -- which is only possible
    because the seam takes the photograph rather than a prepared array, so
    `numpy` and `Pillow` sit behind it with the graph (design.md D26).

    `seen` is what makes the idempotence assertion provable: showing that a
    completed stage opens no session needs something that counts. `calls` is
    derived from it rather than incremented beside it -- two counters in one
    method are two things that can disagree -- and `FakeTagger` keeps the same
    one list for the same reason.
    """

    def __init__(self, vector: list[float]) -> None:
        """Answer `vector` to every call."""
        self.vector = vector
        self.seen: list[Path] = []

    @property
    def calls(self) -> int:
        """Return how many times this session has been asked."""
        return len(self.seen)

    def run(self, photo: Path) -> list[float]:
        """Return the fixed vector, recording that it was asked and about what."""
        self.seen.append(photo)
        return self.vector


# The digests a fake tagger claims it was verified against. Not the real ones:
# an artifact written in a test must not be mistakable for one written against
# the provisioned bytes, and every assertion about a pin names this dict.
FAKE_PINS: dict[str, dict[str, str]] = {
    "wd14/selected_tags.csv": {"sha256": "c" * 64},
    "wd14/model.onnx": {"sha256": "m" * 64},
}


def fake_tagger(vector: list[float] | None = None) -> LocalTagger:
    """Return an opened local tagger that touches no file and no wheel."""
    return LocalTagger(
        session=FakeSession([0.0, 0.9, 0.0] if vector is None else vector),
        labels=tuple(read_labels(INDEX)),
        pins=FAKE_PINS,
    )


def fake_wd14(vector: list[float] | None = None) -> Always[LocalTagger]:
    """Return a resolver handing every flow one opened fake tagger.

    `Always`'s reason, applied to the local tagger: a test driving one double over
    any number of flows should not repeat a lambda, and a wiring composed for a
    verb that never tags still has to say what it *would* have tagged with.
    """
    return Always(fake_tagger(vector))

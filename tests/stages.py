"""The two stages that read a briefing, bound to the one tracked flow's copies.

A briefing is part of a flow now, so `caption` and `sheet` are handed the path
they read it from rather than defaulting to a file at the repository root. Almost
every test in the suite drives them over `summon-anime-wai`; binding it once
here keeps it from being repeated at seventy call sites, and a test that means to
vary the briefing passes `briefing_path=` and overrides it.

Shared here rather than imported from one test module by another, which would
make that module undeletable -- the same rule `tests/images.py` is under. That is
also why `FakeSession` and the three-row label index live here rather than in
`tests/test_wd14.py`: `tests/stages.py` is imported by the module that proves the
ordering *and* by the modules that compose a `Wiring`, and a double defined in
one test module and reached from three is the coupling this file exists to avoid.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from isekai.boundary.wd14 import LocalTagger, read_labels
from isekai.foundation.artifacts import (
    WD14_FILE,
    DanbooruTag,
    DigestRecord,
    Wd14,
    write,
)
from isekai.foundation.flow import Flow, Schema, load_flow
from isekai.foundation.run import (
    WD14,
    Run,
    artifact_name,
)
from isekai.pipeline import caption as caption_stage
from isekai.pipeline import sheet as sheet_stage
from isekai.shared.field_map import FieldMap, Group
from isekai.shared.vocabulary import Vocabulary

FLOW = load_flow("summon-anime-wai")
CAPTION_BRIEFING = FLOW.caption_briefing_path


def caption(
    run: Run,
    reader: caption_stage.Reader,
    *,
    flow: str = FLOW.id,
    briefing_path: Path = CAPTION_BRIEFING,
    new_version: bool = False,
) -> Path | None:
    """Call the caption stage under `summon-anime-wai`'s standing instructions."""
    return caption_stage.caption(
        run, flow, reader, briefing_path=briefing_path, new_version=new_version
    )


# The offline field map every test routes through. It covers all 21 criteria any
# tracked flow declares and places every tag in `conftest.CSV`, so a sheet filled
# here is a real routing decision rather than an empty dict -- and none of it
# touches the committed 2,768-entry table or the provisioned vocabulary.
FIELD_MAP = FieldMap(
    name="tests/stages.py",
    revision=1,
    digest="f" * 64,
    fields={
        "hair_colour": Group(primary=("brown hair",), also=()),
        "hair_silhouette": Group(
            primary=(
                "long hair",
                "short hair",
                "medium hair",
                "very long hair",
                "wavy hair",
                "hair",
            ),
            also=("brown hair",),
        ),
        "eye_colour": Group(primary=("blue eyes", "brown eyes"), also=()),
        "eyebrows": Group(primary=("thick eyebrows",), also=()),
        "skin_ancestry": Group(primary=("dark skin",), also=()),
        "background": Group(primary=("simple background",), also=()),
        "accessories": Group(primary=("glasses",), also=()),
        "expression": Group(primary=("smile",), also=()),
        "gaze": Group(primary=("looking at viewer",), also=()),
        "clothes": Group(primary=("shirt", "collared shirt", "jeans"), also=()),
        "count": Group(primary=(), also=()),
        "age_band": Group(primary=(), also=()),
        "marks": Group(primary=(), also=()),
        "pose": Group(primary=(), also=()),
        "framing": Group(primary=(), also=()),
        "body_shape": Group(primary=(), also=()),
        "bangs": Group(primary=(), also=()),
        "eyelashes": Group(primary=(), also=()),
        "nose": Group(primary=(), also=()),
        "lips": Group(primary=(), also=()),
        "facial_hair": Group(primary=(), also=()),
    },
    excluded=frozenset(),
)

# What `write_wd14` offers when a caller does not care which tags it routes, in
# WD14's own spelling. Three fields' worth, so a default sheet is neither empty
# nor uniform.
TAGS: tuple[DanbooruTag, ...] = tuple(
    DanbooruTag(tag) for tag in ("long_hair", "brown_hair", "smile", "shirt")
)


def write_wd14(
    run: Run,
    tags: Sequence[DanbooruTag] = TAGS,
    *,
    flow: str = FLOW.id,
    version: int = 1,
) -> Path:
    """Write the tag artifact the sheet stage reads, in `tag_wd14`'s own shape.

    One helper rather than a fixture per module: `sheet()` below calls it for any
    test that has not written one, which is why forty-six call sites that used to
    pass an offline sorter double lost it and gained nothing.
    """
    directory = run.directory(flow, WD14)
    path = directory / artifact_name(version)
    listed: Wd14 = {
        "schema": WD14_FILE.schema,
        "producer": {
            "implementation": "wd14",
            "models": ["wd14/model.onnx"],
            "pinned": True,
            "artifacts": dict(FAKE_PINS),
        },
        "tags": [
            {"tag": tag, "confidence": round(0.9 - index / 100, 4)}
            for index, tag in enumerate(tags)
        ],
    }
    write(path, WD14_FILE, listed)
    return path


def sheet(
    run: Run,
    schema: Schema,
    vocabulary: Vocabulary,
    *,
    flow: str = FLOW.id,
    field_map: FieldMap = FIELD_MAP,
    tags: Sequence[DanbooruTag] | None = TAGS,
    new_version: bool = False,
) -> Path | None:
    """Call the sheet stage under `summon-anime-wai`, writing the list it reads.

    **`tags` writes the artifact the stage refuses without**, so a test says what
    it wants routed on one line instead of composing a `wd14/` directory. Pass
    `tags=None` to leave the directory empty, which is how the refusal is driven.

    Written unconditionally rather than only when the directory is empty: a
    parameter whose effect depends on invisible prior state is one a second call
    on the same run would silently ignore, and two of the tests here do call
    twice. The write replaces version 1 in place, so a repeat is a no-op.
    """
    if tags is not None:
        write_wd14(run, tags, flow=flow)
    return sheet_stage.sheet(
        run, flow, schema, vocabulary, field_map, new_version=new_version
    )


@dataclass(frozen=True)
class Always[T]:
    """A resolver that hands every flow the same double.

    `Wiring.reader` is a resolver now, because the flow is what decides which
    implementation runs. A test that means to drive one double
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
FAKE_PINS: dict[str, DigestRecord] = {
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

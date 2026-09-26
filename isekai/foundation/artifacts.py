"""The run directory's contract: what every run file holds, and how it is read.

Each kind of file a run writes has its shape declared here once, as a
`TypedDict`, and its name and version in an `Artifact` descriptor. One `write`
and one `read` serve every kind, so a writer and its reader are checked against
the same declaration rather than each spelling the file by string key.

**A shape is a declaration for the type checker, not a check at run time.** A
`TypedDict` is a plain dict, so no byte a run writes depends on this module
beyond `write_json`'s one form. Why and how: `0028` design D1-D4.

Stdlib only, and on `python -m isekai`'s import graph.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, NewType, NotRequired, TypedDict, TypeVar

from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.refusal import Refusal

# A tag in Danbooru's spelling, `long_hair`, as WD14 emits it. The router
# accepts only this, so a space-spelled stand-in for WD14's output is a type
# error rather than a silent miss (`0028` design D6).
DanbooruTag = NewType("DanbooruTag", str)

T = TypeVar("T", bound=Mapping[str, object])


# --- the records a file carries -----------------------------------------------


class SchemaBlock(TypedDict):
    """The kind a file is, and the version of that kind's shape."""

    name: str
    version: int


class InstructionsRecord(TypedDict):
    """An instruction file a producer read: where it is, and its digest."""

    path: str
    sha256: str


class DigestRecord(TypedDict):
    """A digest with no path: a pinned file, or a text this build holds."""

    sha256: str


class VocabularyRecord(TypedDict):
    """Which vocabulary a sheet's tags were checked against."""

    name: str
    revision: str
    sha256: str


class FieldMapRecord(TypedDict):
    """Which table routed a sheet's tags into its fields."""

    name: str
    revision: int
    sha256: str


class PhotoRecord(TypedDict):
    """What the photograph's copy in a run is."""

    name: str
    sha256: str
    bytes: int
    media_type: str


class SchemaDocument(TypedDict):
    """Which flow schema a sheet was filled against."""

    name: str


class ScoredTag(TypedDict):
    """One tag WD14 emitted, and its confidence."""

    tag: DanbooruTag
    confidence: float


# --- the producers ------------------------------------------------------------


class CaptionProducer(TypedDict):
    """What read a photograph into prose, and the briefing it read."""

    implementation: str
    models: list[str]
    pinned: bool
    briefing: InstructionsRecord


class Wd14Producer(TypedDict):
    """The local tagger, and the digests its session was verified against."""

    implementation: str
    models: list[str]
    pinned: bool
    artifacts: dict[str, DigestRecord]


class TagsProducer(TypedDict):
    """The hosted tagger, and the digest of the prompt it was sent."""

    implementation: str
    models: list[str]
    pinned: bool
    prompt: DigestRecord


# The functional form below, because `from` is a Python keyword.
SheetProducer = TypedDict(
    "SheetProducer",
    {
        "implementation": str,
        "models": list[str],
        "pinned": bool,
        "artifacts": dict[str, DigestRecord],
        "from": int,
    },
)

ChainProducer = TypedDict(
    "ChainProducer",
    {"implementation": str, "from": int, "source": str},
)


class ApprovedProducer(ChainProducer):
    """The draft's producer, and what approving it recorded."""

    edited: bool
    approved_from: int


# --- the kinds ----------------------------------------------------------------


class Frame(TypedDict):
    """The run's frame: what the run is, written once when it is created."""

    schema: SchemaBlock
    id: str
    photo: PhotoRecord


class Failure(TypedDict):
    """What a failed attempt records beyond its number, attempt and kind."""

    stage: str
    seed: NotRequired[int]
    detail: str


class ErrorRecord(Failure):
    """One failed attempt, beside where its artifact would have gone."""

    schema: SchemaBlock
    version: int
    attempt: int
    kind: str


class Caption(TypedDict):
    """A photograph, read into prose."""

    schema: SchemaBlock
    producer: CaptionProducer
    prose: str


class Wd14(TypedDict):
    """The local tagger's list, in Danbooru's spelling."""

    schema: SchemaBlock
    producer: Wd14Producer
    tags: list[ScoredTag]


class Tags(TypedDict):
    """The hosted tagger's list, exactly as it came."""

    schema: SchemaBlock
    producer: TagsProducer
    tags: list[str]


# Today's shape. Runs written before v0.21 hold earlier sheet shapes under the
# same version; readers use only `vocabulary` and `fields`, which every one has.
class Sheet(TypedDict):
    """A tag list, routed into a flow's fields."""

    schema: SchemaBlock
    producer: SheetProducer
    schema_document: SchemaDocument
    vocabulary: VocabularyRecord
    field_map: FieldMapRecord
    fields: dict[str, list[str]]


class ReviewDraft(TypedDict):
    """The operator's editable copy of a sheet."""

    schema: SchemaBlock
    producer: ChainProducer
    flow: str
    sheet: int
    vocabulary: VocabularyRecord
    fields: dict[str, list[str]]


class ReviewApproved(TypedDict):
    """A draft the operator approved: what is rendered."""

    schema: SchemaBlock
    producer: ApprovedProducer
    flow: str
    sheet: int
    vocabulary: VocabularyRecord
    fields: dict[str, list[str]]


class Prompt(TypedDict):
    """The prompt assembled from an approved sheet."""

    schema: SchemaBlock
    producer: ChainProducer
    flow: str
    positive: str
    negative: str
    edited: bool


class Render(TypedDict):
    """The sidecar beside one rendered image."""

    schema: SchemaBlock
    producer: ChainProducer
    flow: str
    seed: int
    sheet_version: int
    graph_sha256: str
    flow_graph_sha256: str
    edited: bool


# --- the descriptors ----------------------------------------------------------


@dataclass(frozen=True)
class Artifact(Generic[T]):
    """One kind of run file: its name, and the version of its shape.

    e.g. `CAPTION_FILE.schema` -> `{"name": "caption", "version": 1}`
    """

    name: str
    version: int

    @property
    def schema(self) -> SchemaBlock:
        """Return the block a file of this kind opens with."""
        return {"name": self.name, "version": self.version}


RUN_FILE: Artifact[Frame] = Artifact("run", 1)
ERROR_FILE: Artifact[ErrorRecord] = Artifact("error", 1)
CAPTION_FILE: Artifact[Caption] = Artifact("caption", 1)
WD14_FILE: Artifact[Wd14] = Artifact("wd14", 1)
TAGS_FILE: Artifact[Tags] = Artifact("tags", 1)
SHEET_FILE: Artifact[Sheet] = Artifact("sheet", 1)
DRAFT_FILE: Artifact[ReviewDraft] = Artifact("review", 1)
# A draft and its approval are one kind at two stages, so they share a version.
APPROVED_FILE: Artifact[ReviewApproved] = Artifact("review", DRAFT_FILE.version)
PROMPT_FILE: Artifact[Prompt] = Artifact("prompt", 1)
RENDER_FILE: Artifact[Render] = Artifact("render", 1)


# --- reading and writing ------------------------------------------------------


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write `payload` as the one JSON form every artifact in a run is written in."""
    write_atomically(path, (json.dumps(payload, indent=2) + "\n").encode())


def write(path: Path, kind: Artifact[T], artifact: T) -> None:
    """Write one whole file of `kind`; the dict's key order is the file's.

    The caller annotates the dict with the kind's shape, `frame: Frame = {...}`.
    `ty` solves `T` from a bare literal as well as from `kind`, and then checks
    nothing; an annotated one is checked key by key.
    """
    write_json(path, artifact)


def read(path: Path, kind: Artifact[T]) -> T:
    """Parse a file of `kind`, refusing a version of its shape this build lacks.

    A best-effort parse of a format you do not know produces fields that look
    fine and mean nothing, so the declared version is checked before any other
    key is touched. The name is not checked.
    """
    parsed: Any = json.loads(path.read_text())
    declared = parsed.get("schema", {}).get("version")
    if declared != kind.version:
        raise Refusal(
            f"{path.name}: declares schema version {declared!r} and this build "
            f"reads version {kind.version}; upgrade isekai to a build that "
            f"declares version {declared!r}, or re-run the stage that wrote it "
            "to produce an artifact this build can read"
        )
    return parsed

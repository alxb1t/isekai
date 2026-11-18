"""Declare the JSON answers of the UI server, one `TypedDict` each.

`ANSWERS` keys each declaration as `tests/record/routes.json` keys its route,
`"<METHOD> <path template>"`. A test holds each against its recorded shape; no handler
reads a declaration. No web framework is imported, so the layer's entry point and its
tests read it whether or not a server is installed.
"""

from typing import Any, Literal, TypedDict

from isekai.pipeline.review import Status

COLLECTION = "/api/c/{collection}"
STAGED = "/api/staging/{staged}"
STAGED_FILE = "/api/staging/{staged}/files/{name}"
RENDER = "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}"
REVIEW = "/api/c/{collection}/review/{digest}/{flow}"
COMPARE = "/compare/{other_flow}/{other_version}/{other_seed}"


class FlowCount(TypedDict):
    """One flow's approved and rendered sources of a library row."""

    flow: str
    approved: int
    rendered: int
    of: int


class LibraryRow(TypedDict):
    """One folder of the library."""

    name: str
    collection: bool
    sources: int
    thumbs: list[str]
    flows: list[FlowCount]
    without_flow: int
    newest: float | None
    kind: str | None


class LibraryInfo(TypedDict):
    """The library's rows."""

    rows: list[LibraryRow]


class CellImage(TypedDict):
    """One render a hub cell shows."""

    version: int
    seed: str


class HubCell(TypedDict):
    """One source's cell in one flow's column."""

    stage: str | None
    renders: int
    refusal: str | None
    status: Status | None
    newest: CellImage | None
    short: int | None
    images: list[CellImage]


class HubSource(TypedDict):
    """One source of a collection and its cells by flow."""

    name: str
    digest: str | None
    width: int | None
    height: int | None
    cells: dict[str, HubCell]
    carries: list[str]


class HubInfo(TypedDict):
    """A collection's hub."""

    collection: str
    flows: list[str]
    sources: list[HubSource]


class Assigned(TypedDict):
    """The cells an assignment changed and the flows it refused."""

    cells: dict[str, HubCell]
    refused: dict[str, str]


class Opened(TypedDict):
    """A staging area just opened."""

    id: str


class Uploaded(TypedDict):
    """A file the staging area has accepted and not yet read."""

    upload: str
    file: str
    state: Literal["waiting"]


class Empty(TypedDict):
    """An answer with no key."""


class Committed(TypedDict):
    """What a staging area's commit wrote, skipped and left out."""

    collection: str
    written: list[str]
    skipped: list[str]
    left_out: list[str]


class TagMatch(TypedDict):
    """One vocabulary tag a query matched."""

    tag: str
    posts: int
    rare: bool


class TagMatches(TypedDict):
    """The tags a query matched and how many there are."""

    matches: list[TagMatch]
    total: int


class OfferedTag(TypedDict):
    """One tag offered for a field."""

    tag: str
    posts: int


class FieldCandidates(TypedDict):
    """The tags offered for each field."""

    fields: dict[str, list[OfferedTag]]


class Renders(TypedDict):
    """How many renders a source holds in a flow and their seeds."""

    count: int
    seeds: list[str]


class Bake(TypedDict):
    """One edit baked onto a render."""

    k: int
    placed_on: int | None
    baked_at: float | None
    edit: str | None
    state: Literal["baked", "queued", "damaged"]
    reason: str | None


class SourceImages(TypedDict):
    """The renders of one flow a render's source holds."""

    flow: str
    images: list[CellImage]


class RenderDetail(TypedDict):
    """One render, its sheet fields, its edits and its source's other renders."""

    flow: str
    version: int
    seed: str
    fields: dict[str, list[str]]
    approved_at: float | None
    came_from: int | None
    kind: Literal["revision", "re-roll"] | None
    count: int | None
    seeds: list[str]
    damaged: str | None
    bakes: list[Bake]
    compare: int | None
    targets: list[str]
    source: list[SourceImages]


class CompareSide(TypedDict):
    """One side of a comparison."""

    flow: str
    version: int
    approved_at: float | None
    renders: Renders
    tokens: int
    seed: str


class Comparison(TypedDict):
    """Two renders side by side, the left `None` when it is the photograph."""

    left: CompareSide | None
    right: CompareSide


class Deleted(TypedDict):
    """A render's withdrawal."""

    deleted: bool


class Budget(TypedDict):
    """The prompt's token budget for a draft."""

    total: int
    per_field: dict[str, int]
    overhead: int
    window: int


class ScoredTag(TypedDict):
    """One tag the tagger scored."""

    tag: str
    confidence: float


class Revision(TypedDict):
    """The version a draft revises."""

    version: int
    seed: str | None
    fields: dict[str, list[str]]


class Drafted(TypedDict):
    """The fields a draft was started from."""

    fields: dict[str, list[str]]
    version: int


class InputDetail(TypedDict):
    """One input of a flow as the review shows it."""

    id: str
    run: str
    flow: str
    schema: list[str]
    vocabulary: int
    width: int
    height: int
    caption: str | None
    caption_command: str | None
    wd14: list[ScoredTag] | None
    tags: list[OfferedTag] | None
    fields: dict[str, list[str]]
    renders: Renders
    revision: Revision | None
    drafted: Drafted | None
    readonly: bool
    draft: str | None
    approved: str | None
    saved: float | None
    approved_at: float | None
    cancel: str | None
    budget: Budget


class DraftSaved(TypedDict):
    """A draft just saved."""

    draft: str
    saved: float
    budget: Budget


class Approval(TypedDict):
    """What an approval wrote and the warnings it raised."""

    approved: str | None
    warnings: list[str]
    at: float | None


class Cancellation(TypedDict):
    """A render's cancellation."""

    back: str | None
    cancelled: bool


class Discarded(TypedDict):
    """The draft a discard removed."""

    discarded: str


class DraftedImage(TypedDict):
    """One image a draft was started for."""

    digest: str
    flow: str
    version: int
    seed: str
    draft: str | None
    waiting: str | None


class Drafts(TypedDict):
    """The images a draft was started for."""

    drafts: list[DraftedImage]


ANSWERS: dict[str, Any] = {
    "GET /api/library": LibraryInfo,
    f"GET {COLLECTION}/hub": HubInfo,
    f"POST {COLLECTION}/assign": Assigned,
    "POST /api/staging": Opened,
    f"PUT {STAGED_FILE}": Uploaded,
    f"DELETE {STAGED_FILE}": Empty,
    f"DELETE {STAGED}": Empty,
    f"POST {STAGED}/commit": Committed,
    "GET /api/tags": TagMatches,
    "GET /api/fields": FieldCandidates,
    f"GET {RENDER}": RenderDetail,
    f"GET {RENDER}{COMPARE}": Comparison,
    f"GET {RENDER}/compare/photo": Comparison,
    f"GET {RENDER}/edit/{{k}}": Bake,
    f"DELETE {RENDER}": Deleted,
    f"GET {REVIEW}": InputDetail,
    f"PUT {REVIEW}/draft": DraftSaved,
    f"POST {REVIEW}/approve": Approval,
    f"POST {REVIEW}/cancel": Cancellation,
    f"POST {REVIEW}/discard": Discarded,
    f"POST {COLLECTION}/draft": Drafts,
}

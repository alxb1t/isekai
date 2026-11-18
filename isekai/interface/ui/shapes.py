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
}

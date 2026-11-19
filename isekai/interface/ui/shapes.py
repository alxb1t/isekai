"""Declare the JSON answers of the UI server, one `TypedDict` each.

`ANSWERS` keys each declaration as `tests/record/routes.json` keys its route,
`"<METHOD> <path template>"`. A test holds each against its recorded shape; no handler
reads a declaration. `UNRECORDED` keys the answers the record lacks, each held by a case
that asks the server. `EVENTS` keys the stream's events by name, each held by a case
that reads what the server publishes. No web framework is imported, so the layer's
entry point and its tests read it whether or not a server is installed.
"""

from typing import Any, Literal, NotRequired, TypedDict

from isekai.foundation import artifacts
from isekai.interface.ui import jobs, library
from isekai.pipeline import importing, tattoos
from isekai.pipeline.review import Status
from isekai.shared import proposal

COLLECTION = "/api/c/{collection}"
TATTOO = "/api/tattoos/{name}"
STAGE1 = "/api/tattoos/{name}/stage1/{digest}"
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

    stage: library.Stage | None
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


class Tattoo(TypedDict):
    """One tattoo of the library."""

    name: str
    kind: tattoos.Kind
    size: list[int]
    kept: str
    outlined: bool
    downscaled_from: list[int] | None
    cut_from: str | None


class Outline(TypedDict):
    """A tattoo's outline and the depth it carries."""

    points: list[list[float]]
    closed: bool
    white: float
    neutral: bool
    depth: float


class OutlinedTattoo(Tattoo):
    """One tattoo with its outline."""

    outline: Outline


class TattooLimits(TypedDict):
    """The bounds the tattoo editor works within."""

    long_side: int
    outline_min: int
    outline_max: int
    floor_stage1: int
    floor_stage2: int
    floor_direct: int
    preview_floor: int
    preview_margin: int
    preview_wait_ms: int
    pair_radius: int
    region_min: int
    depth_min: float
    depth_max: float
    photo_depth: float
    image_depth: float


class Stage1(TypedDict):
    """A tattoo's first-stage pairs for one photograph."""

    pairs: list[list[list[float]]]
    not_on_photo: bool


class Tattoos(TypedDict):
    """The tattoos, their limits and their first-stage pairs."""

    tattoos: list[Tattoo]
    limits: TattooLimits
    stage1: dict[str, Stage1]


class BakeQueued(TypedDict):
    """The edit a bake was queued for."""

    edit: int


class Proposed(TypedDict):
    """The pairs a proposal found and the arm it chose."""

    arm: proposal.Side | None
    pairs: list[list[list[float]]]


class RenderOffer(TypedDict):
    """How many images and bakes a collection holds, and why Render is off."""

    disabled: str | None
    images: int
    others: int
    bakes: int
    other_bakes: int
    refused: str | None


class QuotedSource(TypedDict):
    """One source a quoted flow renders."""

    name: str
    digest: str
    run: str
    version: int | None
    images: int


class QuotedFlow(TypedDict):
    """One flow's images in a quoted collection and the sources they come from."""

    flow: str
    images: int
    sources: list[QuotedSource]


class QuotedBake(TypedDict):
    """One bake a quote holds, by its source, its approval, its seed and its number."""

    flow: str
    name: str
    digest: str
    run: str
    version: int
    seed: str
    k: int


class QuotedRow(TypedDict):
    """One collection's part of a quote."""

    collection: str
    images: int
    flows: list[QuotedFlow]
    bakes: list[QuotedBake]
    refused: str | None


class QuoteEstimate(TypedDict):
    """A quote's seconds, its session limit and the pod's boot and teardown."""

    seconds: float
    limit_s: int
    boot_s: float
    teardown_s: float


class QuotePrice(TypedDict):
    """A quote's price, about, at most, and with the window kept open."""

    about: float
    at_most: float
    keep_open: float


class Quote(TypedDict):
    """One render as the Render dialog quotes it."""

    collections: list[QuotedRow]
    estimate: QuoteEstimate
    price: QuotePrice
    ceiling_s: int
    disabled: str | None


class BillingVolume(TypedDict):
    """The models volume's state and when its window ends."""

    state: str
    ends: str | None


class Billing(TypedDict):
    """Whether a pod may still bill and the volume's window."""

    pod: bool
    volume: BillingVolume | None


class BillingChecked(TypedDict):
    """The billing state gpunit was asked for again."""

    billing: Billing


class JobStage(TypedDict):
    """One Prepare stage's cells done of the cells it was asked for."""

    stage: str
    done: int
    of: int


class JobProgress(TypedDict):
    """When a Prepare started and each stage's count."""

    started: str
    stages: list[JobStage]


class JobSession(TypedDict):
    """A render's session as the page draws it: its steps, its images, its limit."""

    id: str
    started: str
    limit: int
    of: int
    ended: str | None
    steps: dict[str, str]
    images: list[artifacts.SessionImage]


class Job(TypedDict):
    """One job of a slot; a render's `collections` and `session` a Prepare lacks."""

    kind: jobs.Kind
    collection: str
    state: jobs.State
    flow: str | None
    stage: str | None
    message: str | None
    progress: NotRequired[JobProgress]
    collections: NotRequired[list[str]]
    session: NotRequired[JobSession]


class JobStarted(TypedDict):
    """The job a Prepare, a render or a stop answers with."""

    job: Job


class ServedSession(TypedDict):
    """A render session's record, its outcome `None` when no process holds it."""

    schema: artifacts.SchemaBlock
    id: str
    started: str
    ended: str | None
    limit: int
    asked: dict[str, int]
    planned: NotRequired[list[artifacts.SessionPlan]]
    collections: NotRequired[list[str]]
    collection_order: NotRequired[list[str]]
    steps: dict[str, str]
    images: list[artifacts.SessionImage]
    outcome: str | None
    message: str | None


class RunningSession(artifacts.SessionRecord):
    """A running session's record and the collection that holds it."""

    collection: str


class RunningSessions(TypedDict):
    """The render sessions that are running, across collections."""

    sessions: list[RunningSession]


class RefusedImage(TypedDict):
    """One image a draft was asked for, and its own refusal."""

    digest: str
    flow: str
    version: int
    seed: str
    refusal: str | None


class Refused(TypedDict):
    """A refusal, as any route answers one."""

    refusal: str


class DraftRefused(Refused):
    """The draft's refusal, with each image's own."""

    images: list[RefusedImage]


class FileState(TypedDict):
    """One upload's state in an import, as the reader holds it."""

    file: str
    state: importing.Upload
    name: NotRequired[str]
    carries: NotRequired[list[str]]
    copy_of: NotRequired[str | None]
    refusal: NotRequired[str]


class FileEvent(FileState):
    """A file's new state, with the import and the upload it belongs to."""

    staging: str
    upload: str


class Snapshot(TypedDict):
    """The whole truth the stream opens with."""

    jobs: dict[jobs.Kind, Job | None]
    billing: Billing
    hub: NotRequired[HubInfo]
    files: NotRequired[dict[str, FileState]]


class CellEvent(TypedDict):
    """One hub cell after a stage reported progress on it."""

    collection: str
    source: str
    flow: str
    stage: str | None
    state: str | None
    message: str | None
    cell: HubCell


ANSWERS: dict[str, Any] = {
    "GET /api/library": LibraryInfo,
    "GET /api/{rest:path}": Refused,
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
    "GET /api/tattoos": Tattoos,
    f"GET {TATTOO}": OutlinedTattoo,
    f"DELETE {TATTOO}": Empty,
    "POST /api/tattoos": Tattoo,
    f"POST {COLLECTION}/tattoos": Tattoo,
    f"PUT {TATTOO}/outline": Outline,
    f"GET {STAGE1}": Stage1,
    f"PUT {STAGE1}": Stage1,
    f"POST {COLLECTION}/tattoos/{{name}}/bake": BakeQueued,
    f"GET {COLLECTION}/render": RenderOffer,
    "POST /api/render/quote": Quote,
    "POST /api/billing/check": BillingChecked,
}

UNRECORDED: dict[str, Any] = {
    f"POST {COLLECTION}/place/propose": Proposed,
    f"POST {COLLECTION}/prepare": JobStarted,
    "POST /api/jobs/{kind}/stop": JobStarted,
    "POST /api/render": JobStarted,
    "GET /api/sessions/running": RunningSessions,
    f"GET {COLLECTION}/sessions/{{name}}": ServedSession,
}

EVENTS: dict[str, Any] = {
    "snapshot": Snapshot,
    "job": Job,
    "billing": Billing,
    "cell": CellEvent,
    "file": FileEvent,
}

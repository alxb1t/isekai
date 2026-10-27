"""The HTTP surface, and the only module in this package that imports a web framework.

Kept to one file deliberately. `library.py` reads the library and every stage and
imports no web framework, so that reading is exercised by the main suite whether
or not a server is installed; only what genuinely needs one lives here, and
`tests/test_ui_api.py` opens with an `importorskip` for it.

**What this module owns, and what it does not.** It owns HTTP routing and status
codes, the join of caption, sheet, draft, approved and budget into one payload,
serving photograph bytes and the built bundle, the `rare` threshold -- which
exists nowhere else in this repository -- and turning a `Refusal` into a
response. The pipeline owns what a valid sheet is, each run file's shape and its
filename, when approval is legal, and what a token costs.

**A run directory is written only through the functions that own it**: stage
③'s `review()` when a sheet is opened, `save_draft()` on autosave,
`approve()` on the button, `cancel()`, `revise()`, `draft_from()` and
`discard()` on theirs, the run's own `open_run()` and `assign()` on a tick,
and stage ②'s `sheet()` when a draft from another flow fills a target with
no sheet -- run in this process by `interface/drafting.py`'s `draft_across`,
the sequence `draft --flow` runs too (D4).
Nothing here builds an artifact body or an artifact filename, and
`tests/test_ui.py`'s grep is what keeps it so.

**uvicorn is imported here too, and not in `__init__.py`.** `serve()` there
calls this module's `run()` instead, so the server is reached from this one file
and `python -m isekai`'s import graph never reaches it at all.

**Every path inside a collection names the collection, and a run by its digest** (D3):

```
GET  /api/library
GET  /api/c/{collection}/hub   ·   POST …/assign        {sources, flow, remove}
POST /api/c/{collection}/prepare   ·   POST /api/jobs/{prepare,render}/stop
GET  /api/c/{collection}/render  ·  POST …/render{/quote,}  {keep_open, limit_s, images}
GET  /api/sessions/running   ·   GET /api/c/{collection}/sessions/{id}
POST /api/billing/check
POST /api/staging   ·   PUT …/{id}/files/{name}, and GET its /thumb
DELETE /api/staging/{id}   ·   POST …/{id}/commit   {collection, as_is, add}
GET  /events[?collection=&staging=], either or both    Server-Sent Events
GET  /api/c/{collection}/review/{digest}/{flow}         and /photo
PUT  /api/c/{collection}/review/{digest}/{flow}/draft
POST /api/c/{collection}/review/{digest}/{flow}/approve   ·   POST …/cancel
POST /api/c/{collection}/review/{digest}/{flow}/discard
POST /api/c/{collection}/draft         {flow, images: [{digest, flow, version, seed}]}
GET  /api/c/{collection}/renders   ·   GET …/renders/{digest}/{flow}/{version}/{seed}
     and its /image, /thumb, /compare/photo and /compare/{flow}/{version}/{seed}
GET  /api/c/{collection}/sources/{name}   and its /thumb
GET  /api/tags   ·   GET /api/fields?flow=
GET  anything else                                 the bundle's index.html
```
"""

import asyncio
import re
import threading
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path
from types import FrameType
from typing import Any, TypeGuard

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from isekai.boundary.gpu import keyed
from isekai.foundation.artifacts import (
    APPROVED_FILE,
    CAPTION_FILE,
    DRAFT_FILE,
    ONE_RENDER,
    SHEET_FILE,
    TAGS_FILE,
    WD14_FILE,
    Renders,
    ReviewApproved,
    read,
    renders_of,
    require,
)
from isekai.foundation.flow import Flow, load_flow, tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    CAPTIONS,
    NEW_VERSION,
    REVIEW,
    SHEETS,
    SIGNATURE_BYTES,
    TAGS,
    WD14,
    Run,
    approval_of,
    approved_versions,
    assign,
    find_run,
    is_seed,
    is_version,
    latest_artifact,
    media_type,
    open_run,
    sheet_of,
    stage_command,
)
from isekai.interface import render
from isekai.interface.drafting import draft_from_image, refuse_image_drafts
from isekai.interface.ui import events, library
from isekai.interface.ui.billing import Billing
from isekai.interface.ui.jobs import KINDS, Jobs, plan
from isekai.interface.wiring import Wiring
from isekai.pipeline import importing
from isekai.pipeline.generate import image_of
from isekai.pipeline.review import (
    ENCODER_WINDOW,
    Revision,
    TokenBudget,
    approve,
    came_from,
    cancel,
    cancellable,
    current_draft,
    discard,
    draft_image,
    drafted_from,
    review,
    save_draft,
    token_budget,
    waiting_edit,
)
from isekai.pipeline.review import state as review_state
from isekai.pipeline.sheet import tagged_from
from isekai.shared.field_map import FieldMap
from isekai.shared.image import dimensions_or_refuse
from isekai.shared.vocabulary import Vocabulary

# The dropdown's `· rare` marker. This number exists nowhere else in the
# repository: the vocabulary ranks by post count and never calls anything rare,
# so the threshold is the surface's own judgement about what an operator should
# hesitate over, and it is stated here rather than duplicated in TypeScript.
RARE_BELOW = 2000

# Held across a draft update's precondition and its write, so two updates that
# state one precondition cannot both pass it; and across an approval, so no
# update writes after it.
_DRAFT_UPDATE = threading.Lock()

# Enough rows to choose from without the dropdown becoming a list to read. The
# footer states the true match count, so narrowing the fragment stays the way to
# see fewer rather than scrolling.
DEFAULT_LIMIT = 10

# A `Refusal` is the pipeline declining a well-formed request because of what is
# on disk -- an approved input, a changed field set, a tag outside the vocabulary
# -- which is a conflict with state rather than a malformed request. One code for
# all of them, because the page shows the string verbatim and never branches on
# the number.
REFUSED = 409

# A request that did not come from this machine's own browser, addressed to this
# server's own address. Not a `Refusal`: nothing about the run directory is in
# conflict, the request is simply not one this surface answers, so it carries no
# string for the page and never reaches a handler.
FORBIDDEN = 403

# Where gpunit's status answers are appended, in the library: a dot-file is listed
# as no collection.
GPUNIT_LOG = ".gpunit.log"

# The names a loopback listener answers to. `Host: evil.example` resolving to
# 127.0.0.1 is the whole of the DNS-rebinding attack against an unauthenticated
# local API, and it is defeated by comparing the name rather than the socket.
# These four are the only names an attacker cannot make point anywhere: they are
# reserved, so allowing the alias the operator actually types costs nothing.
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})

# The `Sec-Fetch-Site` values a request without `Origin` is answered under: this
# page's own, a typed address or bookmark, and none at all from a non-browser.
SAME_SITE = frozenset({"same-origin", "none", None})


def authorities(host: str, port: int) -> frozenset[str]:
    """Return every `Host` value this server, bound to `host:port`, answers to.

    One function rather than two comparisons, because `Origin` is checked
    against exactly the same set with a scheme in front of it -- and a header
    pair that is allowed to disagree about what the server's address is has no
    security value at all.
    """
    names = LOOPBACK if host in LOOPBACK else frozenset({host})
    return frozenset(f"{name}:{port}" for name in names)


@dataclass(frozen=True)
class Held:
    """One run in one flow, as a review URL names it."""

    run: Run
    flow: Flow

    def directory(self, stage: str) -> Path:
        """Return one of this flow's stage directories inside the run."""
        return self.run.directory(self.flow.id, stage)

    def draft(self) -> Path | None:
        """Return the current draft, or None; `current_draft` decides."""
        return current_draft(self.directory(REVIEW))

    def approved(self) -> Path | None:
        """Return the approved artifact, or None while it is still a draft."""
        return latest_artifact(self.directory(REVIEW), APPROVED)


def create_app(
    root: Path,
    wired: Wiring,
    *,
    flows: Sequence[str],
    bundle: Path,
    wire: Callable[[Path], Wiring],
    host: str,
    port: int,
) -> FastAPI:
    """Return the app's application, serving every collection of the library at `root`.

    `wire` builds one collection's wiring from its runs root, and is called on every
    request inside a collection, so the run-root guard holds for each (D19). `wired`
    supplies what every collection shares: the flows, the vocabulary and the table.
    `flows` are the hub's columns, the flows the surface offers.
    `host` and `port` are the address every request is checked against.
    """
    broadcast = events.Broadcast()
    jobs = Jobs(
        broadcast,
        wired.probe,
        volume=wired.volume,
        raise_volume=lambda: billing.raise_volume(),
        err=wired.err,
    )
    billing = Billing(
        wired.volume, root / GPUNIT_LOG, broadcast, lambda: jobs.running("render")
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Interrupt a running job and end every stream when the server stops."""
        yield
        billing.close()
        jobs.shutdown()
        imports.close()
        broadcast.close()

    app = FastAPI(title="isekai", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.state.broadcast = broadcast
    app.state.billing = billing
    limit = importing.upload_limit()
    allowed = authorities(host, port)
    origins = frozenset(f"http://{one}" for one in allowed)
    shared = _Shared(wired)
    imports = importing.Imports(
        root,
        limit,
        lambda staged, state: broadcast.publish("file", {"staging": staged, **state}),
    )

    @app.middleware("http")
    async def _addressed_here(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Answer only a request addressed to this server, from this server's page.

        **A middleware rather than a dependency**, so it guards every route and
        the bundle alike, and a route added later cannot forget it.

        This API is unauthenticated by design, so the browser's own origin rules
        are the whole of its protection. `Host` defeats DNS rebinding, where a
        page on an attacker's domain resolves that domain to 127.0.0.1 and talks
        to this port with the browser's full cooperation. `Origin`, when the
        browser sends one, defeats the cross-site write. Without `Origin`,
        `Sec-Fetch-Site` decides: an image tag on another site sends no `Origin`
        and is still marked `cross-site` (D24). A client that is not a browser
        sends neither.
        """
        if request.headers.get("Host", "") not in allowed:
            return JSONResponse({"refusal": "not addressed here"}, FORBIDDEN)
        origin = request.headers.get("Origin")
        site = request.headers.get("Sec-Fetch-Site")
        if origin is not None and origin not in origins:
            return JSONResponse({"refusal": "not from this page"}, FORBIDDEN)
        if origin is None and site not in SAME_SITE:
            return JSONResponse({"refusal": "not from this page"}, FORBIDDEN)
        return await call_next(request)

    @app.exception_handler(Refusal)
    async def _refused(request: Request, refusal: Exception) -> JSONResponse:
        """Turn a `Refusal` into a response carrying its string, verbatim."""
        return JSONResponse({"refusal": str(refusal)}, status_code=REFUSED)

    def folder(collection: str) -> Path:
        """Return a collection's folder, its runs root passed through the guard."""
        found = library.collection(root, collection)
        wire(found / library.RUNS)
        return found

    def held(collection: str, digest: str, flow: str) -> Held:
        """Return the run and flow a review URL names, refusing either unknown."""
        found = folder(collection)
        return Held(library.run_named(found, digest), _flow(wired, flow))

    @app.get("/api/library")
    def read_library() -> dict[str, Any]:
        """List the library's folders, collections by their newest file first."""
        rows = library.rows(root, flows, wired.flows_dir)
        return {"rows": [asdict(row) for row in rows]}

    @app.get("/api/c/{collection}/hub")
    def read_hub(collection: str) -> dict[str, Any]:
        """Return a collection's grid: its sources by offered flow, each cell's stage.

        Read from the run directories on every request, so it follows a verb run
        in the terminal while the page is open.
        """
        return _hub(library.hub(folder(collection), flows, wired.flows_dir))

    @app.post("/api/c/{collection}/assign")
    def post_assign(collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Tick a flow for sources, or untick it, through the run's own `assign`.

        Each source is answered on its own: one refused untick leaves the others
        done, and its refusal comes back beside their cells.
        """
        found = folder(collection)
        flow = str(payload.get("flow"))
        if flow not in flows:
            raise Refusal(
                f"{flow!r}: not a flow this surface offers; the flows it offers "
                f"are {', '.join(flows)} -- reload the hub"
            )
        names = payload.get("sources")
        if not _strings(names):
            raise Refusal("the request's `sources` is not a list of source names")
        remove = payload.get("remove") is True
        loaded = offered(flow)
        runs = found / library.RUNS
        named = library.source_files(found)
        cells: dict[str, Any] = {}
        refused: dict[str, str] = {}
        for name in names:
            try:
                source = named(name)
                run = find_run(source, runs) if remove else open_run(source, runs)
                if run is not None:
                    assign(run, flow, remove=remove)
                cell = library.stage(run, loaded) if run else library.Cell(None)
                cells[name] = _cell_out(cell)
            except Refusal as one:
                refused[name] = str(one)
        return {"cells": cells, "refused": refused}

    @app.post("/api/staging")
    def post_staging() -> dict[str, Any]:
        """Open an import: a staging folder under the library's `.staging/`."""
        return {"id": imports.open()}

    @app.put("/api/staging/{staged}/files/{name}", status_code=202)
    async def put_file(staged: str, name: str, request: Request) -> dict[str, Any]:
        """Hold an upload for its import's reader; answer its id and `waiting`.

        The body is the file. One past the limit is refused by its declared
        length before its body is read. Its reading is reported on the stream,
        under its upload id.
        """
        held = imports.reader(staged)
        declared = request.headers.get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > limit:
            raise importing.past_limit(name, int(declared), limit)
        body = await request.body()
        return await run_in_threadpool(held.put, name, body)

    @app.get("/api/staging/{staged}/files/{name}/thumb")
    def read_staged_thumb(staged: str, name: str) -> Response:
        """Serve a staged file's preview, made now and kept nowhere."""
        return Response(
            importing.preview(imports.folder(staged), name),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-store"},
        )

    @app.delete("/api/staging/{staged}")
    def delete_staging(staged: str) -> dict[str, Any]:
        """Cancel an import: its staging folder is deleted, the library unchanged."""
        imports.cancel(staged)
        return {}

    @app.post("/api/staging/{staged}/commit")
    def post_commit(staged: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Commit an import into a new collection, or with `add` into an open one."""
        as_is = payload.get("as_is", [])
        if not _strings(as_is):
            raise Refusal("the request's `as_is` is not a list of file names")
        done = imports.commit(
            staged,
            str(payload.get("collection", "")),
            as_is,
            add=payload.get("add") is True,
        )
        return {
            "collection": done.collection.name,
            "written": list(done.written),
            "skipped": list(done.skipped),
            "left_out": list(done.left_out),
        }

    @app.post("/api/c/{collection}/prepare")
    def post_prepare(collection: str) -> dict[str, Any]:
        """Start Prepare over every assigned cell with no sheet, as one job.

        The local model server is asked first, so a job that could not run
        starts nothing.
        """
        found = folder(collection)
        grid = library.hub(found, flows, wired.flows_dir)
        loaded = {flow: load_flow(flow, wired.flows_dir) for flow in flows}
        steps = plan(
            library.unprepared(grid), {flow: one.tagger for flow, one in loaded.items()}
        )
        cell = cell_event(found, grid, loaded)
        return {"job": jobs.prepare(collection, found, steps, cell)}

    @app.post("/api/jobs/{kind}/stop")
    def post_stop(kind: str) -> dict[str, Any]:
        """Interrupt `kind`'s running stage; no later one starts, the other runs on."""
        if kind not in KINDS:
            raise Refusal(f"there is no {kind} job: stop `prepare` or `render`")
        return {"job": jobs.stop(kind)}

    @cache
    def offered(flow: str) -> Flow:
        """Return a tracked flow by name, loaded once: a flow is pinned while served."""
        return _flow(wired, flow)

    def quoted(
        names: Sequence[str] | None,
    ) -> tuple[dict[str, Path], render.Quote, dict[str, Any]]:
        """Return the quoted collections' folders, their quote, and the dialog's view.

        With no names, every collection, in the Library's order. Only those the
        quote keeps, short of images or refusing a count, are returned.
        """
        if names is None:
            shelf = library.rows(root, flows, wired.flows_dir)
            asked = [row.name for row in shelf if row.collection]
        else:
            asked = list(dict.fromkeys(names))
        found = {name: folder(name) for name in asked}
        made = render.quote([one / library.RUNS for one in found.values()], wired)
        found = {
            name: one
            for name, one in found.items()
            if one / library.RUNS in made.shorts
        }
        disabled = _held() or (
            made.blocked if asked else "Tick a collection to render."
        )
        return found, made, _quote(found, made, disabled, wired.flows_dir)

    def _held() -> str | None:
        """Return what holds Render back in any collection: a render, a pod, no key."""
        if jobs.running("render"):
            return "A render session is running."
        if billing.state()["pod"]:
            return "A pod may still be billing."
        if not keyed(wired.session):
            return (
                "No RunPod key: add RUNPOD_API_KEY to .env, then start "
                "`uv run --env-file .env python -m isekai ui` again."
            )
        return None

    def short_of(found: Path) -> render.Short:
        """Return what a collection folder's approvals lack, as rendering counts it."""
        runs = found / library.RUNS
        return render.short(runs, render.run_ids(runs), wire(runs))

    @app.get("/api/c/{collection}/render")
    def read_render_offer(collection: str) -> dict[str, Any]:
        """Return how many images a collection lacks, and why Render is off, or null.

        It prices nothing; the count is the render stage's own. `others` is the
        images every other collection lacks, which the same dialog renders. `refused`
        is why an approval's count cannot be read, or null: the bar shows it with
        none short.
        """
        short = short_of(folder(collection))
        others = sum(
            sum(short_of(child).images.values())
            for child in library.listed(root)
            if library.is_collection(child) and child.name != collection
        )
        # Nothing short here is no reason while another collection is short.
        refused = short.refused[0] if short.refused else None
        idle = None if short.lines or others else short.blocked
        return {
            "disabled": _held() or refused or idle,
            "images": sum(short.images.values()),
            "others": others,
            "refused": short.refused[0] if short.refused else None,
        }

    @app.post("/api/render/quote")
    def post_quote(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Quote one render of the named collections, its limit and its price at most.

        `collections` names them; absent, every collection short of images is
        quoted. It rents nothing; only the render's own `POST` does.
        """
        names = (payload or {}).get("collections")
        if names is not None and not _strings(names):
            raise Refusal(
                "the quote names no list of collections; close Render and open it again"
            )
        return quoted(names)[2]

    @app.post("/api/render")
    def post_render(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Start the render job the quote of `collections` describes, or refuse why not.

        The quote is taken again here, so what renders is what is on disk now; a
        limit longer than the one the dialog showed, `limit_s`, or another number
        of images than its `images`, is refused, so nothing renders past what the
        operator agreed to.
        """
        body = payload or {}
        reopen = "close Render and open it again to read"
        names = body.get("collections")
        if not _strings(names) or not names:
            raise Refusal(f"the confirmation names no collections; {reopen} the quote")
        found, made, described = quoted(names)
        if described["disabled"] is not None:
            raise Refusal(described["disabled"])
        shown, listed = body.get("limit_s"), body.get("images")
        if not _whole(shown):
            raise Refusal(f"the confirmation names no quoted limit; {reopen} the quote")
        if made.estimate.limit_s > shown:
            raise Refusal(
                f"the quote changed since it was shown: its limit is now "
                f"{made.estimate.limit_s}s, not {shown}s; {reopen} it"
            )
        if not _whole(listed):
            raise Refusal(
                f"the confirmation names no quoted images; {reopen} the quote"
            )
        if made.images != listed:
            raise Refusal(
                f"the quote changed since it was shown: it now renders {made.images} "
                f"images, not {listed}; {reopen} it"
            )
        job = jobs.render(
            found,
            limit=made.estimate.limit_s,
            total=made.images,
            keep_open=bool(body.get("keep_open")),
        )
        return {"job": job}

    def rendering_slot() -> dict[str, Any] | None:
        """Return the render slot while it runs, or None."""
        slot = jobs.slot("render")
        if slot and slot["state"] == "running":
            return slot
        return None

    @app.get("/api/sessions/running")
    def running_sessions() -> dict[str, Any]:
        """Read live disk records across collections, including terminal renders."""
        found = []
        for child in library.listed(root):
            if library.is_collection(child):
                found += [
                    {"collection": child.name, **one} for one in library.running(child)
                ]
        return {"sessions": found}

    @app.get("/api/c/{collection}/sessions/{name}")
    def read_session(collection: str, name: str) -> dict[str, Any]:
        """Return one render session's record; the slot holds its volume steps."""
        return library.session(folder(collection), name)

    @app.post("/api/billing/check")
    def post_check() -> dict[str, Any]:
        """Ask gpunit again; an alert clears only when its records say gone."""
        return {"billing": billing.check()}

    @app.get("/events")
    def read_events(
        collection: str | None = None, staging: str | None = None
    ) -> StreamingResponse:
        """Stream the job slots, `collection`'s hub, `staging`'s files, then changes.

        A reload or a second tab gets the whole truth at once. A collection or an
        import it cannot read is left out of the snapshot, never refused.
        """
        # An import it no longer holds is left out rather than refused: the page's
        # one stream would never open again after a refused connect.
        try:
            held = imports.reader(staging) if staging is not None else None
        except Refusal:
            held = None

        def snapshot() -> dict[str, Any]:
            found = {
                "jobs": {kind: jobs.slot(kind) for kind in KINDS},
                "billing": billing.state(),
            }
            if collection is not None:
                # A collection it cannot read is left out: the screen's own read of it
                # shows the refusal, and the page keeps its stream.
                try:
                    grid = library.hub(folder(collection), flows, wired.flows_dir)
                except Refusal:
                    pass
                else:
                    found["hub"] = _hub(grid)
            if held is not None:
                found["files"] = held.files()
            return found

        return StreamingResponse(
            events.stream(broadcast, snapshot, collection=collection, staging=staging),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/api/tags")
    def read_tags(q: str = "", limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
        """Answer a tag fragment from the vocabulary the pipeline itself searches.

        The server ranks and the client does not. Shipping all 8,106 tags would
        put a second copy of the ranking rule in TypeScript, and `total` is the
        true match count so the dropdown can say how narrow the fragment got.
        """
        vocabulary = shared.vocabulary()
        fragment = q.strip()
        found = vocabulary.search(fragment) if fragment else []
        return {
            "matches": [
                {
                    "tag": tag,
                    "posts": (posts := vocabulary.count(tag)),
                    "rare": posts < RARE_BELOW,
                }
                for tag in found[: max(limit, 0)]
            ],
            "total": len(found),
        }

    @app.get("/api/fields")
    def read_fields(flow: str) -> dict[str, Any]:
        """Answer every candidate tag for every criterion `flow` declares.

        **The whole table in one response, once per flow.** ~40 KB, so the
        overlay filters with no round trip per keystroke, ordered by post count
        through `Vocabulary.rank` and cut at nothing. A declared field the table
        holds nothing for is present and empty; the excluded list is not served.
        """
        return shared.candidates(_flow(wired, flow))

    @app.get("/api/c/{collection}/review/{digest}/{flow}")
    def read_input(collection: str, digest: str, flow: str) -> dict[str, Any]:
        """Return everything Review shows for one run in one flow, in one payload.

        The fields come from the approved artifact while the input is approved and
        from the current draft otherwise, which is what makes an input approved in
        an earlier sitting open read-only rather than empty.
        """
        one = held(collection, digest, flow)
        if latest_artifact(one.directory(SHEETS)) is not None:
            # Opening a sheet takes its draft through the stage that owns it (D5);
            # `review` writes nothing where a draft or an approval is there.
            review(one.run, one.flow.id)
        draft = one.draft()
        approved = one.approved()
        state = review_state(one.directory(REVIEW))
        fields: dict[str, list[str]] = {}
        renders = ONE_RENDER
        revision = drafted = None
        if state == "approved" and approved is not None:
            # No command rewrites an approved sheet: `review` copies it and
            # refuses the same damage, so only a hand repairs it.
            remedy = f"restore it in {approved} by hand, then reload the page"
            body = read(approved, APPROVED_FILE, remedy=remedy)
            fields = _fields(approved, body, remedy)
            renders = renders_of(approved, body, remedy)
            revision = _revision(one, body, renders)
            drafted = _drafted(one, approved, body, remedy)
        elif draft is not None:
            remedy = _remedy(one, "review")
            body = read(draft, DRAFT_FILE)
            fields = _fields(draft, body, remedy)
            renders = renders_of(draft, body, remedy)
            revision = _revision(one, body, renders)
            drafted = _drafted(one, draft, body, remedy)
        budget = token_budget(fields, one.flow.schema, one.flow)
        caption, caption_from = _caption(one)
        width, height = _dimensions(one.run)
        return {
            "id": one.run.digest,
            "run": one.run.id,
            "flow": one.flow.id,
            "schema": list(one.flow.schema.names),
            "vocabulary": len(shared.vocabulary()),
            "width": width,
            "height": height,
            "caption": (
                _prose(one, caption, caption_from or one.flow.id) if caption else None
            ),
            # The one artifact a skipped verb leaves missing on a page under
            # review, so the page names what writes it. Built here: the browser
            # never spells a command.
            "caption_command": None if caption else _command(one, "caption"),
            # The flow whose caption is shown, where the sheet holds its tags
            # and this flow holds no caption of its own; else null.
            "caption_from": caption_from,
            # Both lists are `null` where the artifact is absent -- which is
            # three legitimate states, none of them a failure.
            "wd14": _wd14(one),
            "tags": _tags(one, shared.vocabulary()),
            "fields": fields,
            # Seeds as decimal strings: a 64-bit seed is past what a JavaScript
            # number holds exactly.
            "renders": _renders_out(renders),
            # The approval a draft or the approval shown was copied from, its
            # fields and the image being revised; null for a copy of a sheet.
            "revision": revision,
            # The other flow's approval a draft was drafted from, and the fields
            # of its own sheet; null for any other draft.
            "drafted": drafted,
            # **Approval with nothing newer beside it is what makes a sheet
            # read-only**, which is precisely `state() == "approved"`.
            "readonly": state == "approved",
            "draft": draft.name if draft else None,
            "approved": approved.name if approved else None,
            "saved": _saved(draft),
            # The approved artifact's own time, which the draft's cannot stand
            # in for: `approve()` unlinks the draft.
            "approved_at": _saved(approved),
            # Why *Cancel approve* is disabled, or null while it can run.
            "cancel": _rendering(collection) or cancellable(one.run, one.flow.id),
            "budget": _budget(budget),
        }

    @app.get("/api/c/{collection}/review/{digest}/{flow}/photo")
    def read_photo(collection: str, digest: str, flow: str) -> Response:
        """Serve the photograph's bytes, whole. `image.py` reads headers, not pixels."""
        return _photograph(held(collection, digest, flow).run.photo)

    @app.put("/api/c/{collection}/review/{digest}/{flow}/draft")
    def put_draft(
        collection: str, digest: str, flow: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Replace the draft's values in place, through the one function that owns it.

        The whole draft, every time: a debounced `PUT` of everything is what
        makes the receipt the page shows true.

        **Two preconditions, and both answer `409`.** An input that is approved
        and holds no later draft refuses an update at all: approval is the end
        of a review. And an update whose `saved` does not match the draft on
        disk refuses, because two overlapping `PUT`s would otherwise commit in
        the order the server finishes them. The check and the write hold one
        lock, so of two updates stating one precondition, the later fails it.
        """
        one = held(collection, digest, flow)
        # Before the lock: a malformed body refuses without waiting on a write.
        fields = _update(payload)
        renders = _renders_in(payload)
        with _DRAFT_UPDATE:
            if review_state(one.directory(REVIEW)) == "approved":
                raise Refusal(
                    f"{one.run.id} is approved, and an approved sheet is never "
                    "edited in place; approval is the end of a review -- correct "
                    f"it with `{_command(one, 'review', '--new-version')}`, which "
                    "writes a fresh draft beside the approved artifact, and "
                    "reload: the input comes back re-opened and editable, with "
                    "its approved artifact still named"
                )
            _precondition(one, payload)
            written = save_draft(one.run, one.flow.id, fields, renders)
        budget = token_budget(fields, one.flow.schema, one.flow)
        return {
            "draft": written.name,
            "saved": _saved(written),
            "budget": _budget(budget),
        }

    @app.post("/api/c/{collection}/review/{digest}/{flow}/approve")
    def post_approve(
        collection: str, digest: str, flow: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Validate and approve the draft, through the only writer of an approval.

        Under the draft lock, so an update in flight either lands before the
        approval reads the draft or finds the input approved and is refused.
        **It states the draft update's precondition**, so a page approves only
        the draft it last read, never one another writer has since moved.
        """
        one = held(collection, digest, flow)
        with _DRAFT_UPDATE:
            _precondition(one, payload or {})
            written, warnings = approve(
                one.run, one.flow.id, one.flow.schema, shared.vocabulary()
            )
        return {
            "approved": written.name if written else None,
            "warnings": warnings,
            "at": _saved(written),
        }

    @app.post("/api/c/{collection}/review/{digest}/{flow}/cancel")
    def post_cancel(collection: str, digest: str, flow: str) -> dict[str, Any]:
        """Turn the approval back into its draft, refused while a render runs.

        `back` names what the flow is left on: the draft, or for a deleted copy
        the draft or approval beneath it, null where nothing is.
        """
        one = held(collection, digest, flow)
        with _DRAFT_UPDATE:
            rendering = _rendering(collection)
            if rendering is not None:
                raise Refusal(
                    f"{rendering} Wait for it to end, then cancel the approval again."
                )
            left = cancel(one.run, one.flow.id)
        return {"back": None if left is None else left.name}

    def _rendering(collection: str) -> str | None:
        """Return what a render running for `collection` says, or None."""
        slot = rendering_slot()
        return (
            "A render session is running."
            if slot and slot["collection"] == collection
            else None
        )

    @app.post("/api/c/{collection}/review/{digest}/{flow}/discard")
    def post_discard(
        collection: str, digest: str, flow: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Delete the waiting draft, as `review --discard` does; an approval refuses.

        **It states the draft update's precondition**, so a page deletes only the
        draft it last read, never one another tab has since edited.
        """
        one = held(collection, digest, flow)
        with _DRAFT_UPDATE:
            _precondition(one, payload or {}, "discard again")
            gone = discard(one.run, one.flow.id)
        return {"discarded": gone.name}

    @app.post("/api/c/{collection}/draft", response_model=None)
    def post_draft(
        collection: str, payload: dict[str, Any]
    ) -> dict[str, Any] | JSONResponse:
        """Draft `flow` from every image named, or, when any is refused, none.

        As `draft --flow` does: an image's own flow a revision, another drafted
        from its approval. A target's waiting draft with edits of its own is
        answered as `waiting`, and nothing is written for it. A refusal answers
        each image with its own refusal, or null, so the page can deselect the rest.
        """
        found = folder(collection)
        name = payload.get("flow")
        if not isinstance(name, str) or name not in flows:
            raise Refusal(
                f"{name!r}: not a flow this surface drafts; the flows it drafts are "
                f"{', '.join(flows) or 'none'} -- reload the image's large view to "
                "choose one; nothing was written"
            )
        target = offered(name)
        named = _images(payload)
        answers: list[str | None] = [None] * len(named)
        drafts = [{**_image_out(*one), "draft": None, "waiting": None} for one in named]
        # Each image to write, by its place in `named`.
        located: list[tuple[int, Path, Revision]] = []
        with _DRAFT_UPDATE:
            for at, (digest, flow, version, seed) in enumerate(named):
                try:
                    # A flow this build does not track names no directory of a run.
                    one = offered(flow)
                    run = library.run_named(found, digest)
                    image = image_of(run, one, version, seed)
                    # The draft in hand is opened rather than refused; the
                    # review stage, and the CLI through it, still refuses it.
                    waiting = waiting_edit(run, name)
                except Refusal as refused:
                    answers[at] = str(refused)
                    continue
                if waiting is not None:
                    drafts[at]["waiting"] = waiting.name
                else:
                    located.append((at, image, (run, flow, version, seed)))
            # Each other image the collection holds is answered by the review stage.
            checked = refuse_image_drafts(
                target,
                [(image, held) for _, image, held in located],
                shared.vocabulary,
                shared.field_map,
            )
            for (at, _, _), answer in zip(located, checked, strict=True):
                answers[at] = answer
            if any(answer is not None for answer in answers):
                return JSONResponse(
                    {
                        "refusal": "; ".join(a for a in answers if a is not None),
                        "images": [
                            {**_image_out(*one), "refusal": answer}
                            for one, answer in zip(named, answers, strict=True)
                        ],
                    },
                    REFUSED,
                )
            for at, _, held in located:
                drafts[at]["draft"] = draft_from_image(
                    target, held, shared.vocabulary, shared.field_map
                ).name
        return {"drafts": drafts}

    @app.get("/api/c/{collection}/renders")
    def read_renders(collection: str) -> dict[str, Any]:
        """Return each source's images by offered flow, approvals newest first.

        `ready` is how many images each flow's newest approval lacks, as the
        render stage counts them.
        """
        suffixes = {flow: offered(flow).output_suffix for flow in flows}
        return {
            "flows": list(flows),
            "sources": [
                {
                    "name": one.name,
                    "digest": one.digest,
                    "ready": {
                        flow: library.lacking(one.run, offered(flow)) for flow in flows
                    },
                    "cells": {
                        flow: [
                            _version_out(version)
                            for version in library.versions(
                                one.run, flow, suffixes[flow]
                            )
                        ]
                        if one.run is not None
                        else []
                        for flow in flows
                    },
                }
                for one in library.sources(folder(collection))
            ],
        }

    def rendered(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> tuple[Run, Path, Path]:
        """Return a render's run, its image and the approval it was rendered from."""
        found = folder(collection)
        run = library.run_named(found, digest)
        one = offered(flow)
        number = _version(version)
        approval = approval_of(run, flow, number)
        image = image_of(run, one, number, seed)
        if not image.is_file():
            raise Refusal(
                f"{image.name}: its record is there, its image is gone; render it "
                f"again with `python -m isekai render {found / library.RUNS}`"
            )
        return run, image, approval

    @app.get("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}")
    def read_render(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> dict[str, Any]:
        """Return one render's large view: the approval's filled fields beside it.

        It is headed by what the version was: the one it came from, a revision or
        a re-roll, and its count and seeds; or, where its `renders` no render
        takes, damaged, naming the file, with no count.
        """
        run, _, approval = rendered(collection, digest, flow, version, seed)
        _, fields = _approved(approval)
        number = _version(version)
        suffix = offered(flow).output_suffix
        listed = library.versions(run, flow, suffix)
        held = next((one for one in listed if one.version == number), None)
        if held is None:
            raise Refusal(
                f"{approval.name}: it was gone when its version was listed; reload "
                "the page"
            )
        return {
            "flow": flow,
            "version": number,
            "seed": str(seed),
            "fields": {name: tags for name, tags in fields.items() if tags},
            "approved_at": _saved(approval),
            "came_from": held.came_from,
            "kind": held.kind,
            "count": held.count,
            "seeds": _decimal(held.seeds),
            "damaged": held.damaged,
            # The newest older version that rendered this seed, or null.
            "compare": library.paired(run, flow, number, seed, suffix),
            # Every offered flow, this one first, assigned or not: a draft assigns.
            "targets": sorted(flows, key=lambda name: name != flow),
            # The cell's images, as Renders draws them: oldest version first.
            "images": _images_out(library.rendered_images(run, flow, suffix)),
            # The source's images, a row per offered flow holding any: the pick.
            "source": [
                {"flow": name, "images": _images_out(images)}
                for name in flows
                if (
                    images := library.rendered_images(
                        run, name, offered(name).output_suffix
                    )
                )
            ],
        }

    @app.get(
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/compare/{other_flow}/{other_version}/{other_seed}"
    )
    def read_compare(
        collection: str,
        digest: str,
        flow: str,
        version: str,
        seed: int,
        other_flow: str,
        other_version: str,
        other_seed: int,
    ) -> dict[str, Any]:
        """Return the image picked beside the one compare started from, of one source.

        The picked is the left, this the right. Between two flows, only the
        fields both declare are compared.
        e.g. `…/summon/v4/7/compare/flat/v1/5` -> flat's v1 · 5 left, summon's
        v4 · 7 right
        """
        number, other_number = _version(version), _version(other_version)
        if (other_flow, other_number, other_seed) == (flow, number, seed):
            raise Refusal(
                f"{flow} {version} · {seed}: an image compared with itself shows no "
                "change; go back to its large view and pick another"
            )
        _, _, origin = rendered(collection, digest, flow, version, seed)
        _, _, picked = rendered(
            collection, digest, other_flow, other_version, other_seed
        )
        one, other = offered(flow), offered(other_flow)
        right, right_fields = _side(one, number, origin)
        left, left_fields = _side(other, other_number, picked)
        changed = [
            {"field": name, "left": left_fields[name], "right": right_fields[name]}
            for name in one.schema.names
            if name in other.schema.names and left_fields[name] != right_fields[name]
        ]
        return {
            "left": {"flow": other_flow, **left, "seed": str(other_seed)},
            "right": {"flow": flow, **right, "seed": str(seed)},
            "changed": changed,
            "different_seeds": other_seed != seed,
            "same_sheet": not changed,
        }

    @app.get(
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/compare/photo"
    )
    def read_compare_photo(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> dict[str, Any]:
        """Return the image beside its source's photograph: the pair, no fields.

        The photograph is the left; the page reads its bytes at the run's `/photo`.
        """
        _, _, origin = rendered(collection, digest, flow, version, seed)
        right, _ = _side(offered(flow), _version(version), origin)
        return {"left": None, "right": {"flow": flow, **right, "seed": str(seed)}}

    @app.get("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/image")
    def read_render_image(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> FileResponse:
        """Serve the render's bytes, whole."""
        return FileResponse(rendered(collection, digest, flow, version, seed)[1])

    @app.get("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/thumb")
    def read_render_thumb(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> FileResponse:
        """Serve the render's thumbnail, made in the library's cache the first time."""
        run, image, _ = rendered(collection, digest, flow, version, seed)
        return FileResponse(
            library.thumbnail(root, run, image), media_type="image/jpeg"
        )

    @app.get("/api/c/{collection}/sources/{name}")
    def read_source(collection: str, name: str) -> Response:
        """Serve a source's bytes, whole, with or without a run.

        One in a format the render does not read, placed by hand, is served as an
        upright JPEG of it, so the viewer shows what its thumbnail does.
        """
        source = library.source_files(folder(collection))(name)
        return _photograph(source, other=library.source_jpeg)

    @app.get("/api/c/{collection}/sources/{name}/thumb")
    def read_source_thumb(collection: str, name: str) -> FileResponse:
        """Serve a source's thumbnail, upright, made in the library's cache once."""
        source = library.source_files(folder(collection))(name)
        return FileResponse(
            library.source_thumbnail(root, source), media_type="image/jpeg"
        )

    @app.get("/api/{rest:path}")
    def no_route(rest: str) -> JSONResponse:
        """Answer an unknown API path as not found, never with the page."""
        return JSONResponse({"refusal": f"no route /api/{rest}"}, 404)

    # Every other path is a screen of the app, so a reload or a deep link loads
    # the shell and its router draws the screen (D3).
    app.mount(
        "/assets",
        StaticFiles(directory=bundle / "assets", check_dir=False),
        name="assets",
    )

    @app.get("/{rest:path}")
    def page(rest: str) -> FileResponse:
        """Return the bundle's `index.html`, whatever screen the path names."""
        return FileResponse(bundle / "index.html")

    return app


class _Shared:
    """What every collection shares, read once when first asked for.

    Read on first use rather than at start, so a missing vocabulary is a
    refusal on the page that needs it rather than a server that never starts.
    """

    def __init__(self, wired: Wiring) -> None:
        """Hold the wiring the vocabulary and the table are read through."""
        self._wired = wired
        self._vocabulary: Vocabulary | None = None
        self._field_map: FieldMap | None = None
        self._candidates: dict[str, dict[str, Any]] = {}

    def vocabulary(self) -> Vocabulary:
        """Return the vocabulary, read once."""
        if self._vocabulary is None:
            self._vocabulary = self._wired.vocabulary()
        return self._vocabulary

    def field_map(self) -> FieldMap:
        """Return the field map held against the vocabulary, read once."""
        if self._field_map is None:
            self._field_map = self._wired.field_map(self.vocabulary())
        return self._field_map

    def candidates(self, flow: Flow) -> dict[str, Any]:
        """Return every candidate tag for every criterion `flow` declares, ranked."""
        if flow.id not in self._candidates:
            vocabulary, table = self.vocabulary(), self.field_map()
            self._candidates[flow.id] = {
                "fields": {
                    name: [
                        {"tag": tag, "posts": vocabulary.count(tag)}
                        for tag in vocabulary.rank(table.group(name))
                    ]
                    for name in flow.schema.names
                }
            }
        return self._candidates[flow.id]


# A number a request spells: ASCII digits alone, since `str.isdigit` also passes
# a superscript `int` cannot read.
_DECIMAL = re.compile(r"[0-9]+")


def cell_event(
    found: Path, grid: library.Hub, loaded: Mapping[str, Flow]
) -> Callable[[Mapping[str, Any]], dict[str, Any] | None]:
    """Return what turns a progress line into a `cell` event, its stage read from disk.

    A line naming a run or a flow the job did not start reads None.
    """
    collection = grid.name
    sources = {one.run.id: one.name for one in grid.sources if one.run}

    def cell(line: Mapping[str, Any]) -> dict[str, Any] | None:
        run_id, flow = str(line.get("run")), str(line.get("flow"))
        if run_id not in sources or flow not in loaded:
            return None
        run = Run(run_id, found / library.RUNS / run_id)
        return {
            "collection": collection,
            "source": sources[run_id],
            "flow": flow,
            "stage": line.get("stage"),
            "state": line.get("state"),
            "message": line.get("message"),
            "cell": _cell_out(library.stage(run, loaded[flow])),
        }

    return cell


def _approved(approval: Path) -> tuple[ReviewApproved, dict[str, list[str]]]:
    """Read an approval the page shows, and its fields; only a hand repairs one."""
    remedy = f"restore it in {approval} by hand, then reload the page"
    body = read(approval, APPROVED_FILE, remedy=remedy)
    return body, _fields(approval, body, remedy)


def _revision(
    one: Held, body: Mapping[str, Any], renders: Renders
) -> dict[str, Any] | None:
    """Describe the approval a draft or an approval was copied from, and its image.

    The image is the one the draft records, whatever its seeds became; a record
    naming none falls back to the first listed seed rendered under that
    approval, or null.
    e.g. from 1, seeds [7], outputs/001/7.png there -> {"version": 1, "seed": "7", …}
    """
    version = came_from(body)
    if version is None:
        return None
    approval = approval_of(one.run, one.flow.id, version)
    if not approval.is_file():
        return None
    if (image := draft_image(body)) is not None:
        seed = image["seed"]
    else:
        seed = next(
            (
                seed
                for seed in renders["seeds"]
                if image_of(one.run, one.flow, version, seed).is_file()
            ),
            None,
        )
    return {
        "version": version,
        "seed": None if seed is None else str(seed),
        "fields": _approved(approval)[1],
    }


def _drafted(
    one: Held, draft: Path, body: Mapping[str, Any], remedy: str
) -> dict[str, Any] | None:
    """Describe the other flow's approval a draft was drafted from, and its sheet.

    `image`, its seed a decimal string, is the one the draft records, if any.
    `remedy` repairs the draft or approval; a damaged sheet names itself, since
    no command rewrites a sheet one records: `review` copies the same damage.
    e.g. from summon 1, on sheet 1 -> {"flow": "summon-…", "approval": 1, "fields": …}
    """
    origin = drafted_from(body)
    if origin is None:
        return None
    require(draft, body, "sheet", int, remedy)
    sheet = sheet_of(one.run, one.flow.id, body["sheet"])
    restore = f"restore {sheet} by hand, then reload the page"
    held = read(sheet, SHEET_FILE, remedy=restore)
    drafted: dict[str, Any] = {**origin, "fields": _fields(sheet, held, restore)}
    if (image := draft_image(body)) is not None:
        drafted["image"] = {**image, "seed": str(image["seed"])}
    return drafted


def _caption(one: Held) -> tuple[Path | None, str | None]:
    """Return `one`'s newest caption, and the flow it is borrowed from, or None.

    Where `one` holds no caption and its newest sheet holds another flow's tags,
    that flow's newest caption is borrowed. An unreadable sheet borrows nothing.
    """
    own = latest_artifact(one.directory(CAPTIONS))
    newest = latest_artifact(one.directory(SHEETS))
    if own is not None or newest is None:
        return own, None
    try:
        source = tagged_from(read(newest, SHEET_FILE))
    except Refusal:
        return None, None
    borrowed = (
        None if source is None else latest_artifact(one.run.directory(source, CAPTIONS))
    )
    return (borrowed, source) if borrowed is not None else (None, None)


def _side(
    flow: Flow, version: int, approval: Path
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Return one side of a comparison as the page shows it, and every field."""
    body, fields = _approved(approval)
    remedy = f"restore it in {approval} by hand, then reload the page"
    for name in flow.schema.names:
        fields.setdefault(name, [])
    return {
        "version": version,
        "approved_at": _saved(approval),
        "renders": _renders_out(renders_of(approval, body, remedy)),
        "tokens": token_budget(fields, flow.schema, flow).total,
    }, fields


def _images(payload: Mapping[str, Any]) -> list[tuple[str, str, int, int]]:
    """Return a draft's images, refusing a list that is not of rendered images.

    e.g. `{"images": [{"digest": "0d4b…", "flow": "f", "version": 1, "seed": "7"}]}`
         -> `[("0d4b…", "f", 1, 7)]`
    """
    images = payload.get("images")
    fix = (
        "send each image's digest, flow, version and decimal seed -- nothing was "
        "written"
    )
    if not isinstance(images, list) or not images:
        raise Refusal(f"the draft names no images; {fix}")
    named = []
    for image in images:
        if not (
            isinstance(image, dict)
            and isinstance(image.get("digest"), str)
            and isinstance(image.get("flow"), str)
            and _numbered(image.get("version"))
            and isinstance(image.get("seed"), str)
            and is_seed(image["seed"])
        ):
            raise Refusal(f"the draft's image {image!r} is not one; {fix}")
        named.append(
            (image["digest"], image["flow"], image["version"], int(image["seed"]))
        )
    return named


def _image_out(digest: str, flow: str, version: int, seed: int) -> dict[str, Any]:
    """Describe an image a draft is written from, its seed a decimal string."""
    return {"digest": digest, "flow": flow, "version": version, "seed": str(seed)}


def _version_out(version: library.Version) -> dict[str, Any]:
    """Describe an approval's version, each seed a decimal string as `renders` is."""
    return {
        **asdict(version),
        "seeds": _decimal(version.seeds),
        "rendered": _decimal(version.rendered),
    }


def _images_out(images: Sequence[tuple[int, int]]) -> list[dict[str, Any]]:
    """Describe rendered images by version and decimal seed, as Renders names them.

    e.g. [(1, 7)] -> [{"version": 1, "seed": "7"}]
    """
    return [{"version": version, "seed": str(seed)} for version, seed in images]


def _decimal(seeds: Sequence[int]) -> list[str]:
    """Return seeds as decimal strings: a 64-bit seed is past a page's number."""
    return [str(seed) for seed in seeds]


def _numbered(value: object) -> TypeGuard[int]:
    """Return whether a request's value is a version a run's file names can spell.

    e.g. 2 -> True, 1000 -> False
    """
    return _whole(value) and is_version(value)


def _whole(value: object) -> TypeGuard[int]:
    """Return whether a request's value is a whole number, a JSON `true` not one."""
    return isinstance(value, int) and not isinstance(value, bool)


def _version(text: str) -> int:
    """Return the approval number a URL's version names.

    e.g. "v2" -> 2
    """
    digits = text.removeprefix("v")
    if not _DECIMAL.fullmatch(digits):
        raise Refusal(
            f"{text!r} names no version; a version is v and the approval's number, "
            "e.g. v1 -- go back to the collection's Renders to choose one"
        )
    return int(digits)


def _quote(
    found: Mapping[str, Path],
    made: render.Quote,
    disabled: str | None,
    flows_dir: Path,
) -> dict[str, Any]:
    """Describe a quote as the Render dialog shows it: a row per collection."""
    return {
        "collections": [
            _quoted_row(name, one, made.shorts[one / library.RUNS], flows_dir)
            for name, one in found.items()
        ],
        "estimate": {
            "seconds": made.estimate.seconds,
            "limit_s": made.estimate.limit_s,
            "boot_s": made.timing.boot_s,
            "teardown_s": made.timing.teardown_s,
        },
        "price": {
            "about": made.about,
            "at_most": made.at_most,
            "keep_open": made.keep_open,
        },
        "ceiling_s": made.ceiling_s,
        "disabled": disabled,
    }


def _quoted_row(
    name: str, found: Path, short: render.Short, flows_dir: Path
) -> dict[str, Any]:
    """Describe one collection's part of a quote, each run by its source."""
    runs = {
        one.run.id: (one.name, one.run)
        for one in library.hub(found, (), flows_dir).sources
        if one.run is not None
    }

    def source(run_id: str, flow: str) -> dict[str, Any]:
        name, run = runs.get(
            run_id, (run_id, Run(run_id, found / library.RUNS / run_id))
        )
        versions = approved_versions(run.directory(flow, REVIEW))
        return {
            "name": name,
            "digest": run.digest,
            "version": versions[-1] if versions else None,
        }

    flows = [
        {
            "flow": line.flow,
            "images": line.images,
            "sources": [
                {**source(run_id, flow), "images": images}
                for run_id, flow, images in short.wanted
                if flow == line.flow
            ],
        }
        for line in short.lines
    ]
    return {
        "collection": name,
        "images": sum(short.images.values()),
        "flows": flows,
        "left_out": [
            {**source(run_id, flow), "flow": flow, "reason": reason}
            for run_id, flow, reason in short.left_out
        ],
        "refused": short.refused[0] if short.refused else None,
    }


def _photograph(
    path: Path, *, other: Callable[[Path], bytes] | None = None
) -> Response:
    """Serve the photograph at `path` as the image its bytes are, never its name's.

    A source keeps the name it arrived with, and one ending `.html` served by its
    suffix would run as a page on this surface's own origin; `nosniff` keeps the
    browser from guessing past the declared type. Bytes neither JPEG nor PNG are
    refused, or served as the JPEG `other` makes of them.
    """
    headers = {"X-Content-Type-Options": "nosniff"}
    with path.open("rb") as handle:
        head = handle.read(SIGNATURE_BYTES)
    try:
        kind, _ = media_type(head)
    except Refusal:
        if other is None:
            raise
        return Response(other(path), media_type="image/jpeg", headers=headers)
    return FileResponse(path, media_type=kind, headers=headers)


def _hub(grid: library.Hub) -> dict[str, Any]:
    """Describe a collection's grid as the page draws it."""
    return {
        "collection": grid.name,
        "flows": list(grid.flows),
        "sources": [
            {
                "name": one.name,
                "digest": one.digest,
                "width": one.size[0] if one.size else None,
                "height": one.size[1] if one.size else None,
                "cells": {flow: _cell_out(cell) for flow, cell in one.cells.items()},
                "carries": list(one.carries),
            }
            for one in grid.sources
        ],
    }


def _cell_out(cell: library.Cell) -> dict[str, Any]:
    """Describe a hub cell, each of its images' seeds a decimal string."""

    def image(one: library.Rendered) -> dict[str, Any]:
        return {"version": one.version, "seed": str(one.seed)}

    return {
        **asdict(cell),
        "newest": None if cell.newest is None else image(cell.newest),
        "images": [image(one) for one in cell.images],
    }


def _flow(wired: Wiring, flow: str) -> Flow:
    """Return the tracked flow a URL names, refusing one this build does not track."""
    tracked = tracked_flows(wired.flows_dir)
    if flow not in tracked:
        raise Refusal(
            f"{flow}: not a flow this build tracks; the flows it tracks are "
            f"{', '.join(tracked)} -- go back to the collection's hub to choose one"
        )
    return load_flow(flow, wired.flows_dir)


def _dimensions(run: Run) -> tuple[int, int]:
    """Return the photograph's size, as a `Refusal` rather than an exit."""
    return dimensions_or_refuse(
        run.photo,
        "the page reads the photograph's own header to size itself and there is "
        "nothing to fall back to -- re-export it as a JPEG or PNG",
    )


def _wd14(one: Held) -> list[dict[str, Any]] | None:
    """Return the local tagger's scored list for the page, or None if absent.

    Stored sorted by confidence descending, and passed through in that order:
    the sort is what makes a wrong tag arrive pre-refuted by the right one above
    it, so re-ordering here would throw away the reason the number is shown.
    """
    path = latest_artifact(one.directory(WD14))
    if path is None:
        return None
    found = read(path, WD14_FILE)
    remedy = _remedy(one, "tag")
    require(path, found, "tags", list, remedy)
    scored: list[dict[str, Any]] = []
    for index, entry in enumerate(found["tags"]):
        item = entry if isinstance(entry, dict) else {}
        tag, confidence = item.get("tag"), item.get("confidence")
        # `bool` is an `int`, and a flag is no confidence.
        if (
            not isinstance(tag, str)
            or isinstance(confidence, bool)
            or not isinstance(confidence, int | float)
        ):
            raise Refusal(
                f"{path.name}: its tag entry {index} is not a tag and a confidence; "
                f"{remedy}"
            )
        scored.append({"tag": tag, "confidence": float(confidence)})
    return scored


def _tags(one: Held, vocabulary: Vocabulary) -> list[dict[str, Any]] | None:
    """Return the hosted tagger's committable tags for the page, or None if absent.

    **Filtered to what the vocabulary carries, on the way to the page and never
    on the way to disk.** Roughly nine in ten of this model's tags were outside
    the vocabulary on an acceptance collection and could be committed to no field;
    the artifact keeps every tag the model returned. Deduplicated here only:
    `{tag, posts}` repeats carry no information and would be duplicate Vue keys.
    The local tagger's list is not filtered -- it emits the vocabulary itself.
    """
    path = latest_artifact(one.directory(TAGS))
    if path is None:
        return None
    listed = read(path, TAGS_FILE).get("tags")
    if not _strings(listed):
        raise Refusal(
            f"{path.name}: its `tags` is not a list of strings; {_remedy(one, 'tag')}"
        )
    return [
        {"tag": name, "posts": vocabulary.count(name)}
        for name in dict.fromkeys(listed)
        if name in vocabulary
    ]


def _command(one: Held, verb: str, *flags: str) -> str:
    """Return the command that runs `verb` for `one`, as the operator pastes it.

    e.g. "caption" -> "python -m isekai caption --flow f --runs b/runs r"
    """
    return stage_command(one.run, verb, one.flow.id, options=flags)


def _remedy(one: Held, verb: str, flow: str | None = None) -> str:
    """Return the remedy naming the command that rewrites `verb`'s file for `one`.

    `flow` names another flow's file instead.

    e.g. "tag" -> "rewrite it with `python -m isekai tag --flow f --new-version r`"
    """
    command = stage_command(one.run, verb, flow or one.flow.id, options=NEW_VERSION)
    return f"rewrite it with `{command}`"


def _strings(value: object) -> TypeGuard[list[str]]:
    """Return whether `value` is a list of strings: tags, or collection names."""
    return isinstance(value, list) and all(isinstance(one, str) for one in value)


def _untagged(fields: Mapping[str, object]) -> str | None:
    """Return the first field whose value is not a list of tags, or None."""
    return next((name for name, tags in fields.items() if not _strings(tags)), None)


def _fields(path: Path, body: Mapping[str, Any], remedy: str) -> dict[str, list[str]]:
    """Return a sheet's fields, refusing by name one that is not a list of tags."""
    require(path, body, "fields", dict, remedy)
    if (name := _untagged(body["fields"])) is not None:
        raise Refusal(f"{path.name}: its `{name}` is not a list of tags; {remedy}")
    return dict(body["fields"])


def _prose(one: Held, path: Path, flow: str) -> str:
    """Return `flow`'s caption's prose, refusing by name a caption that has none."""
    body = read(path, CAPTION_FILE)
    require(path, body, "prose", str, _remedy(one, "caption", flow))
    return body["prose"]


def _update(payload: Mapping[str, Any]) -> dict[str, list[str]]:
    """Return an update's fields, refusing one that is not an object of tag lists."""
    fields = payload.get("fields", {})
    fix = "send each field as a list of strings -- nothing was saved"
    if not isinstance(fields, dict):
        raise Refusal(f"the update's `fields` is not an object of tag lists; {fix}")
    if (name := _untagged(fields)) is not None:
        raise Refusal(f"the update's {name} is not a list of tags; {fix}")
    return fields


def _renders_in(payload: Mapping[str, Any]) -> Renders | None:
    """Return an update's `renders`, its seeds parsed from decimal strings, or None.

    e.g. `{"count": 2, "seeds": ["18402"]}` -> `{"count": 2, "seeds": [18402]}`
    """
    held = payload.get("renders")
    if held is None:
        return None
    fix = "send a count and a list of decimal seeds -- nothing was saved"
    if not isinstance(held, dict) or not isinstance(held.get("seeds", []), list):
        raise Refusal(f"the update's `renders` is not a count and its seeds; {fix}")
    seeds = held.get("seeds", [])
    if not all(isinstance(seed, str) and _DECIMAL.fullmatch(seed) for seed in seeds):
        raise Refusal(f"the update's renders seeds are not decimal numbers; {fix}")
    return {"count": held.get("count"), "seeds": [int(seed) for seed in seeds]}


def _renders_out(renders: Renders) -> dict[str, Any]:
    """Describe `renders` for the page, each seed as its decimal string."""
    return {
        "count": renders["count"],
        "seeds": _decimal(renders["seeds"]),
    }


def _precondition(
    one: Held, payload: Mapping[str, Any], again: str = "make the correction again"
) -> None:
    """Refuse an update, an approval or a discard against a draft that has moved.

    `again` is what the page does once it has read the draft on disk.

    **`st_mtime` is the precondition because nothing else exists.** The draft
    carries no timestamp, no revision counter and no digest, and adding one
    changes the draft's shape. `put_draft`'s lock orders the check and the
    write; this is what orders the sends.

    **A payload carrying no `saved` states no precondition**, and is allowed.
    """
    offered = payload.get("saved")
    if offered is None:
        return
    draft = one.draft()
    if draft is not None and _saved(draft) != offered:
        raise Refusal(
            f"{draft.name} changed since this page last read it; another tab or "
            "another save got there first -- reload the input to see what is on "
            f"disk, then {again}"
        )


def _budget(budget: TokenBudget) -> dict[str, Any]:
    """Describe a token budget. One spelling, so two endpoints cannot disagree."""
    return {
        "total": budget.total,
        "per_field": dict(budget.per_field),
        "overhead": budget.overhead,
        "window": ENCODER_WINDOW,
    }


def _saved(path: Path | None) -> float | None:
    """Return when this artifact was last written, as the server's own clock says.

    The server's, never the browser's. The page shows the time beside the file
    it names, and a receipt a client wrote for itself is a claim about a save
    rather than a record of one.
    """
    return path.stat().st_mtime if path is not None else None


def run(app: FastAPI, *, host: str, port: int) -> None:
    """Block, serving `app`, until the operator stops it.

    A thin wrapper so that `__init__.py` composes the surface without importing
    a web framework at module scope.
    """
    broadcast: events.Broadcast = app.state.broadcast

    class Server(uvicorn.Server):
        def handle_exit(self, sig: int, frame: FrameType | None) -> None:
            # A signal cannot take the broadcast lock; wake queues on the loop.
            broadcast.closed = True
            asyncio.get_running_loop().call_soon(broadcast.close)
            super().handle_exit(sig, frame)

    Server(
        uvicorn.Config(
            app, host=host, port=port, log_level="warning", timeout_graceful_shutdown=1
        )
    ).run()

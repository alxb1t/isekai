"""The HTTP surface, and the entry to the modules that import a web framework.

`library.py` and `surface.py` import no web framework, so what they hold is
exercised by the main suite whether or not a server is installed. The modules of
`routes/` import FastAPI and are reached through this module alone, so
`tests/test_ui_api.py` opens with an `importorskip` for it. They hold the
vocabulary, tattoo library and place routes, `RenderRoutes` and `StreamRoutes`;
`create_app` takes what a test replaces and declares the routes that read it,
and the rest.

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
the sequence `draft --flow` runs too (D4); a render's thumbnails leave through
the library's `drop_thumbnails()`, the render through the render stage's
`discard_render()`, and the approvals, drafts, sheets, source copies and
own copies of the photograph's description its last render leaves through
`withdraw()`.
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
GET  /api/c/{collection}/render  ·  POST …/render{/quote,}
     {keep_open, limit_s, images, bakes}
GET  /api/sessions/running   ·   GET /api/c/{collection}/sessions/{id}
POST /api/billing/check
POST /api/staging   ·   PUT, GET and DELETE …/{id}/files/{name}, and GET its /thumb
DELETE /api/staging/{id}   ·   POST …/{id}/commit   {collection, as_is, add}
GET  /events[?collection=&staging=], either or both    Server-Sent Events
GET  /api/c/{collection}/review/{digest}/{flow}         and /photo, /source/{version}
PUT  /api/c/{collection}/review/{digest}/{flow}/draft
POST /api/c/{collection}/review/{digest}/{flow}/approve   ·   POST …/cancel
POST /api/c/{collection}/review/{digest}/{flow}/discard
POST /api/c/{collection}/draft         {flow, images: [{digest, flow, version, seed}]}
GET  /api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}
     and its /image, /thumb, /compare/photo and /compare/{flow}/{version}/{seed}
GET  …/renders/{digest}/{flow}/{version}/{seed}/edit/{k}   and its /image and /thumb
DELETE /api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}
GET  /api/c/{collection}/sources/{name}   and its /thumb
GET  /api/tattoos?digest=   ·   POST /api/tattoos   {staging, file, name}
GET  /api/tattoos/{name}?digest=   and its /design
DELETE /api/tattoos/{name}?digest=
PUT  /api/tattoos/{name}/outline?digest=   {points, closed, white, neutral, depth}
GET  and PUT /api/tattoos/{name}/stage1/{digest}   {pairs, not_on_photo}
POST /api/c/{collection}/tattoos   {name, digest, flow}
POST /api/c/{collection}/tattoos/{name}/ink
     {points, white, neutral, depth, digest, flow}      a JPEG, no-store
POST /api/c/{collection}/tattoos/{name}/preview
     {target, digest, flow, version, seed, edit, pairs, limb, exclusions}
     a JPEG, no-store
POST /api/c/{collection}/tattoos/{name}/bake
     {digest, flow, version, seed, edit, pairs, limb, exclusions}      {edit: k}
POST /api/c/{collection}/place/propose
     {digest, flow, version, seed, points}      {arm, pairs}, no-store
GET  /api/tags   ·   GET /api/fields?flow=
GET  anything else                                 the bundle's index.html
```
"""

import asyncio
import threading
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from contextlib import AbstractContextManager, asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from types import FrameType
from typing import Any, TypeGuard

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from isekai.foundation.artifacts import (
    Renders,
    renders_of,
)
from isekai.foundation.flow import Flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    REVIEW,
    assign,
    edit_files,
    edit_numbers,
    find_run,
    is_seed,
    is_version,
    open_run,
)
from isekai.interface.drafting import draft_from_image, refuse_image_drafts
from isekai.interface.ui import events, library
from isekai.interface.ui.billing import Billing
from isekai.interface.ui.jobs import Jobs
from isekai.interface.ui.routes.common import (
    _approved,
    _cell_out,
    _decimal,
    _hub,
    _photograph,
    _renders_out,
    _saved,
    _strings,
    _untagged,
    _whole,
)
from isekai.interface.ui.routes.keys import BAKE_KEYS as BAKE_KEYS
from isekai.interface.ui.routes.keys import INK_KEYS as INK_KEYS
from isekai.interface.ui.routes.keys import OUTLINE_KEYS as OUTLINE_KEYS
from isekai.interface.ui.routes.keys import PREVIEW_KEYS as PREVIEW_KEYS
from isekai.interface.ui.routes.keys import PROPOSE_KEYS as PROPOSE_KEYS
from isekai.interface.ui.routes.keys import STAGE1_KEYS as STAGE1_KEYS
from isekai.interface.ui.routes.place import mount as place_mount
from isekai.interface.ui.routes.rendering import cell_event as cell_event
from isekai.interface.ui.routes.rendering import mount as render_mount
from isekai.interface.ui.routes.reviewing import _budget, _command
from isekai.interface.ui.routes.reviewing import mount as review_mount
from isekai.interface.ui.routes.stream import mount as stream_mount
from isekai.interface.ui.routes.tattoos import mount as tattoo_mount
from isekai.interface.ui.routes.vocabulary import RARE_BELOW as RARE_BELOW
from isekai.interface.ui.routes.vocabulary import mount as vocabulary_mount
from isekai.interface.ui.surface import _DECIMAL, Held, Surface, _version
from isekai.interface.wiring import Wiring
from isekai.pipeline import importing
from isekai.pipeline.generate import discard_render, image_of
from isekai.pipeline.review import (
    Revision,
    approve,
    cancel,
    discard,
    save_draft,
    token_budget,
    waiting_edit,
    withdraw,
)
from isekai.pipeline.review import state as review_state

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


def create_app(
    root: Path,
    wired: Wiring,
    *,
    flows: Sequence[str],
    bundle: Path,
    wire: Callable[[Path], Wiring],
    host: str,
    port: int,
    make_jobs: Callable[..., Jobs] = Jobs,
    file_response: Callable[..., Response] = FileResponse,
    save_draft: Callable[..., Path] = save_draft,
    approve: Callable[..., tuple[Path | None, list[str]]] = approve,
    precondition: Callable[..., None] = _precondition,
    draft_lock: AbstractContextManager[Any] | None = None,
) -> FastAPI:
    """Return the app's application, serving every collection of the library at `root`.

    `wire` builds one collection's wiring from its runs root, and is called on every
    request inside a collection, so the run-root guard holds for each (D19). `wired`
    supplies what every collection shares: the flows, the vocabulary and the table.
    `flows` are the hub's columns, the flows the surface offers.
    `host` and `port` are the address every request is checked against.
    `make_jobs` builds the jobs the app holds; a test passes its own.
    `file_response` answers the photographs and images; a test passes its own.
    `save_draft` writes a draft update; a test passes its own.
    `approve` writes an approval; a test passes its own.
    `precondition` refuses a draft that has moved; a test passes its own.
    `draft_lock` is held across each draft write; the app builds its own when
    none is passed.
    """
    broadcast = events.Broadcast()
    jobs = make_jobs(
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
    imports = importing.Imports(
        root,
        limit,
        lambda staged, state: broadcast.publish("file", {"staging": staged, **state}),
    )
    surface = Surface(
        root,
        wired,
        flows=flows,
        wire=wire,
        jobs=jobs,
        billing=billing,
        imports=imports,
        broadcast=broadcast,
        limit=limit,
        file_response=file_response,
        save_draft=save_draft,
        approve=approve,
        precondition=precondition,
        draft_lock=draft_lock if draft_lock is not None else threading.Lock(),
    )
    shared = surface.shared
    folder, held, offered = surface.folder, surface.held, surface.offered
    _rendering = surface.rendering
    rendered, baked, bake_image = surface.rendered, surface.baked, surface.bake_image

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

    @app.get("/api/staging/{staged}/files/{name}")
    def read_staged(staged: str, name: str) -> Response:
        """Serve a staged file full size, as it was cleaned."""
        served = _photograph(
            surface.file_response, importing.staged_file(imports.folder(staged), name)
        )
        served.headers["Cache-Control"] = "no-store"
        return served

    @app.delete("/api/staging/{staged}/files/{name}")
    def delete_staged(staged: str, name: str) -> dict[str, Any]:
        """Remove a read file from its import before the commit; refused once sealed."""
        imports.reader(staged).remove(name)
        return {}

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
        with surface.draft_lock:
            if review_state(one.directory(REVIEW)) == "approved":
                raise Refusal(
                    f"{one.run.id} is approved, and an approved sheet is never "
                    "edited in place; approval is the end of a review -- correct "
                    f"it with `{_command(one, 'review', '--new-version')}`, which "
                    "writes a fresh draft beside the approved artifact, and "
                    "reload: the input comes back re-opened and editable, with "
                    "its approved artifact still named"
                )
            surface.precondition(one, payload)
            written = surface.save_draft(one.run, one.flow.id, fields, renders)
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
        with surface.draft_lock:
            surface.precondition(one, payload or {})
            written, warnings = surface.approve(
                one.run,
                one.flow.id,
                one.flow.schema,
                shared.vocabulary(),
                excluded=shared.field_map().excluded,
                definition=one.flow,
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
        the draft or approval beneath it, null where nothing is. `cancelled` is
        false for a flow at its draft, which a cancel leaves unchanged.
        """
        one = held(collection, digest, flow)
        with surface.draft_lock:
            rendering = _rendering(collection)
            if rendering is not None:
                raise Refusal(
                    f"{rendering} Wait for it to end, then cancel the approval again."
                )
            left, changed = cancel(one.run, one.flow.id)
        return {"back": None if left is None else left.name, "cancelled": changed}

    @app.post("/api/c/{collection}/review/{digest}/{flow}/discard")
    def post_discard(
        collection: str, digest: str, flow: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Delete the waiting draft, as `review --discard` does; an approval refuses.

        **It states the draft update's precondition**, so a page deletes only the
        draft it last read, never one another tab has since edited.
        """
        one = held(collection, digest, flow)
        with surface.draft_lock:
            surface.precondition(one, payload or {}, "discard again")
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
        with surface.draft_lock:
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

    @app.get("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}")
    def read_render(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> dict[str, Any]:
        """Return one render's large view: the approval's filled fields beside it.

        It is headed by what the version was: the one it came from, a revision or
        a re-roll, and its count and seeds; or, where its `renders` no render
        takes, damaged, naming the file, with no count.
        """
        run, image, approval = rendered(collection, digest, flow, version, seed)
        _, fields = _approved(approval)
        number = _version(version)
        suffix = offered(flow).output_suffix
        listed = library.versions(run, flow)
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
            "fields": _filled(fields),
            "approved_at": _saved(approval),
            "came_from": held.came_from,
            "kind": held.kind,
            "count": held.count,
            "seeds": _decimal(held.seeds),
            "damaged": held.damaged,
            # The seed's edits by number, the chain the large view draws.
            "bakes": [asdict(one) for one in library.bakes(image.parent, seed)],
            # The newest older version that rendered this seed, or null.
            "compare": library.paired(run, flow, number, seed, suffix),
            # Every offered flow, this one first, assigned or not: a draft assigns.
            "targets": sorted(flows, key=lambda name: name != flow),
            # The source's images, a row per offered flow holding any, each oldest
            # version first, then by seed: the large view's walk and the pick.
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

        The picked is the left, this the right: the pair alone.
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
        right = _side(offered(flow), number, origin)
        left = _side(offered(other_flow), other_number, picked)
        return {
            "left": {"flow": other_flow, **left, "seed": str(other_seed)},
            "right": {"flow": flow, **right, "seed": str(seed)},
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
        right = _side(offered(flow), _version(version), origin)
        return {"left": None, "right": {"flow": flow, **right, "seed": str(seed)}}

    @app.get("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/image")
    def read_render_image(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> Response:
        """Serve the render's bytes, whole."""
        return surface.file_response(
            rendered(collection, digest, flow, version, seed)[1]
        )

    @app.get("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/thumb")
    def read_render_thumb(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> Response:
        """Serve the render's thumbnail, made in the library's cache the first time."""
        run, image, _ = rendered(collection, digest, flow, version, seed)
        return surface.file_response(
            library.thumbnail(root, run, image), media_type="image/jpeg"
        )

    @app.get("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/edit/{k}")
    def read_bake(
        collection: str, digest: str, flow: str, version: str, seed: int, k: str
    ) -> dict[str, Any]:
        """Return one bake's record: its state, what it was placed on and its time."""
        return asdict(baked(collection, digest, flow, version, seed, k)[1])

    @app.get(
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/edit/{k}/image"
    )
    def read_bake_image(
        collection: str, digest: str, flow: str, version: str, seed: int, k: str
    ) -> Response:
        """Serve a bake's image bytes, whole."""
        return surface.file_response(
            bake_image(collection, digest, flow, version, seed, k)[1]
        )

    @app.get(
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/edit/{k}/thumb"
    )
    def read_bake_thumb(
        collection: str, digest: str, flow: str, version: str, seed: int, k: str
    ) -> Response:
        """Serve a bake's thumbnail, made in the library's cache the first time."""
        run, image = bake_image(collection, digest, flow, version, seed, k)
        return surface.file_response(
            library.thumbnail(root, run, image), media_type="image/jpeg"
        )

    @app.delete("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}")
    def delete_render(
        collection: str, digest: str, flow: str, version: str, seed: int
    ) -> dict[str, Any]:
        """Delete the render and its thumbnails, as `discard` does, while none runs.

        The thumbnails go while the image still names them; then `withdraw`
        deletes the approval its last render leaves, older ones with no render and
        the newest's waiting draft, and, with no approval left, the flow's sheets.
        """
        run, image, _ = rendered(collection, digest, flow, version, seed)
        with surface.draft_lock:
            rendering = _rendering(collection)
            if rendering is not None:
                raise Refusal(
                    f"{rendering} Wait for it to end, then delete the render again."
                )
            library.drop_thumbnails(run, image)
            for number in edit_numbers(image.parent, seed):
                if (own := edit_files(image.parent, seed, number)[0]).is_file():
                    library.drop_thumbnails(run, own)
            discard_render(image)
            withdraw(run, flow, _version(version))
        return {"deleted": True}

    @app.get("/api/c/{collection}/sources/{name}")
    def read_source(collection: str, name: str) -> Response:
        """Serve a source's bytes, whole, with or without a run.

        One in a format the render does not read, placed by hand, is served as an
        upright JPEG of it, so the viewer shows what its thumbnail does.
        """
        source = library.source_files(folder(collection))(name)
        return _photograph(surface.file_response, source, other=library.source_jpeg)

    @app.get("/api/c/{collection}/sources/{name}/thumb")
    def read_source_thumb(collection: str, name: str) -> Response:
        """Serve a source's thumbnail, upright, made in the library's cache once."""
        source = library.source_files(folder(collection))(name)
        return surface.file_response(
            library.source_thumbnail(root, source), media_type="image/jpeg"
        )

    vocabulary_mount(app, surface)
    tattoo_mount(app, surface)
    place_mount(app, surface)
    render_mount(app, surface)
    stream_mount(app, surface)
    review_mount(app, surface)

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


def _side(flow: Flow, version: int, approval: Path) -> dict[str, Any]:
    """Return one side of a comparison as the page shows it."""
    body, fields = _approved(approval)
    remedy = f"restore it in {approval} by hand, then reload the page"
    for name in flow.schema.names:
        fields.setdefault(name, [])
    return {
        "version": version,
        "approved_at": _saved(approval),
        "renders": _renders_out(renders_of(approval, body, remedy)),
        "tokens": token_budget(fields, flow.schema, flow).total,
    }


def _filled(fields: Mapping[str, list[str]]) -> dict[str, list[str]]:
    """Return the fields that hold a tag.

    e.g. `{"a": ["x"], "b": []}` -> `{"a": ["x"]}`
    """
    return {name: tags for name, tags in fields.items() if tags}


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


def _images_out(images: Sequence[tuple[int, int]]) -> list[dict[str, Any]]:
    """Describe rendered images by version and decimal seed, as the page names them.

    e.g. [(1, 7)] -> [{"version": 1, "seed": "7"}]
    """
    return [{"version": version, "seed": str(seed)} for version, seed in images]


def _numbered(value: object) -> TypeGuard[int]:
    """Return whether a request's value is a version a run's file names can spell.

    e.g. 2 -> True, 1000 -> False
    """
    return _whole(value) and is_version(value)


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


class Server(uvicorn.Server):
    """uvicorn's server, ending every open stream as soon as a signal stops it."""

    def __init__(self, config: uvicorn.Config, broadcast: events.Broadcast) -> None:
        """Serve `config`, closing `broadcast` on the signal that stops it."""
        super().__init__(config)
        self._broadcast = broadcast

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        """Mark the streams closed, wake them on the loop, then stop as uvicorn does."""
        # A signal cannot take the broadcast lock; wake queues on the loop.
        self._broadcast.closed = True
        asyncio.get_running_loop().call_soon(self._broadcast.close)
        super().handle_exit(sig, frame)


def run(app: FastAPI, *, host: str, port: int) -> None:
    """Block, serving `app`, until the operator stops it.

    A thin wrapper so that `__init__.py` composes the surface without importing
    a web framework at module scope.
    """
    Server(
        uvicorn.Config(
            app, host=host, port=port, log_level="warning", timeout_graceful_shutdown=1
        ),
        app.state.broadcast,
    ).run()

"""The HTTP surface, and the entry to the modules that import a web framework.

`library.py` and `surface.py` import no web framework, so what they hold is
exercised by the main suite whether or not a server is installed. The modules of
`routes/` import FastAPI and this module mounts them, so
`tests/test_ui_api.py` opens with an `importorskip` for it. They hold the
vocabulary, tattoo library and place routes, `HubRoutes`, `StagingRoutes`,
`ImageRoutes`, `SourceRoutes`, `RenderRoutes`, `StreamRoutes` and
`ReviewRoutes`; `create_app` takes what a test replaces, builds the surface and
mounts each, while the guard, the refusal handler and the catch-alls are this
module's own.

**What this module owns, and what it does not.** It owns the guard on every
request, the mounting of each resource and the built bundle, and turning a
`Refusal` into a response. The join of caption, sheet, draft, approved and
budget into one payload is the review routes' own, in `routes/reviewing.py`. The
pipeline owns what a valid sheet is, each run file's shape and its filename,
when approval is legal, and what a token costs.

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
from pathlib import Path
from types import FrameType
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from isekai.foundation.refusal import Refusal
from isekai.interface.ui import events
from isekai.interface.ui.billing import Billing
from isekai.interface.ui.jobs import Jobs
from isekai.interface.ui.routes.common import REFUSED, _saved
from isekai.interface.ui.routes.hub import mount as hub_mount
from isekai.interface.ui.routes.images import mount as images_mount
from isekai.interface.ui.routes.place import mount as place_mount
from isekai.interface.ui.routes.rendering import mount as render_mount
from isekai.interface.ui.routes.reviewing import mount as review_mount
from isekai.interface.ui.routes.sources import mount as sources_mount
from isekai.interface.ui.routes.staging import mount as staging_mount
from isekai.interface.ui.routes.stream import mount as stream_mount
from isekai.interface.ui.routes.tattoos import mount as tattoo_mount
from isekai.interface.ui.routes.vocabulary import mount as vocabulary_mount
from isekai.interface.ui.surface import Held, Surface
from isekai.interface.wiring import Wiring
from isekai.pipeline import importing
from isekai.pipeline.review import (
    approve,
    save_draft,
)

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


MOUNTS: tuple[Callable[[FastAPI, Surface], None], ...] = (
    hub_mount,
    staging_mount,
    images_mount,
    sources_mount,
    vocabulary_mount,
    tattoo_mount,
    place_mount,
    render_mount,
    stream_mount,
    review_mount,
)


def _addressed_here(
    allowed: frozenset[str], origins: frozenset[str]
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """Return the middleware answering only requests addressed to `allowed`."""

    async def guard(
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

    return guard


def _bundle(app: FastAPI, bundle: Path) -> None:
    """Register the catch-alls and the assets' mount, after every resource."""

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

    app.middleware("http")(_addressed_here(allowed, origins))

    @app.exception_handler(Refusal)
    async def _refused(request: Request, refusal: Exception) -> JSONResponse:
        """Turn a `Refusal` into a response carrying its string, verbatim."""
        return JSONResponse({"refusal": str(refusal)}, status_code=REFUSED)

    for mount in MOUNTS:
        mount(app, surface)

    _bundle(app, bundle)
    return app


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

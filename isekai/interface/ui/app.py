"""The HTTP surface, and the only module in this package that imports the `ui` extra.

Kept to one file deliberately. `batch.py` performs the whole startup refusal
order and imports no web framework, so that order is exercised by the main suite
with the `ui` extra uninstalled; only what genuinely needs a server lives here,
and `tests/test_ui_api.py` opens with an `importorskip` for it.

**What this module owns, and what it does not.** It owns HTTP routing and status
codes, the join of caption, sheet, draft, approved and budget into one payload,
serving photograph bytes and the built bundle, the `rare` threshold -- which
exists nowhere else in this repository -- and turning a `Refusal` into a
response. The pipeline owns what a valid sheet is, the artifact envelope and its
filename, when approval is legal, and what a token costs.

**Three write functions reach a run directory, all of stage ③'s**: `review()` at
startup, `save_draft()` on autosave and `approve()` on the button. Nothing here
builds an artifact body or an artifact filename, and `tests/test_ui.py`'s grep is
what keeps that at three (design.md D11).

**uvicorn is imported here too, and not in `__init__.py`.** `serve()` there
calls this module's `run()` instead, so the whole `ui` extra is reached from this
one file and `python -m isekai`'s import graph never reaches it at all. Nothing
is suppressed for it anywhere: the `dev` group pins `fastapi` and `uvicorn`, so
`uv sync --locked` installs both and the import resolves in the environment the
gate runs in.

**The flow is in none of the paths.** The batch has exactly one and
`/api/batch` names it; a URL here is a contract between a server and a Vue app in
the same repository, so widening it later is a find-and-replace. The paths are
`GET /api/batch`, `/api/tags`, `/api/fields`, `/api/inputs/{identifier}` and
`/api/inputs/{identifier}/photo`, `PUT /api/inputs/{identifier}/draft` and
`POST /api/inputs/{identifier}/approve`, with the built bundle mounted at `/`.
"""

from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import read_artifact
from isekai.interface.ui.batch import Batch, Input
from isekai.pipeline.review import TokenBudget, approve, save_draft, token_budget

# The dropdown's `· rare` marker. This number exists nowhere else in the
# repository: the vocabulary ranks by post count and never calls anything rare,
# so the threshold is the surface's own judgement about what an operator should
# hesitate over, and it is stated here rather than duplicated in TypeScript.
RARE_BELOW = 2000

# Enough rows to choose from without the dropdown becoming a list to read. The
# footer states the true match count, so narrowing the fragment stays the way to
# see fewer rather than scrolling.
DEFAULT_LIMIT = 10

# A `Refusal` is the pipeline declining a well-formed request because of what is
# on disk -- an approved input, a changed field set, a tag outside the vocabulary
# -- which is a conflict with state rather than a malformed request. One code for
# all of them, because the page shows the string verbatim in one header line and
# never branches on the number (design.md D6).
REFUSED = 409

# A request that did not come from this machine's own browser, addressed to this
# server's own address. Not a `Refusal`: nothing about the run directory is in
# conflict, the request is simply not one this surface answers, so it carries no
# string for the page and never reaches a handler.
FORBIDDEN = 403

# The names a loopback listener answers to. `Host: evil.example` resolving to
# 127.0.0.1 is the whole of the DNS-rebinding attack against an unauthenticated
# local API, and it is defeated by comparing the name rather than the socket.
# These four are the only names an attacker cannot make point anywhere: they are
# reserved, so allowing the alias the operator actually types costs nothing.
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


def authorities(host: str, port: int) -> frozenset[str]:
    """Return every `Host` value this server, bound to `host:port`, answers to.

    One function rather than two comparisons, because `Origin` is checked
    against exactly the same set with a scheme in front of it -- and a header
    pair that is allowed to disagree about what the server's address is has no
    security value at all.
    """
    names = LOOPBACK if host in LOOPBACK else frozenset({host})
    return frozenset(f"{name}:{port}" for name in names)


def create_app(batch: Batch, *, host: str, port: int) -> FastAPI:
    """Return the review surface's application, bound to one established batch.

    `host` and `port` are the address the server binds, and they are parameters
    rather than the module constant because they are what every request is
    checked against: an app that inferred its own address could not be tested
    for rejecting someone else's.
    """
    app = FastAPI(title="isekai review", docs_url=None, redoc_url=None)
    allowed = authorities(host, port)
    origins = frozenset(f"http://{one}" for one in allowed)

    @app.middleware("http")
    async def _addressed_here(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Answer only a request addressed to this server, from this server's page.

        **The first middleware in this repository, and it guards all seven
        routes** -- which is why it is a middleware rather than a dependency:
        the static mount is not a route and would not carry one, and a route
        added later would have to remember to.

        This API is unauthenticated by design, so the browser's own origin rules
        are the whole of its protection, and both halves of that are checked
        here. `Host` defeats DNS rebinding, where a page on an attacker's domain
        resolves that domain to 127.0.0.1 and talks to this port with the
        browser's full cooperation. `Origin`, when the browser sends one,
        defeats the cross-site write: a `PUT` from another page carries its
        origin and never this one's.
        """
        if request.headers.get("Host", "") not in allowed:
            return JSONResponse({"refusal": "not addressed here"}, FORBIDDEN)
        origin = request.headers.get("Origin")
        if origin is not None and origin not in origins:
            return JSONResponse({"refusal": "not from this page"}, FORBIDDEN)
        return await call_next(request)

    @app.exception_handler(Refusal)
    async def _refused(request: Request, refusal: Exception) -> JSONResponse:
        """Turn a `Refusal` into a response carrying its string, verbatim."""
        return JSONResponse({"refusal": str(refusal)}, status_code=REFUSED)

    @app.get("/api/batch")
    def read_batch() -> dict[str, Any]:
        """Describe the batch: its flow, its schema, its inputs and their state."""
        # **The count is every input holding an approved artifact**, which is
        # what `Batch.approved_count` reads off the directory -- and `re-opened`
        # holds one. Deriving it from `status == "approved"` was the trap: that
        # agreed with the directory only while the two states were the only two,
        # and the third ends the coincidence (design.md D5). Read off `state()`
        # rather than by walking the directory a second time, so the count and
        # the statuses cannot disagree by construction rather than by luck.
        summaries = [_summary(batch, held) for held in batch.inputs]
        return {
            "flow": batch.flow.id,
            "schema": list(batch.flow.schema.names),
            "vocabulary": len(batch.vocabulary),
            "approved": sum(1 for held in summaries if held["status"] != "draft"),
            "inputs": summaries,
        }

    @app.get("/api/tags")
    def read_tags(q: str = "", limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
        """Answer a tag fragment from the vocabulary the pipeline itself searches.

        The server ranks and the client does not. Shipping all 8,106 tags would
        put a second copy of the ranking rule in TypeScript, and `total` is the
        true match count so the dropdown can say how narrow the fragment got.
        """
        fragment = q.strip()
        found = batch.vocabulary.search(fragment) if fragment else []
        return {
            # The count is bound where it is used. The `is not None` guard this
            # once carried dropped no row -- `count()` returns `int` -- and read
            # as though some fragment match might have no count (v0.18 R11).
            "matches": [
                {
                    "tag": tag,
                    "posts": (posts := batch.vocabulary.count(tag)),
                    "rare": posts < RARE_BELOW,
                }
                for tag in found[: max(limit, 0)]
            ],
            "total": len(found),
        }

    # Built once, because neither input can move: the table and the vocabulary are
    # frozen for the life of the app, so rebuilding ~3,000 rows per request would
    # re-rank a constant. `/api/tags` is not built this way because its answer
    # depends on the fragment.
    candidates = {
        "fields": {
            name: [
                {"tag": tag, "posts": batch.vocabulary.count(tag)}
                for tag in batch.vocabulary.rank(batch.field_map.group(name))
            ]
            for name in batch.flow.schema.names
        }
    }

    @app.get("/api/fields")
    def read_fields() -> dict[str, Any]:
        """Answer every candidate tag for every criterion the acting flow declares.

        **The whole table in one response, once.** ~40 KB for a couple of thousand
        tags, so the overlay filters with no round trip per keystroke, and a
        sitting that never opens the reference pays nothing because this is not on
        `/api/batch`'s payload. Riding that one would tax every page load for a
        surface that may never open; a `?field=` form would be a round trip per
        field and would pre-build a per-field ranking that is deliberately
        deferred (design.md D13).

        **Ordered by post count and cut at nothing.** Through `Vocabulary.rank`,
        which is the same call `/api/tags` ranks through, so no second ranking
        enters the system rather than merely no second *rule*. A cutoff was
        measured against the operator's own approved sheets and refused:
        `>10,000` hides ten of the 113 tags he approved, and the ones he reaches
        for -- `gold bracelet` 2,081, `train station` 2,180 -- are in the tail
        (design.md D7).

        **A declared field the table holds nothing for is present and empty**, and
        the excluded list is not served at all. An empty group is the honest answer
        for a criterion the vocabulary cannot express, and a missing row is
        indistinguishable from one nobody has authored yet; the excluded list is an
        assertion about the table rather than material to browse, and showing the
        tags that are never an answer is the opposite of what the reference is for.
        """
        return candidates

    @app.get("/api/inputs/{identifier}")
    def read_input(identifier: str) -> dict[str, Any]:
        """Return everything the page shows for one input, joined into one payload.

        The fields come from the draft while one exists and from the approved
        artifact once it does not, which is what makes an input approved in an
        earlier sitting open read-only rather than empty.
        """
        held = batch.find(identifier)
        draft = batch.draft_path(held)
        approved = batch.approved_path(held)
        state = batch.state(held)
        # The draft while one exists, the approved artifact once it does not.
        # That is what makes an input approved in an earlier sitting open with
        # its sheet rather than empty (design.md D5).
        holding = draft if draft is not None else approved
        fields: dict[str, list[str]] = (
            {
                name: list(tags)
                for name, tags in read_artifact(holding)["fields"].items()
            }
            if holding is not None
            else {}
        )
        budget = token_budget(fields, batch.flow.schema, batch.flow)
        caption = batch.caption_path(held)
        return {
            "id": held.id,
            "width": held.width,
            "height": held.height,
            "caption": str(read_artifact(caption)["prose"]) if caption else None,
            # Both lists ride on this payload rather than on endpoints of their
            # own, and both are `null` where the artifact is absent -- which is
            # three legitimate states, none of them a failure (design.md D20).
            "wd14": _wd14(batch, held),
            "tags": _tags(batch, held),
            "fields": fields,
            # **Approval with nothing newer beside it is what makes a sheet
            # read-only**, which is precisely `state() == "approved"`. Not the
            # absence of a draft, which the rail never keyed on; and not
            # approval alone, which `v0.22.1` used and which made
            # `review --new-version` write a draft this page would not edit
            # (design.md D5).
            "readonly": state == "approved",
            "draft": draft.name if draft else None,
            "approved": approved.name if approved else None,
            "saved": _saved(draft),
            # The approved artifact's own time, which the draft's cannot stand
            # in for: `approve()` unlinks the draft, so once an input is
            # approved `saved` has nothing left to report.
            "approved_at": _saved(approved),
            "budget": _budget(budget),
        }

    @app.get("/api/inputs/{identifier}/photo")
    def read_photo(identifier: str) -> FileResponse:
        """Serve the photograph's bytes, whole. `image.py` reads headers, not pixels."""
        return FileResponse(batch.find(identifier).run.photo)

    @app.put("/api/inputs/{identifier}/draft")
    def put_draft(identifier: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Replace the draft's values in place, through the one function that owns it.

        The whole draft, every time. There is no Save control on the page and no
        partial update here: a debounced `PUT` of everything is what makes the
        receipt the page shows true.

        **Two preconditions, and both answer `409`.** An input that is approved
        **and holds no later draft** refuses an update at all: an approved sheet
        is never edited in place, and approval is the end of a review. An input
        re-opened with `review --new-version` is not that state and is accepted,
        which is what the verb writes the draft for. And an update whose `saved`
        does not match the draft on disk refuses, because the page autosaves on a
        debounce and two overlapping `PUT`s were free to commit in the order the
        server happened to finish them -- last write wins, where "last" is not
        the operator's last keystroke (design.md D6).
        """
        held = batch.find(identifier)
        if batch.state(held) == "approved":
            raise Refusal(
                f"{identifier} is approved, and an approved sheet is never "
                "edited in place; approval is the end of a review -- correct it "
                f"with `python -m isekai review --flow {batch.flow.id} "
                "--new-version`, which writes a fresh draft beside the approved "
                "artifact, and reload: the input comes back re-opened and "
                "editable, with its approved artifact still named"
            )
        _precondition(batch, held, payload)
        fields = {
            name: [str(tag) for tag in tags]
            for name, tags in dict(payload.get("fields", {})).items()
        }
        written = save_draft(held.run, batch.flow.id, fields)
        budget = token_budget(fields, batch.flow.schema, batch.flow)
        return {
            "draft": written.name,
            "saved": _saved(written),
            "budget": _budget(budget),
        }

    @app.post("/api/inputs/{identifier}/approve")
    def post_approve(identifier: str) -> dict[str, Any]:
        """Validate and approve the draft, through the only writer of an approval."""
        held = batch.find(identifier)
        written, warnings = approve(
            held.run, batch.flow.id, batch.flow.schema, batch.vocabulary
        )
        return {
            "approved": written.name if written else None,
            "warnings": warnings,
            "at": _saved(written),
        }

    # Mounted last, so every `/api/` path above wins. `html=True` is what makes a
    # reload of any address serve the page rather than a 404.
    app.mount("/", StaticFiles(directory=batch.bundle, html=True), name="bundle")
    return app


def _summary(batch: Batch, held: Input) -> dict[str, Any]:
    """Describe one input for the rail: its size, and where it is in stage ③.

    The state is `Batch.state`'s and is not recomputed here. `draft` holds no
    approved artifact; `approved` holds one and nothing newer; `re-opened` holds
    one *and* a later draft, which is what `review --new-version` writes and the
    only state in which the form is offered over an approved input.
    """
    return {
        "id": held.id,
        "width": held.width,
        "height": held.height,
        "status": batch.state(held),
    }


def _wd14(batch: Batch, held: Input) -> list[dict[str, Any]] | None:
    """Return the local tagger's scored list for the page, or None if absent.

    Stored sorted by confidence descending, and passed through in that order:
    the sort is what makes a wrong tag arrive pre-refuted by the right one above
    it, so re-ordering here would throw away the reason the number is shown.
    """
    path = batch.wd14_path(held)
    if path is None:
        return None
    found: Any = read_artifact(path)["tags"]
    return [
        {"tag": str(one["tag"]), "confidence": float(one["confidence"])}
        for one in found
    ]


def _tags(batch: Batch, held: Input) -> list[dict[str, Any]] | None:
    """Return the hosted tagger's committable tags for the page, or None if absent.

    **Filtered to what the vocabulary carries, and the filter is v0.20's
    acceptance rather than a preference.** On the acceptance batch roughly nine
    in ten of this model's tags were outside the vocabulary -- `fashion
    photography`, `centered subject`, `detailed textures in lace fabric` -- and
    could be committed to no field at all. The operator's verdict on the
    unfiltered list was that only the marked ones carried value, so the rest are
    attention spent on the busiest pane in the surface (design.md D29).

    **Filtered on the way to the page and never on the way to disk.** The
    artifact keeps every tag the model returned; that is `tagging`'s rule and
    nothing here touches it. Narrowing the *record* would make it disagree with
    what the model actually said, and being able to look behind the router is
    why it exists.

    Membership is decided here for the reason it always was: `/api/tags` answers
    a fragment query and has no membership form, so asking per tag would be one
    round trip each, and the vocabulary is already held by this process.

    The local tagger's list is **not** filtered, and the asymmetry is the whole
    point -- it is scored against the vocabulary it emits, so every tag it
    returns is committable by construction.
    """
    path = batch.tags_path(held)
    if path is None:
        return None
    listed: Any = read_artifact(path)["tags"]
    # One `str()` and one lookup per tag. `count()` normalises the spelling and
    # hits the same mapping `__contains__` does, so asking both questions
    # separately would normalise a forty-tag list eighty times for one answer --
    # and they are not the same question: a tag the vocabulary carries with a
    # count of zero is *in* it, so membership cannot be read off the number.
    # Deduplicated, and **only here**. `OfferedTag` is `{tag, posts}` where
    # `posts` is a pure function of `tag`, so a repeat is a byte-identical
    # object carrying no information -- and it was a duplicate Vue key.
    # `tagging:output:the-list-is-stored-unnarrowed` forbids canonicalising,
    # filtering against a vocabulary and re-ordering, none of which this is, and
    # the artifact on disk is untouched either way. `_wd14` must **not** get the
    # same treatment: `ScoredTag` is `{tag, confidence}`, where two rows can
    # legitimately differ (design.md D7).
    # `dict.fromkeys` preserves order, so the dedup is visible in the iterator
    # rather than spread across a parallel set and a two-clause condition.
    return [
        {"tag": name, "posts": batch.vocabulary.count(name)}
        for name in dict.fromkeys(str(tag) for tag in listed)
        if name in batch.vocabulary
    ]


def _precondition(batch: Batch, held: Input, payload: Mapping[str, Any]) -> None:
    """Refuse an update written against a draft that has since moved on disk.

    **`st_mtime` is the precondition because nothing else exists.** The draft
    carries no timestamp, no revision counter and no digest; `schema.version` is
    the constant `1`, an artifact *format* version, and `save_draft` never
    advances the filename's `NNN` by design. A `revision` int in the body is the
    correct answer and changes the artifact shape, which `read_artifact` refuses
    for any unknown schema -- that touches every reader in the package and is
    not a patch. A lock around `save_draft` fixes nothing: out-of-order *sends*
    still commit out of order (design.md D6).

    **A payload carrying no `saved` states no precondition**, and is allowed:
    the mtime is already on the wire as the field every response returns, so a
    client that echoes it gets the check and one that cannot has the behaviour
    it had before.
    """
    offered = payload.get("saved")
    if offered is None:
        return
    draft = batch.draft_path(held)
    if draft is not None and _saved(draft) != offered:
        raise Refusal(
            f"{draft.name} changed since this page last read it; another tab or "
            "another save got there first -- reload the input to see what is on "
            "disk, then make the correction again"
        )


def _budget(budget: TokenBudget) -> dict[str, Any]:
    """Describe a token budget. One spelling, so two endpoints cannot disagree."""
    return {
        "total": budget.total,
        "per_field": dict(budget.per_field),
        "overhead": budget.overhead,
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
    the `ui` extra at module scope.
    """
    uvicorn.run(app, host=host, port=port, log_level="warning")

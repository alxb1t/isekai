"""The render and jobs routes: prepare, stop, the offer, the quote, the sessions."""

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from isekai.boundary.gpu import keyed
from isekai.foundation.flow import Flow, load_flow, tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import REVIEW, Run, approved_versions, edit_at
from isekai.interface import render
from isekai.interface.ui import library
from isekai.interface.ui.jobs import KINDS, plan
from isekai.interface.ui.routes.common import _cell_out, _strings, _whole
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface
from isekai.pipeline.edit import image_of as edit_image_of


class RenderRoutes:
    """The routes that start, quote and stop the prepare and render jobs."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose jobs, billing and folders the routes read."""
        self.surface = surface

    def post_prepare(self, collection: str) -> dict[str, Any]:
        """Start Prepare over every assigned cell with no sheet, as one job.

        The local model server is asked first, so a job that could not run
        starts nothing.
        """
        found = self.surface.folder(collection)
        grid = library.hub(found, self.surface.flows, self.surface.wired.flows_dir)
        loaded = {
            flow: load_flow(flow, self.surface.wired.flows_dir)
            for flow in self.surface.flows
        }
        steps = plan(
            library.unprepared(grid), {flow: one.tagger for flow, one in loaded.items()}
        )
        cell = cell_event(found, grid, loaded)
        return {"job": self.surface.jobs.prepare(collection, found, steps, cell)}

    def post_stop(self, kind: str) -> dict[str, Any]:
        """Interrupt `kind`'s running stage; no later one starts, the other runs on."""
        if kind not in KINDS:
            raise Refusal(f"there is no {kind} job: stop `prepare` or `render`")
        return {"job": self.surface.jobs.stop(kind)}

    def quoted(
        self, names: Sequence[str] | None, without: object = None
    ) -> tuple[dict[str, Path], render.Quote, dict[str, Any], list[Path]]:
        """Return the quoted folders, quote, dialog's view and photographs taken out.

        With no names, every collection, in the Library's order. Only those the
        quote keeps, short of images, refusing a count or holding a bake, are
        returned, and only
        what `without` takes out of them.
        """
        if names is None:
            shelf = library.rows(
                self.surface.root, self.surface.flows, self.surface.wired.flows_dir
            )
            asked = [row.name for row in shelf if row.collection]
        else:
            asked = list(dict.fromkeys(names))
        found = {name: self.surface.folder(name) for name in asked}
        taken = _taken_out(without, found)
        made = render.quote(
            [one / library.RUNS for one in found.values()], self.surface.wired, taken
        )
        found = {
            name: one
            for name, one in found.items()
            if one / library.RUNS in made.shorts
        }
        kept = {one / library.RUNS for one in found.values()}
        taken = [path for path in taken if path.parent.parent in kept]
        disabled = self._held() or (
            made.blocked if asked else "Tick a collection to render."
        )
        return (
            found,
            made,
            _quote(found, made, disabled, self.surface.wired.flows_dir),
            taken,
        )

    def _held(self) -> str | None:
        """Return what holds Render back in any collection: a render, a pod, no key."""
        if self.surface.jobs.running("render"):
            return "A render session is running."
        if self.surface.billing.state()["pod"]:
            return "A pod may still be billing."
        if not keyed(self.surface.wired.session):
            return (
                "No RunPod key: add RUNPOD_API_KEY to .env, then start "
                "`uv run --env-file .env python -m isekai ui` again."
            )
        return None

    def short_of(self, found: Path) -> render.Short:
        """Return what a collection folder's approvals lack, as rendering counts it."""
        runs = found / library.RUNS
        return render.short(runs, render.run_ids(runs), self.surface.wire(runs))

    def bakes_in(self, found: Path) -> int:
        """Return how many bakes a collection folder holds, none taken out."""
        runs = found / library.RUNS
        return render.edits_of(
            runs,
            render.run_ids(runs),
            tracked_flows(self.surface.wired.flows_dir),
            (),
        ).count

    def read_render_offer(self, collection: str) -> dict[str, Any]:
        """Return how many images and bakes a collection holds, and why Render is off.

        It prices nothing; the counts are the render stage's own. `others` and
        `other_bakes` are what every other collection lacks and holds queued, which
        the same dialog renders. `refused` is why an approval's count cannot be
        read, or null: the bar shows it with none short.
        """
        here = self.surface.folder(collection)
        short = self.short_of(here)
        elsewhere = [
            child
            for child in library.listed(self.surface.root)
            if library.is_collection(child) and child.name != collection
        ]
        others = sum(sum(self.short_of(child).images.values()) for child in elsewhere)
        bakes = self.bakes_in(here)
        other_bakes = sum(self.bakes_in(child) for child in elsewhere)
        # Nothing short here is no reason while another collection is short or holds
        # a bake.
        refused = short.refused[0] if short.refused else None
        busy = short.lines or others or bakes or other_bakes
        idle = None if busy else short.blocked
        return {
            "disabled": self._held() or refused or idle,
            "images": sum(short.images.values()),
            "others": others,
            "bakes": bakes,
            "other_bakes": other_bakes,
            "refused": short.refused[0] if short.refused else None,
        }

    def post_quote(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Quote one render of the named collections, its limit and its price at most.

        `collections` names them; absent, every collection short of images or
        holding a bake is quoted. `without` lists each `{collection, run, flow}`
        taken out of it. It rents nothing; only the render's own `POST` does.
        """
        names = (payload or {}).get("collections")
        if names is not None and not _strings(names):
            raise Refusal(
                "the quote names no list of collections; close Render and open it again"
            )
        return self.quoted(names, (payload or {}).get("without"))[2]

    def post_render(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Start the render job the quote of `collections` describes, or refuse why not.

        The quote is taken again here, so what renders is what is on disk now; a
        limit longer than the one the dialog showed, `limit_s`, or another number
        of images than its `images` or of bakes than its `bakes`, is refused, so
        nothing renders past what the operator agreed to. What `without` takes out
        stays out of the render.
        """
        body = payload or {}
        reopen = "close Render and open it again to read"
        names = body.get("collections")
        if not _strings(names) or not names:
            raise Refusal(f"the confirmation names no collections; {reopen} the quote")
        found, made, described, taken = self.quoted(names, body.get("without"))
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
        shown_bakes = body.get("bakes")
        if not _whole(shown_bakes):
            raise Refusal(f"the confirmation names no quoted bakes; {reopen} the quote")
        if made.bakes != shown_bakes:
            raise Refusal(
                f"the quote changed since it was shown: it now renders {made.bakes} "
                f"bakes, not {shown_bakes}; {reopen} it"
            )
        job = self.surface.jobs.render(
            found,
            limit=made.estimate.limit_s,
            total=made.images,
            keep_open=bool(body.get("keep_open")),
            without=taken,
        )
        return {"job": job}

    def running_sessions(self) -> dict[str, Any]:
        """Read live disk records across collections, including terminal renders."""
        found = []
        for child in library.listed(self.surface.root):
            if library.is_collection(child):
                found += [
                    {"collection": child.name, **one} for one in library.running(child)
                ]
        return {"sessions": found}

    def read_session(self, collection: str, name: str) -> dict[str, Any]:
        """Return one render session's record; the slot holds its volume steps."""
        return library.session(self.surface.folder(collection), name)

    def post_check(self) -> dict[str, Any]:
        """Ask gpunit again; an alert clears only when its records say gone."""
        return {"billing": self.surface.billing.check()}


def cell_event(
    found: Path, grid: library.Hub, loaded: Mapping[str, Flow]
) -> Callable[[Mapping[str, Any]], list[dict[str, Any]]]:
    """Return what turns a progress line into `cell` events, each stage read from disk.

    A line naming a flow gives that cell's event; a line naming no flow, a
    photograph's stage, gives one per assigned flow, every cell reading the one
    description (D17). A line naming a run or a flow the job did not start gives none.
    """
    collection = grid.name
    sources = {one.run.id: one.name for one in grid.sources if one.run}

    def cells(line: Mapping[str, Any]) -> list[dict[str, Any]]:
        run_id, named = str(line.get("run")), line.get("flow")
        if run_id not in sources:
            return []
        run = Run(run_id, found / library.RUNS / run_id)
        if named is None:
            flows = [flow for flow in loaded if run.directory(flow).is_dir()]
        else:
            flows = [str(named)] if str(named) in loaded else []
        return [
            {
                "collection": collection,
                "source": sources[run_id],
                "flow": flow,
                "stage": line.get("stage"),
                "state": line.get("state"),
                "message": line.get("message"),
                "cell": _cell_out(library.stage(run, loaded[flow])),
            }
            for flow in flows
        ]

    return cells


def _quote(
    found: Mapping[str, Path],
    made: render.Quote,
    disabled: str | None,
    flows_dir: Path,
) -> dict[str, Any]:
    """Describe a quote as the Render dialog shows it: a row per collection."""
    return {
        "collections": [
            _quoted_row(
                name,
                one,
                made.shorts[one / library.RUNS],
                made.edits[one / library.RUNS],
                flows_dir,
            )
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
    name: str,
    found: Path,
    short: render.Short,
    edits: render.Edits,
    flows_dir: Path,
) -> dict[str, Any]:
    """Describe one collection's part of a quote, each run by its source.

    Each bake is listed beside the images, by its photograph, the approval that
    holds it, its seed and its number.
    """
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
            "run": run_id,
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
    bakes = []
    for record in edits.records:
        baked, flow, version, seed, k = edit_at(edit_image_of(record))
        bakes.append(
            {
                "flow": flow,
                **source(baked.id, flow),
                "version": version,
                "seed": str(seed),
                "k": k,
            }
        )
    return {
        "collection": name,
        "images": sum(short.images.values()),
        "flows": flows,
        "bakes": bakes,
        "refused": short.refused[0] if short.refused else None,
    }


def _taken_out(value: object, found: Mapping[str, Path]) -> list[Path]:
    """Return the `<runs>/<run-id>/<flow>` each entry of a quote's `without` names.

    Refuse an entry naming a run or flow its collection, one of `found`, does not
    hold, so no path the page sends reaches the disk unchecked.
    e.g. [{"collection": "b", "run": "0d4b…_ada", "flow": "f"}] -> [b/runs/0d4b…_ada/f]
    """
    if value is None:
        return []
    entries = [
        [one.get(key) for key in ("collection", "run", "flow")]
        if isinstance(one, dict)
        else [None]
        for one in (value if isinstance(value, list) else [None])
    ]
    named = [entry for entry in entries if _strings(entry)]
    if len(named) < len(entries):
        raise Refusal(
            "the quote names no list of photographs taken out; "
            "close Render and open it again"
        )
    taken = []
    for collection, run_id, flow in named:
        runs = found[collection] / library.RUNS if collection in found else None
        if (
            runs is None
            or run_id not in render.run_ids(runs)
            or flow not in Run(run_id, runs / run_id).flows
        ):
            raise Refusal(
                f"the quote takes out {run_id}/{flow}, which {collection} does not "
                "hold; close Render and open it again"
            )
        taken.append(runs / run_id / flow)
    return taken


ROUTES = (
    Route("POST", "/api/c/{collection}/prepare", "post_prepare"),
    Route("POST", "/api/jobs/{kind}/stop", "post_stop"),
    Route("GET", "/api/c/{collection}/render", "read_render_offer"),
    Route("POST", "/api/render/quote", "post_quote"),
    Route("POST", "/api/render", "post_render"),
    Route("GET", "/api/sessions/running", "running_sessions"),
    Route("GET", "/api/c/{collection}/sessions/{name}", "read_session"),
    Route("POST", "/api/billing/check", "post_check"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the render and jobs routes on `app`, over `surface`."""
    register(app, RenderRoutes(surface), ROUTES)

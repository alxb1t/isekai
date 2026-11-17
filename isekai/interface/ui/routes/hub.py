"""The hub's routes: the library's list, a collection's grid, and the assign route."""

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import assign, find_run, open_run
from isekai.interface.ui import library
from isekai.interface.ui.routes.common import _cell_out, _hub, _strings
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface


class HubRoutes:
    """The routes that list the library and tick a flow for a collection's sources."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose folders and flows the routes read."""
        self.surface = surface

    def read_library(self) -> dict[str, Any]:
        """List the library's folders, collections by their newest file first."""
        rows = library.rows(
            self.surface.root, self.surface.flows, self.surface.wired.flows_dir
        )
        return {"rows": [asdict(row) for row in rows]}

    def read_hub(self, collection: str) -> dict[str, Any]:
        """Return a collection's grid: its sources by offered flow, each cell's stage.

        Read from the run directories on every request, so it follows a verb run
        in the terminal while the page is open.
        """
        return _hub(
            library.hub(
                self.surface.folder(collection),
                self.surface.flows,
                self.surface.wired.flows_dir,
            )
        )

    def post_assign(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Tick a flow for sources, or untick it, through the run's own `assign`.

        Each source is answered on its own: one refused untick leaves the others
        done, and its refusal comes back beside their cells.
        """
        found = self.surface.folder(collection)
        flow = str(payload.get("flow"))
        if flow not in self.surface.flows:
            raise Refusal(
                f"{flow!r}: not a flow this surface offers; the flows it offers "
                f"are {', '.join(self.surface.flows)} -- reload the hub"
            )
        names = payload.get("sources")
        if not _strings(names):
            raise Refusal("the request's `sources` is not a list of source names")
        remove = payload.get("remove") is True
        loaded = self.surface.offered(flow)
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


ROUTES = (
    Route("GET", "/api/library", "read_library"),
    Route("GET", "/api/c/{collection}/hub", "read_hub"),
    Route("POST", "/api/c/{collection}/assign", "post_assign"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the hub's routes on `app`, over `surface`."""
    register(app, HubRoutes(surface), ROUTES)

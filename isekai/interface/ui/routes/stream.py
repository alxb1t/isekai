"""The events stream: the job slots, a hub and an import's files, then changes."""

from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from isekai.foundation.refusal import Refusal
from isekai.interface.ui import events, library
from isekai.interface.ui.jobs import KINDS
from isekai.interface.ui.routes.common import _hub
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface


class StreamRoutes:
    """The route that streams what the jobs, the billing and the library report."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose jobs, billing and imports the stream reads."""
        self.surface = surface

    def read_events(
        self, collection: str | None = None, staging: str | None = None
    ) -> StreamingResponse:
        """Stream the job slots, `collection`'s hub, `staging`'s files, then changes.

        A reload or a second tab gets the whole truth at once. A collection or an
        import it cannot read is left out of the snapshot, never refused.
        """
        # An import it no longer holds is left out rather than refused: the page's
        # one stream would never open again after a refused connect.
        try:
            held = self.surface.imports.reader(staging) if staging is not None else None
        except Refusal:
            held = None

        def snapshot() -> dict[str, Any]:
            found = {
                "jobs": {kind: self.surface.jobs.slot(kind) for kind in KINDS},
                "billing": self.surface.billing.state(),
            }
            if collection is not None:
                # A collection it cannot read is left out: the screen's own read of it
                # shows the refusal, and the page keeps its stream.
                try:
                    grid = library.hub(
                        self.surface.folder(collection),
                        self.surface.flows,
                        self.surface.wired.flows_dir,
                    )
                except Refusal:
                    pass
                else:
                    found["hub"] = _hub(grid)
            if held is not None:
                found["files"] = held.files()
            return found

        return StreamingResponse(
            events.stream(
                self.surface.broadcast, snapshot, collection=collection, staging=staging
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )


ROUTES = (Route("GET", "/events", "read_events"),)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the events stream on `app`, over `surface`."""
    register(app, StreamRoutes(surface), ROUTES)

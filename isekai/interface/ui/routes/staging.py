"""The staging routes: an import's folder, its files, its cancel and its commit."""

from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool

from isekai.foundation.refusal import Refusal
from isekai.interface.ui.routes.common import _photograph, _strings
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface
from isekai.pipeline import importing


class StagingRoutes:
    """The routes that open, fill, cancel and commit an import."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose imports and file response the routes read."""
        self.surface = surface

    def post_staging(self) -> dict[str, Any]:
        """Open an import: a staging folder under the library's `.staging/`."""
        return {"id": self.surface.imports.open()}

    async def put_file(
        self, staged: str, name: str, request: Request
    ) -> dict[str, Any]:
        """Hold an upload for its import's reader; answer its id and `waiting`.

        The body is the file. One past the limit is refused by its declared
        length before its body is read. Its reading is reported on the stream,
        under its upload id.
        """
        held = self.surface.imports.reader(staged)
        declared = request.headers.get("content-length")
        if (
            declared is not None
            and declared.isdigit()
            and int(declared) > self.surface.limit
        ):
            raise importing.past_limit(name, int(declared), self.surface.limit)
        body = await request.body()
        return await run_in_threadpool(held.put, name, body)

    def read_staged(self, staged: str, name: str) -> Response:
        """Serve a staged file full size, as it was cleaned."""
        served = _photograph(
            self.surface.file_response,
            importing.staged_file(self.surface.imports.folder(staged), name),
        )
        served.headers["Cache-Control"] = "no-store"
        return served

    def delete_staged(self, staged: str, name: str) -> dict[str, Any]:
        """Remove a read file from its import before the commit; refused once sealed."""
        self.surface.imports.reader(staged).remove(name)
        return {}

    def read_staged_thumb(self, staged: str, name: str) -> Response:
        """Serve a staged file's preview, made now and kept nowhere."""
        return Response(
            importing.preview(self.surface.imports.folder(staged), name),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-store"},
        )

    def delete_staging(self, staged: str) -> dict[str, Any]:
        """Cancel an import: its staging folder is deleted, the library unchanged."""
        self.surface.imports.cancel(staged)
        return {}

    def post_commit(self, staged: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Commit an import into a new collection, or with `add` into an open one."""
        as_is = payload.get("as_is", [])
        if not _strings(as_is):
            raise Refusal("the request's `as_is` is not a list of file names")
        done = self.surface.imports.commit(
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


ROUTES = (
    Route("POST", "/api/staging", "post_staging"),
    Route("PUT", "/api/staging/{staged}/files/{name}", "put_file", 202),
    Route("GET", "/api/staging/{staged}/files/{name}", "read_staged"),
    Route("DELETE", "/api/staging/{staged}/files/{name}", "delete_staged"),
    Route("GET", "/api/staging/{staged}/files/{name}/thumb", "read_staged_thumb"),
    Route("DELETE", "/api/staging/{staged}", "delete_staging"),
    Route("POST", "/api/staging/{staged}/commit", "post_commit"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the staging routes on `app`, over `surface`."""
    register(app, StagingRoutes(surface), ROUTES)

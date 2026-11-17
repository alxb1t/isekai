"""The sources' routes: a source's bytes and its thumbnail."""

from fastapi import FastAPI, Response

from isekai.interface.ui import library
from isekai.interface.ui.routes.common import _photograph
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface


class SourceRoutes:
    """The routes that serve one source of a collection."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose folders and file response the routes read."""
        self.surface = surface

    def read_source(self, collection: str, name: str) -> Response:
        """Serve a source's bytes, whole, with or without a run.

        One in a format the render does not read, placed by hand, is served as an
        upright JPEG of it, so the viewer shows what its thumbnail does.
        """
        source = library.source_files(self.surface.folder(collection))(name)
        return _photograph(
            self.surface.file_response, source, other=library.source_jpeg
        )

    def read_source_thumb(self, collection: str, name: str) -> Response:
        """Serve a source's thumbnail, upright, made in the library's cache once."""
        source = library.source_files(self.surface.folder(collection))(name)
        return self.surface.file_response(
            library.source_thumbnail(self.surface.root, source),
            media_type="image/jpeg",
        )


ROUTES = (
    Route("GET", "/api/c/{collection}/sources/{name}", "read_source"),
    Route("GET", "/api/c/{collection}/sources/{name}/thumb", "read_source_thumb"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the sources' routes on `app`, over `surface`."""
    register(app, SourceRoutes(surface), ROUTES)

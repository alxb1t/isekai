"""A resource's routes as a table: a method, a path and the name of the handler.

`register` reads each handler off the resource, so a row naming a method the
class lacks fails when the app is built, in every test of the server.
"""

from collections.abc import Sequence
from typing import NamedTuple

from fastapi import FastAPI


class Route(NamedTuple):
    """One route of a resource: its HTTP method, its path and its handler's name."""

    method: str
    path: str
    handler: str


def register(app: FastAPI, resource: object, table: Sequence[Route]) -> None:
    """Add each row of `table` to `app`, its handler read off `resource`.

    e.g. Route("GET", "/api/tags", "read_tags") -> `resource.read_tags` on GET /api/tags
    """
    for route in table:
        app.add_api_route(
            route.path, getattr(resource, route.handler), methods=[route.method]
        )

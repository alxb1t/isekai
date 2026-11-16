"""What more than one resource's routes read: a body's keys, a photograph and its size.

The approvals' fields, a draft's seeds and a file's time, as the page shows them.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any, TypeGuard

from fastapi import Response

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    Renders,
    ReviewApproved,
    read,
    require,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import SIGNATURE_BYTES, Run, media_type
from isekai.interface.ui import library
from isekai.shared.image import dimensions_or_refuse


def _needs(payload: Mapping[str, Any], keys: Sequence[str]) -> None:
    """Refuse a body that lacks any of `keys`, naming each."""
    missing = [key for key in keys if key not in payload]
    if missing:
        raise Refusal(f"the request lacks {', '.join(missing)}; send {', '.join(keys)}")


def _dimensions(run: Run) -> tuple[int, int]:
    """Return the photograph's size, as a `Refusal` rather than an exit."""
    return dimensions_or_refuse(
        run.photo,
        "the page reads the photograph's own header to size itself and there is "
        "nothing to fall back to -- re-export it as a JPEG or PNG",
    )


def _whole(value: object) -> TypeGuard[int]:
    """Return whether a request's value is a whole number, a JSON `true` not one."""
    return isinstance(value, int) and not isinstance(value, bool)


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


def _strings(value: object) -> TypeGuard[list[str]]:
    """Return whether `value` is a list of strings: tags, names, or a run's flow."""
    return isinstance(value, list) and all(isinstance(one, str) for one in value)


def _approved(approval: Path) -> tuple[ReviewApproved, dict[str, list[str]]]:
    """Read an approval the page shows, and its fields; only a hand repairs one."""
    remedy = f"restore it in {approval} by hand, then reload the page"
    body = read(approval, APPROVED_FILE, remedy=remedy)
    return body, _fields(approval, body, remedy)


def _decimal(seeds: Sequence[int]) -> list[str]:
    """Return seeds as decimal strings: a 64-bit seed is past a page's number."""
    return [str(seed) for seed in seeds]


def _photograph(
    file_response: Callable[..., Response],
    path: Path,
    *,
    other: Callable[[Path], bytes] | None = None,
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
    return file_response(path, media_type=kind, headers=headers)


def _untagged(fields: Mapping[str, object]) -> str | None:
    """Return the first field whose value is not a list of tags, or None."""
    return next((name for name, tags in fields.items() if not _strings(tags)), None)


def _fields(path: Path, body: Mapping[str, Any], remedy: str) -> dict[str, list[str]]:
    """Return a sheet's fields, refusing by name one that is not a list of tags."""
    require(path, body, "fields", dict, remedy)
    if (name := _untagged(body["fields"])) is not None:
        raise Refusal(f"{path.name}: its `{name}` is not a list of tags; {remedy}")
    return dict(body["fields"])


def _renders_out(renders: Renders) -> dict[str, Any]:
    """Describe `renders` for the page, each seed as its decimal string."""
    return {
        "count": renders["count"],
        "seeds": _decimal(renders["seeds"]),
    }


def _saved(path: Path | None) -> float | None:
    """Return when this artifact was last written, as the server's own clock says.

    The server's, never the browser's. The page shows the time beside the file
    it names, and a receipt a client wrote for itself is a claim about a save
    rather than a record of one.
    """
    return path.stat().st_mtime if path is not None else None

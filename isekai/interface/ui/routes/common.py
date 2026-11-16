"""What more than one resource's routes read: a body's keys and a photograph's size."""

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any, TypeGuard

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import Run
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

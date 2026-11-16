"""The place routes: a tattoo's ink, its preview, its bake and its proposed pairs."""

import math
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeGuard

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

from isekai.foundation.edit import load_edit
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import edit_files, is_seed
from isekai.interface.ui.routes.common import _needs
from isekai.interface.ui.routes.keys import (
    BAKE_KEYS,
    INK_KEYS,
    PREVIEW_KEYS,
    PROPOSE_KEYS,
)
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Held, Surface
from isekai.interface.wiring import proposer_of
from isekai.pipeline import tattoos
from isekai.pipeline.edit import request_placed
from isekai.shared.image import upright_image

if TYPE_CHECKING:
    from PIL.Image import Image

# The tracked edit a bake requests.
BAKE_EDIT = "tattoo-wai"


def _is_point(value: object) -> TypeGuard[list[float]]:
    """Return whether `value` is `[x, y]`, two finite numbers from 0 up."""
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(
            isinstance(each, int | float)
            and not isinstance(each, bool)
            and math.isfinite(each)
            and each >= 0
            for each in value
        )
    )


def _points_of(value: object) -> list[tuple[float, float]]:
    """Return the tattoo's points a body names, each a finite, non-negative `[x, y]`.

    e.g. [[10, 20.5]] -> [(10.0, 20.5)]; a negative, a non-number or none is refused.
    """
    if not isinstance(value, list) or not value:
        raise Refusal(
            "points is the tattoo's points on the photograph, `[[x, y], ...]`; "
            "send at least one"
        )
    found: list[tuple[float, float]] = []
    for number, point in enumerate(value, 1):
        if not _is_point(point):
            raise Refusal(
                f"point {number} is {point!r}; send each as `[x, y]`, two finite "
                "numbers from 0 up, in the photograph's pixels"
            )
        found.append((float(point[0]), float(point[1])))
    return found


def _upright_of(path: Path, what: str) -> "Image":
    """Return the image at `path` upright, as RGB, or refuse in words naming `what`."""
    from PIL.Image import DecompressionBombError

    try:
        return upright_image(path)
    except (OSError, DecompressionBombError) as unreadable:
        raise Refusal(
            f"{what} cannot be read ({unreadable}); reload the page"
        ) from unreadable


class PlaceRoutes:
    """The routes of placement: ink, preview, bake and proposed pairs."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose runs, renders and wiring the routes read."""
        self.surface = surface

    def post_ink(self, collection: str, name: str, payload: dict[str, Any]) -> Response:
        """Return a tattoo's ink on its outline's crop, a JPEG made now, kept nowhere.

        The tattoo is found on the render named by `digest` and `flow`, whose
        photograph a cut reads.
        """
        self.surface.folder(collection)
        _needs(payload, INK_KEYS)
        one = self.surface.held(
            collection, str(payload["digest"]), str(payload["flow"])
        )
        view = tattoos.ink_view(
            self.surface.root,
            name,
            one.run.photo,
            one.run.digest,
            payload["points"],
            payload["white"],
            payload["neutral"],
            payload["depth"],
        )
        return Response(
            view.jpeg,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-store",
                "X-Ink-Box": ",".join(str(side) for side in view.box),
                "X-Ink-White": str(view.white),
            },
        )

    def placed_on(
        self, collection: str, payload: Mapping[str, Any]
    ) -> tuple[Held, Path]:
        """Return the run a placement body names and the image it is placed on.

        The image is the render's, or the baked edit `edit` of it when the body
        names one; an edit with no image yet is refused.
        """
        one = self.surface.held(
            collection, str(payload["digest"]), str(payload["flow"])
        )
        seed = str(payload["seed"])
        if not is_seed(seed):
            raise Refusal(
                f"{seed!r} is no seed; send the render's seed as its address shows it"
            )
        _, image, _ = self.surface.rendered(
            collection,
            one.run.digest,
            str(payload["flow"]),
            str(payload["version"]),
            int(seed),
        )
        edit = payload.get("edit")
        if edit is None:
            return one, image
        if isinstance(edit, bool) or not isinstance(edit, int) or edit < 1:
            raise Refusal(
                f"edit {edit!r} is no edit's number; send the number of a baked "
                "edit, or none for the render"
            )
        own = edit_files(image.parent, int(seed), edit)[0]
        if not own.is_file():
            raise Refusal(
                f"edit {edit} of {seed} has no image yet; it waits for its render "
                "session, or is gone"
            )
        return one, own

    def post_preview(
        self, collection: str, name: str, payload: dict[str, Any]
    ) -> Response:
        """Return a tattoo's warped ink for a stage's pairs, a JPEG made now.

        `target` is `photo` for stage 1 and `render` for every other stage; the
        image is the crop of that target the pairs and the limb name. Nothing is
        kept.
        """
        _needs(payload, PREVIEW_KEYS)
        one, image = self.placed_on(collection, payload)
        made = tattoos.preview(
            self.surface.root,
            name,
            one.run.photo,
            one.run.digest,
            image,
            str(payload["target"]),
            payload["pairs"],
            payload["limb"],
            payload["exclusions"],
        )
        return Response(
            made.jpeg,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-store",
                "X-Preview-Box": ",".join(str(side) for side in made.box),
                "X-Ink-White": str(made.white),
            },
        )

    def post_bake(
        self, collection: str, name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Queue the edit request of a tattoo placed by pairs; answer its number.

        The composite and the placement are made now and handed to the edit stage,
        which writes the request's files and never its image: the render session
        samples it.
        """
        _needs(payload, BAKE_KEYS)
        one, image = self.placed_on(collection, payload)
        made = tattoos.composite(
            self.surface.root,
            name,
            one.run.photo,
            one.run.digest,
            image,
            payload["pairs"],
            payload["limb"],
            payload["exclusions"],
        )
        asked = request_placed(
            load_edit(BAKE_EDIT),
            image,
            made.png,
            made.values,
            overrides={},
            seed=None,
            rng=self.surface.wired.rng,
        )
        return {"edit": asked.number}

    def post_propose(self, collection: str, payload: dict[str, Any]) -> JSONResponse:
        """Return the pairs proposed for a render, `{arm, pairs}`, made now.

        `points` are the tattoo's on the photograph, in its upright pixels. A pair is
        the photograph's point then the render's. Nothing is kept, and an answer with
        no pair is no refusal.
        """
        _needs(payload, PROPOSE_KEYS)
        points = _points_of(payload["points"])
        one, image = self.placed_on(
            collection, {key: payload[key] for key in PROPOSE_KEYS}
        )
        proposer = proposer_of(self.surface.wired)
        answer = proposer.propose(
            _upright_of(one.run.photo, "the photograph"),
            _upright_of(image, "the render"),
            points,
        )
        return JSONResponse(
            {
                "arm": answer.arm,
                "pairs": [[[*seen], [*drawn]] for seen, drawn in answer.pairs],
            },
            headers={"Cache-Control": "no-store"},
        )


ROUTES = (
    Route("POST", "/api/c/{collection}/tattoos/{name}/ink", "post_ink"),
    Route("POST", "/api/c/{collection}/tattoos/{name}/preview", "post_preview"),
    Route("POST", "/api/c/{collection}/tattoos/{name}/bake", "post_bake"),
    Route("POST", "/api/c/{collection}/place/propose", "post_propose"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the place routes on `app`, over `surface`."""
    register(app, PlaceRoutes(surface), ROUTES)

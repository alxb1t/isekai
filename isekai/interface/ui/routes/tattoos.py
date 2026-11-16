"""The tattoo library's routes: list, read, keep, cut, remove, outline and pairs."""

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, Response

from isekai.foundation.refusal import Refusal
from isekai.interface.ui.routes.common import _dimensions, _needs
from isekai.interface.ui.routes.keys import OUTLINE_KEYS, STAGE1_KEYS
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface
from isekai.pipeline import importing, tattoos
from isekai.shared.ink import load_ink_config


def _digest_asked(digest: str | None) -> str:
    """Return the `digest` a tattoo request names, refusing a request with none."""
    if digest is None:
        raise Refusal(
            "the request's `digest` is the render's photograph digest, as its address "
            "shows; send it as `?digest=`"
        )
    return digest


def _tattoo_limits() -> dict[str, Any]:
    """Return the bounds the page and the server both read: one source, two configs."""
    config = tattoos.load_tattoo_config()
    ink = load_ink_config(tattoos.INK_CONFIG)
    return {
        "long_side": config.long_side,
        "outline_min": config.outline_min,
        "outline_max": config.outline_max,
        "depth_min": ink.depth_min,
        "depth_max": ink.depth_max,
        "photo_depth": ink.photo_depth,
        "image_depth": ink.image_depth,
        "floor_stage1": config.floor_stage1,
        "floor_stage2": config.floor_stage2,
        "floor_direct": config.floor_direct,
        "preview_floor": config.preview_floor,
        "preview_margin": config.preview_margin,
        "preview_wait_ms": config.preview_wait_ms,
        "pair_radius": config.pair_radius,
        "region_min": config.region_min,
    }


class TattooRoutes:
    """The routes of the tattoo library: uploads, cuts, outlines and pairs."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose library, imports and runs the routes read."""
        self.surface = surface

    def read_tattoos(self, digest: str | None = None) -> dict[str, Any]:
        """List the tattoos a render lists, with the limits the page reads.

        The uploads and the cuts of the photograph `digest`, each with its stage-1
        state on it.
        """
        asked = _digest_asked(digest)
        return {
            "tattoos": [
                asdict(one) for one in tattoos.listed(self.surface.root, asked)
            ],
            "limits": _tattoo_limits(),
            "stage1": {
                name: asdict(state)
                for name, state in tattoos.stage1_states(
                    self.surface.root, asked
                ).items()
            },
        }

    def read_tattoo(self, name: str, digest: str | None = None) -> dict[str, Any]:
        """Return one tattoo with its outline, refusing an unknown name."""
        asked = _digest_asked(digest)
        return {
            **asdict(tattoos.named(self.surface.root, name, asked)),
            "outline": asdict(tattoos.read_outline(self.surface.root, name, asked)),
        }

    def delete_tattoo(self, name: str, digest: str | None = None) -> dict[str, Any]:
        """Remove one tattoo of the library, found from the checked name and digest."""
        tattoos.remove(self.surface.root, name, _digest_asked(digest))
        return {}

    def read_tattoo_design(self, name: str, digest: str | None = None) -> Response:
        """Serve an uploaded tattoo's image whole, refusing a cut, which has none."""
        return Response(
            tattoos.design_bytes(self.surface.root, name, _digest_asked(digest)),
            media_type="image/png",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    def post_tattoo(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Keep a staged file as a tattoo, then cancel the import it came in.

        A file that still carries metadata is refused, and a refusal leaves the
        import open so the name can be changed.
        """
        staged, file, name = (payload.get(key) for key in ("staging", "file", "name"))
        if not (isinstance(staged, str) and isinstance(file, str)):
            raise Refusal(
                "the request's `staging` and `file` are the import's id and the staged "
                "file's name; send both"
            )
        if not isinstance(name, str):
            raise Refusal("the request's `name` is the tattoo's name; send one")
        path = importing.staged_file(self.surface.imports.folder(staged), file)
        carried = importing.verify(path)
        if carried:
            raise Refusal(
                f"{file} still carries {', '.join(carried)}; clean it as an import "
                "does, then keep it"
            )
        kept = tattoos.keep(self.surface.root, name, path.read_bytes())
        self.surface.imports.cancel(staged)
        return asdict(kept)

    def post_cut(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Keep a cut: a tattoo with no image, from the photograph of a run."""
        one = self.surface.held(
            collection, str(payload.get("digest")), str(payload.get("flow"))
        )
        name = payload.get("name")
        if not isinstance(name, str):
            raise Refusal("the request's `name` is the tattoo's name; send one")
        return asdict(
            tattoos.cut(self.surface.root, name, one.run.digest, _dimensions(one.run))
        )

    def put_outline(
        self, name: str, payload: dict[str, Any], digest: str | None = None
    ) -> dict[str, Any]:
        """Replace a tattoo's outline and tone with what the page sent, whole."""
        _needs(payload, OUTLINE_KEYS)
        return asdict(
            tattoos.save_outline(
                self.surface.root,
                name,
                _digest_asked(digest),
                payload["points"],
                payload["closed"],
                payload["white"],
                payload["neutral"],
                payload["depth"],
            )
        )

    def get_stage1(self, name: str, digest: str) -> dict[str, Any]:
        """Return a tattoo's pairs and flag on a photograph; none if never placed."""
        return asdict(tattoos.read_stage1(self.surface.root, name, digest))

    def put_stage1(
        self, name: str, digest: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Replace a tattoo's pairs and flag on a photograph with what the page sent."""
        _needs(payload, STAGE1_KEYS)
        return asdict(
            tattoos.save_stage1(
                self.surface.root,
                name,
                digest,
                payload["pairs"],
                payload["not_on_photo"],
            )
        )


ROUTES = (
    Route("GET", "/api/tattoos", "read_tattoos"),
    Route("GET", "/api/tattoos/{name}", "read_tattoo"),
    Route("DELETE", "/api/tattoos/{name}", "delete_tattoo"),
    Route("GET", "/api/tattoos/{name}/design", "read_tattoo_design"),
    Route("POST", "/api/tattoos", "post_tattoo"),
    Route("POST", "/api/c/{collection}/tattoos", "post_cut"),
    Route("PUT", "/api/tattoos/{name}/outline", "put_outline"),
    Route("GET", "/api/tattoos/{name}/stage1/{digest}", "get_stage1"),
    Route("PUT", "/api/tattoos/{name}/stage1/{digest}", "put_stage1"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the tattoo library's routes on `app`, over `surface`."""
    register(app, TattooRoutes(surface), ROUTES)

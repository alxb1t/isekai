"""The images' routes: a render's large view, its compare, its files, and its delete."""

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Response

from isekai.foundation.artifacts import (
    renders_of,
)
from isekai.foundation.flow import Flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import edit_files, edit_numbers
from isekai.interface.ui import library
from isekai.interface.ui.routes.common import (
    _approved,
    _decimal,
    _renders_out,
    _saved,
)
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface, _version
from isekai.pipeline.generate import discard_render
from isekai.pipeline.review import token_budget, withdraw


def _side(flow: Flow, version: int, approval: Path) -> dict[str, Any]:
    """Return one side of a comparison as the page shows it."""
    body, fields = _approved(approval)
    remedy = f"restore it in {approval} by hand, then reload the page"
    for name in flow.schema.names:
        fields.setdefault(name, [])
    return {
        "version": version,
        "approved_at": _saved(approval),
        "renders": _renders_out(renders_of(approval, body, remedy)),
        "tokens": token_budget(fields, flow.schema, flow).total,
    }


def _filled(fields: Mapping[str, list[str]]) -> dict[str, list[str]]:
    """Return the fields that hold a tag.

    e.g. `{"a": ["x"], "b": []}` -> `{"a": ["x"]}`
    """
    return {name: tags for name, tags in fields.items() if tags}


def _images_out(images: Sequence[tuple[int, int]]) -> list[dict[str, Any]]:
    """Describe rendered images by version and decimal seed, as the page names them.

    e.g. [(1, 7)] -> [{"version": 1, "seed": "7"}]
    """
    return [{"version": version, "seed": str(seed)} for version, seed in images]


class ImageRoutes:
    """The routes that answer for one render: its views, its files and its delete."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose renders and bakes the routes read."""
        self.surface = surface

    def read_render(
        self, collection: str, digest: str, flow: str, version: str, seed: int
    ) -> dict[str, Any]:
        """Return one render's large view: the approval's filled fields beside it.

        It is headed by what the version was: the one it came from, a revision or
        a re-roll, and its count and seeds; or, where its `renders` no render
        takes, damaged, naming the file, with no count.
        """
        run, image, approval = self.surface.rendered(
            collection, digest, flow, version, seed
        )
        _, fields = _approved(approval)
        number = _version(version)
        suffix = self.surface.offered(flow).output_suffix
        listed = library.versions(run, flow)
        held = next((one for one in listed if one.version == number), None)
        if held is None:
            raise Refusal(
                f"{approval.name}: it was gone when its version was listed; reload "
                "the page"
            )
        return {
            "flow": flow,
            "version": number,
            "seed": str(seed),
            "fields": _filled(fields),
            "approved_at": _saved(approval),
            "came_from": held.came_from,
            "kind": held.kind,
            "count": held.count,
            "seeds": _decimal(held.seeds),
            "damaged": held.damaged,
            # The seed's edits by number, the chain the large view draws.
            "bakes": [asdict(one) for one in library.bakes(image.parent, seed)],
            # The newest older version that rendered this seed, or null.
            "compare": library.paired(run, flow, number, seed, suffix),
            # Every offered flow, this one first, assigned or not: a draft assigns.
            "targets": sorted(self.surface.flows, key=lambda name: name != flow),
            # The source's images, a row per offered flow holding any, each oldest
            # version first, then by seed: the large view's walk and the pick.
            "source": [
                {"flow": name, "images": _images_out(images)}
                for name in self.surface.flows
                if (
                    images := library.rendered_images(
                        run, name, self.surface.offered(name).output_suffix
                    )
                )
            ],
        }

    def read_compare(
        self,
        *,
        collection: str,
        digest: str,
        flow: str,
        version: str,
        seed: int,
        other_flow: str,
        other_version: str,
        other_seed: int,
    ) -> dict[str, Any]:
        """Return the image picked beside the one compare started from, of one source.

        The picked is the left, this the right: the pair alone.
        e.g. `…/summon/v4/7/compare/flat/v1/5` -> flat's v1 · 5 left, summon's
        v4 · 7 right
        """
        number, other_number = _version(version), _version(other_version)
        if (other_flow, other_number, other_seed) == (flow, number, seed):
            raise Refusal(
                f"{flow} {version} · {seed}: an image compared with itself shows no "
                "change; go back to its large view and pick another"
            )
        _, _, origin = self.surface.rendered(collection, digest, flow, version, seed)
        _, _, picked = self.surface.rendered(
            collection, digest, other_flow, other_version, other_seed
        )
        right = _side(self.surface.offered(flow), number, origin)
        left = _side(self.surface.offered(other_flow), other_number, picked)
        return {
            "left": {"flow": other_flow, **left, "seed": str(other_seed)},
            "right": {"flow": flow, **right, "seed": str(seed)},
        }

    def read_compare_photo(
        self, collection: str, digest: str, flow: str, version: str, seed: int
    ) -> dict[str, Any]:
        """Return the image beside its source's photograph: the pair, no fields.

        The photograph is the left; the page reads its bytes at the run's `/photo`.
        """
        _, _, origin = self.surface.rendered(collection, digest, flow, version, seed)
        right = _side(self.surface.offered(flow), _version(version), origin)
        return {"left": None, "right": {"flow": flow, **right, "seed": str(seed)}}

    def read_render_image(
        self, collection: str, digest: str, flow: str, version: str, seed: int
    ) -> Response:
        """Serve the render's bytes, whole."""
        return self.surface.file_response(
            self.surface.rendered(collection, digest, flow, version, seed)[1]
        )

    def read_render_thumb(
        self, collection: str, digest: str, flow: str, version: str, seed: int
    ) -> Response:
        """Serve the render's thumbnail, made in the library's cache the first time."""
        run, image, _ = self.surface.rendered(collection, digest, flow, version, seed)
        return self.surface.file_response(
            library.thumbnail(self.surface.root, run, image), media_type="image/jpeg"
        )

    def read_bake(
        self, collection: str, digest: str, flow: str, version: str, seed: int, k: str
    ) -> dict[str, Any]:
        """Return one bake's record: its state, what it was placed on and its time."""
        return asdict(self.surface.baked(collection, digest, flow, version, seed, k)[1])

    def read_bake_image(
        self, collection: str, digest: str, flow: str, version: str, seed: int, k: str
    ) -> Response:
        """Serve a bake's image bytes, whole."""
        return self.surface.file_response(
            self.surface.bake_image(collection, digest, flow, version, seed, k)[1]
        )

    def read_bake_thumb(
        self, collection: str, digest: str, flow: str, version: str, seed: int, k: str
    ) -> Response:
        """Serve a bake's thumbnail, made in the library's cache the first time."""
        run, image = self.surface.bake_image(collection, digest, flow, version, seed, k)
        return self.surface.file_response(
            library.thumbnail(self.surface.root, run, image), media_type="image/jpeg"
        )

    def delete_render(
        self, collection: str, digest: str, flow: str, version: str, seed: int
    ) -> dict[str, Any]:
        """Delete the render and its thumbnails, as `discard` does, while none runs.

        The thumbnails go while the image still names them; then `withdraw`
        deletes the approval its last render leaves, older ones with no render and
        the newest's waiting draft, and, with no approval left, the flow's sheets.
        """
        run, image, _ = self.surface.rendered(collection, digest, flow, version, seed)
        with self.surface.draft_lock:
            rendering = self.surface.rendering(collection)
            if rendering is not None:
                raise Refusal(
                    f"{rendering} Wait for it to end, then delete the render again."
                )
            library.drop_thumbnails(run, image)
            for number in edit_numbers(image.parent, seed):
                if (own := edit_files(image.parent, seed, number)[0]).is_file():
                    library.drop_thumbnails(run, own)
            discard_render(image)
            withdraw(run, flow, _version(version))
        return {"deleted": True}


ROUTES = (
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}",
        "read_render",
    ),
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/compare/{other_flow}/{other_version}/{other_seed}",
        "read_compare",
    ),
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/compare/photo",
        "read_compare_photo",
    ),
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/image",
        "read_render_image",
    ),
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/thumb",
        "read_render_thumb",
    ),
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/edit/{k}",
        "read_bake",
    ),
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/edit/{k}/image",
        "read_bake_image",
    ),
    Route(
        "GET",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}/edit/{k}/thumb",
        "read_bake_thumb",
    ),
    Route(
        "DELETE",
        "/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}",
        "delete_render",
    ),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the images' routes on `app`, over `surface`."""
    register(app, ImageRoutes(surface), ROUTES)

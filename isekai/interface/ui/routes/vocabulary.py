"""The vocabulary's routes: a tag fragment answered, a flow's candidate tags listed."""

from typing import Any

from fastapi import FastAPI

from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Surface, _flow

# The dropdown's `· rare` marker. This number exists nowhere else in this
# repository: the vocabulary ranks by post count and never calls anything rare,
# so the threshold is the surface's own judgement about what an operator should
# hesitate over, and it is stated here rather than duplicated in TypeScript.
RARE_BELOW = 2000

# Enough rows to choose from without the dropdown becoming a list to read. The
# footer states the true match count, so narrowing the fragment stays the way to
# see fewer rather than scrolling.
DEFAULT_LIMIT = 10


class VocabularyRoutes:
    """The routes that answer from the vocabulary every collection shares."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose shared vocabulary the routes read."""
        self.surface = surface

    def read_tags(self, q: str = "", limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
        """Answer a tag fragment from the vocabulary the pipeline itself searches.

        The server ranks and the client does not. Shipping all 8,106 tags would
        put a second copy of the ranking rule in TypeScript, and `total` is the
        true match count so the dropdown can say how narrow the fragment got.
        """
        vocabulary = self.surface.shared.vocabulary()
        fragment = q.strip()
        found = (
            vocabulary.search(fragment, skip=self.surface.shared.field_map().excluded)
            if fragment
            else []
        )
        return {
            "matches": [
                {
                    "tag": tag,
                    "posts": (posts := vocabulary.count(tag)),
                    "rare": posts < RARE_BELOW,
                }
                for tag in found[: max(limit, 0)]
            ],
            "total": len(found),
        }

    def read_fields(self, flow: str) -> dict[str, Any]:
        """Answer every candidate tag for every criterion `flow` declares.

        **The whole table in one response, once per flow.** ~40 KB, so the
        overlay filters with no round trip per keystroke, ordered by post count
        through `Vocabulary.rank` and cut at nothing. A declared field the table
        holds nothing for is present and empty; the excluded list is not served.
        """
        return self.surface.shared.candidates(_flow(self.surface.wired, flow))


ROUTES = (
    Route("GET", "/api/tags", "read_tags"),
    Route("GET", "/api/fields", "read_fields"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the vocabulary's routes on `app`, over `surface`."""
    register(app, VocabularyRoutes(surface), ROUTES)

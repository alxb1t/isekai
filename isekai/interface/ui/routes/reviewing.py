"""The review routes: what Review shows for one run in one flow."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Response

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    CAPTION_FILE,
    DRAFT_FILE,
    ONE_RENDER,
    SHEET_FILE,
    TAGS_FILE,
    WD14_FILE,
    Renders,
    read,
    renders_of,
    require,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    CAPTIONS,
    NEW_VERSION,
    PHOTOGRAPH_VERBS,
    REVIEW,
    SHEETS,
    TAGS,
    WD14,
    approval_of,
    latest_artifact,
    photo_of,
    sheet_of,
    stage_command,
)
from isekai.interface.ui.routes.common import (
    _approved,
    _dimensions,
    _fields,
    _photograph,
    _renders_out,
    _saved,
    _strings,
)
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import Held, Surface
from isekai.pipeline.generate import image_of
from isekai.pipeline.review import (
    ENCODER_WINDOW,
    TokenBudget,
    came_from,
    cancellable,
    draft_image,
    review,
    source_copy,
    token_budget,
)
from isekai.pipeline.review import state as review_state
from isekai.shared.vocabulary import Vocabulary


class ReviewRoutes:
    """The routes that read a run's input and write its draft and its approval."""

    def __init__(self, surface: Surface) -> None:
        """Hold the surface whose folders, flows and writers the routes read."""
        self.surface = surface

    def read_input(self, collection: str, digest: str, flow: str) -> dict[str, Any]:
        """Return everything Review shows for one run in one flow, in one payload.

        The fields come from the approved artifact while the input is approved and
        from the current draft otherwise, which is what makes an input approved in
        an earlier sitting open read-only rather than empty.
        """
        one = self.surface.held(collection, digest, flow)
        if latest_artifact(one.directory(SHEETS)) is not None:
            # Opening a sheet takes its draft through the stage that owns it (D5);
            # `review` writes nothing where a draft or an approval is there.
            review(one.run, one.flow.id)
        draft = one.draft()
        approved = one.approved()
        state = review_state(one.directory(REVIEW))
        fields: dict[str, list[str]] = {}
        renders = ONE_RENDER
        revision = drafted = None
        if state == "approved" and approved is not None:
            # No command rewrites an approved sheet: `review` copies it and
            # refuses the same damage, so only a hand repairs it.
            remedy = f"restore it in {approved} by hand, then reload the page"
            body = read(approved, APPROVED_FILE, remedy=remedy)
            fields = _fields(approved, body, remedy)
            renders = renders_of(approved, body, remedy)
            revision = _revision(one, body, renders)
            drafted = _drafted(one, approved, body, remedy)
        elif draft is not None:
            remedy = _remedy(one, "review")
            body = read(draft, DRAFT_FILE)
            fields = _fields(draft, body, remedy)
            renders = renders_of(draft, body, remedy)
            revision = _revision(one, body, renders)
            drafted = _drafted(one, draft, body, remedy)
        budget = token_budget(fields, one.flow.schema, one.flow)
        caption = latest_artifact(photo_of(one.run, CAPTIONS))
        width, height = _dimensions(one.run)
        return {
            "id": one.run.digest,
            "run": one.run.id,
            "flow": one.flow.id,
            "schema": list(one.flow.schema.names),
            "vocabulary": len(self.surface.shared.vocabulary()),
            "width": width,
            "height": height,
            "caption": _prose(one, caption) if caption else None,
            # The one artifact a skipped verb leaves missing on a page under
            # review, so the page names what writes it. Built here: the browser
            # never spells a command.
            "caption_command": None if caption else _command(one, "caption"),
            # Both lists are `null` where the artifact is absent -- which is
            # three legitimate states, none of them a failure.
            "wd14": _wd14(one),
            "tags": _tags(one, self.surface.shared.vocabulary()),
            "fields": fields,
            # Seeds as decimal strings: a 64-bit seed is past what a JavaScript
            # number holds exactly.
            "renders": _renders_out(renders),
            # The approval a draft or the approval shown was copied from, its
            # fields and the image being revised; null for a copy of a sheet.
            "revision": revision,
            # The fields of a draft's own sheet and the number of its source copy,
            # the image it was drafted from; null for a draft holding none.
            "drafted": drafted,
            # **Approval with nothing newer beside it is what makes a sheet
            # read-only**, which is precisely `state() == "approved"`.
            "readonly": state == "approved",
            "draft": draft.name if draft else None,
            "approved": approved.name if approved else None,
            "saved": _saved(draft),
            # The approved artifact's own time, which the draft's cannot stand
            # in for: `approve()` unlinks the draft.
            "approved_at": _saved(approved),
            # Why *Cancel approve* is disabled, or null while it can run.
            "cancel": self.surface.rendering(collection)
            or cancellable(one.run, one.flow.id),
            "budget": _budget(budget),
        }

    def read_photo(self, collection: str, digest: str, flow: str) -> Response:
        """Serve the photograph's bytes, whole. `image.py` reads headers, not pixels."""
        return _photograph(
            self.surface.file_response,
            self.surface.held(collection, digest, flow).run.photo,
        )

    def read_source_copy(
        self, collection: str, digest: str, flow: str, version: int
    ) -> Response:
        """Serve the image draft `version` was drafted from, refusing one not held."""
        one = self.surface.held(collection, digest, flow)
        copy = source_copy(one.run, one.flow.id, version)
        if not copy.is_file():
            raise Refusal(
                f"{one.run.id}: flow {one.flow.id} holds no image a draft numbered "
                f"{version} was drafted from; go back to Review to reload the page"
            )
        return _photograph(self.surface.file_response, copy)


def _revision(
    one: Held, body: Mapping[str, Any], renders: Renders
) -> dict[str, Any] | None:
    """Describe the approval a draft or an approval was copied from, and its image.

    The image is the one the draft records, whatever its seeds became; a record
    naming none falls back to the first listed seed rendered under that
    approval, or null.
    e.g. from 1, seeds [7], outputs/001/7.png there -> {"version": 1, "seed": "7", …}
    """
    version = came_from(body)
    if version is None:
        return None
    approval = approval_of(one.run, one.flow.id, version)
    if not approval.is_file():
        return None
    if (image := draft_image(body)) is not None:
        seed = image["seed"]
    else:
        seed = next(
            (
                seed
                for seed in renders["seeds"]
                if image_of(one.run, one.flow, version, seed).is_file()
            ),
            None,
        )
    return {
        "version": version,
        "seed": None if seed is None else str(seed),
        "fields": _approved(approval)[1],
    }


def _drafted(
    one: Held, path: Path, body: Mapping[str, Any], remedy: str
) -> dict[str, Any] | None:
    """Describe the sheet a draft from another flow's image was drafted on.

    None unless the flow holds a source copy under the number of `path`, a draft
    or an approval; `version` is that number. `remedy` repairs the draft or
    approval; a damaged sheet names itself, since no command rewrites a sheet one
    records: `review` copies the same damage.
    e.g. review/001.draft.json, sources/001.png there -> {"fields": …, "version": 1}
    """
    version = int(path.name[:3])
    if not source_copy(one.run, one.flow.id, version).is_file():
        return None
    require(path, body, "sheet", int, remedy)
    sheet = sheet_of(one.run, one.flow.id, body["sheet"])
    restore = f"restore {sheet} by hand, then reload the page"
    held = read(sheet, SHEET_FILE, remedy=restore)
    return {"fields": _fields(sheet, held, restore), "version": version}


def _prose(one: Held, path: Path) -> str:
    """Return the photograph's caption's prose, refusing by name a caption with none."""
    body = read(path, CAPTION_FILE)
    require(path, body, "prose", str, _remedy(one, "caption"))
    return body["prose"]


def _wd14(one: Held) -> list[dict[str, Any]] | None:
    """Return the local tagger's scored list for the page, or None if absent.

    Stored sorted by confidence descending, and passed through in that order:
    the sort is what makes a wrong tag arrive pre-refuted by the right one above
    it, so re-ordering here would throw away the reason the number is shown.
    The list is the photograph's, every flow's (D17).
    """
    path = latest_artifact(photo_of(one.run, WD14))
    if path is None:
        return None
    found = read(path, WD14_FILE)
    remedy = _remedy(one, "tag")
    require(path, found, "tags", list, remedy)
    scored: list[dict[str, Any]] = []
    for index, entry in enumerate(found["tags"]):
        item = entry if isinstance(entry, dict) else {}
        tag, confidence = item.get("tag"), item.get("confidence")
        # `bool` is an `int`, and a flag is no confidence.
        if (
            not isinstance(tag, str)
            or isinstance(confidence, bool)
            or not isinstance(confidence, int | float)
        ):
            raise Refusal(
                f"{path.name}: its tag entry {index} is not a tag and a confidence; "
                f"{remedy}"
            )
        scored.append({"tag": tag, "confidence": float(confidence)})
    return scored


def _tags(one: Held, vocabulary: Vocabulary) -> list[dict[str, Any]] | None:
    """Return the hosted tagger's committable tags for the page, or None if absent.

    **Filtered to what the vocabulary carries, on the way to the page and never
    on the way to disk.** Roughly nine in ten of this model's tags were outside
    the vocabulary on an acceptance collection and could be committed to no field;
    the artifact keeps every tag the model returned. Deduplicated here only:
    `{tag, posts}` repeats carry no information and would be duplicate Vue keys.
    The local tagger's list is not filtered -- it emits the vocabulary itself.
    The list is the photograph's, every flow's (D17).
    """
    path = latest_artifact(photo_of(one.run, TAGS))
    if path is None:
        return None
    listed = read(path, TAGS_FILE).get("tags")
    if not _strings(listed):
        raise Refusal(
            f"{path.name}: its `tags` is not a list of strings; {_remedy(one, 'tag')}"
        )
    return [
        {"tag": name, "posts": vocabulary.count(name)}
        for name in dict.fromkeys(listed)
        if name in vocabulary
    ]


def _command(one: Held, verb: str, *flags: str) -> str:
    """Return the command that runs `verb` for `one`, as the operator pastes it.

    The photograph's verbs name no flow.
    e.g. "review" -> "python -m isekai review --flow f --runs b/runs r"
    """
    return stage_command(one.run, verb, *_flow_of(one, verb), options=flags)


def _remedy(one: Held, verb: str) -> str:
    """Return the remedy naming the command that rewrites `verb`'s file for `one`.

    e.g. "tag" -> "rewrite it with `python -m isekai tag --new-version r`"
    """
    command = stage_command(one.run, verb, *_flow_of(one, verb), options=NEW_VERSION)
    return f"rewrite it with `{command}`"


def _flow_of(one: Held, verb: str) -> tuple[str, ...]:
    """Return the flows `verb`'s command names: `one`'s, or none for a photograph's."""
    return () if verb in PHOTOGRAPH_VERBS else (one.flow.id,)


def _budget(budget: TokenBudget) -> dict[str, Any]:
    """Describe a token budget. One spelling, so two endpoints cannot disagree."""
    return {
        "total": budget.total,
        "per_field": dict(budget.per_field),
        "overhead": budget.overhead,
        "window": ENCODER_WINDOW,
    }


ROUTES = (
    Route("GET", "/api/c/{collection}/review/{digest}/{flow}", "read_input"),
    Route("GET", "/api/c/{collection}/review/{digest}/{flow}/photo", "read_photo"),
    Route(
        "GET",
        "/api/c/{collection}/review/{digest}/{flow}/source/{version}",
        "read_source_copy",
    ),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the review routes on `app`, over `surface`."""
    register(app, ReviewRoutes(surface), ROUTES)

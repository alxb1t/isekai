"""The review routes: what Review shows for one run in one flow."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeGuard

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

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
    group_of,
    is_rendered,
    is_seed,
    is_version,
    latest_artifact,
    photo_of,
    sheet_of,
    stage_command,
)
from isekai.interface.drafting import draft_from_image, refuse_image_drafts
from isekai.interface.ui import library
from isekai.interface.ui.routes.common import (
    REFUSED,
    _approved,
    _dimensions,
    _fields,
    _photograph,
    _renders_out,
    _saved,
    _strings,
    _untagged,
    _whole,
)
from isekai.interface.ui.routes.table import Route, register
from isekai.interface.ui.surface import _DECIMAL, Held, Surface
from isekai.pipeline.generate import image_of
from isekai.pipeline.review import (
    ENCODER_WINDOW,
    Revision,
    TokenBudget,
    came_from,
    cancel,
    cancellable,
    discard,
    draft_image,
    review,
    source_copy,
    token_budget,
    waiting_edit,
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

    def put_draft(
        self, collection: str, digest: str, flow: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Replace the draft's values in place, through the one function that owns it.

        The whole draft, every time: a debounced `PUT` of everything is what
        makes the receipt the page shows true.

        **Two preconditions, and both answer `409`.** An input that is approved
        and holds no later draft refuses an update at all: approval is the end
        of a review. And an update whose `saved` does not match the draft on
        disk refuses, because two overlapping `PUT`s would otherwise commit in
        the order the server finishes them. The check and the write hold one
        lock, so of two updates stating one precondition, the later fails it.
        """
        one = self.surface.held(collection, digest, flow)
        # Before the lock: a malformed body refuses without waiting on a write.
        fields = _update(payload)
        renders = _renders_in(payload)
        with self.surface.draft_lock:
            if review_state(one.directory(REVIEW)) == "approved":
                raise Refusal(
                    f"{one.run.id} is approved, and an approved sheet is never "
                    "edited in place; approval is the end of a review -- correct "
                    f"it with `{_command(one, 'review', '--new-version')}`, which "
                    "writes a fresh draft beside the approved artifact, and "
                    "reload: the input comes back re-opened and editable, with "
                    "its approved artifact still named"
                )
            self.surface.precondition(one, payload)
            written = self.surface.save_draft(one.run, one.flow.id, fields, renders)
        budget = token_budget(fields, one.flow.schema, one.flow)
        return {
            "draft": written.name,
            "saved": _saved(written),
            "budget": _budget(budget),
        }

    def post_approve(
        self,
        collection: str,
        digest: str,
        flow: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Validate and approve the draft, through the only writer of an approval.

        Under the draft lock, so an update in flight either lands before the
        approval reads the draft or finds the input approved and is refused.
        **It states the draft update's precondition**, so a page approves only
        the draft it last read, never one another writer has since moved.
        """
        one = self.surface.held(collection, digest, flow)
        with self.surface.draft_lock:
            self.surface.precondition(one, payload or {})
            written, warnings = self.surface.approve(
                one.run,
                one.flow.id,
                one.flow.schema,
                self.surface.shared.vocabulary(),
                excluded=self.surface.shared.field_map().excluded,
                definition=one.flow,
            )
        return {
            "approved": written.name if written else None,
            "warnings": warnings,
            "at": _saved(written),
        }

    def post_cancel(self, collection: str, digest: str, flow: str) -> dict[str, Any]:
        """Turn the approval back into its draft, refused while a render runs.

        `back` names what the flow is left on: the draft, or for a deleted copy
        the draft or approval beneath it, null where nothing is. `cancelled` is
        false for a flow at its draft, which a cancel leaves unchanged.
        """
        one = self.surface.held(collection, digest, flow)
        with self.surface.draft_lock:
            rendering = self.surface.rendering(collection)
            if rendering is not None:
                raise Refusal(
                    f"{rendering} Wait for it to end, then cancel the approval again."
                )
            left, changed = cancel(one.run, one.flow.id)
        return {"back": None if left is None else left.name, "cancelled": changed}

    def post_discard(
        self,
        collection: str,
        digest: str,
        flow: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Delete the waiting draft, as `review --discard` does; an approval refuses.

        **It states the draft update's precondition**, so a page deletes only the
        draft it last read, never one another tab has since edited.
        """
        one = self.surface.held(collection, digest, flow)
        with self.surface.draft_lock:
            self.surface.precondition(one, payload or {}, "discard again")
            gone = discard(one.run, one.flow.id)
        return {"discarded": gone.name}

    def post_draft(self, collection: str, payload: dict[str, Any]) -> object:
        """Draft `flow` from every image named, or, when any is refused, none.

        As `draft --flow` does: an image's own flow a revision, another drafted
        from its approval. A target's waiting draft with edits of its own is
        answered as `waiting`, and nothing is written for it. A refusal answers
        each image with its own refusal, or null, so the page can deselect the rest.
        """
        found = self.surface.folder(collection)
        name = payload.get("flow")
        if not isinstance(name, str) or name not in self.surface.flows:
            raise Refusal(
                f"{name!r}: not a flow this surface drafts; the flows it drafts are "
                f"{', '.join(self.surface.flows) or 'none'} -- reload the image's "
                "large view to choose one; nothing was written"
            )
        target = self.surface.offered(name)
        named = _images(payload)
        answers: list[str | None] = [None] * len(named)
        drafts = [{**_image_out(*one), "draft": None, "waiting": None} for one in named]
        # Each image to write, by its place in `named`.
        located: list[tuple[int, Path, Revision]] = []
        with self.surface.draft_lock:
            for at, (digest, flow, version, seed) in enumerate(named):
                try:
                    # A flow this build does not track names no directory of a run.
                    one = self.surface.offered(flow)
                    run = library.run_named(found, digest)
                    image = image_of(run, one, version, seed)
                    # The draft in hand is opened rather than refused; the
                    # review stage, and the CLI through it, still refuses it.
                    waiting = waiting_edit(run, name)
                except Refusal as refused:
                    answers[at] = str(refused)
                    continue
                if waiting is not None:
                    drafts[at]["waiting"] = waiting.name
                else:
                    located.append((at, image, (run, flow, version, seed)))
            # Each other image the collection holds is answered by the review stage.
            checked = refuse_image_drafts(
                target,
                [(image, held) for _, image, held in located],
                self.surface.shared.vocabulary,
                self.surface.shared.field_map,
            )
            for (at, _, _), answer in zip(located, checked, strict=True):
                answers[at] = answer
            if any(answer is not None for answer in answers):
                return JSONResponse(
                    {
                        "refusal": "; ".join(a for a in answers if a is not None),
                        "images": [
                            {**_image_out(*one), "refusal": answer}
                            for one, answer in zip(named, answers, strict=True)
                        ],
                    },
                    REFUSED,
                )
            for at, _, held in located:
                drafts[at]["draft"] = draft_from_image(
                    target,
                    held,
                    self.surface.shared.vocabulary,
                    self.surface.shared.field_map,
                ).name
        return {"drafts": drafts}


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
                if is_rendered(
                    group_of(one.run, one.flow.id, version),
                    seed,
                    one.flow.output_suffix,
                )
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


def _update(payload: Mapping[str, Any]) -> dict[str, list[str]]:
    """Return an update's fields, refusing one that is not an object of tag lists."""
    fields = payload.get("fields", {})
    fix = "send each field as a list of strings -- nothing was saved"
    if not isinstance(fields, dict):
        raise Refusal(f"the update's `fields` is not an object of tag lists; {fix}")
    if (name := _untagged(fields)) is not None:
        raise Refusal(f"the update's {name} is not a list of tags; {fix}")
    return fields


def _renders_in(payload: Mapping[str, Any]) -> Renders | None:
    """Return an update's `renders`, its seeds parsed from decimal strings, or None.

    e.g. `{"count": 2, "seeds": ["18402"]}` -> `{"count": 2, "seeds": [18402]}`
    """
    held = payload.get("renders")
    if held is None:
        return None
    fix = "send a count and a list of decimal seeds -- nothing was saved"
    if not isinstance(held, dict) or not isinstance(held.get("seeds", []), list):
        raise Refusal(f"the update's `renders` is not a count and its seeds; {fix}")
    seeds = held.get("seeds", [])
    if not all(isinstance(seed, str) and _DECIMAL.fullmatch(seed) for seed in seeds):
        raise Refusal(f"the update's renders seeds are not decimal numbers; {fix}")
    return {"count": held.get("count"), "seeds": [int(seed) for seed in seeds]}


def _images(payload: Mapping[str, Any]) -> list[tuple[str, str, int, int]]:
    """Return a draft's images, refusing a list that is not of rendered images.

    e.g. `{"images": [{"digest": "0d4b…", "flow": "f", "version": 1, "seed": "7"}]}`
         -> `[("0d4b…", "f", 1, 7)]`
    """
    images = payload.get("images")
    fix = (
        "send each image's digest, flow, version and decimal seed -- nothing was "
        "written"
    )
    if not isinstance(images, list) or not images:
        raise Refusal(f"the draft names no images; {fix}")
    named = []
    for image in images:
        if not (
            isinstance(image, dict)
            and isinstance(image.get("digest"), str)
            and isinstance(image.get("flow"), str)
            and _numbered(image.get("version"))
            and isinstance(image.get("seed"), str)
            and is_seed(image["seed"])
        ):
            raise Refusal(f"the draft's image {image!r} is not one; {fix}")
        named.append(
            (image["digest"], image["flow"], image["version"], int(image["seed"]))
        )
    return named


def _image_out(digest: str, flow: str, version: int, seed: int) -> dict[str, Any]:
    """Describe an image a draft is written from, its seed a decimal string."""
    return {"digest": digest, "flow": flow, "version": version, "seed": str(seed)}


def _numbered(value: object) -> TypeGuard[int]:
    """Return whether a request's value is a version a run's file names can spell.

    e.g. 2 -> True, 1000 -> False
    """
    return _whole(value) and is_version(value)


ROUTES = (
    Route("GET", "/api/c/{collection}/review/{digest}/{flow}", "read_input"),
    Route("GET", "/api/c/{collection}/review/{digest}/{flow}/photo", "read_photo"),
    Route(
        "GET",
        "/api/c/{collection}/review/{digest}/{flow}/source/{version}",
        "read_source_copy",
    ),
    Route("PUT", "/api/c/{collection}/review/{digest}/{flow}/draft", "put_draft"),
    Route("POST", "/api/c/{collection}/review/{digest}/{flow}/approve", "post_approve"),
    Route("POST", "/api/c/{collection}/review/{digest}/{flow}/cancel", "post_cancel"),
    Route("POST", "/api/c/{collection}/review/{digest}/{flow}/discard", "post_discard"),
    Route("POST", "/api/c/{collection}/draft", "post_draft"),
)


def mount(app: FastAPI, surface: Surface) -> None:
    """Register the review routes on `app`, over `surface`."""
    register(app, ReviewRoutes(surface), ROUTES)

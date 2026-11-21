"""What the UI's routes share: the folders, the wiring, the flows and the jobs.

`create_app` builds one `Surface` and the routes read it. It also holds the seams
a test replaces: the file response the library's files answer through (the
built bundle's page keeps its own), `save_draft`, `approve`, the precondition
check and the draft lock. This module imports no web framework, so the layer's
entry point and its tests read it whether or not a server is installed.
"""

import re
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from isekai.foundation.flow import Flow, load_flow, tracked_flows
from isekai.foundation.library import collection_held
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    REVIEW,
    Run,
    approval_of,
    command,
    current_draft,
    edit_files,
    is_rendered,
    latest_artifact,
    render_record,
)
from isekai.interface.ui import events, library, uploads
from isekai.interface.ui.billing import Billing
from isekai.interface.ui.jobs import Jobs
from isekai.interface.wiring import Wiring
from isekai.pipeline.generate import image_of
from isekai.shared.field_map import FieldMap
from isekai.shared.vocabulary import Vocabulary


@dataclass(frozen=True)
class Held:
    """One run in one flow, as a review URL names it."""

    run: Run
    flow: Flow

    def directory(self, stage: str) -> Path:
        """Return one of this flow's stage directories inside the run."""
        return self.run.directory(self.flow.id, stage)

    def draft(self) -> Path | None:
        """Return the current draft, or None; `current_draft` decides."""
        return current_draft(self.directory(REVIEW))

    def approved(self) -> Path | None:
        """Return the approved artifact, or None while it is still a draft."""
        return latest_artifact(self.directory(REVIEW), APPROVED)


class _Shared:
    """What every collection shares, read once when first asked for.

    Read on first use rather than at start, so a missing vocabulary is a
    refusal on the page that needs it rather than a server that never starts.
    """

    def __init__(self, wired: Wiring) -> None:
        """Hold the wiring the vocabulary and the table are read through."""
        self._wired = wired
        self._vocabulary: Vocabulary | None = None
        self._field_map: FieldMap | None = None
        self._candidates: dict[str, dict[str, Any]] = {}

    def vocabulary(self) -> Vocabulary:
        """Return the vocabulary, read once."""
        if self._vocabulary is None:
            self._vocabulary = self._wired.vocabulary()
        return self._vocabulary

    def field_map(self) -> FieldMap:
        """Return the field map held against the vocabulary, read once."""
        if self._field_map is None:
            self._field_map = self._wired.field_map(self.vocabulary())
        return self._field_map

    def candidates(self, flow: Flow) -> dict[str, Any]:
        """Return every candidate tag for every criterion `flow` declares, ranked."""
        if flow.id not in self._candidates:
            vocabulary, table = self.vocabulary(), self.field_map()
            self._candidates[flow.id] = {
                "fields": {
                    name: [
                        {"tag": tag, "posts": vocabulary.count(tag)}
                        for tag in vocabulary.rank(table.group(name))
                    ]
                    for name in flow.schema.names
                }
            }
        return self._candidates[flow.id]


# A number a request spells: ASCII digits alone, since `str.isdigit` also passes
# a superscript `int` cannot read.
_DECIMAL = re.compile(r"[0-9]+")
# The most digits a bake number is read from: a longer spelling is refused unread.
_BAKE_DIGITS = 18


def _version(text: str) -> int:
    """Return the approval number a URL's version names.

    e.g. "v2" -> 2
    """
    digits = text.removeprefix("v")
    if not _DECIMAL.fullmatch(digits):
        raise Refusal(
            f"{text!r} names no version; a version is v and the approval's number, "
            "e.g. v1 -- go back to the collection's hub to choose one"
        )
    return int(digits)


def _flow(wired: Wiring, flow: str) -> Flow:
    """Return the tracked flow a URL names, refusing one this build does not track."""
    tracked = tracked_flows(wired.flows_dir)
    if flow not in tracked:
        raise Refusal(
            f"{flow}: not a flow this build tracks; the flows it tracks are "
            f"{', '.join(tracked)} -- go back to the collection's hub to choose one"
        )
    return load_flow(flow, wired.flows_dir)


class Surface:
    """What the routes of one library share, and the lookups every one of them makes."""

    def __init__(
        self,
        root: Path,
        wired: Wiring,
        *,
        flows: Sequence[str],
        wire: Callable[[Path], Wiring],
        jobs: Jobs,
        billing: Billing,
        imports: uploads.Imports,
        broadcast: events.Broadcast,
        limit: int,
        file_response: Callable[..., Any],
        save_draft: Callable[..., Path],
        approve: Callable[..., tuple[Path | None, list[str]]],
        precondition: Callable[..., None],
        draft_lock: AbstractContextManager[Any],
    ) -> None:
        """Hold the library at `root`, its wiring and the parts the server builds."""
        self.root = root
        self.wired = wired
        self.flows = flows
        self.wire = wire
        self.jobs = jobs
        self.billing = billing
        self.imports = imports
        self.broadcast = broadcast
        self.limit = limit
        self.file_response = file_response
        self.save_draft = save_draft
        self.approve = approve
        self.precondition = precondition
        self.draft_lock = draft_lock
        self.shared = _Shared(wired)
        self.offered = cache(self._load)

    def _load(self, flow: str) -> Flow:
        """Return a tracked flow by name, loaded once: a flow is pinned while served."""
        return _flow(self.wired, flow)

    def folder(self, collection: str) -> Path:
        """Return a collection's folder, its runs root passed through the guard."""
        found = library.collection(self.root, collection)
        self.wire(found / library.RUNS)
        return found

    def held(self, collection: str, digest: str, flow: str) -> Held:
        """Return the run and flow a review URL names, refusing either unknown."""
        found = self.folder(collection)
        return Held(library.run_named(found, digest), _flow(self.wired, flow))

    def rendering_slot(self) -> dict[str, Any] | None:
        """Return the render slot while it runs, or None."""
        slot = self.jobs.slot("render")
        if slot and slot["state"] == "running":
            return slot
        return None

    def rendering(self, collection: str) -> str | None:
        """Return what a render running for `collection` says, or None.

        The render slot answers for this server's job: a session over several
        collections renders each, not only the first its slot names. A session any
        process holds in the collection answers by its lock, as the verb does.
        """
        slot = self.rendering_slot()
        ours = slot and collection in slot.get("collections", [slot["collection"]])
        if ours or collection_held(library.collection(self.root, collection)):
            return "A render session is running."
        return None

    def rendered(
        self, collection: str, digest: str, flow: str, version: str, seed: int
    ) -> tuple[Run, Path, Path]:
        """Return a render's run, its image and the approval it was rendered from.

        A missing image is refused: with its record gone too, as a deleted render's
        is, nothing is there to render again.
        """
        found = self.folder(collection)
        run = library.run_named(found, digest)
        one = self.offered(flow)
        number = _version(version)
        approval = approval_of(run, flow, number)
        image = image_of(run, one, number, seed)
        if not is_rendered(image.parent, seed, one.output_suffix):
            if not render_record(image.parent, seed).is_file():
                raise Refusal(
                    f"{image.name}: no render is here, "
                    "its record and its image are gone"
                )
            raise Refusal(
                f"{image.name}: its record is there, its image is gone; render it "
                f"again with `{command('render', str(found / library.RUNS))}`"
            )
        return run, image, approval

    def baked(
        self,
        collection: str,
        digest: str,
        flow: str,
        version: str,
        seed: int,
        k: str,
    ) -> tuple[Run, library.Bake, Path]:
        """Return a render's bake `k`: its run, its listing and where its image is.

        `k` is text, so no number a request spells is a 422: one the seed has no
        edit for is refused, as is a bake whose record cannot be read.
        """
        run, image, _ = self.rendered(collection, digest, flow, version, seed)
        held = {one.k: one for one in library.bakes(image.parent, seed)}
        # A held number is small: a spelling too long to convert holds none.
        number = int(k) if _DECIMAL.fullmatch(k) and len(k) <= _BAKE_DIGITS else None
        if number is None or number not in held:
            raise Refusal(
                f"{flow} {version} · {seed} holds no bake {k!r}; go back to its "
                "large view to choose one"
            )
        bake = held[number]
        if bake.state == "damaged":
            raise Refusal(str(bake.reason))
        return run, bake, edit_files(image.parent, seed, number)[0]

    def bake_image(
        self,
        collection: str,
        digest: str,
        flow: str,
        version: str,
        seed: int,
        k: str,
    ) -> tuple[Run, Path]:
        """Return a baked bake's run and image, refusing one still queued."""
        run, bake, image = self.baked(collection, digest, flow, version, seed, k)
        if bake.state == "queued":
            raise Refusal(
                f"bake {k} of {seed} is queued and has no image yet; the next "
                "render session bakes it, "
                f"`{command('render', str(self.folder(collection) / library.RUNS))}`"
            )
        return run, image

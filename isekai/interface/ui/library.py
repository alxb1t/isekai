"""The library: every batch the surface serves, read from the folders alone.

A folder in the library is a batch when it holds `sources/` (D40), so no marker
file can disagree with the disk. Its runs root is `<batch>/runs`, and every
figure here is a listing read on each call: the hub writes nothing. Its columns
are the flows `config/ui.json` offers.

```
~/isekai/                      the library, `ISEKAI_LIBRARY`
  <batch>/ sources/ runs/ log.txt
  .staging/                    a dot-folder: never listed
  .cache/<digest>/…            thumbnails, made on first request
```

No web framework, so the whole of it is tested with no server involved.
"""

import io
import json
import os
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from isekai.foundation.artifacts import (
    APPROVED_FILE,
    DRAFT_FILE,
    SHEET_FILE,
    WD14_FILE,
    Artifact,
    read,
    renders_of,
)
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.flow import load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    CAPTIONS,
    FRAME_NAME,
    ID_DIGEST_CHARS,
    ID_SEPARATOR,
    OUTPUTS,
    PROMPTS,
    REVIEW,
    SHEETS,
    TAGS,
    WD14,
    Run,
    approved_versions,
    digest_of,
    latest_artifact,
)
from isekai.interface.wiring import trackable
from isekai.pipeline.generate import approval_of, group_of, rendered_seeds
from isekai.pipeline.importing import SOURCES, UI_CONFIG
from isekai.pipeline.review import Status, current_draft
from isekai.pipeline.review import state as review_state
from isekai.shared.image import metadata_in

VARIABLE = "ISEKAI_LIBRARY"
DEFAULT = Path("~/isekai")
RUNS = "runs"
LOG = "log.txt"
# The library's thumbnails, a dot-folder so it is listed as no batch (D9).
CACHE = ".cache"
# A thumbnail's long side, in pixels.
THUMB_SIDE = 512

# What a run directory's stage folder says was written last, for Home's row.
_KINDS: Mapping[str, str] = {
    CAPTIONS: "caption",
    WD14: "tag",
    TAGS: "tag",
    SHEETS: "sheet",
    REVIEW: "review",
    PROMPTS: "prompt",
    OUTPUTS: "render",
}

# A source's digest, and what it carries, by what its file's stat says: reading
# every photograph on every listing would read the whole library each time.
_DIGESTS: dict[tuple[str, int, int, int], str] = {}
_CARRIES: dict[tuple[str, int, int, int], tuple[str, ...]] = {}


def root(environ: Mapping[str, str] = os.environ) -> Path:
    """Return the library directory `ISEKAI_LIBRARY` names, `~/isekai` when unset."""
    return Path(environ.get(VARIABLE) or DEFAULT).expanduser()


def open_library(library: Path) -> Path:
    """Return the library, created when absent, refusing one git can reach (D18).

    A batch holds copies of photographs, so the rule a runs root is under holds
    for the library that holds every runs root.
    """
    resolved = library.resolve()
    if trackable(resolved):
        raise Refusal(
            f"the library {resolved} is inside this repository and outside its "
            "ignored .data/ root; a batch holds copies of photographs, so it would "
            f"be one `git add` from being published -- set {VARIABLE} to a "
            "directory outside the repository, or under .data/"
        )
    try:
        resolved.mkdir(parents=True, exist_ok=True)
    except OSError as failed:
        raise Refusal(
            f"the library {resolved} cannot be created ({failed.strerror}); set "
            f"{VARIABLE} to a directory you can write, then start `isekai ui` again"
        ) from failed
    return resolved


@dataclass(frozen=True)
class FlowCount:
    """One flow's figures in a batch, out of the sources whose runs hold it."""

    flow: str
    approved: int
    rendered: int
    of: int


@dataclass(frozen=True)
class Row:
    """One folder of the library, as Home lists it."""

    name: str
    batch: bool
    sources: int = 0
    flows: tuple[FlowCount, ...] = ()
    without_flow: int = 0
    newest: float | None = None
    kind: str | None = None


@dataclass(frozen=True)
class Cell:
    """One source in one flow: its stage, read from the run's directory.

    `stage` is None where the run holds no directory for the flow, or there is no
    run. `refusal` is set, and `stage` is `unreadable`, where the file that decides
    the stage cannot be read. `status` is where stage ③ stands, `review.state`'s
    answer, wherever the cell has a sheet.
    """

    stage: str | None
    renders: int = 0
    refusal: str | None = None
    status: Status | None = None


@dataclass(frozen=True)
class Source:
    """One file under `sources/`, its run if it has one, and a cell per flow.

    `carries` names what the file holds beyond its pixels and orientation: a
    source imported as it is, which the hub marks not cleaned.
    """

    name: str
    run: Run | None
    cells: Mapping[str, Cell] = field(default_factory=dict)
    carries: tuple[str, ...] = ()

    @property
    def digest(self) -> str | None:
        """Return the digest the run is named by, or None."""
        return self.run.digest if self.run else None


@dataclass(frozen=True)
class Hub:
    """A batch's grid: its sources by the offered flows."""

    name: str
    flows: tuple[str, ...]
    sources: tuple[Source, ...]


def is_batch(folder: Path) -> bool:
    """Return whether `folder` is a batch: a folder holding `sources/`."""
    return (folder / SOURCES).is_dir()


def listed(library: Path) -> list[Path]:
    """Return every folder of the library, dot-folders left out, by name."""
    if not library.is_dir():
        return []
    return sorted(
        item
        for item in library.iterdir()
        if item.is_dir() and not item.name.startswith(".")
    )


def offered(flows_dir: Path, config: Path = UI_CONFIG) -> tuple[str, ...]:
    """Return the flows `config` offers, refusing one this build does not track."""
    names = tuple(json.loads(config.read_text())["flows"])
    for name in names:
        try:
            load_flow(name, flows_dir)
        except Refusal as untracked:
            raise Refusal(
                f"config/ui.json offers {name}, which does not load: {untracked}; "
                "fix its `flows`, then start `isekai ui` again"
            ) from untracked
    return names


def rows(library: Path, flows: Sequence[str], flows_dir: Path) -> list[Row]:
    """Return Home's rows: batches by their newest file, newest first, then the rest.

    A folder that is not a batch is listed and never opened.
    """
    folders = listed(library)
    suffixes = _suffixes(flows, flows_dir)
    batches = [_row(one, suffixes) for one in folders if is_batch(one)]
    batches.sort(key=lambda row: row.newest or 0.0, reverse=True)
    return batches + [Row(one.name, False) for one in folders if not is_batch(one)]


def batch(library: Path, name: str) -> Path:
    """Return the batch folder `name` names, refusing one the library does not hold."""
    folder = library / name
    if (
        name in ("", ".", "..")
        or "/" in name
        or name.startswith(".")
        or not (folder.is_dir() and is_batch(folder))
    ):
        raise Refusal(
            f"the library holds no batch named {name!r}; go back to the library "
            "to choose one"
        )
    return folder


def run_named(folder: Path, digest: str) -> Run:
    """Return the run in batch `folder` whose identifier begins with `digest`.

    e.g. "0d4b7e6fb2a8" -> runs/0d4b7e6fb2a8_ada
    """
    found = _runs(folder / RUNS).get(digest)
    if found is None:
        raise Refusal(
            f"{folder.name} holds no run named {digest!r}; go back to the batch's "
            "hub to choose one"
        )
    return found


def hub(folder: Path, flows: Sequence[str], flows_dir: Path) -> Hub:
    """Return batch `folder`'s grid over `flows`, each cell's stage from its run."""
    return _grid(folder, _suffixes(flows, flows_dir))


def sources(folder: Path) -> tuple[Source, ...]:
    """Return batch `folder`'s sources and their runs, reading no stage and no mark."""
    return _grid(folder, {}, marks=False).sources


def unprepared(grid: Hub) -> dict[str, list[str]]:
    """Return, per flow, the runs of every assigned cell that has no sheet yet.

    e.g. {"summon-anime-wai": ["0d4b7e6fb2a8_ada"], "conjure-anime-wai": []}
    """
    return {
        flow: [
            one.run.id
            for one in grid.sources
            if one.run is not None and one.cells[flow].stage in ("assigned", "tagged")
        ]
        for flow in grid.flows
    }


@dataclass(frozen=True)
class Version:
    """One approval of a source in a flow, and the seeds rendered under it.

    `at` is when the approval was written; `count` and `seeds` are its renders.
    """

    version: int
    at: float
    count: int
    seeds: tuple[int, ...]
    rendered: tuple[int, ...]


def versions(run: Run, flow: str, suffix: str) -> list[Version]:
    """Return `run`'s approvals in `flow`, newest first, each with its rendered seeds.

    An approval no hand can read is refused naming the file, as Review refuses it.
    """
    directory = run.directory(flow, REVIEW)
    found = []
    for number in reversed(approved_versions(directory)):
        path = approval_of(run, flow, number)
        remedy = f"restore it in {path} by hand, then reload the page"
        held = renders_of(path, read(path, APPROVED_FILE, remedy=remedy), remedy)
        group = group_of(run, flow, number)
        found.append(
            Version(
                number,
                path.stat().st_mtime,
                held["count"],
                tuple(held["seeds"]),
                tuple(rendered_seeds(group, suffix)),
            )
        )
    return found


def thumbnail(library: Path, run: Run, image: Path) -> Path:
    """Return `image`'s thumbnail in the library's cache, made the first time only.

    A JPEG at most `THUMB_SIDE` on its long side, under `.cache/<digest>/` at the
    image's path in the run. e.g. `…/outputs/001/42.png` -> `.cache/0d4b…/…/42.jpg`
    """
    within = image.relative_to(run.path).with_suffix(".jpg")
    cached = library / CACHE / run.digest / within
    if cached.is_file():
        return cached
    write_atomically(cached, _shrunk(image))
    return cached


def _shrunk(image: Path) -> bytes:
    """Return `image` as a JPEG at most `THUMB_SIDE` on its long side."""
    # Here, not at module scope: Pillow is a wheel, and this module is read by
    # tests of the hub that never make a thumbnail.
    from PIL import Image

    try:
        with Image.open(image) as opened:
            small = opened.convert("RGB")
            small.thumbnail((THUMB_SIDE, THUMB_SIDE))
    except OSError as unread:
        raise Refusal(
            f"{image.name}: is not an image this build can read ({unread}); delete "
            f"{image} and its .render.json, then render it again"
        ) from unread
    out = io.BytesIO()
    small.save(out, "JPEG", quality=85)
    return out.getvalue()


def source_files(folder: Path) -> Callable[[str], Path]:
    """Return what finds a file under batch `folder`'s `sources/` by name, or refuses.

    The folder is listed once, however many names are asked for.
    """
    found = {path.name: path for path in _sources(folder)}

    def named(name: str) -> Path:
        if name not in found:
            raise Refusal(
                f"{folder.name} holds no source named {name!r}; reload the hub to "
                "see its sources"
            )
        return found[name]

    return named


def _suffixes(flows: Sequence[str], flows_dir: Path) -> dict[str, str]:
    """Return each of `flows`' render suffix, by flow, in the order given."""
    return {flow: load_flow(flow, flows_dir).output_suffix for flow in flows}


def _grid(folder: Path, suffixes: Mapping[str, str], *, marks: bool = True) -> Hub:
    """Return batch `folder`'s grid over the flows `suffixes` names.

    Without `marks`, no source is read for its not-cleaned mark: Home shows none.
    """
    runs = _runs(folder / RUNS)
    sources = tuple(
        _source(path, runs.get(_digest(path)), suffixes, marks=marks)
        for path in _sources(folder)
    )
    return Hub(folder.name, tuple(suffixes), sources)


def stage(run: Run, flow: str, suffix: str) -> Cell:
    """Return `run`'s stage in `flow`, the furthest its directory holds.

    rendered ×n > approved > draft > sheet > tagged > assigned > no flow. The
    file that decides it is read, so a format this build does not know marks
    the cell rather than the batch.
    """
    if not run.directory(flow).is_dir():
        return Cell(None)
    review = run.directory(flow, REVIEW)
    approved = approved_versions(review)
    status = review_state(review)
    try:
        if approved:
            _check(latest_artifact(review, APPROVED), APPROVED_FILE)
            renders = rendered_seeds(
                run.directory(flow, OUTPUTS, f"{approved[-1]:03d}"), suffix
            )
            if renders:
                return Cell("rendered", len(renders), status=status)
            return Cell("approved", status=status)
        if (draft := current_draft(review)) is not None:
            _check(draft, DRAFT_FILE)
            return Cell("draft", status=status)
        if (sheet := latest_artifact(run.directory(flow, SHEETS))) is not None:
            _check(sheet, SHEET_FILE)
            return Cell("sheet", status=status)
        if (tags := latest_artifact(run.directory(flow, WD14))) is not None:
            _check(tags, WD14_FILE)
            return Cell("tagged")
    except Refusal as refused:
        return Cell("unreadable", refusal=str(refused))
    return Cell("assigned")


def _check(path: Path | None, kind: Artifact[Any]) -> None:
    """Read `path` as `kind`, so a file this build cannot read refuses here."""
    if path is not None:
        read(path, kind)


def _sources(folder: Path) -> list[Path]:
    """Return the files under `sources/`, dot-files left out, by name."""
    return sorted(
        item
        for item in (folder / SOURCES).iterdir()
        if item.is_file() and not item.name.startswith(".")
    )


def _key(path: Path) -> tuple[str, int, int, int]:
    """Return what a file's stat says about whether it changed."""
    info = path.stat()
    return (str(path), info.st_size, info.st_mtime_ns, info.st_ino)


def _digest(path: Path) -> str:
    """Return the twelve-character digest a run of this file is named by."""
    key = _key(path)
    if key not in _DIGESTS:
        _DIGESTS[key] = digest_of(path.read_bytes())[:ID_DIGEST_CHARS]
    return _DIGESTS[key]


def _carries(path: Path) -> tuple[str, ...]:
    """Return what a source carries beyond its pixels and orientation.

    Read from its bytes alone, so a clean source render would refuse is not
    marked, and no source is decoded to list a batch.
    e.g. a JPEG imported as it is -> ("EXIF", "XMP"); a cleaned one -> ()
    """
    key = _key(path)
    if key not in _CARRIES:
        _CARRIES[key] = tuple(metadata_in(path.read_bytes()))
    return _CARRIES[key]


def _runs(runs: Path) -> dict[str, Run]:
    """Return the runs under `runs` that hold a frame, by their identifier's digest."""
    if not runs.is_dir():
        return {}
    return {
        item.name[:ID_DIGEST_CHARS]: Run(item.name, item)
        for item in sorted(runs.iterdir())
        if item.name[ID_DIGEST_CHARS:].startswith(ID_SEPARATOR)
        and (item / FRAME_NAME).is_file()
    }


def _source(
    path: Path, run: Run | None, suffixes: Mapping[str, str], *, marks: bool
) -> Source:
    """Return one source, with its cell in every offered flow."""
    cells = {
        flow: stage(run, flow, suffix) if run else Cell(None)
        for flow, suffix in suffixes.items()
    }
    return Source(path.name, run, cells, _carries(path) if marks else ())


def _row(folder: Path, suffixes: Mapping[str, str]) -> Row:
    """Return one batch's row: its counts per flow and its newest file."""
    grid = _grid(folder, suffixes, marks=False)
    newest, kind = _newest(folder)
    counts = [_count(grid.sources, flow) for flow in grid.flows]
    bare = [
        one for one in grid.sources if all(c.stage is None for c in one.cells.values())
    ]
    return Row(
        folder.name,
        True,
        sources=len(grid.sources),
        flows=tuple(count for count in counts if count.of),
        without_flow=len(bare),
        newest=newest,
        kind=kind,
    )


def _count(sources: Sequence[Source], flow: str) -> FlowCount:
    """Return `flow`'s figures, out of the sources whose runs hold it."""
    held = [one.cells[flow] for one in sources if one.cells[flow].stage is not None]
    return FlowCount(
        flow,
        approved=sum(1 for c in held if c.stage in ("approved", "rendered")),
        rendered=sum(1 for c in held if c.stage == "rendered"),
        of=len(held),
    )


def _files(folder: Path) -> Iterator[Path]:
    """Yield every file under `folder`, dot-entries left out."""
    for directory, names, files in os.walk(folder):
        names[:] = [name for name in names if not name.startswith(".")]
        for name in files:
            if not name.startswith("."):
                yield Path(directory) / name


def _newest(folder: Path) -> tuple[float | None, str | None]:
    """Return the time and kind of the newest file written under `folder`.

    e.g. runs/<run>/<flow>/outputs/001/42.png -> (its mtime, "render")
    """
    newest = max(_files(folder), key=lambda path: path.stat().st_mtime, default=None)
    if newest is None:
        return None, None
    return newest.stat().st_mtime, _kind(newest.relative_to(folder).parts)


def _kind(parts: Sequence[str]) -> str:
    """Return what a file at `parts` under a batch was written by."""
    if parts[0] == SOURCES:
        return "import"
    if parts[0] == RUNS and len(parts) > 3:
        return _KINDS.get(parts[3], "run")
    if parts[0] == RUNS:
        return "run"
    return "file"

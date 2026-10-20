"""The library: every batch the surface serves, read from the folders alone.

A folder in the library is a batch when it holds `sources/` (D40), so no marker
file can disagree with the disk. Its runs root is `<batch>/runs`, and every
figure here is a listing read on each call: the hub writes nothing.

```
~/isekai/                      the library, `ISEKAI_LIBRARY`
  <batch>/ sources/ runs/ log.txt
  .staging/                    a dot-folder: never listed
```

Stdlib only, so the whole of it is tested with no server involved.
"""

import os
from collections.abc import Iterator, Mapping, Sequence
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
)
from isekai.foundation.flow import load_flow, tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    ID_DIGEST_CHARS,
    ID_SEPARATOR,
    OUTPUTS,
    REVIEW,
    SHEETS,
    WD14,
    Run,
    approved_versions,
    digest_of,
    latest_artifact,
)
from isekai.interface.wiring import trackable
from isekai.pipeline.generate import rendered_seeds
from isekai.pipeline.review import current_draft

VARIABLE = "ISEKAI_LIBRARY"
DEFAULT = Path("~/isekai")
SOURCES = "sources"
RUNS = "runs"

# What a run directory's stage folder says was written last, for Home's row.
_KINDS: Mapping[str, str] = {
    "captions": "caption",
    "wd14": "tag",
    "tags": "tag",
    "sheets": "sheet",
    "review": "review",
    "prompts": "prompt",
    "outputs": "render",
}


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
    the stage cannot be read.
    """

    stage: str | None
    renders: int = 0
    refusal: str | None = None


@dataclass(frozen=True)
class Source:
    """One file under `sources/`, its run if it has one, and a cell per flow."""

    name: str
    run: Run | None
    cells: Mapping[str, Cell] = field(default_factory=dict)

    @property
    def digest(self) -> str | None:
        """Return the twelve-character digest the run is named by, or None."""
        return self.run.id[:ID_DIGEST_CHARS] if self.run else None


@dataclass(frozen=True)
class Hub:
    """A batch's grid: its sources by the tracked flows."""

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


def rows(library: Path, flows_dir: Path) -> list[Row]:
    """Return Home's rows: batches by their newest file, newest first, then the rest.

    A folder that is not a batch is listed and never opened.
    """
    folders = listed(library)
    batches = [_row(one, flows_dir) for one in folders if is_batch(one)]
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
    runs = folder / RUNS
    prefix = f"{digest}{ID_SEPARATOR}"
    found = sorted(item.name for item in runs.glob(f"{prefix}*") if item.is_dir())
    if len(digest) != ID_DIGEST_CHARS or not found:
        raise Refusal(
            f"{folder.name} holds no run named {digest!r}; go back to the batch's "
            "hub to choose one"
        )
    return Run(found[0], runs / found[0])


def hub(folder: Path, flows_dir: Path) -> Hub:
    """Return batch `folder`'s grid, each cell's stage read from its run."""
    flows = tuple(tracked_flows(flows_dir))
    suffixes = {flow: load_flow(flow, flows_dir).output_suffix for flow in flows}
    runs = _runs(folder / RUNS)
    sources = tuple(
        _source(path, runs.get(_digest(path)), suffixes) for path in _sources(folder)
    )
    return Hub(folder.name, flows, sources)


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
    try:
        if approved:
            _check(latest_artifact(review, APPROVED), APPROVED_FILE)
            renders = rendered_seeds(
                run.directory(flow, OUTPUTS, f"{approved[-1]:03d}"), suffix
            )
            return Cell("rendered", len(renders)) if renders else Cell("approved")
        if (draft := current_draft(review)) is not None:
            _check(draft, DRAFT_FILE)
            return Cell("draft")
        if (sheet := latest_artifact(run.directory(flow, SHEETS))) is not None:
            _check(sheet, SHEET_FILE)
            return Cell("sheet")
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


def _digest(path: Path) -> str:
    """Return the twelve-character digest a run of this file is named by."""
    return digest_of(path.read_bytes())[:ID_DIGEST_CHARS]


def _runs(runs: Path) -> dict[str, Run]:
    """Return the runs under `runs`, by the digest their identifier begins with."""
    if not runs.is_dir():
        return {}
    return {
        item.name[:ID_DIGEST_CHARS]: Run(item.name, item)
        for item in sorted(runs.iterdir())
        if item.is_dir() and item.name[ID_DIGEST_CHARS:].startswith(ID_SEPARATOR)
    }


def _source(path: Path, run: Run | None, suffixes: Mapping[str, str]) -> Source:
    """Return one source, with its cell in every tracked flow."""
    cells = {
        flow: stage(run, flow, suffix) if run else Cell(None)
        for flow, suffix in suffixes.items()
    }
    return Source(path.name, run, cells)


def _row(folder: Path, flows_dir: Path) -> Row:
    """Return one batch's row: its counts per flow and its newest file."""
    grid = hub(folder, flows_dir)
    newest, kind = _newest(folder)
    present = [flow for flow in grid.flows if _has(grid.sources, flow)]
    bare = [one for one in grid.sources if not any(one.cells[f].stage for f in present)]
    return Row(
        folder.name,
        True,
        sources=len(grid.sources),
        flows=tuple(_count(grid.sources, flow) for flow in present),
        without_flow=len(bare),
        newest=newest,
        kind=kind,
    )


def _has(sources: Sequence[Source], flow: str) -> bool:
    """Return whether any source's run holds `flow`."""
    return any(one.cells[flow].stage is not None for one in sources)


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

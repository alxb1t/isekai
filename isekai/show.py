"""The inspection command: a run's artifacts, its active versions, its producers.

A filename carries only what resume decides on, which leaves a directory that is
precise and unreadable. This is what a person reads instead -- and it is also the
answer to "where is this run", which is why no progress file ships: nothing but a
human is watching before a review UI exists, and the inspection command is what
that human reads.

**It reads; it never decides.** Every fact here comes out of a file, which is the
opposite rule from the completion tests, and that is the point: control flow uses
listings, and people get the whole record.

Stdlib only.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.caption import DIRECTORY as CAPTIONS
from isekai.generate import OUTPUTS, PROMPTS
from isekai.review import APPROVED
from isekai.review import DIRECTORY as REVIEW
from isekai.run import Run, approved_versions, versions
from isekai.sheet import DIRECTORY as SHEETS

# The stages in the order a run passes through them, and whether each one is
# scoped to a flow. Declared once here so the listing cannot drift from the
# layout it describes.
STAGES: tuple[tuple[str, bool], ...] = (
    (CAPTIONS, False),
    (SHEETS, True),
    (REVIEW, True),
    (PROMPTS, True),
)


@dataclass(frozen=True)
class Listing:
    """One stage's artifacts in one run, and which of them is active."""

    stage: str
    flow: str | None
    versions: list[int]
    active: int | None
    approved: list[int]
    producers: dict[int, str]


def _producer_of(path: Path) -> str:
    """Return a one-line description of what produced the artifact at `path`."""
    try:
        body: Any = json.loads(path.read_text())
    except (OSError, ValueError):
        return "unreadable"
    producer = body.get("producer", {})
    parts = [str(producer.get("implementation", "unknown"))]
    models = producer.get("models")
    if models:
        parts.append("+".join(str(model) for model in models))
    if producer.get("pinned") is False:
        parts.append("unpinned")
    briefing = producer.get("briefing")
    if briefing:
        parts.append(f"briefing {str(briefing.get('sha256', ''))[:12]}")
    if producer.get("from") is not None:
        parts.append(f"from {producer['from']:03d}")
    if producer.get("edited") is not None:
        parts.append("edited" if producer["edited"] else "unedited")
    return " · ".join(parts)


def _listing(stage: str, flow: str | None, directory: Path) -> Listing:
    """Build one stage's listing from a directory of artifacts."""
    present = versions(directory)
    approved = approved_versions(directory)
    # The active version is the highest *approved* one where approval applies,
    # and the highest present one otherwise -- because downstream stages read
    # approval, and a draft is not something to proceed from.
    active = (approved or present or [None])[-1] if (approved or present) else None
    producers: dict[int, str] = {}
    for version in present:
        for candidate in (
            directory / f"{version:03d}.{APPROVED}.json",
            directory / f"{version:03d}.draft.json",
            directory / f"{version:03d}.json",
        ):
            if candidate.exists():
                producers[version] = _producer_of(candidate)
                break
    return Listing(stage, flow, present, active, approved, producers)


def listings(run: Run) -> list[Listing]:
    """Return one listing per stage, and per flow for the stages that have flows."""
    found: list[Listing] = []
    for stage, per_flow in STAGES:
        directory = run.directory(stage)
        if not per_flow:
            found.append(_listing(stage, None, directory))
            continue
        if not directory.is_dir():
            found.append(_listing(stage, None, directory))
            continue
        for flow in sorted(path.name for path in directory.iterdir() if path.is_dir()):
            found.append(_listing(stage, flow, directory / flow))
    return found


def rendered(run: Run) -> list[tuple[str, int, list[int]]]:
    """Return each flow's rendered seeds, by sheet version, from filenames alone."""
    outputs = run.directory(OUTPUTS)
    if not outputs.is_dir():
        return []
    found: list[tuple[str, int, list[int]]] = []
    for flow in sorted(path.name for path in outputs.iterdir() if path.is_dir()):
        for group in sorted((outputs / flow).iterdir()):
            if not group.is_dir() or not group.name.isdigit():
                continue
            seeds = sorted(
                int(image.stem)
                for image in group.iterdir()
                if image.suffix == ".png" and image.stem.isdigit()
            )
            found.append((flow, int(group.name), seeds))
    return found


def report(run: Run) -> Iterator[str]:
    """Yield the lines a person reads to answer "where is this run"."""
    frame = run.frame
    photo = frame["photo"]
    yield f"{run.id}"
    yield f"  photo    {photo['name']}  {photo['media_type']}  {photo['bytes']} bytes"
    yield f"           sha256 {photo['sha256']}"

    for listing in listings(run):
        name = (
            listing.stage if listing.flow is None else f"{listing.stage}/{listing.flow}"
        )
        if not listing.versions:
            yield f"  {name:<22} (none)"
            continue
        yield f"  {name}"
        for version in listing.versions:
            mark = "*" if version == listing.active else " "
            state = " approved" if version in listing.approved else ""
            producer = listing.producers.get(version, "")
            yield f"   {mark} {version:03d}{state}  {producer}"

    for flow, version, seeds in rendered(run):
        yield f"  {OUTPUTS}/{flow}/{version:03d}"
        for seed in seeds:
            yield f"     {seed}.png"

    yield "  * marks the active version for each stage"

"""The inspection command: a run's artifacts, its active versions, its producers.

A filename carries only what resume decides on, which leaves a directory that is
precise and unreadable. This is what a person reads instead -- and it is also the
answer to "where is this run", which is why no progress file ships: a person
reads this command, and the review UI reads the run directory itself.

**It reads; it never decides.** Every fact here comes out of a file, which is the
opposite rule from the completion tests, and that is the point: control flow uses
listings, and people get the whole record.

Stdlib only.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.run import (
    ARTIFACT,
    CAPTIONS,
    OUTPUTS,
    PROMPTS,
    REVIEW,
    SHEETS,
    TAGS,
    WD14,
    Run,
    is_approved,
)
from isekai.pipeline.generate import rendered_seeds

# The stages in the order a run passes through them. Every one of them is a
# flow's own now -- the run is input above and flow below -- so there is nothing
# left for a per-flow-ness column to say. Declared once here so the listing cannot
# drift from the layout it describes.
#
# **The tuple is explicit, so a new stage directory is invisible to `show` until
# it is named here.** By the standing rule that a version does not go into files
# it never touches, editing this would be out of v0.20's scope -- and the rule
# does not apply, because v0.20 does not inherit this gap, it **creates** it.
# Shipping a stage `show` cannot see is shipping a verb that lies about what a
# run holds (design.md D23).
STAGES: tuple[str, ...] = (CAPTIONS, WD14, TAGS, SHEETS, REVIEW, PROMPTS)


@dataclass(frozen=True)
class Listing:
    """One stage's artifacts in one flow of one run, and which of them is active."""

    stage: str
    flow: str
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


def _listing(stage: str, flow: str, directory: Path) -> Listing:
    """Build one stage's listing from a single reading of its directory.

    One `os.listdir`, not three: the versions, the approved ones and each
    version's actual filename all come out of the same pass, so the listing does
    not stat three candidate names per version to find the one that is there.
    """
    names: dict[int, str] = {}
    approved: list[int] = []
    if directory.is_dir():
        for name in sorted(os.listdir(directory)):
            match = ARTIFACT.match(name)
            if match is None:
                continue
            version = int(match.group("version"))
            names[version] = name
            if is_approved(name):
                approved.append(version)
    present = sorted(names)
    # The active version is the highest *approved* one where approval applies,
    # and the highest present one otherwise -- because downstream stages read
    # approval, and a draft is not something to proceed from.
    ranked = sorted(approved) or present
    active = ranked[-1] if ranked else None
    producers = {
        version: _producer_of(directory / names[version]) for version in present
    }
    return Listing(stage, flow, present, active, sorted(approved), producers)


def listings(run: Run) -> list[Listing]:
    """Return one listing per stage per flow, in flow order then stage order."""
    return [
        _listing(stage, flow, run.directory(flow, stage))
        for flow in run.flows
        for stage in STAGES
    ]


def rendered(run: Run, flows_dir: Path = FLOWS_DIR) -> list[tuple[str, int, list[int]]]:
    """Return each flow's rendered seeds, by sheet version, from filenames alone.

    The flow is loaded once, not once per sheet version, and it is loaded at all
    because what counts as a produced output is the flow's answer rather than an
    extension written in here.

    **`flows_dir` is a parameter because `Wiring` has one**, and this was the one
    place in the package that read the module default instead -- so `show`
    against an injected flows root went to `flows/` regardless of what was
    passed, and refused naming a flow the caller never asked about (v0.16 R2).
    """
    return [
        (flow, int(group.name), rendered_seeds(group, suffix))
        for flow in run.flows
        for suffix in (load_flow(flow, flows_dir).output_suffix,)
        for group in sorted(run.directory(flow, OUTPUTS).glob("*"))
        if group.is_dir() and group.name.isdigit()
    ]


def report(run: Run, flows_dir: Path = FLOWS_DIR) -> list[str]:
    """Return the lines a person reads to answer "where is this run".

    **A list rather than a generator, so no refusal can escape mid-print.**
    `rendered()` loads a flow and a flow refuses, and a generator's body does
    not start until the caller asks for its first line -- so a run holding a
    directory no flow answers for printed fifteen lines of record and *then*
    failed, leaving half a report above the refusal (v0.16 R2). Both callers
    drain this in full, so laziness bought nothing and cost the ordering; a
    list makes "everything refusable is read first" true by construction rather
    than by a paragraph asking the next editor to keep it so.
    """
    lines: list[str] = []
    frame = run.frame
    photo = frame["photo"]
    stages = listings(run)
    outputs = rendered(run, flows_dir)
    lines.append(f"{run.id}")
    lines.append(
        f"  photo    {photo['name']}  {photo['media_type']}  {photo['bytes']} bytes"
    )
    lines.append(f"           sha256 {photo['sha256']}")

    for listing in stages:
        name = f"{listing.flow}/{listing.stage}"
        if not listing.versions:
            lines.append(f"  {name:<22} (none)")
            continue
        lines.append(f"  {name}")
        for version in listing.versions:
            mark = "*" if version == listing.active else " "
            state = " approved" if version in listing.approved else ""
            producer = listing.producers.get(version, "")
            lines.append(f"   {mark} {version:03d}{state}  {producer}")

    for flow, version, seeds in outputs:
        lines.append(f"  {flow}/{OUTPUTS}/{version:03d}")
        for seed in seeds:
            lines.append(f"     {seed}")

    lines.append("  * marks the active version for each stage")
    return lines

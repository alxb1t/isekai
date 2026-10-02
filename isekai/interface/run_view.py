"""The inspection command: a run's artifacts, its active versions, its producers.

It also lists every failure record, and names every file or directory below a
flow that it does not read, so a run is never described as other than it is.

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
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.foundation.artifacts import VERSIONS
from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    ARTIFACT,
    CAPTIONS,
    ERROR,
    OUTPUTS,
    PROMPTS,
    REVIEW,
    SHEETS,
    TAGS,
    WD14,
    Kind,
    Run,
    failure_named,
    is_approved,
)
from isekai.pipeline.generate import (
    is_render,
    is_sidecar,
    render_groups,
    rendered_seeds,
)

# The stages in the order a run passes through them. Every one of them is a
# flow's own -- the run is input above and flow below -- so there is nothing for
# a per-flow-ness column to say. Declared once here so the listing cannot drift
# from the layout it describes.
#
# **The tuple is explicit, so a new stage directory reads as `not read` until it
# is named here.** Shipping a stage `show` cannot list is shipping a verb that
# says less than a run holds.
STAGES: tuple[str, ...] = (CAPTIONS, WD14, TAGS, SHEETS, REVIEW, PROMPTS)


@dataclass(frozen=True, order=True)
class FailureRecord:
    """One failure record, read from its name alone."""

    version: int
    attempt: int
    kind: Kind


@dataclass(frozen=True)
class Listing:
    """One stage's artifacts in one flow of one run, and which of them is active."""

    stage: str
    flow: str
    versions: list[int]
    active: int | None
    approved: list[int]
    producers: dict[int, str]
    failures: list[FailureRecord]


def _failure_of(name: str) -> FailureRecord | None:
    """Return the failure record `name` is, or None when it is not one."""
    named = failure_named(name)
    return None if named is None else FailureRecord(*named)


def _producer_of(path: Path) -> str:
    """Return a one-line description of what produced the artifact at `path`.

    A file this build would refuse to read is marked, never parsed: `show` reads
    a run in any state, so it reports the refusal rather than raising it.
    e.g. `declares version 2; this build reads 1`
    """
    try:
        body: Any = json.loads(path.read_text())
    except (OSError, ValueError):
        return "unreadable"
    schema = body.get("schema") if isinstance(body, dict) else None
    if not isinstance(schema, dict):
        return "unreadable"
    kind, declared = schema.get("name"), schema.get("version")
    if kind is None:
        return "declares no kind, which this build does not read"
    if not isinstance(kind, str) or kind not in VERSIONS:
        return f"declares kind {kind!r}, which this build does not read"
    if declared != VERSIONS[kind]:
        return f"declares version {declared!r}; this build reads {VERSIONS[kind]}"
    producer = body.get("producer", {})
    if not isinstance(producer, dict):
        return "unreadable"
    parts = [str(producer.get("implementation", "unknown"))]
    models = producer.get("models")
    if models:
        if not isinstance(models, list):
            return "unreadable"
        parts.append("+".join(str(model) for model in models))
    if producer.get("pinned") is False:
        parts.append("unpinned")
    briefing = producer.get("briefing")
    if briefing:
        if not isinstance(briefing, dict):
            return "unreadable"
        parts.append(f"briefing {str(briefing.get('sha256', ''))[:12]}")
    origin = producer.get("from")
    if origin is not None:
        if not isinstance(origin, int):
            return "unreadable"
        parts.append(f"from {origin:03d}")
    if producer.get("edited") is not None:
        parts.append("edited" if producer["edited"] else "unedited")
    return " · ".join(parts)


def _listing(stage: str, flow: str, directory: Path) -> Listing:
    """Build one stage's listing from a single reading of its directory.

    One `os.listdir`, not three: the versions, the approved ones, each version's
    actual filename and the failure records all come out of the same pass, so the
    listing does not stat three candidate names per version to find the one there.
    """
    names: dict[int, str] = {}
    approved: list[int] = []
    failures: list[FailureRecord] = []
    if directory.is_dir():
        for name in sorted(os.listdir(directory)):
            match = ARTIFACT.match(name)
            if match is None:
                if (failure := _failure_of(name)) is not None:
                    failures.append(failure)
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
    return Listing(
        stage, flow, present, active, sorted(approved), producers, sorted(failures)
    )


def listings(run: Run) -> list[Listing]:
    """Return one listing per stage per flow, in flow order then stage order."""
    return [
        _listing(stage, flow, run.directory(flow, stage))
        for flow in run.flows
        for stage in STAGES
    ]


def rendered(
    run: Run, flows_dir: Path = FLOWS_DIR, flows: Sequence[str] | None = None
) -> list[tuple[str, int, list[int]]]:
    """Return each flow's rendered seeds, by approval, from filenames alone.

    The outputs directory is the approval's number, not the sheet's. The flow
    is loaded once, not once per approval, and it is loaded at all
    because what counts as a produced output is the flow's answer rather than an
    extension written in here.

    **`flows_dir` is a parameter because `Wiring` has one**: reading the module
    default instead would send `show` against an injected flows root to `flows/`
    regardless of what was passed, and refuse naming a flow the caller never
    asked about. `flows` narrows the listing to those of the run's flows, so a
    caller can read one flow without loading the others; it is every flow the run
    holds by default.
    """
    return [
        (flow, int(group.name), rendered_seeds(group, suffix))
        for flow in (run.flows if flows is None else flows)
        for suffix in (load_flow(flow, flows_dir).output_suffix,)
        for group in render_groups(run, flow)
    ]


def render_failures(run: Run) -> dict[tuple[str, int], list[FailureRecord]]:
    """Return each render group's failure records, keyed by flow and group.

    e.g. `{("summon-anime-wai", 1): [FailureRecord(1, 1, "permanent")]}`
    """
    found: dict[tuple[str, int], list[FailureRecord]] = {}
    for flow in run.flows:
        for group in render_groups(run, flow):
            failures = [
                failure
                for name in os.listdir(group)
                if (failure := _failure_of(name)) is not None
            ]
            if failures:
                found[(flow, int(group.name))] = sorted(failures)
    return found


def _unread_in(directory: Path, below: str, read: Callable[[Path], bool]) -> list[str]:
    """Return the names in `directory` that `read` rejects, as paths below the run."""
    if not directory.is_dir():
        return []
    return [
        f"{below}/{path.name}" + ("/" if path.is_dir() else "")
        for path in directory.iterdir()
        if not read(path)
    ]


def unread(run: Run, flows_dir: Path = FLOWS_DIR) -> list[str]:
    """Return every name below a flow that `show` does not read, sorted.

    A flow reads its stage directories and `outputs`; a stage, its artifacts and
    failure records; `outputs`, its numbered groups; a group, its renders, their
    sidecars and its failure records. A directory ends in `/`, never descended.
    e.g. `["summon-anime-wai/outputs/001/notes.txt", "summon-anime-wai/stray/"]`
    """
    names: list[str] = []
    for flow in run.flows:
        suffix = load_flow(flow, flows_dir).output_suffix
        names += _unread_in(
            run.directory(flow),
            flow,
            lambda path: path.is_dir() and path.name in (*STAGES, OUTPUTS),
        )
        for stage in STAGES:
            names += _unread_in(
                run.directory(flow, stage),
                f"{flow}/{stage}",
                lambda path: bool(ARTIFACT.match(path.name) or ERROR.match(path.name)),
            )
        names += _unread_in(
            run.directory(flow, OUTPUTS),
            f"{flow}/{OUTPUTS}",
            lambda path: path.is_dir() and path.name.isdigit(),
        )
        for group in render_groups(run, flow):
            names += _unread_in(
                group,
                f"{flow}/{OUTPUTS}/{group.name}",
                lambda path: (
                    is_render(path, suffix)
                    or is_sidecar(path)
                    or bool(ERROR.match(path.name))
                ),
            )
    return sorted(names)


def report(run: Run, flows_dir: Path = FLOWS_DIR) -> list[str]:
    """Return the lines a person reads to answer "where is this run".

    **A list rather than a generator, so no refusal can escape mid-print.**
    `rendered()` loads a flow and a flow refuses, and a generator's body does
    not start until the caller asks for its first line -- so a run holding a
    directory no flow answers for would print lines of record and *then* fail,
    leaving half a report above the refusal. Both callers drain this in full, so
    laziness buys nothing and costs the ordering; a list makes "everything
    refusable is read first" true by construction rather than by a paragraph
    asking the next editor to keep it so.
    """
    lines: list[str] = [run.id]
    # A frame this build cannot read is marked, like an artifact, and the rest
    # listed: `show` reads a run in whatever state it is in.
    try:
        photo = run.photo_record
    except Refusal as unreadable:
        lines.append(f"  photo    {unreadable}")
    else:
        lines.append(
            f"  photo    {photo['name']}  {photo['media_type']}  {photo['bytes']} bytes"
        )
        lines.append(f"           sha256 {photo['sha256']}")
    stages = listings(run)
    outputs = rendered(run, flows_dir)
    group_failures = render_failures(run)
    stray = unread(run, flows_dir)

    for listing in stages:
        name = f"{listing.flow}/{listing.stage}"
        if not listing.versions and not listing.failures:
            lines.append(f"  {name:<22} (none)")
            continue
        lines.append(f"  {name}")
        for version in listing.versions:
            mark = "*" if version == listing.active else " "
            state = " approved" if version in listing.approved else ""
            producer = listing.producers.get(version, "")
            lines.append(f"   {mark} {version:03d}{state}  {producer}")
        lines += _failure_lines(listing.failures)

    for flow, version, seeds in outputs:
        lines.append(f"  {flow}/{OUTPUTS}/{version:03d}")
        for seed in seeds:
            lines.append(f"     {seed}")
        lines += _failure_lines(group_failures.get((flow, version), []))

    for path in stray:
        lines.append(f"  not read  {path}")

    lines.append(
        "  * marks the active version for each stage · ! marks a failure record"
    )
    return lines


def _failure_lines(failures: list[FailureRecord]) -> list[str]:
    """Return one `!` line per failure record."""
    return [
        f"   ! {record.version:03d}  failed · attempt {record.attempt} · {record.kind}"
        for record in failures
    ]

"""The requests a render names, and the argv `generate` and `edit` run with.

`render.py` imports this module and this module never imports `render.py`.
"""

import re
import shlex
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from isekai.foundation.flow import load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    Run,
    command,
    render_groups,
    rendered_seeds,
    runs_in,
)
from isekai.interface.compare_view import COLLECTION_PHOTOS
from isekai.interface.plan import Edits, Line
from isekai.interface.wiring import Wiring

REQUEST = re.compile(r"([a-z0-9-]+)=([1-9][0-9]*|[a-z][a-z0-9-]*)")

# `generate`'s argv and the wiring it runs on -> its exit status.
Generate = Callable[[list[str], Wiring], int]


@dataclass(frozen=True)
class Request:
    """One `<flow>=<count|source>` argument."""

    flow: str
    value: str

    @property
    def by_count(self) -> bool:
        """Return whether this flow draws seeds rather than taking a source's."""
        return self.value.isdigit()

    @property
    def mode(self) -> str:
        """Return the `generate` flag this request renders with."""
        return "--count" if self.by_count else "--seeds-from"

    def __str__(self) -> str:
        """Spell the request as the operator typed it."""
        return f"{self.flow}={self.value}"


def parse_request(text: str) -> Request:
    """Return the request `text` spells, or refuse naming the shape.

    e.g. "control-anime-wai=summon-anime-wai" -> Request("control-anime-wai", ...)
    """
    match = REQUEST.fullmatch(text)
    if match is None:
        raise Refusal(
            f"'{text}' is not <flow>=<count> or <flow>=<source>, "
            "e.g. summon-anime-wai=1"
        )
    return Request(match[1], match[2])


def in_session_sources(requests: Sequence[Request]) -> list[bool]:
    """Return, per request, whether its source renders by count earlier in the line.

    Such a source has no seeds until the pod is up, so its dependent has no check
    before the pod; one placed before its source could never take its seeds, and
    is refused. So is a request whose source is another source request's flow, in
    either order: its seeds are the ones that request takes, so it names them.
    """
    counted = {r.flow: i for i, r in enumerate(requests) if r.by_count}
    sourced = {r.flow: r for r in requests if not r.by_count}
    deferred = []
    for i, request in enumerate(requests):
        chain = None if request.by_count else sourced.get(request.value)
        if chain is not None and chain is not request:
            raise Refusal(
                f"'{request}' takes its seeds from '{chain}', itself a source "
                f"request; write '{request.flow}={chain.value}' for the same seeds"
            )
        j = None if request.by_count else counted.get(request.value)
        if j is not None and j > i:
            raise Refusal(
                f"'{request}' comes before its source '{requests[j]}'; "
                "put the source first"
            )
        deferred.append(j is not None)
    return deferred


def again(roots: Sequence[Path], without: Sequence[Path] = ()) -> str:
    """Return the command that renders what each of `roots` lacks, in one session.

    Each of `without` stays out of it, as its `--without`.
    """
    argv = ["uv", "run", "python", "-m", "isekai", "render", *map(str, roots)]
    return shlex.join([*argv, *without_flags(without)])


def without_flags(without: Sequence[Path]) -> list[str]:
    """Return a `--without` per path, as `isekai render` takes them.

    e.g. [Path("b/runs/r1/f")] -> ["--without", "b/runs/r1/f"]
    """
    return [arg for path in without for arg in ("--without", str(path))]


def _taken(roots: Sequence[Path], without: Sequence[Path]) -> list[Path]:
    """Return each of `without` under the one of `roots` it names, as that is named.

    Refuse a path under no root, or naming no run's flow there.
    e.g. roots [Path("b/runs")], without [Path("./b/runs/r1/f")] -> [b/runs/r1/f]
    """
    named = {runs.resolve(): runs for runs in roots}
    taken = []
    for path in without:
        runs = named.get(path.parent.parent.resolve())
        if runs is None:
            raise Refusal(
                f"--without {path} is under no runs root this session names; "
                "name its collection's runs/ too, or drop it"
            )
        run_id, flow = path.parent.name, path.name
        if run_id not in run_ids(runs) or flow not in Run(run_id, runs / run_id).flows:
            raise Refusal(
                f"--without {path} names no run's flow; give <runs>/<run-id>/<flow>"
            )
        taken.append(runs / run_id / flow)
    return taken


def run_ids(runs: Path) -> list[str]:
    """Return every run under `runs`, by id; a collection not yet assigned has none."""
    return [run.id for run in runs_in(runs)]


def _asked(
    runs: Path,
    ids: Sequence[str],
    requests: Sequence[Request],
    deferred: Sequence[bool],
    free: Wiring,
    verb: Sequence[str],
    *,
    generate: Generate,
) -> list[Line] | None:
    """Return the requests' lines over `runs` once their free checks pass, else None."""
    flows = [arg for request in requests for arg in ("--flow", request.flow)]
    if not ids:
        photos = shlex.quote(str(runs.parent / COLLECTION_PHOTOS))
        asked = command(
            "assign", " ".join(flows), "--runs", shlex.quote(str(runs)), f"{photos}/*"
        )
        raise Refusal(
            f"{runs} holds no run; open them from the collection's photographs with: "
            f"uv run {asked}"
        )
    where = ("--runs", str(runs), *ids)
    if generate([*verb, *flows, *where], free) != 0:
        return None
    for request, late in zip(requests, deferred, strict=True):
        if request.by_count or late:
            continue
        argv = [*verb, "--flow", request.flow, "--seeds-from", request.value, *where]
        if generate(argv, free) != 0:
            return None
    counts = {r.flow: int(r.value) for r in requests if r.by_count}
    return [_requested(request, runs, ids, counts, free) for request in requests]


def _requested(
    request: Request,
    runs: Path,
    ids: Sequence[str],
    counts: Mapping[str, int],
    wired: Wiring,
) -> Line:
    """Return a request's line, planned per run in `ids`.

    `counts` is each by-count request's count, by flow. A by-count request plans
    its count; a source request plans the count of a by-count source in the line,
    else the images its source holds now. A source of a source never reaches it.
    """
    if request.by_count:
        planned = [(run_id, counts[request.flow]) for run_id in ids]
    elif request.value in counts:
        planned = [(run_id, counts[request.value]) for run_id in ids]
    else:
        suffix = load_flow(request.value, wired.flows_dir).output_suffix
        planned = []
        for run_id in ids:
            groups = render_groups(Run(run_id, runs / run_id), request.value)
            seeds = rendered_seeds(groups[-1], suffix) if groups else []
            planned.append((run_id, len(seeds)))
    head = ("--flow", request.flow, request.mode, request.value)
    where = ("--runs", str(runs), *ids)
    return Line(runs, request.flow, head, where, tuple(planned))


def _edit_argv(
    runs: Path, held: Edits, flag: Sequence[str], server: str | None = None
) -> list[str]:
    """Return the `edit --pending` line over `held`'s cells, on `server` when given.

    e.g. ("r1/f",) -> edit --pending r1/f --runs <runs>; with a server, only the
    checks are skipped and the edits are sampled
    """
    where = ["--server", server] if server is not None else []
    return ["edit", *flag, "--pending", *held.cells, *where, "--runs", str(runs)]

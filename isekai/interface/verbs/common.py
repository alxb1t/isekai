"""What the verbs share: the argument types, the reporter and the run helpers."""

import argparse
import json
import shlex
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, TypeVar, cast

from isekai.boundary.comfy import TransportFailure
from isekai.foundation.artifacts import SEED_RANGE, SESSION_ID
from isekai.foundation.flow import tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import FRAME_NAME, RUNS_ROOT, Run, open_run
from isekai.interface.wiring import Wiring
from isekai.shared.ink import load_ink_config

T = TypeVar("T")


def _seed(value: str) -> int:
    """Parse a seed: an unsigned 64-bit integer, refused at parse time if it is not."""
    try:
        seed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
    if seed not in SEED_RANGE:
        raise argparse.ArgumentTypeError(
            f"{seed} is outside the sampler's unsigned 64-bit range"
        )
    return seed


def _positive(below_one: str) -> Callable[[str], int]:
    """Return a parser of a positive integer, refusing one below 1 with `below_one`."""

    def parse(value: str) -> int:
        try:
            whole = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from None
        if whole < 1:
            raise argparse.ArgumentTypeError(below_one)
        return whole

    return parse


# A render count: every one of them costs money.
_count = _positive("a render count below 1 renders nothing")
_seconds = _positive("a session limit below 1s ends at once")


def _session_id(value: str) -> str:
    """Return `value` as a session's id, refusing one that is not a start in UTC.

    The id names a file, so nothing but the one shape reaches a path.
    e.g. "20261024T091200Z" -> "20261024T091200Z"
    """
    if SESSION_ID.fullmatch(value) is None:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a start in UTC, e.g. 20261024T091200Z"
        )
    return value


def _depth(value: str) -> float:
    """Parse a depth: a number in the ink config's range, refused at parse time.

    e.g. "1.6" -> 1.6
    """
    config = load_ink_config()
    try:
        depth = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from None
    if not config.depth_min <= depth <= config.depth_max:
        raise argparse.ArgumentTypeError(
            f"{value} is outside {config.depth_min} to {config.depth_max}; "
            "give a depth in that range"
        )
    return depth


class _Targets(argparse.Action):
    """Split `render`'s positionals into its runs roots and its requests.

    A directory is a runs root; any other word holding `=` is a request, and the
    rest are runs roots the session refuses by name.
    e.g. [".data/b1/runs", "summon-anime-wai=1"] -> runs [b1/runs], requests [...]
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        """Set `runs` and `requests` on `namespace` from `values`, in order."""
        words = [str(value) for value in cast("list[object]", values)]
        asked = [w for w in words if "=" in w and not Path(w).is_dir()]
        namespace.runs = [Path(w) for w in words if w not in asked]
        namespace.requests = asked
        if not namespace.runs:
            parser.error("name at least one collection's runs/")


@dataclass(frozen=True)
class Verb:
    """A verb as one row: its name, the arguments it adds and the run that serves it.

    `run` is `None` for a verb `dispatch`'s tail runs.
    """

    name: str
    arguments: Callable[[argparse.ArgumentParser], None]
    run: Callable[[argparse.Namespace, Wiring], int] | None = None


def photographs(parser: argparse.ArgumentParser) -> None:
    """Add `photos` and `--runs` to `parser`."""
    parser.add_argument(
        "photos",
        nargs="*",
        help="photographs, or run identifiers for a run that already exists",
    )
    # The root every run lives under. It defaults to `.data/runs`, and it is a
    # flag because a version's acceptance run wants its own directory rather
    # than one pile every version adds to. A run holds a copy of the
    # photograph, so a run root is a directory of personal photographs by
    # construction -- which is why `wiring` refuses one that resolves INSIDE
    # this repository and outside `.data/`, where nothing ignores it and a
    # `git add` would publish it. A path outside the repository needs no
    # check at all: version control cannot reach it, whatever it is, and that
    # is what keeps a run on another disk expressible (D18).
    parser.add_argument(
        "--runs",
        type=Path,
        default=RUNS_ROOT,
        help=f"the directory runs live under (default {RUNS_ROOT.name}/)",
    )


def required_flow(parser: argparse.ArgumentParser) -> None:
    """Add `--flow` to `parser`, required and repeatable."""
    # Required, and repeatable, on every stage verb on a flow. Such a stage cannot
    # act without knowing which flow asked, because the flow is what supplies what
    # it reads: its schema, its graph and its dials. "Every tracked flow" is not a
    # selection, it is the absence of one -- and at the last verb it spends money.
    parser.add_argument(
        "--flow",
        action="append",
        dest="flows",
        required=True,
        metavar="FLOW",
        help="a flow to act on; repeatable, and required",
    )


def progress_flag(parser: argparse.ArgumentParser) -> None:
    """Add `--progress` to `parser`: a JSON line per item, the prose kept apart."""
    parser.add_argument(
        "--progress",
        choices=["json"],
        default=None,
        help="print a JSON line per item's start and end; prose goes to stderr",
    )


@dataclass(frozen=True)
class Reporter:
    """Where a verb's lines go: prose to `out`, or with `progress` JSON to `out`.

    e.g. {"run": "0d4b…_ada", "flow": "summon-anime-wai", "stage": "sheet",
    "state": "done"}
    """

    out: TextIO
    err: TextIO
    progress: bool

    def say(self, line: str) -> None:
        """Print a line meant for a person: on stderr while JSON holds stdout."""
        print(line, file=self.err if self.progress else self.out)

    def item(
        self,
        run: str,
        flow: str | None,
        stage: str,
        state: str,
        message: str | None = None,
        **more: str | int,
    ) -> None:
        """Print one item's `start`, `done` or `refused` line, when asked for JSON.

        `more` adds what the item names beyond its run and flow, as a render its seed.
        A photograph's stage names no flow, and its line carries none.
        """
        if not self.progress:
            return
        line: dict[str, str | int] = {
            "run": run,
            **({} if flow is None else {"flow": flow}),
            "stage": stage,
            "state": state,
            **more,
        }
        if message is not None:
            line["message"] = message
        # Flushed: a job reads this from a pipe, line by line, as it happens.
        print(json.dumps(line), file=self.out, flush=True)


def say(reporter: Reporter, run: Run, verb: str, written: Path | None) -> None:
    """Report what a stage did, including that it was already complete."""
    if written is None:
        reporter.say(f"{run.id}: {verb} is already complete")
    else:
        reporter.say(f"{run.id}: {verb} wrote {written.name}")


def once(read: Callable[[], T]) -> Callable[[], T]:
    """Return `read`, answered at most once: its answer or its refusal is kept.

    A refusal is the build's or the endpoint's, not a photograph's, so meeting
    it again would redo the work to learn nothing. A transient
    transport failure is the exception: it is raised and not kept, since the
    endpoint may answer the next ask, and keeping it would refuse every later
    photograph in the session and spend each one's render budget.
    """
    outcome: list[T | Refusal] = []

    def reading() -> T:
        if not outcome:
            try:
                outcome.append(read())
            except TransportFailure as failed:
                if failed.kind == "transient":
                    raise
                outcome.append(failed)
            except Refusal as refused:
                outcome.append(refused)
        kept = outcome[0]
        if isinstance(kept, Refusal):
            raise kept
        return kept

    return reading


def run_for(identifier: str, wired: Wiring) -> Run:
    """Return the run an argument names: a photograph to open, or a run to resume."""
    named = run_or_photo(identifier, wired)
    return named if isinstance(named, Run) else open_run(named, wired.runs_root)


def run_or_photo(identifier: str, wired: Wiring) -> Run | Path:
    """Return the run an argument names by its id, or the photograph it names.

    A photograph is offered by path and an existing run by its id, and which one
    was meant is decided by what is on disk rather than by a flag.
    """
    directory = wired.runs_root / identifier
    if (directory / FRAME_NAME).is_file():
        return Run(identifier, directory)
    photo = Path(identifier)
    if not photo.is_file():
        raise Refusal(
            f"{identifier!r} is neither a photograph on disk nor a run under "
            f"{wired.runs_root}; give the path to a JPEG or PNG, or the name of "
            f"a run directory under {wired.runs_root}"
        )
    return photo


def require_tracked(names: Sequence[str], wired: Wiring) -> None:
    """Refuse the names that are no tracked flow, naming the flows there are."""
    tracked = tracked_flows(wired.flows_dir)
    unknown = [name for name in names if name not in tracked]
    if unknown:
        raise Refusal(
            f"{', '.join(unknown)}: not a flow this build tracks; the flows it "
            f"carries are {', '.join(tracked) or '(none)'}"
        )


def parse_cells(named: Sequence[str], wired: Wiring) -> list[tuple[str, str]]:
    """Return each cell's run id and flow, refusing a bad cell before any run opens.

    A cell is split at its last `/`, and naming one twice names it once.
    e.g. ["r1/summon-anime-wai"] -> [("r1", "summon-anime-wai")]
    """
    cells: dict[str, tuple[str, str]] = {}
    for cell in named:
        run_id, _, flow = cell.rpartition("/")
        if not run_id or not flow:
            raise Refusal(f"{cell}: not a cell; name one as <run-id>/<flow>")
        cells[cell] = (run_id, flow)
    require_tracked(list(dict.fromkeys(flow for _, flow in cells.values())), wired)
    runs = shlex.quote(str(wired.runs_root))
    for cell, (run_id, flow) in cells.items():
        if not (wired.runs_root / run_id / FRAME_NAME).is_file():
            raise Refusal(
                f"{cell}: no run {run_id} under {wired.runs_root}; run "
                f"`python -m isekai assign --flow {flow} --runs {runs} <photo>` first"
            )
    return list(cells.values())
